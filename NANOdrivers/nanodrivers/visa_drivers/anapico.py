from numpy import *
import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_anapico_address = gs.anapico_address


class ANAPICO(v.BaseVisa):
    """Class for AnaPico Signal Generator operation.
     Args:
         device_num:
             GPIB num (float) or full device address (string)
     """
    def __init__(self, device_num=global_anapico_address):
        super().__init__(device_num)  # initialise device with the init of parent class VisaDevice
        self.write(r':SYST:COMM:LAN:RTMO {}'.format(str(1)))  # reconnect timeout in seconds

    def on(self, channel):
        """
        Function to turn on power on selected channel
        Args:
            channel: output channel

        Returns: None

        """
        command = r'OUTP{} ON'.format(str(channel))
        self.write(command)

    def off(self, channel):
        """
        Function to turn on power off selected channel
        Args:
            channel: output channel

        Returns: None

        """
        command = r'OUTP{} OFF'.format(str(channel))
        self.write(command)

    def set_power(self, channel, output_power):
        """
        Function to set power
        Args:
            channel: output channel
            output_power: output power in db

        Returns: None

        """
        command = r'SOUR{}:POW {}'.format(str(channel), str(output_power))
        self.write(command)

    def set_freq(self, channel, frequency):
        """
        Function to set frequency
        Args:
            channel: output channel
            frequency: output frequency in Hz

        Returns: None

        """
        command = r'SOUR{}:FREQ {}'.format(str(channel), str(frequency))
        self.write(command)
