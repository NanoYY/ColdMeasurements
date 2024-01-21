import time
import numpy as np
from numpy import *
import os
from ctypes import *

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_dSA_address = gs.din_SA_address


class Din_SA(v.BaseVisa):
    """ Class for Stanford_Research_Systems, SR785, Dynamic Signal Analyzer
    NOTE: This device might need termination character '\\n' (new line) to be added to the end of the command.
    If it is not added an error 'Timeout expired before operation completed.'

    Args:
        device_num:
            GPIB num (float) or full device address (string)
        termination_char:
            Should be "new line" for some commands

    """

    def __int__(self, device_num=global_dSA_address):
        super().__int__(device_num)

    def idn(self):
        """
        Base Visa command queries *IDN?.

        Returns: Name of the device if connection exist

        """
        try:
            print("Connection exist:", self.query('*IDN?\n'))
        except:
            self.__error_message()


    def start(self):
        self.write('STRT')

    def GPIB_output(self):
        self.write('OUTX 0')

    def get_freq(self, lines=100, d=0):
        self.write('*CLS')
        max_freq = float(self.query('FSPN? {}'.format(int(d))))
        min_freq = float(self.query('FSTR? {}'.format(int(d))))
        fr = np.linspace(min_freq, max_freq, lines)
        return fr

    def read_d(self, avg=1, d=0):
        self.write('*CLS')

        def read_c():
            self.start()
            self.GPIB_output()
            time.sleep(8 + 0.5)
            read_s = self.query('DSPY? {}'.format(int(d)))
            rear_f = np.array(read_s.split(','), dtype=float)
            return rear_f

        fft_0 = read_c()
        for i in range(avg - 1):
            fft_0 += read_c()

        fft_0 = fft_0 / avg

        return fft_0[:-1]
