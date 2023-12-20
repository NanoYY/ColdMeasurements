import numpy as np
from numpy import *
import os
from ctypes import *

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_loking_address = gs.loking_address
class LOCKING(v.BaseVisa):
    """Class for Stanford_Research_Systems, SR844, Lock-In Amplifier

    Args:
        device_num:
            GPIB num (float) or full device address (string)

    """

    def __int__(self, device_num=global_loking_address):
        super().__int__(device_num)


    def clear(self):
        return self.write('*CLS')


    def get_sensitivity(self):
        return self.query_float('SENS ?')

    def set_sensitivity(self, s):
        """ Function to set sensitivity of Loking input

        Args:
            s: sensitivity, needs to be selected from table
                0: 100 nVrms / -127 dBm
                1: 300 nVrms / -117 dBm
                2: 1 μVrms / -107 dBm
                3: 3 μVrms / -97 dBm
                4: 10 μVrms / -87 dBm
                5: 30 μVrms / -77 dBm
                6: 100 μVrms / -67 dBm
                7: 300 μVrms / -57 dBm
                8: 1 mVrms / -47 dBm
                9: 3 mVrms / -37 dBm
                10: 10 mVrms / -27 dBm
                11: 30 mVrms / -17 dBm
                12: 100 mVrms / -7 dBm
                13: 300 mVrms / +3 dBm
                14: 1 Vrms / +13 dBm

        Returns: info line about current sensitivity

        """
        sensitivity_options = [
            '0: 100 nVrms / -127 dBm',
            '1: 300 nVrms / -117 dBm',
            '2: 1 μVrms / -107 dBm',
            '3: 3 μVrms / -97 dBm',
            '4: 10 μVrms / -87 dBm',
            '5: 30 μVrms / -77 dBm',
            '6: 100 μVrms / -67 dBm',
            '7: 300 μVrms / -57 dBm',
            '8: 1 mVrms / -47 dBm',
            '9: 3 mVrms / -37 dBm',
            '10: 10 mVrms / -27 dBm',
            '11: 30 mVrms / -17 dBm',
            '12: 100 mVrms / -7 dBm',
            '13: 300 mVrms / +3 dBm',
            '14: 1 Vrms / +13 dBm']
        self.query_float('SENS {}'.format(str(s)))
        return sensitivity_options[s]

    def set_auto_sens(self):
        '''

        Returns: Not really reliable. Sets too sensitive rate. Not recommended to use

        '''
        return self.write('AGAN')

    def get_phase(self):
        return self.query_float('PHAS ?')

    def get_ref_impedance(self):
        imp = self.query_int('REFZ ?')
        if imp == 0: return '50 Ohm'
        if imp == 1: return '1 MOhm '

    def get_input_impedance(self):
        imp = self.query_int('INPZ ?')
        if imp == 0: return '50 Ohm'
        if imp == 1: return '1 MOhm '

    def get_time_const(self):
        tconst = self.query_int('OFLT ?')
        if tconst == 0: return '100 mus'
        if tconst == 17: return '30 ks'
        else: return tconst

    def get_X_data(self):
        return self.query_float('OUTP?1')

    def get_Y_data(self):
        return self.query_float('OUTP?2')

    def set_phase(self, pha):
        return self.write('PHAS {}'.format(pha))