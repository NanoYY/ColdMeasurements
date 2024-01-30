import numpy as np
from numpy import *
from ctypes import *
import pyvisa

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_lokin_address = gs.loking_address


def get_class_attributes(print_it=False):
    """
    Function returns all class attributes

    Returns: list of all variables globally defined within class

    """
    list_of_att = dict()
    for attribute in LOCKIN.__dict__.keys():
        if attribute[:2] != '__':
            value = getattr(LOCKIN, attribute)
            if not callable(value):
                list_of_att[attribute] = value
                if print_it:
                    print(attribute, '=', value)

    return list_of_att


class LOCKIN(v.BaseVisa):
    """
    Class for Stanford_Research_Systems, SR844, Lock-In Amplifier

    Args:
        device_num:
            GPIB num (float) or full device address (string)

    """

    def __init__(self, device_address=global_lokin_address):
        super().__init__(device_address)

        # Base params
        self.sensitivity = None
        self.get_sensitivity()

        self.ref_impedance = None
        self.get_ref_impedance()

        self.input_impedance = None
        self.get_input_impedance()

        self.time_const = None
        self.get_time_const()

        # Meas params
        self.phase = None
        self.get_phase()

    def dump(self, print_it=False):
        """
        Function returns all pre-defined class attributes
        (all variables used in the code with the latest value read)

        Returns: list of all variables defined in class __init__

        """
        list_of_att = dict()
        for attribute, value in self.__dict__.items():
            list_of_att[attribute] = value
            if print_it:
                print(attribute, '=', value)
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument:
                list_of_att[attribute] = str(value)
        return list_of_att

    def clear(self):
        return self.write('*CLS')

    def get_sensitivity(self):
        """
        Function to get current sensitivity value
        Returns: sensitivity, needs to be selected from table
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

        """
        self.sensitivity = self.query_float('SENS ?')
        return self.sensitivity

    def get_phase(self):
        """
        Function to get current phase value
        Returns: phase in deg

        """
        self.phase = self.query_float('PHAS ?')
        return self.phase

    def get_ref_impedance(self):
        self.ref_impedance = self.query_int('REFZ ?')
        if self.ref_impedance == 0: return '50 Ohm'
        if self.ref_impedance == 1: return '1 MOhm '

    def get_input_impedance(self):
        self.input_impedance = self.query_int('INPZ ?')
        if self.input_impedance == 0: return '50 Ohm'
        if self.input_impedance == 1: return '1 MOhm '

    def get_time_const(self):
        self.time_const = self.query_int('OFLT ?')
        if self.time_const == 0: return '100 mus'
        if self.time_const == 17: return '30 ks'
        else: return self.time_const

    def get_X_data(self):
        return self.query_float('OUTP?1')

    def get_Y_data(self):
        return self.query_float('OUTP?2')

    def set_phase(self, pha):
        return self.write('PHAS {}'.format(pha))

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
        """
        Function to set autotunned sensitivity. Doesn't work well...

        Returns: Not really reliable. Sets too sensitive rate. Not recommended to use

        """
        return self.write('AGAN')
