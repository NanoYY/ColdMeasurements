# -*- coding: utf-8 -*-
"""Measure the energy-relaxation time T1."""
import ast
from typing import List, Optional

import h5py
import numpy as np

#time
from datetime import datetime, timedelta
import time

#matlab import
import scipy.io
from scipy.io import savemat
import pyvisa

from anaconda_navigator.utils.url_utils import file_name

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import pulsed
from presto.utils import format_precision, rotate_opt, sin2

from ._base import Base, project

DAC_CURRENT = 40_500  # uA
CONVERTER_CONFIGURATION = {
    "adc_mode": AdcMode.Mixed,
    "adc_fsample": AdcFSample.G2,
    "dac_mode": [DacMode.Mixed42, DacMode.Mixed02, DacMode.Mixed02, DacMode.Mixed02],
    # "dac_mode": DacMode.Mixed,
    "dac_fsample": [DacFSample.G10, DacFSample.G6, DacFSample.G6, DacFSample.G6],
}
IDX_LOW = 1_500
IDX_HIGH = 2_000


# def gate(t, start, stop):
#     return np.heaviside(t - start, 1) - np.heaviside(t - stop, 1)
#
#
# def gaussian(x, cent, sig):
#     return np.exp(-np.power((x - cent) / sig, 2.0) / 2)
#
#
# def sin2(number_of_samples, start=1, stop=9, sig_feft=0.2, sig_right=0.2):
#     t = np.linspace(0, 10, number_of_samples)
#     return gate(t, start, stop) + gaussian(t, cent=start, sig=sig_feft) * (1 - np.heaviside(t - start, 1)) + gaussian(t, cent=stop, sig=sig_right) * (np.heaviside(t - stop, 1))

def gate(t, start, stop):
    return np.heaviside(t - start, 1) - np.heaviside(t - stop, 1)


def gaussian(t, cent, sig, start, end):
    Result = np.zeros(int(t[-1]))
    Result[start:end] = np.exp(-np.power((t[start:end] - cent) / sig, 2.0) / 2)
    return Result

def Gauss(nr_samples,edge,sig_left=2,sig_right=0.001):
    t = np.linspace(1, nr_samples, nr_samples, endpoint=True)
    Left = gaussian(t, edge, sig_left, 0, edge)
    Middle = gate(t, edge+1, t[-edge])
    Right = gaussian(t, int(t[-edge]), sig_right,int(t[-edge-1]),int(t[-1]))
    return Left + Middle + Right

class T1(Base):
    def __init__(
        self,
        LO_port: int,
        IF_port: int,
        Readout_port: int,

        LO_freq: float,
        IF_freq: float,
        LO_amp: float,
        IF_amp: float,
        LO_duration: float,
        IF_duration: float,
        Readout_duration: float,
        delay: float,

        wait_delay: float,
        LO_sample_delay: float,
        num_averages: int,

        envelope_function = None,  # function

        drag: float = 0.0,
        save_: bool = False,
        file_folder = str,
        file_name = 'Pulse_test',



    ) -> None:
        self.LO_port = LO_port
        self.IF_port = IF_port
        self.Readout_port = Readout_port

        self.LO_freq = LO_freq
        self.IF_freq = IF_freq
        self.LO_amp = LO_amp
        self.IF_amp = IF_amp
        self.LO_duration = LO_duration
        self.IF_duration = IF_duration
        self.Readout_duration = Readout_duration
        self.num_averages = num_averages
        self.drag = drag

        self.delay =  np.atleast_1d(delay).astype(np.float64)              # if a single float is passed,
        self.wait_delay = np.atleast_1d(wait_delay).astype(np.float64)     # it's converted into a single-element array
        self.LO_sample_delay = np.atleast_1d(LO_sample_delay).astype(np.float64)


        self.t_arr = None  # replaced by run
        self.data = None  # replaced by run

        self.save_ = save_
        self.file_name = str(file_name)
        self.file_folder = str(file_folder)

        # Get the DAC sampling rate (for example)
        dac_sampling_rate = 1e9  # Placeholder value, replace with actual sampling rate
        num_samples = int(round(self.IF_duration * dac_sampling_rate))

        if envelope_function is not None:
            self.IF_envelope_function = envelope_function(num_samples, self.drag)
        else:
            self.IF_envelope_function = sin2(num_samples, self.drag)


    # @staticmethod
    # def control_envelope_func(control_ns, drag):
    #     return self.control_envelope(control_ns, drag=drag)

    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
    ) -> str:
        # Instantiate interface class
        with pulsed.Pulsed(
                address=presto_address,
                port=presto_port,
                ext_ref_clk=ext_ref_clk,
                **CONVERTER_CONFIGURATION,
        ) as pls:
            assert pls.hardware is not None

            pls.hardware.set_adc_attenuation(self.Readout_port, 0.0)  # readout signal goes to here
            pls.hardware.set_dac_current(self.LO_port, DAC_CURRENT)       # readout signal goes from here
            pls.hardware.set_dac_current(self.IF_port, DAC_CURRENT)       # control of sample / pump port
            pls.hardware.set_inv_sinc(self.LO_port, 2)              # compensate the bandwidth limitations introduced by DAC
            pls.hardware.set_inv_sinc(self.IF_port, 2)
            pls.hardware.configure_mixer(
                freq=self.LO_freq,
                in_ports=self.Readout_port,
                out_ports=self.LO_port,
                sync=False,  # sync in next call
            )
            pls.hardware.configure_mixer(
                freq=self.IF_freq,
                out_ports=self.IF_port,
                sync=True,  # sync here
            )

            # ************************************
            # *** Setup measurement parameters ***
            # ************************************

            # Setup lookup tables for frequencies
            # we only need to use carrier 1
            pls.setup_freq_lut(
                output_ports=self.LO_port,
                group=0,
                frequencies=0.0,
                phases=0.0,
                phases_q=0.0,
            )
            pls.setup_freq_lut(
                output_ports=self.IF_port,
                group=0,
                frequencies=0.0,
                phases=0.0,
                phases_q=0.0,
            )

            # Setup lookup tables for amplitudes
            pls.setup_scale_lut(
                output_ports=self.LO_port,
                group=0,
                scales=self.LO_amp,
            )

            pls.setup_scale_lut(
                output_ports=self.IF_port,
                group=0,
                scales=self.IF_amp,
            )

            # Setup readout and control pulses
            # use setup_long_drive to create a pulse with square envelope
            # setup_long_drive supports smooth rise and fall transitions for the pulse,
            # but we keep it simple here
            LO_pulse = pls.setup_long_drive(
                output_port=self.LO_port,
                group=0,
                duration=self.LO_duration,
                amplitude=1.0,
                amplitude_q=1.0,
                rise_time=0e-9,
                fall_time=0e-9,
            )
            IF_ns = int(round(self.IF_duration *
                                   pls.get_fs("dac")))  # number of samples in the control template

            # IF_envelope = self.IF_envelope_function(IF_ns, drag=self.drag)
            # print(IF_envelope_function.type)

            IF_pulse = pls.setup_template(
                output_port=self.IF_port,
                group=0,
                template=self.IF_envelope_function,
                template_q=self.IF_envelope_function if self.drag == 0.0 else None,
                envelope=True,
            )

            # Setup sampling window
            pls.set_store_ports(self.Readout_port)
            pls.set_store_duration(self.Readout_duration)

            # ******************************
            # *** Program pulse sequence ***
            # ******************************

            T = 0.0  # s, start at time zero ...

            pls.store(T + self.LO_sample_delay)

            pls.reset_phase(T, self.LO_port)  # set phase to 0 at given time
            pls.output_pulse(T, LO_pulse)
            T += self.delay

            pls.reset_phase(T, self.IF_port)
            pls.output_pulse(T, IF_pulse)
            # T += self.control_duration
            # increasing delay
            T += self.delay
            # Readout

            T += self.LO_duration
            # Wait for decay
            T += self.wait_delay

            pls.run(
                period=T,
                repeat_count=1,
                num_averages=self.num_averages,
                print_time=False,
            )
            self.t_arr, self.data = pls.get_store_data()

        list_of_att = dict()
        for attribute, value in self.__dict__.items():  # will save all variable wich startes with self.
            list_of_att[attribute] = value
            # print(attribute, '=', value) # will print all saved attributes of the class
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument:
                list_of_att[attribute] = str(value)

        if self.save_:
            now = datetime.now()
            full_file_name = self.file_folder + '\\' + self.file_name + now.strftime(r'--%Y.%m.%d__%H.%M.%S') + '.mat'
            savemat(full_file_name, list_of_att)
            print('Data is saved to ', full_file_name)
            return list_of_att

        else:
            print('Run finished')
            return list_of_att


