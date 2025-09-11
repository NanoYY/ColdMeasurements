from numpy import *
import numpy as np
import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs
import pyvisa
import time

global_sim_address = gs.SIM_address


def get_class_attributes(print_it=False):
    """
    Function returns all class attributes

    Returns: list of all variables globally defined within class

    """
    list_of_att = dict()
    for attribute in ANAPICO.__dict__.keys():
        if attribute[:2] != '__':
            value = getattr(ANAPICO, attribute)
            if not callable(value):
                list_of_att[attribute] = value
                if print_it:
                    print(attribute, '=', value)

    return list_of_att


class SIM(v.BaseVisa):
    """
    A driver for Stanford Research Systems SIM 928 DC source modules installed
    in a SIM900 mainframe.

     Args:
         device_num:
             GPIB num (float) or full device address (string)
         slot_num:
             slot with SIM928

     """

    def __init__(self, device_num=global_sim_address, slot_num=6):
        super().__init__(device_num)  # initialise mainframe with the init of parent class VisaDevice
        self.write("CONN {}, 'xyz'\n".format(slot_num))  # connected to slot
        try:
            self.status = self.get_status()
            self.voltage = self.get_volt()
        except:
            self.write("CONN {}, 'xyz'\n".format(slot_num))  # connected to slot

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

    def get_status(self):
        """
        Function to get ON/OFF status.
        Returns: status
        """
        command = "EXON?\n"
        self.status = int(self.query(command)[:-2])
        return self.status

    def get_volt(self):
        """
        Function to get set voltage.
        Returns: voltage in Volts
        """
        command = "VOLT?\n"
        self.voltage = float(self.query(command)[:-2])
        return self.voltage

    def set_on(self):
        """
        Function to turn ON output power.
        Returns: None
        """
        command = "OPON\n"
        self.write(command)

    def set_off(self):
        """
        Function to turn OFF output power.
        Returns: None
        """
        command = "OPOF\n"
        self.write(command)

    def set_volt(self, voltage, sudo=False):
        """
        Function to get set voltage.
        Args:
            voltage: sets voltage in volts
            sudo: removes all restrictions from the voltage. "True strength is owning your choices and facing the consequences."
        Returns: None
        """

        if sudo:
            command = "VOLT{}\n".format(np.round(voltage, 5))
            self.write(command)
        else:
            if voltage < 0 or voltage > 15:
                return ValueError
            else:
                command = "VOLT{}\n".format(np.round(voltage, 5))
                self.write(command)

    def disconnect(self):
        self.write('xyz')  # disconnected from the slot
        print('SIM928 is now disconnected from SIM900 mainframe')
