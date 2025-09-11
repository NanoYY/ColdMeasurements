import numpy as np
from numpy import *
import os
from ctypes import *

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_awg_address = gs.awg_address


class AWG(v.BaseVisa):
    """
        Class for Agilent Technologies, 33510B, Arbitrary Waveform Generator

        Args:
            device_num:
                GPIB num (float) or full device address (string)

    """

    def __int__(self, device_num=global_awg_address):
        super().__int__(device_num)

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
