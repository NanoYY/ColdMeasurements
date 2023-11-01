from numpy import *
import nidaqmx

global_dac_address = 'Dev1'  # yes, instead of normal address it should be dev1


class DAQ:
    """Class for NI Digital Analog Converter, USB-6341 operation. Based on NI-DAQmx
     Args:
         device_num:
             Should be dev1
     """
    def __init__(self, device_num=global_dac_address):
        self.dev = device_num
        self.task = nidaqmx.Task()

    def add_ai_channel(self, channel_num=0):
        task = task.ai_channels.add_ai_voltage_chan("{}/ai{}".format(self.dev, str(channel_num)))
        return task

