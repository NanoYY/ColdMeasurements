from __future__ import (absolute_import, division, print_function)

from numpy import *
import numpy as np
import pyvisa
import time

import nanodrivers.visa_drivers.visa_dev as v


global_ls_address = 'GPIB0::5::INSTR'

"""
For Finncryo lakeshore bridge: 

3.16 mA (100%) --> 305 mK 

"""
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
    https://www.lakeshore.com/docs/default-source/product-downloads/manuals/370_manual.pdf?sfvrsn=6574e993_1
     Args:
         device_num:
             GPIB num (float) or full device address (string)
     """
    def __init__(self, device_num=global_ls_address):
        super().__init__(device_num)

        self.PID = np.array([nan, nan, nan])
        self.get_PID()

        self.channel_temp = np.full(20, np.nan)

        for i in [1, 2, 5, 6]:
            self.get_temp(i)

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
        channel = int(channel)
        self.channel_temp[channel-1] = float((self.query('RDGK? {}'.format(channel)))[:-2])
        return self.channel_temp[channel-1]

    def get_PID(self):
        """
        Function to get PID control
        Returns: PID parameters

        """
        sr = self.query('PID?')[:-2].split(',')
        for i in range(3):
            self.PID[i] = float(sr[i])

        return self.PID

    def get_setpoint(self):
        """
        Function to set temperature of specific channel
        Args:
            set_temp: temperature in Kelvins to be set on channel
            channel: channel number [1..6]
        Returns: None

        """
        return float(self.query('SETP?')[:-2])

    def set_setpoint(self, set_temp):
        """
        Function to set temperature of specific channel
        Args:
            set_temp: temperature in Kelvins to be set on channel
            channel: channel number [1..6]
        Returns: None

        """
        self.write('SETP {}'.format(str(set_temp)))

    def set_PID(self, P, I, D):
        """
        Function to set PID
        Args:
            P: gain, must have a value greater than zero for the control loop to operate.
            The value for control loop Proportional (gain): 0.001 to 1000.

            I: The value for control loop Integral (reset): 0 to 10000.
            D: The value for control loop Derivative (rate): 0 to 2500.

        Example: PID 10,100,20[term] – P = 10, I = 100 seconds, and D = 20 seconds.

        Returns: None

        """
        self.write('PID {},{},{}'.format(str(P), str(I), str(D)))

    def adjust_PID(self):
        """
        Function to update PID accordingly to the temperature using a table
        TODO: setUP script to sweep over PID parameters to find optimal
        Returns: None
        """

        current_temp = self.get_setpoint()
        print(current_temp)
        P = 20
        I = 0
        D = 0
        if current_temp <= 0.5:
            P = 20
            I = 0.1
            D = 2
        elif 1.6 <= current_temp <= 1.9:
            P = 20
            I = 3
            D = 2
        elif 1.9 < current_temp <= 2.1:
            P = 20
            I = 4
            D = 2
        elif 2.1 < current_temp <= 2.3:
            P = 8
            I = 4
            D = 6
        elif 2.3 < current_temp <= 2.7:
            P = 30
            I = 5
            D = 20
        elif 2.7 < current_temp <= 2.9:
            P = 5
            I = 1
            D = 2
        elif 2.9 < current_temp <= 3.2:
            P = 38
            I = 2
            D = 8
        elif 3.2 < current_temp <= 6:
            P = 30
            I = 4
            D = 5

        self.set_PID(P, I, D)
        print('PID param updated to {},{},{}'.format(str(P), str(I), str(D)))

