from numpy import *
import numpy as np
import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs
import pyvisa


global_anapico_address = gs.anapico_address


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


class ANAPICO(v.BaseVisa):
    """Class for AnaPico Signal Generator operation.
     Args:
         device_num:
             GPIB num (float) or full device address (string)

     """
    def __init__(self, device_num=global_anapico_address):
        super().__init__(device_num)  # initialise device with the init of parent class VisaDevice
        self.write(r':SYST:COMM:LAN:RTMO {}'.format(str(1)))  # reconnect timeout in seconds

        self.channel_status = np.array([nan, nan, nan, nan])
        self.channel_freqs = np.array([nan, nan, nan, nan])
        self.channel_pow = np.array([nan, nan, nan, nan])

        for i in [1, 2, 3, 4]:
            self.get_status(i)
            self.get_freq(i)
            self.get_power(i)

    def dump(self, print_it=False):
        """
        Function returns all pre-defined class attributes
        (all variables used in the code with the latest value read)

        Returns: list of all variables defined in class __init__

        """
        for i in [1, 2, 3, 4]:
            self.get_status(i)
            self.get_freq(i)
            self.get_power(i)

        list_of_att = dict()
        for attribute, value in self.__dict__.items():
            list_of_att[attribute] = value
            if print_it:
                print(attribute, '=', value)
            if type(value) == pyvisa.resources.tcpip.TCPIPInstrument:
                list_of_att[attribute] = str(value)
        return list_of_att

    def get_status(self, channel):
        """
        Function to get status of each channel.
        Note: channels on the device starts from 1!
        Args:
            channel: [1, 2, 3, 4]

        Returns: 1 - on, 0 - off

        """
        channel_py = channel-1
        self.channel_status[channel_py] = self.query('OUTPut{}:STATe?'.format(str(channel)))
        return self.channel_status[channel_py]

    def get_freq(self, channel):
        """
        Function to get frequency of each channel.
        Note: channels on the device starts from 1!
        Args:
            channel: [1..4]

        Returns: freq in Hz

        """
        channel_py = channel - 1
        self.channel_freqs[channel_py] = self.query('SOUR{}:FREQ?'.format(str(channel)))
        return self.channel_freqs[channel_py]

    def get_power(self, channel):
        """
        Function to get power of each channel.
        Note: channels on the device starts from 1!
        Args:
            channel: [1..4]

        Returns: power in dbm

        """
        channel_py = channel - 1
        self.channel_pow[channel_py] = self.query('SOUR{}:POW?'.format(str(channel)))
        return self.channel_pow[channel_py]

    def set_on(self, channel):
        """
        Function to turn ON channel output power.
        Note: channels on the device starts from 1!
        Args:
            channel: channel number [1..4]

        Returns: None

        """
        channel_py = channel - 1
        command = r'OUTP{} ON'.format(str(channel))
        self.write(command)
        self.channel_status[channel_py] = 1

    def set_off(self, channel):
        """
        Function to turn OFF channel output power.
        Note: channels on the device starts from 1!
        Args:
            channel: channel number [1..4]

        Returns: None

        """
        channel_py = channel - 1
        command = r'OUTP{} OFF'.format(str(channel))
        self.write(command)
        self.channel_status[channel_py] = 0

    def set_power(self, channel, ch_power):
        """
        Function to set output power.
        Note: channels on the device starts from 1!
        Args:
            channel: output channel
            ch_power: output power in dbm

        Returns: None

        """
        channel_py = channel - 1
        command = r'SOUR{}:POW {}'.format(str(channel), str(ch_power))
        self.write(command)
        self.channel_pow[channel_py] = ch_power

    def set_freq(self, channel, frequency):
        """
        Function to set frequency.
        Note: channels on the device starts from 1!
        Args:
            channel: output channel
            frequency: output frequency in Hz

        Returns: None

        """
        channel_py = channel - 1
        command = r'SOUR{}:FREQ {}'.format(str(channel), str(frequency))
        self.write(command)
        self.channel_freqs[channel_py] = frequency
