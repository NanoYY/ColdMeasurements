from __future__ import (absolute_import, division, print_function)

from numpy import *
import pyvisa

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_dc_address = gs.dc_source_address


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


class DC(v.BaseVisa):
    """Class for HEWLETT-PACKARD, 33120A operation Function Generator / Arbitrary Waveform Generator
     Args:
         device_num:
             GPIB num (float) or full device address (string)


     """
    def __init__(self, device_num=global_dc_address):
        super().__init__(device_num)
        self.volt = None
        self.set_volt(0)

        self.set_impedance('INF')
        self.impedance = self.get_impedance()

        self.shape = None
        self.set_shape(shape_mode='DC')

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
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument or \
                    type(value) == pyvisa.resources.gpib.GPIBInstrument:
                list_of_att[attribute] = str(value)
        return list_of_att

    def get_impedance(self):
        """
        Function to get output impedance (output load).
        Options are: 50|INFinity|MINimum|MAXimum
        Default: INF

        Returns: Output load, string

        """
        self.impedance = self.query('OUTPut:LOAD?')
        return self.impedance

    def get_shape(self):
        """
        Function to get shape of output signal (for example, DC or sinusoidal modulation).
        Options are: SINusoid|SQUare|TRIangle|RAMP|NOISe|USER|DC
        Default: DC

        Returns: Shape, string

        """
        self.shape = self.query('FUNCtion:SHAP?')
        return self.shape

    def set_impedance(self, imp='INF'):
        """
        Function to set output impedance (output load).
        Options are: 50|INFinity|MINimum|MAXimum
        Default: INF

        Returns: None

        """
        self.impedance = imp
        self.write('OUTPut:LOAD {}'.format(str(self.imp)))

    def set_shape(self, shape_mode='DC'):
        """
        Function to set shape of output signal (for example, DC or sinusoidal modulation).
        Options are: SINusoid|SQUare|TRIangle|RAMP|NOISe|USER|DC
        Default: DC

        Returns: None

        """
        self.shape = shape_mode
        self.write('FUNCtion:SHAP {}'.format(str(self.shape)))

    def set_volt(self, volt):
        """
        Function to set voltage
        Args:
            volt: voltage in volts

        Returns: None

        """
        self.volt = volt
        self.write('VOLT:OFFS {}'.format(str(self.volt)))
