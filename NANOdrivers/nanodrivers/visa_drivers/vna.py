from __future__ import (absolute_import, division, print_function)

from numpy import *
import numpy as np
import nanodrivers.visa_drivers.visa_dev as v
import time
import nanodrivers.visa_drivers.global_settings as gs

global_vna_address = gs.vna_address


def magtodb(mag):
    return 20 * np.log10(mag)  # applied to power measurement


def dbtomag(db):
    """
    Function
    Args:
        db:

    Returns:

    """
    return np.pow(10, db / 20)  # applied to power measurement


def get_class_attributes(print_it=False):
    """
    Function returns all class attributes

    Returns: list of all variables globally defined within class

    """
    list_of_att = dict()
    for attribute in VNA.__dict__.keys():
        if attribute[:2] != '__':
            value = getattr(VNA, attribute)
            if not callable(value):
                list_of_att[attribute] = value
                if print_it:
                    print(attribute, '=', value)

    return list_of_att


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
        self.type = None
        self.get_sweep_type()

        self.form = form
        self.write('INIT1:CONT OFF')  # single sweep mode
        self.write("CALC1:FORM MLOG")  # set data format to

        self.cent_freq = None
        self.span = None
        self.star_freq = None
        self.stop_freq = None
        self.cw_freq = None

        self.status = None

        self.nop = None
        self.get_nop()

        self.band = None
        self.get_band()

        self.power = None
        self.get_power()

    def get_instance_attributes(self, print_it=False):
        """
        Function returns all pre-defined class attributes

        Returns: list of all variables defined in class __init__

        """
        list_of_att = dict()
        for attribute, value in self.__dict__.items():
            list_of_att[attribute] = value
            if print_it:
                print(attribute, '=', value)
        return list_of_att

    def sys_help(self):
        """
        Build-in help command

        Args: None
        Returns: Full list of commands available for the device

        """
        return print(self.query('SYSTem:HELP:HEAD?'))

    def get_sweep_type(self):
        self.type = self.query('SENS1:SWE:TYPE?')[:-1]
        return self.type

    def get_data(self):
        """
        Readout in CW mode. After initialisation of the measurements a pause need to be set.
        The pause = sweep time + 0.2 s. Otherwise readout request will come before measurement ends
        """

        self.set_on()
        self.write("INIT1:IMM")
        time.sleep(0.2 + self.get_sweep_time())
        data_str = self.query("CALC1:DATA? SDAT")
        data = np.array(data_str.rstrip().split(",")).astype("float64")
        s = data[0::2] + 1j * data[1::2]
        self.set_off()

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
            return

    def get_sweep_time(self):
        return self.query_float('SENS1:SWE:TIME?')

    def get_power(self):
        self.power = self.query_float('SOUR1:POW?')
        return self.power

    def get_band(self):
        self.band = self.query_float(':SENS1:BAND?')
        return self.band

    def get_nop(self):
        self.nop = int(self.query_float('SENS1:SWE:POIN?'))
        return self.nop

    def get_start_freq(self):
        self.star_freq = self.query_float(':SENS1:FREQ:STAR?')
        return self.star_freq

    def get_stop_freq(self):
        self.stop_freq = self.query_float(':SENS1:FREQ:STOP?')
        return self.stop_freq

    def get_cent_freq(self):
        self.cent_freq = self.query_float(':SENS1:FREQ:CENT?')
        return self.cent_freq

    def get_freq(self):
        """
        Function to get frequency sweep array
        Args: None

        Returns: freq array

        """

        self.star_freq = self.get_start_freq()
        self.stop_freq = self.get_stop_freq()
        self.nop = self.get_nop()
        freq = np.linspace(self.star_freq, self.stop_freq, self.nop)
        return freq

    def get_status(self):
        self.status = self.query_int('OUTP?')
        return self.status

    def set_lin(self):
        self.write('SENS1:SWE:TYPE LIN')
        self.type = self.get_sweep_type()
        return self.type

    def set_cw(self):
        self.write('SENS1:SWE:TYPE CW')
        self.type = self.get_sweep_type()
        return self.type

    def set_on(self):
        self.write('OUTP ON')

    def set_off(self):
        self.write('OUTP OFF')

    def set_cw_freq(self, freq):
        """
        Set single frequency point for CW mode in Hz
        """

        self.write(':SENS1:SWE:TYPE CW')  # change to CW mode
        if freq < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            freq = freq * 1e9
        self.cw_freq = freq
        self.write('SENS1:FREQ:CW {}'.format(str(self.cw_freq)))

    def set_start_freq(self, start_fr):
        self.star_freq = start_fr
        self.write('SENS1:FREQ: STAR {}'.format(str(self.star_freq)))

    def set_stop_freq(self, stop_fr):
        self.stop_freq = stop_fr
        self.write('SENS1:FREQ: STOP {}'.format(str(self.stop_freq)))

    def set_span(self, span):
        self.span = span
        self.write('SENS1:FREQ: SPAN {}'.format(str(self.span)))

    def set_cent_freq(self, cent_fr):
        self.cent_freq = cent_fr
        self.write('SENS1:FREQ: CENT {}'.format(str(self.cent_freq)))

    def set_freq_start_stop(self, start_fr, stop_fr, nop):
        """
        Set frequency sweep in Hz with start-stop-number_of_points setup
        """

        if start_fr < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            start_fr = start_fr * 1e9
        if stop_fr < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            stop_fr = stop_fr * 1e9

        self.star_freq = start_fr
        self.stop_freq = stop_fr
        self.nop = nop

        self.set_nop(self.nop)
        self.set_start_freq(self.star_freq)
        self.set_stop_freq(self.stop_freq)

    def set_freq_cent_span(self, cent_fr, span, nop):
        """
        Set frequency sweep in Hz with start-stop-number_of_points setup
        """

        if start_cent < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            start_cent = cent_fr * 1e9
        if span < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            span = span * 1e9

        self.cent_freq = cent_fr
        self.span = span
        self.nop = nop

        self.set_nop(self.nop)
        self.set_cent_freq(self.star_freq)
        self.set_span(self.stop_freq)

    def set_power(self, meas_power):
        if meas_power >= 10:
            print('Too high power! Power=10 will be set')
            meas_power = 10
        self.power = meas_power
        self.write('SOUR1:POW {}'.format(str(self.power)))

    def set_band(self, bandwidth):
        """
        Sets bandwidth. Possible values: {1 Hz .. 1MHz}.
        Within the value range, the entered value is rounded up to
        {1, 1.5, 2, 3, 5, 7}·pow(10,n) Hz for (n ≥ 0).
        Values exceeding the maximum bandwidth are rounded down.
        """
        self.band = bandwidth
        self.write(':SENS1:BAND {}'.format(str(self.band)))

    def set_nop(self, nop):
        self.nop = nop
        self.write('SENS1:SWE:POIN {}'.format(str(self.nop)))

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
