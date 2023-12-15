
"""Contain all static address of devices
    Args:
        anapico_address:
            supports LAN and USB
        vna_address:
            supports LAN and GPIB
        dc_source_address:
            supports GPIB
"""

anapico_address = 'TCPIP0::169.254.5.91::inst0::INSTR'

# vna_address = 'GPIB0::20::INSTR'
vna_address = 'TCPIP0::169.254.36.111::hislip0::INSTR'

dc_source_address = 'GPIB0::26::INSTR'

loking_address = 'GPIB0::30::INSTR'

din_SA_address = 'GPIB0::10::INSTR'


awg_address = 'GPIB0::13::INSTR'

sa_address = 'GPIB0::7::INSTR'

