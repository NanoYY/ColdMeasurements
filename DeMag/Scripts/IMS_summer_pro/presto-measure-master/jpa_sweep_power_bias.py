# -*- coding: utf-8 -*-
"""
3D sweep of pump power, DC bias and frequency of probe, to see where we get gain.
"""

import math
from typing import List, Optional, Union

import h5py
import numpy as np
import numpy.typing as npt

from presto import lockin
from presto.utils import ProgressBar

from _base import Base


class JpaSweepPowerBias(Base):
    def __init__(
        self,
        freq_center: float,
        freq_span: float,
        df: float,
        num_averages: int,
        amp: float,
        bias_arr: Union[List[float], npt.NDArray[np.float64]],
        pump_pwr_arr: Union[List[int], npt.NDArray[np.int64]],
        output_port: int,
        input_port: int,
        bias_port: int,
        pump_port: int,
        pump_freq: Optional[float] = None,
        dither: bool = True,
        num_skip: int = 0,
    ) -> None:
        self.freq_center = freq_center
        self.freq_span = freq_span
        self.df = df  # modified after tuning
        self.num_averages = num_averages
        self.amp = amp
        self.bias_arr = np.atleast_1d(bias_arr).astype(np.float64)
        self.pump_pwr_arr = np.atleast_1d(pump_pwr_arr).astype(np.int64)
        self.output_port = output_port
        self.input_port = input_port
        self.bias_port = bias_port
        self.pump_port = pump_port
        self.pump_freq = 2 * self.freq_center if pump_freq is None else pump_freq
        self.dither = dither
        self.num_skip = num_skip

        self.freq_arr = None  # replaced by run
        self.ref_resp_arr = None  # replaced by run
        self.ref_pwr_arr = None  # replaced by run
        self.resp_arr = None  # replaced by run
        self.pwr_arr = None  # replaced by run

    def run(
        self,
        presto_address: str,
        presto_port: Optional[int] = None,
        ext_ref_clk: bool = False,
    ) -> str:
        with lockin.Lockin(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **self.DC_PARAMS,
        ) as lck:
            lck.hardware.set_adc_attenuation(self.input_port, self.ADC_ATTENUATION)
            lck.hardware.set_dac_current(self.output_port, self.DAC_CURRENT)
            lck.hardware.set_inv_sinc(self.output_port, 0)

            nr_bias = len(self.bias_arr)
            nr_pump_pwr = len(self.pump_pwr_arr)
            _, self.df = lck.tune(0.0, self.df)

            f_start = self.freq_center - self.freq_span / 2
            f_stop = self.freq_center + self.freq_span / 2
            n_start = int(round(f_start / self.df))
            n_stop = int(round(f_stop / self.df))
            n_arr = np.arange(n_start, n_stop + 1)
            nr_freq = len(n_arr)
            self.freq_arr = self.df * n_arr

            self.ref_resp_arr = np.zeros((nr_bias, nr_freq), np.complex128)
            self.ref_pwr_arr = np.zeros((nr_bias, nr_freq), np.float64)
            self.resp_arr = np.zeros((nr_pump_pwr, nr_bias, nr_freq), np.complex128)
            self.pwr_arr = np.zeros((nr_pump_pwr, nr_bias, nr_freq), np.float64)

            lck.hardware.set_lmx(0.0, 0, self.pump_port)  # start with pump off for reference
            lck.hardware.set_dc_bias(self.bias_arr[0], self.bias_port)
            lck.hardware.sleep(0.1, False)

            lck.hardware.configure_mixer(
                freq=self.freq_arr[0],
                in_ports=self.input_port,
                out_ports=self.output_port,
            )
            lck.set_df(self.df)
            og = lck.add_output_group(self.output_port, 1)
            og.set_frequencies(0.0)
            og.set_amplitudes(self.amp)
            og.set_phases(0.0, 0.0)

            lck.set_dither(self.dither, self.output_port)
            ig = lck.add_input_group(self.input_port, 1)
            ig.set_frequencies(0.0)

            lck.apply_settings()

            pb = ProgressBar((nr_pump_pwr + 1) * nr_bias * nr_freq)
            pb.start()
            for kk, pump_pwr in enumerate(np.r_[-1, self.pump_pwr_arr]):
                if kk == 0:
                    lck.hardware.set_lmx(0.0, 0, self.pump_port)
                else:
                    lck.hardware.set_lmx(self.pump_freq, pump_pwr, self.pump_port)
                lck.hardware.sleep(0.1, False)
                for jj, bias in enumerate(self.bias_arr):
                    lck.hardware.set_dc_bias(bias, self.bias_port)
                    lck.hardware.sleep(0.1, False)

                    _d = lck.sweep_nco(
                        input_port=self.input_port,
                        input_freqs=self.freq_arr,
                        output_port=self.output_port,
                        output_freqs=self.freq_arr,
                        nr_averages=self.num_averages,
                        status_callback=pb.increment,
                    )
                    data_i = _d[self.input_port][1][:, 0]
                    data_q = _d[self.input_port][2][:, 0]
                    data = data_i.real + 1j * data_q.real  # using zero IF
                    if kk == 0:
                        self.ref_resp_arr[jj, :] = data
                    else:
                        self.resp_arr[kk - 1, jj, :] = data

            pb.done()

            # Mute outputs at the end of the sweep
            og.set_amplitudes(0.0)
            lck.apply_settings()
            lck.hardware.set_dc_bias(0.0, self.bias_port)
            lck.hardware.set_lmx(0.0, 0, self.pump_port)

        return self.save()

    def save(self, save_filename: Optional[str] = None) -> str:
        return super()._save(__file__, save_filename=save_filename)

    @classmethod
    def load(cls, load_filename: str) -> "JpaSweepPowerBias":
        with h5py.File(load_filename, "r") as h5f:
            freq_center = float(h5f.attrs["freq_center"])  # type: ignore
            freq_span = float(h5f.attrs["freq_span"])  # type: ignore
            df = float(h5f.attrs["df"])  # type: ignore
            num_averages = int(h5f.attrs["num_averages"])  # type: ignore
            amp = float(h5f.attrs["amp"])  # type: ignore
            output_port = int(h5f.attrs["output_port"])  # type: ignore
            input_port = int(h5f.attrs["input_port"])  # type: ignore
            bias_port = int(h5f.attrs["bias_port"])  # type: ignore
            pump_port = int(h5f.attrs["pump_port"])  # type: ignore
            pump_freq = float(h5f.attrs["pump_freq"])  # type: ignore
            dither = bool(h5f.attrs["dither"])  # type: ignore
            num_skip = int(h5f.attrs["num_skip"])  # type: ignore

            bias_arr: npt.NDArray[np.float64] = h5f["bias_arr"][()]  # type: ignore
            pump_pwr_arr: npt.NDArray[np.int64] = h5f["pump_pwr_arr"][()]  # type: ignore
            freq_arr: npt.NDArray[np.float64] = h5f["freq_arr"][()]  # type: ignore
            ref_resp_arr: npt.NDArray[np.complex128] = h5f["ref_resp_arr"][()]  # type: ignore
            ref_pwr_arr: npt.NDArray[np.float64] = h5f["ref_pwr_arr"][()]  # type: ignore
            resp_arr: npt.NDArray[np.complex128] = h5f["resp_arr"][()]  # type: ignore
            pwr_arr: npt.NDArray[np.float64] = h5f["pwr_arr"][()]  # type: ignore

        self = cls(
            freq_center=freq_center,
            freq_span=freq_span,
            df=df,
            num_averages=num_averages,
            amp=amp,
            bias_arr=bias_arr,
            pump_pwr_arr=pump_pwr_arr,
            output_port=output_port,
            input_port=input_port,
            bias_port=bias_port,
            pump_port=pump_port,
            pump_freq=pump_freq,
            dither=dither,
            num_skip=num_skip,
        )
        self.freq_arr = freq_arr
        self.ref_resp_arr = ref_resp_arr
        self.ref_pwr_arr = ref_pwr_arr
        self.resp_arr = resp_arr
        self.pwr_arr = pwr_arr

        return self

    def analyze(self, quantity: str = "signal", marker_freq: Optional[float] = None):
        assert self.freq_arr is not None
        assert self.ref_resp_arr is not None
        assert self.ref_pwr_arr is not None
        assert self.resp_arr is not None
        assert self.pwr_arr is not None

        import matplotlib.pyplot as plt

        nr_pump_pwr = len(self.pump_pwr_arr)
        nr_bias = len(self.bias_arr)

        if quantity == "power":
            print("using power")
            ref_arr = self.ref_pwr_arr
            resp_arr = self.pwr_arr
            ref_db = 10 * np.log10(ref_arr)
            data_db = 10 * np.log10(resp_arr)
        elif quantity == "signal":
            print("using signal")
            ref_arr = self.ref_resp_arr
            resp_arr = self.resp_arr
            ref_db = 20 * np.log10(np.abs(ref_arr))
            data_db = 20 * np.log10(np.abs(resp_arr))
        else:
            raise ValueError

        gain_db = np.zeros_like(data_db)
        for pp in range(nr_pump_pwr):
            for bb in range(nr_bias):
                gain_db[pp, bb, :] = data_db[pp, bb, :] - ref_db[bb, :]

        # choose limits for colorbar
        cutoff = 1.0  # %
        lowlim = np.percentile(gain_db, cutoff)
        highlim = np.percentile(gain_db, 100.0 - cutoff)
        abslim = max(abs(lowlim), abs(highlim))

        # extent
        x_min = 1e-9 * self.freq_arr[0]
        x_max = 1e-9 * self.freq_arr[-1]
        dx = 1e-9 * (self.freq_arr[1] - self.freq_arr[0])
        y_min = self.bias_arr[0]
        y_max = self.bias_arr[-1]
        dy = self.bias_arr[1] - self.bias_arr[0]

        ret_fig = []
        if nr_pump_pwr == 1:
            fig, ax = plt.subplots(tight_layout=True)
            im = ax.imshow(
                gain_db[0, :, :],
                origin="lower",
                aspect="auto",
                extent=(x_min - dx / 2, x_max + dx / 2, y_min - dy / 2, y_max + dy / 2),
                vmin=-abslim,
                vmax=abslim,
                cmap="RdBu_r",
            )
            ax.set_title(f"Pump power {self.pump_pwr_arr[0]}")
            ax.set_xlabel("Frequency [GHz]")
            ax.set_ylabel("DC bias [V]")
            cb = fig.colorbar(im)
            cb.set_label("Gain [dB]")
            if marker_freq is not None:
                ax.axvline(marker_freq / 1e9, color="tab:gray", alpha=0.2)
            fig.show()
            ret_fig.append(fig)
        else:
            nr_rows = 3
            nr_columns = 4
            nr_plots = nr_rows * nr_columns
            nr_figs = math.ceil(nr_pump_pwr / nr_plots)

            for jj in range(nr_figs):
                fig, ax = plt.subplots(
                    nr_rows, nr_columns, sharex=True, sharey=True, tight_layout=True
                )
                for ii in range(nr_plots):
                    idx = jj * nr_plots + ii
                    if idx >= nr_pump_pwr:
                        break
                    _ax = ax[ii // nr_columns][ii % nr_columns]
                    _ax.imshow(
                        gain_db[idx, :, :],
                        origin="lower",
                        aspect="auto",
                        extent=(x_min - dx / 2, x_max + dx / 2, y_min - dy / 2, y_max + dy / 2),
                        vmin=-abslim,
                        vmax=abslim,
                        cmap="RdBu_r",
                    )
                    _ax.set_title(str(self.pump_pwr_arr[jj * nr_plots + ii]))
                    if marker_freq is not None:
                        _ax.axvline(marker_freq / 1e9, color="tab:gray", alpha=0.2)
                fig.show()
                ret_fig.append(fig)

        return ret_fig
