from numpy import *
import numpy as np
import time
import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_sa_address = gs.sa_address


class Anri(v.BaseVisa):
    """Class for ANRITSU MS2830A signal analyzer
     Args:
         device_num:
             GPIB num (float) or full device address (string)
     """

    def __init__(self, device_num=global_sa_address):
        super().__init__(device_num)  # initialise device with the init of parent class VisaDevice
        self.write(r':SYST:COMM:LAN:RTMO {}'.format(str(1)))  # reconnect timeout in seconds

    def set_cent_freq(self, freq):
        """
        Function to set center frequency
        Args:
            freq: in Hz

        Returns: None

        """
        self.write('FREQ:CENT {}'.format(str(freq)))

    def set_span(self, span):
        """
        Function to set frequency span
        Args:
            span: in Hz

        Returns: None

        """
        self.write('FREQ:SPAN {}'.format(str(span)))

    def set_band_kHz(self, band):
        """
        Function to set frequency span
        Args:
            band: in kHz

        Returns: None

        """
        self.write('BAND {}KHZ'.format(str(band)))

    def set_band_Hz(self, band):
        """
        Function to set frequency span
        Args:
            band: in Hz

        Returns: None

        """
        self.write('BAND {}HZ'.format(str(band)))

    def set_nop(self, nop):
        """ Sets number of points

        Args:
            nop: max 10001

        Returns: None

        ''"""
        self.write('SWEep:POINts {}'.format(str(nop)))

    def get_nop(self):
        return self.query_int('SWEep:POINts?')

    def get_sweep_time(self):
        return self.query_float('SWEep:TIME?')

    def sweep_mode_cont(self):
        self.write('INIT:MODE:CONT')

    def sweep_mode_sing(self):
        self.write('INIT:MODE:SING')

    def get_data(self):
        self.write('INIT:IMM')
        time.sleep(20 + self.get_sweep_time())
        raw_data = self.query('TRAC? TRAC1')
        data = np.array(raw_data.split(','), dtype=float)
        return data
