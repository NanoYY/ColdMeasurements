from numpy import *
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
        self.write('FREQ:CENT {}'.format(str(freq)))

    def set_span(self, span):
        self.write('FREQ:SPAN {}'.format(str(span)))

    def set_band_kHz(self, band):
        self.write('BAND {}KHZ'.format(str(band)))

    def set_band_Hz(self, band):
        self.write('BAND {}HZ'.format(str(band)))

    def set_nop(self, nop):
        """ Sets number of points

        Args:
            nop: number of points. max 10001

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
        raw_data = self.query_str('TRAC? TRAC1')
        data = np.array(raw_data.split(','), dtype=float)
        return data