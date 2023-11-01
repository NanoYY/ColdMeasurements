from numpy import *
import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_dc_address = gs.dc_source_address


class DC(v.BaseVisa):
    """Class for HEWLETT-PACKARD, 33120A operation Function Generator / Arbitrary Waveform Generator
     Args:
         device_num:
             GPIB num (float) or full device address (string)


     """
    def __init__(self, device_num=global_dc_address):
        super().__init__(device_num)

    def set_volt(self, volt):
        self.write_str('VOLT:OFFS {}'.format(str(volt)))

