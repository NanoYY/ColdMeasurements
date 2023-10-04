import numpy as np
from numpy import *


def setup_anapico(power=-30, frequency = 6e9, channel = 1):
    try:
        print(anapico.query('*IDN?'))
        print('Connection exist')
    except:
        rm = pyvisa.ResourceManager()
#         anapico = rm.open_resource('USB0::0x03EB::0xAFFF::3C6-0B4F40003-0985::INSTR') # USB connection
        anapico = rm.open_resource('TCPIP0::169.254.5.91::inst0::INSTR') # LAN connection
        print(anapico.query('*IDN?'))
        anapico.write(r':SYST:COMM:LAN:RTMO {}'.format(str(1)))
    if power<=0:
#         print('Flux power set:', power)
        anapico.write(r'SOUR{}:POW {}'.format(str(channel), str(power)))
        anapico.write(r'SOUR{}:FREQ {}'.format(str(channel), str(frequency)))
    else:
        print('Flux power is too high:', power)
    return anapico

def anapico_on(channel=1):
    anapico.write(r'OUTP{} ON'.format(str(channel)))

def anapico_off(channel=1):
    anapico.write(r'OUTP{} OFF'.format(str(channel)))

def anapico_freq(freq, channel=1):
    anapico.write(r'SOUR{}:FREQ {}'.format(str(channel), str(freq)))

def anapico_power(power, channel=1):
    anapico.write(r'SOUR{}:POW {}'.format(str(channel), str(power)))

