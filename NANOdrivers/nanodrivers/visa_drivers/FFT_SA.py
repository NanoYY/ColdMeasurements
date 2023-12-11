import numpy as np
from numpy import *
import os
from ctypes import *

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_dSA_address = gs.din_SA_adress

class Din_SA(v.BaseVisa):
    """ Class for Stanford_Research_Systems, SR785, Dynamic Signal Analyzer
    NOTE: This device needs termination character '\\n' (new line) to be added to the end of the command.
    If it is not added an error 'Timeout expired before operation completed.'

    Args:
        device_num:
            GPIB num (float) or full device address (string)
        termination_char:
            Should be "new line"

    """

    def __int__(self, device_num=global_dSA_address, termination_char='\n'):
        super().__int__(device_num, termination_char='\n')

    def idn(self):
        try:
            print("Connection exist:", self.query_str('*IDN?'))
        except:
            self.__error_message()