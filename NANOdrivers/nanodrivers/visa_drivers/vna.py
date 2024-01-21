from numpy import *
import numpy as np
import nanodrivers.visa_drivers.visa_dev as v
import time
import nanodrivers.visa_drivers.global_settings as gs

global_vna_address = gs.vna_address

def magtodb(mag):
    return 20 * np.log10(mag)  # applied to power measurement


def dbtomag(db):
    return np.pow(10, db/20)  # applied to power measurement


class VNA(v.BaseVisa):
    """Class for Vector Network Analyzer Rohde-Schwarz, ZNB20-2Port operation.
     Args:
         device_num:
             GPIB num (float) or full device address (string)
         form:
             Readout data format:
                0: Magnitude(db)-Phase(radians)
                1: Magnitude(linear)-Phase(radians)
                2: Magnitude(db)-Phase(degrees)
                3: Magnitude(linear)-Phase(degrees)
                4: Real-Imag
                5: Complex

     """
    def __init__(self, device_num=global_vna_address, form=0):
        super().__init__(device_num)
        self.form = form
        self.write('INIT1:CONT OFF')  # single sweep mode
        self.write("CALC1:FORM MLOG")  # set data format to

    def get_data(self):
        """
        Readout in CW mode. After initialisation of the measurements a pause need to be set.
        The pause = sweep time + 0.2 s. Otherwise readout request will come before measurement ends
        """
        self.on()
        self.write("INIT1:IMM")
        time.sleep(0.2 + self.ask_sweep_time())
        data_str = self.query("CALC1:DATA? SDAT")
        data = np.array(data_str.rstrip().split(",")).astype("float64")
        s = data[0::2] + 1j * data[1::2]
        self.off()

        if self.form == 0:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return magtodb(abs(s)), angle(s)
        elif self.form == 1:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return abs(s), angle(s)
        elif self.form == 2:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return magtodb(abs(s)), angle(s)
        elif self.form == 3:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return abs(s), angle(s)
        elif self.form == 4:
            return data[0::2], data[1::2]
        elif self.form == 5:
            return s

    def on(self):
        self.write('OUTP ON')

    def off(self):
        self.write('OUTP OFF')

    def ask_nop(self):
        return self.query_int('SENS1:SWE:POIN?')

    def ask_sweep_time(self):
        return self.query_float('SENS1:SWE:TIME?')

    def set_cw_freq(self, freq):
        """
        Set single frequency point for CW mode in Hz
        """
        self.write(':SENS1:SWE:TYPE CW')   # change to CW mode
        if freq < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            freq = freq*1e9
        self.write('SENS1:FREQ:CW {}'.format(str(freq)))

    def set_freq_start_stop(self, start_fr, stop_fr):
        """
        Set frequency sweep in Hz with start-stop-number_of_points setup
        """

        if start_fr < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            start_fr = start_fr*1e9
        if stop_fr < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            stop_fr = stop_fr*1e9

        self.write('SENS1:FREQ: STAR {}'.format(str(start_fr)))
        self.write('SENS1:FREQ: STOP {}'.format(str(stop_fr)))

    def set_freq_cent_span(self, start_cent, span):
        """
        Set frequency sweep in Hz with start-stop-number_of_points setup
        """

        if start_cent < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            start_cent = start_cent * 1e9
        if span < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            span = span * 1e9

        self.write('SENS1:FREQ: CENT {}'.format(str(start_cent)))
        self.write('SENS1:FREQ: SPAN {}'.format(str(span)))

    def set_power(self, meas_power):
        if meas_power >= 10:
            print('Too high power! Power=10 will be set')
            meas_power = 10
        self.write('SOUR1:POW {}'.format(str(meas_power)))

    def set_band(self, bandwidth):
        """
        Sets bandwidth. Possible values: {1 Hz .. 1MHz}.
        Within the value range, the entered value is rounded up to
        {1, 1.5, 2, 3, 5, 7}·pow(10,n) Hz for (n ≥ 0).
        Values exceeding the maximum bandwidth are rounded down.
        """
        self.write(':SENS1:BAND {}'.format(str(bandwidth)))

    def set_nop(self, nop):
        self.write('SENS1:SWE:POIN {}'.format(str(nop)))

    def cw_meas(self, freq=6e9, meas_power=-10, band=10):
        """
        Full measurements in CW mode
        """
        self.set_band(band)
        self.set_cw_freq(freq)
        self.set_power(meas_power)

        return self.get_data()

    def lin_meas_ss(self, start_fr=4e9, stop_fr=8e9, nop=5000, meas_power=-10, band=10):
        """
        Full measurements in linear mode in start-stop regime
        """
        self.set_freq_start_stop(start_fr, stop_fr)
        self.set_nop(nop)
        self.set_band(band)
        self.set_power(meas_power)

        return self.get_data()

    def lin_meas_cs(self, cent_fr=6e9, span=2e9, nop=5000, meas_power=-10, band=10):
        """
        Full measurements in linear mode in cent-span regime
        """
        self.set_freq_cent_span(cent_fr, span)
        self.set_nop(nop)
        self.set_band(band)
        self.set_power(meas_power)

        return self.get_data()


