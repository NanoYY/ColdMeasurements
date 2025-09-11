from __future__ import (absolute_import, division, print_function)

from numpy import *
import numpy as np
import pyvisa
import time

import nanodrivers.visa_drivers.visa_dev as v
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
    Function returns VNA class attributes.
    Args:
        print_it: If True, prints class_attributes. Default: False
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
    """
    Class for Vector Network Analyzer Rohde-Schwarz, ZNB20-2Port operation.
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

        self.type = nan
        self.get_sweep_type()
        self.ref_source = None
        self.get_ref_source()

        self.form = form
        self.write('INIT1:CONT OFF')  # single sweep mode
        self.write("CALC1:FORM MLOG")  # set data format to

        self.cent_freq = nan
        self.span = nan
        self.star_freq = nan
        self.stop_freq = nan
        self.cw_freq = nan
        self.freq = nan

        if self.type == 'LIN':
            self.get_cent_freq()
            self.get_stop_freq()
            self.get_start_freq()
            self.get_span()
            self.get_freq()

        self.elength = nan
        self.get_elength()

        self.status_output = nan
        self.get_status()

        self.nop = nan
        self.get_nop()

        self.band = nan
        self.get_band()

        self.power = nan
        self.get_power()
        #
        self.write('SENSe1:AVERage:STATe 0')  # sets averaging of output off
        self.avg_status = nan
        self.get_avg_status()

        self.avgs = nan
        self.set_avgs(1) # sets averaging number to 1

    def dump(self, print_it=False):
        """
        Function returns all pre-defined class attributes
        (all variables used in the code with the latest value read)
        Args:
            print_it: If True, prints class_attributes. Default: False
        Returns: list of all variables defined in class __init__

        """
        list_of_att = dict()
        for attribute, value in self.__dict__.items():
            list_of_att[attribute] = value
            if print_it:
                print(attribute, '=', value)
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument or \
                    type(value) == pyvisa.resources.gpib.GPIBInstrument:
                list_of_att[attribute] = str(value)
        return list_of_att

    def sys_help(self):
        """
        Build-in help command

        Args: None
        Returns: Full list of commands available for the device

        """
        return print(self.query('SYSTem:HELP:HEAD?'))

    def get_sweep_type(self):
        """
        Function to get sweep type
        Returns: LINear | LOGarithmic | POWer | CW | POINt | SEGMent

        """
        self.type = self.query('SENS1:SWE:TYPE?')[:-1]
        return self.type

    def get_ref_source(self):
        self.ref_source = self.query('SENSe1:ROSCillator:SOURce?')[:-1]
        return self.ref_source

    def get_elength(self):
        """
        Defines the offset parameter for test port 1 as an electrical length
        Returns:electrical length in m

        """

        self.elength = float(self.query('SENSe1:CORRection:EDELay1:ELENgth?')[:-1])
        return self.elength

    def get_avg_status(self):
        """
        Query sweep average.
        Returns: 0 - off, 1 - on

        """
        self.avg_status = int(self.query('SENSe1:AVERage:STATe?')[:-1])
        return self.avg_status

    def get_avgs(self):
        """
        Queries the number of consecutive sweeps to be combined for the sweep average
        Returns: averages

        """
        self.avgs = self.query('SENSe1:AVERage:COUNt?')
        return self.avgs

    def get_data(self, freq = False):
        """
        Readout in any mode. After initialisation of the measurements a pause need to be set.
        The pause = sweep time + 0.2 s.
        Otherwise, readout request will come before measurement ends.

        Args:
            freq: returns freq if True

        Returns: data in specified form

        """

        self.set_on()
        self.write("INIT1:IMM")
        time.sleep(0.2 + self.get_sweep_time()*1.1)
        data_str = self.query("CALC1:DATA? SDAT")
        data = np.array(data_str.rstrip().split(",")).astype("float64")
        s = data[0::2] + 1j * data[1::2]
        self.set_off()

        if self.form == 0:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return_1 = magtodb(abs(s))
            return_2 = angle(s)

        elif self.form == 1:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return_1 = abs(s)
            return_2 = angle(s)
        elif self.form == 2:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return_1 = magtodb(abs(s))
            return_2 = angle(s)
            return magtodb(abs(s)), angle(s)
        elif self.form == 3:
            # print('WARNING: CHECK ANGLE (rad or deg)!')
            return_1 = abs(s)
            return_2 = angle(s)

        elif self.form == 4:
            return_1 = data[0::2]
            return_2 = data[1::2]

        if freq:
            return return_1, return_2, self.get_freq()
        else:
            return return_1, return_2



    def get_sweep_time(self):
        """
        Function to get estimated time for one full sweep
        Returns: sweep time in seconds

        """
        return self.query_float('SENS1:SWE:TIME?')

    def get_power(self):
        """
        Function to get output power
        Returns: output power in db

        """
        self.power = self.query_float('SOUR1:POW?')
        return self.power

    def get_band(self):
        """
        Function to get bandwidth
        Returns: bandwidth in Hz

        """
        self.band = self.query_float(':SENS1:BAND?')
        return self.band

    def get_nop(self):
        """
        Function to get number of points
        Returns: number of points

        """
        self.nop = int(self.query_float('SENS1:SWE:POIN?'))
        return self.nop

    def get_start_freq(self):
        """
        Function to get start frequency in the linear sweep regime
        Returns: start frequency in Hz

        """
        self.star_freq = self.query_float(':SENS1:FREQ:STAR?')
        return self.star_freq

    def get_stop_freq(self):
        """
        Function to get stop frequency in the linear sweep regime
        Returns: stop frequency in Hz

        """
        self.stop_freq = self.query_float(':SENS1:FREQ:STOP?')
        return self.stop_freq

    def get_cent_freq(self):
        """
        Function to get center frequency in the linear sweep regime
        Returns: center frequency in Hz

        """
        self.cent_freq = self.query_float(':SENS1:FREQ:CENT?')
        return self.cent_freq

    def get_span(self):
        """
       Function to get frequency span in the linear sweep regime
       Returns: span in Hz

       """
        self.span = float(self.query('SENS1:FREQ:SPAN?')[:-1])
        return self.span

    def get_freq(self):
        """
        Function to get frequency sweep array in linear regime

        Returns: freq array

        """

        self.star_freq = self.get_start_freq()
        self.stop_freq = self.get_stop_freq()
        self.nop = self.get_nop()
        self.freq = np.linspace(self.star_freq, self.stop_freq, self.nop)
        return self.freq

    def get_status(self):
        """
        Function to get status of output power (on/off)
        Returns: o - off, 1 - on

        """
        self.status_output = int(self.query('OUTP?')[:-1])
        return self.status_output

    def set_elength(self, elength=0):
        """
        Defines the offset parameter for test port 1 as an electrical length

        Args:
            elength: elength in m

        Returns: None

        """
        self.elength = elength
        self.write('SENSe1:CORRection:EDELay1:ELENgth {}'.format(str(self.elength)))

    def set_avgs(self, factor=1):
        """
        Defines the number of consecutive sweeps to be combined for the sweep average

        Args:
            factor: number of averages

        Returns: None

        """

        self.avgs = factor
        self.write('SENSe1:AVERage:COUNt {}'.format(str(self.avgs)))

    def set_lin(self):
        """
        Sets measurement mode to Linear.
        Returns: None

        """
        self.write('SENS1:SWE:TYPE LIN')
        self.type = self.get_sweep_type()

    def set_cw(self):
        """
        Sets measurement mode to CW.
        Returns: None

        """
        self.write('SENS1:SWE:TYPE POIN')
        self.type = self.get_sweep_type()

    def set_on(self):
        """
        Function turns ON output power
        Returns: None

        """
        self.write('OUTP ON')

    def set_off(self):
        """
        Function turns OFF output power
        Returns: None

        """
        self.write('OUTP OFF')

    def set_cw_freq(self, freq):
        """
        Set single frequency point for CW mode in Hz
        """

        self.set_cw()  # change to CW mode
        if freq < 100:
            print("Warning: probably frequency range is GHz, but Hz needed. Frequency will be converted to Hz")
            freq = freq * 1e9
        self.cw_freq = freq
        self.write('SENS1:FREQ:CW {}'.format(str(self.cw_freq)))

    def set_start_freq(self, start_fr):
        self.star_freq = start_fr
        self.write('SENS1:FREQ:STAR {}'.format(str(self.star_freq)))

    def set_stop_freq(self, stop_fr):
        self.stop_freq = stop_fr
        self.write('SENS1:FREQ:STOP {}'.format(str(self.stop_freq)))

    def set_span(self, span):
        self.span = span
        self.write('SENS1:FREQ:SPAN {}'.format(str(self.span)))

    def set_cent_freq(self, cent_fr):
        self.cent_freq = cent_fr
        self.write('SENS1:FREQ:CENT {}'.format(str(self.cent_freq)))

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
        if meas_power >= 15:
            print('Too high power! Power=10 will be set')
            meas_power = 15
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
        self.set_freq_start_stop(start_fr, stop_fr, nop)
        self.set_nop(nop)
        self.set_band(band)
        self.set_power(meas_power)

        return self.get_data()

    def lin_meas_cs(self, cent_fr=6e9, span=2e9, nop=5000, meas_power=-10, band=10):
        """
        Full measurements in linear mode in cent-span regime
        """
        self.set_freq_cent_span(cent_fr, span, nop)
        self.set_nop(nop)
        self.set_band(band)
        self.set_power(meas_power)

        return self.get_data()