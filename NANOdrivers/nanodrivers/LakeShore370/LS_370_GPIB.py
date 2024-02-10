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

        self.PID = np.array([nan, nan, nan])

        self.channel_temp = np.array([nan, nan, nan, nan, nan, nan, nan, nan])

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

    def get_temp(self, channel=6):
        """
        Function to get temperature of specific channel
        Args:
            channel: channel number [1..6]

        Returns: temperature in Kelvins

        """
        self.channel_temp[channel] = float(self.query('RDGK? {}').format(channel)[:-2])
        return self.channel_temp[channel]

    def get_PID(self):
        """
        Function to get PID control
        Returns: PID parameters

        """
        sr = self.query('PID?')[:-2].split(',')
        for i in range(3):
            self.PID[i] = float(sr[i])

        return self.PID

    def set_setpoint(self, temp, channel=6, sudo_mode=False):
        """
        Function to set temperature of specific channel
        Args:
            temp: temperature in Kelvins
            channel: channel number [1..6]
            sudo_mode: If this mode is used, no restriction will be applied. Be careful.
        Returns: None

        """
        if temp<1.4:
            self.channel_temp[channel] = temp
            self.write('SETP {}'.format(str(self.channel_temp[channel])))
            return True
        elif sudo_mode:
            print('WARNING! Temperature might be too high: {} K'.format(temp))
            print('However, the temperature {} K will be set as new set point.'.format(temp))
            self.channel_temp[channel] = temp
            self.write('SETP {}'.format(str(self.channel_temp[channel])))
            return True
        else:
            print('WARNING! Temperature is too high: {} K'.format(temp))
            print('The temperature {} K will NOT be set as new set point.'.format(temp))
            return False

    def set_new_temperature(self, temp):
        """
        Function to set new temperature on MC. Uses predefined PID parameters.
        Main advantage is minimal waiting time. In the future adjustment of PID parameters will be added.

        Args:
            temp: Temperature in Kelvins

        Returns: True once setting new temperature is finished.

        """
        initial_temperature = self.get_temp()

        # to prevent overheating when the temperature difference is too high, first set 0.8 of set point.

        delta = temp-initial_temperature
        if delta<0:
            self.set_setpoint(temp)
            print('Just cooling down')
        else:
            new_temp1 = initial_temperature + 0.8*delta
            self.set_setpoint(new_temp1)
            print('Heats up to initial temperature + 0.8*delta')
            time.sleep(60*delta*2)
            new_temp2 = initial_temperature + 0.9 * delta
            self.set_setpoint(new_temp2)
            print('Heats up to initial temperature + 0.9*delta')
            time.sleep(30*delta*2)
            new_temp3 = initial_temperature + delta
            self.set_setpoint(new_temp3)
            print('Heats up to set point')
            time.sleep(20*delta*2)

        temps = np.array([])
        for i in range(5):
            temps = np.append(temps, self.get_temp())
            time.sleep(10)

        while not(temp-0.001 < np.mean(temps) < temp+0.001):
            temps = np.delete(temps, 0)
            temps = np.append(temps, self.get_temp())
            time.sleep(10)

        return True
