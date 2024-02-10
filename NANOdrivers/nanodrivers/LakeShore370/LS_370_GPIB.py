from __future__ import (absolute_import, division, print_function)

from numpy import *
import numpy as np
import pyvisa
import time

import nanodrivers.visa_drivers.visa_dev as v


global_ls_address = 'GPIB0::5::INSTR'


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


class LakeShore(v.BaseVisa):
    """
    Class for Lake Shore 370.
     Args:
         device_num:
             GPIB num (float) or full device address (string)

     """
    def __init__(self, device_num=global_ls_address):
        super().__init__(device_num)

        self.PID = None

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
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument or type(value) == pyvisa.resources.gpib.GPIBInstrument:
                list_of_att[attribute] = str(value)
        return list_of_att

    def get_temp(self, channel):
        """
        Function to get temperature of specific channel
        Args:
            channel: channel number [1..6]

        Returns: temperature in Kelvins

        """
        float(ls.query('RDGK? 6')[:-2])