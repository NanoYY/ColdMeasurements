import numpy as np
from numpy import *
import os
from ctypes import *


class DigAtt(object):
    """Class for Vaunix digital attenuator
         Args:
             device_num:
                 GPIB num (float) or full device address (string)
    """

    def set_att(self, raw_freq, raw_atten):
        """ Function to set attenuation
             Args:
                 raw_freq:
                    Base frequency in GHz
                 raw_atten:
                    Attenuation in dB
             """
        address_dll = r"C:\Users\Demag\PycharmProjects\ColdMeasurements\nanodrivers\nanodrivers\non_visa_drivers\dAttenuator_dll\VNX_atten64.dll"
        this_dir = os.path.abspath("")  # <-- Path to file her
        vnx = cdll.LoadLibrary(os.path.join(this_dir, address_dll))
        vnx.fnLDA_SetTestMode(False)
        DeviceIDArray = c_int * 20
        Devices = DeviceIDArray()

        vnx.fnLDA_GetNumDevices()                   # yes, this ...
        vnx.fnLDA_GetDevInfo(Devices)
        vnx.fnLDA_GetSerialNumber(Devices[0])
        vnx.fnLDA_InitDevice(Devices[0])       # ... lines are needed

        min_freq = vnx.fnLDA_GetMinWorkingFrequency(Devices[0])  # in "100kHz units????". Yes, it is not MHz
        max_freq = vnx.fnLDA_GetMaxWorkingFrequency(Devices[0])
        min_working_freq_in_MHz = int(min_freq / 10)  # Now it is in MHz
        max_working_freq_in_MHz = int(max_freq / 10)

        max_att = vnx.fnLDA_GetMaxAttenuation(Devices[0]) / 4  # in decibels
        min_att = vnx.fnLDA_GetMinAttenuation(Devices[0]) / 4
        step = vnx.fnLDA_GetAttenuationStep(Devices[0]) / 4

        atten = int(raw_atten)
        freq_GHz = float(raw_freq)
        freq_MHz = freq_GHz * 1e3

        test_freq = freq_MHz > max_working_freq_in_MHz or freq_MHz < min_working_freq_in_MHz  # True if out of range
        test_att = atten > max_att or atten < min_att  # True if out of range

        if test_freq or test_att:
            print("Failure on frequency", freq_GHz)
            print("Failure on attenuation:", atten)
            closedev = vnx.fnLDA_CloseDevice(Devices[0])
            if closedev != 0:
                print('CloseDevice returned an error', closedev)
            return 1

        # Set the working frequency in MHz
        result = vnx.fnLDA_SetWorkingFrequency(Devices[0], int(freq_MHz * 10))  # in "100kHz units????". Yes, it is not MHz
        if result != 0:
            print('SetFrequency returned error', result)
            return 1

        # Sets the Attenuation in decibels
        result_1 = vnx.fnLDA_SetAttenuation(Devices[0], int(atten) * 4)
        if result_1 != 0:
            print('SetAttenuation returned error', result_1)
            return 1

        closedev = vnx.fnLDA_CloseDevice(Devices[0])
        if closedev != 0:
            print('CloseDevice returned an error', closedev)
        return 0
