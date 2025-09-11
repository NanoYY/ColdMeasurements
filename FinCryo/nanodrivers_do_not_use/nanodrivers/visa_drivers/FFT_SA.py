import time
import numpy as np
from numpy import *
import os
from ctypes import *

import nanodrivers.visa_drivers.visa_dev as v
import nanodrivers.visa_drivers.global_settings as gs

global_dSA_address = gs.din_SA_address


class Din_SA(v.BaseVisa):
    """ Class for Stanford_Research_Systems, SR785, Dynamic Signal Analyzer
    NOTE: This device might need termination character '\\n' (new line) to be added to the end of the command.
    If it is not added an error 'Timeout expired before operation completed.'

    Args:
        device_num:
            GPIB num (float) or full device address (string)
        termination_char:
            Should be "new line" for some commands

    """

    def __int__(self, device_num=global_dSA_address):
        super().__int__(device_num)

    def idn(self):
        """
        Base Visa command queries *IDN?.

        Returns: Name of the device if connection exist

        """
        try:
            print("Connection exist:", self.query('*IDN?\n'))
        except:
            self.__error_message()


    def start(self):
        self.write('STRT')

    def GPIB_output(self):
        self.write('OUTX 0')

    def get_freq(self, lines=100, d=0):
        self.write('*CLS')
        max_freq = float(self.query('FSPN? {}'.format(int(d))))
        min_freq = float(self.query('FSTR? {}'.format(int(d))))
        fr = np.linspace(min_freq, max_freq, lines)
        return fr

    def initialize(self):

        # Set up parameters
        FFTline_index = 3  # FFT lines, resolution 100(0), 200(1), 400(2), 800(3)
        nump = (100 * 2 ** FFTline_index) + 1
        # numavg = 1
        # fastavgrate = 100
        fmax = 25  # 12.5
        loop = 1

        # Send commands to the instrument
        self.write('MEAS 2, 2')  # Measure Power Spectrum 1
        time.sleep(0.1)
        self.write(f'FSPN 2, {fmax}')  # Frequency span works
        time.sleep(0.1)
        self.write(f'FLIN 2, {FFTline_index}')  # FFT lines, resolution 100(0), 200(1), 400(2), 800(3) works
        time.sleep(0.1)
        self.write('FSTR 2, 0')  # Start freq works
        time.sleep(0.1)
        self.write('IAOM 0')  # Auto offset off works
        time.sleep(0.1)
        # numofavg = 2  # 4; CAN NOT BE 1
        self.write('UNDB 2, 0')  # Sets dBUnits to Off (0), On(1), dBm (2), and dBspl (3)
        time.sleep(0.1)
        self.write('UNPK 2, 2')  # Sets pkUnits to Off (0), pk (1), rms (2), and pp (3)
        time.sleep(0.1)
        self.write('PSDU 2, 1')  # Sets psd Units to Off (0), or On (1)
        time.sleep(0.1)
        # self.write('UNIT? 0')
        # SPAunit = self.read()
        self.write('OUTX 0')  # Output to GPIB interface
        time.sleep(0.1)
        self.write('LINK 0')  # Sets (queries) the Analyzer Configuration...
        # The parameter i selects Independent Channels (0) or Dual Channels (1)
        time.sleep(0.1)
        self.write('LINK?')
        time.sleep(0.1)
        SPAChannelLink = self.read()
        time.sleep(0.1)
        self.write('LINK?')
        time.sleep(0.1)
        SPAChannelLink = self.read()
        time.sleep(0.1)

        self.write('I1MD 0')  # Sets (queries) the Ch1 Input Mode...
        # The parameter i selects A (single-ended) (0) or A-B (differential) (1)
        time.sleep(0.1)
        self.write('I1MD?')
        time.sleep(0.1)
        SPAInputModeCH1 = self.read()
        time.sleep(0.1)
        self.write('I1GD 0')  # Sets (queries) the Ch1 Input Grounding...
        # The parameter i selects Float (0) or Ground (1)
        time.sleep(0.1)
        self.write('I1GD?')
        time.sleep(0.1)
        SPAInputGNDCH1 = self.read()
        time.sleep(0.1)
        self.write('I1CP 1')  # Sets (queries) the Ch1 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I1CP?')
        SPAInputCouplingDefaultCH1 = self.read()
        time.sleep(0.1)

        self.write('I2MD 0')  # Sets (queries) the Ch2 Input Mode...
        # The parameter i selects A (single-ended) (0) or A-B (differential) (1)
        time.sleep(0.1)
        self.write('I2MD?')
        time.sleep(0.1)
        SPAInputModeCH2 = self.read()
        time.sleep(0.1)
        self.write('I2GD 0')  # Sets (queries) the Ch2 Input Grounding...
        # The parameter i selects Float (0) or Ground (1)
        time.sleep(0.1)
        self.write('I2GD?')
        time.sleep(0.1)
        SPAInputGNDCH2 = self.read()
        time.sleep(0.1)
        self.write('I2CP 1')  # Sets (queries) the Ch2 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I2CP?')
        SPAInputCouplingDefaultCH2 = self.read()
        time.sleep(0.1)

        self.write('ADON 0')  # Sets (queries) the Done Volume...
        # The parameter i selects Quiet (0) or Noisy (1)
        time.sleep(0.1)
        self.write('ADON?')
        time.sleep(0.1)
        SPAAlarmDone = self.read()
        time.sleep(0.1)
        self.write('STRT')
        time.sleep(0.1)

        # Second part of the script
        self.write('I1CP 0')  # Sets (queries) the Ch1 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I1CP?')
        SPAInputCouplingTimeTraceCH1 = self.read()
        time.sleep(0.1)
        self.write('I2CP 0')  # Sets (queries) the Ch2 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I2CP?')
        SPAInputCouplingTimeTraceCH2 = self.read()
        time.sleep(0.1)

        self.write('MEAS 0, 4')  # Measure Time 1
        time.sleep(0.1)
        self.write('MEAS 1, 5')  # Measure Time 2
        time.sleep(0.1)
        self.write('STRT')
        time.sleep(0.1)
        self.write('MEAS? 0')
        time.sleep(0.1)
        SPAMeasTimeTraceCH1 = self.read()
        time.sleep(0.1)
        self.write('MEAS? 1')
        time.sleep(0.1)
        SPAMeasTimeTraceCH2 = self.read()
        time.sleep(2 * (nump - 1) / fmax)
        self.clear()
        time.sleep(0.1)
        self.write('DSPN? 0')
        time.sleep(0.1)
        RawTimetracePointsCH1 = int(self.read())
        time.sleep(0.1)
        self.write('DSPB? 0')
        time.sleep(0.4)
        data = self.read_raw(RawTimetracePointsCH1)
        RawTimetraceCH1 = list(data)
        self.clear()
        time.sleep(0.1)
        self.write('DSPN? 1')
        time.sleep(0.1)
        RawTimetracePointsCH2 = int(self.read())
        time.sleep(0.1)
        self.write('DSPB? 1')
        time.sleep(0.4)
        data = self.read_raw(RawTimetracePointsCH2)
        RawTimetraceCH2 = list(data)

        self.write('I1CP 0')  # Sets (queries) the Ch1 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I1CP?')
        SPAInputCouplingPSDCH1 = self.read()
        time.sleep(0.1)
        self.write('I2CP 0')  # Sets (queries) the Ch2 Input Coupling...
        # The parameter i selects DC (0), AC (1) or ICP (2)
        time.sleep(0.1)
        self.write('I2CP?')
        SPAInputCouplingPSDCH2 = self.read()
        time.sleep(0.1)

        self.write('MEAS 0, 2')  # Measure Power Spectrum 1
        time.sleep(0.1)
        self.write('MEAS 1, 3')  # Measure Power Spectrum 2
        time.sleep(0.1)
        self.write(f'FSPN 2, {fmax}')  # Frequency span
        time.sleep(0.1)
        self.write(f'FLIN 2, {FFTline_index}')  # FFT lines, resolution 100(0), 200(1), 400(2), 800(3) works
        time.sleep(0.1)
        

    def read_d(self, avg=1, d=0):
        self.write('*CLS')

        def read_c():

            self.start()
            self.GPIB_output()
            time.sleep(35 + 0.5)
            read_s = self.query('DSPY? {}'.format(int(d)))
            rear_f = np.array(read_s.split(','), dtype=float)
            return rear_f

        fft_0 = read_c()
        for i in range(avg - 1):
            fft_0 += read_c()

        fft_0 = fft_0 / avg

        return fft_0[:-1]

    def read_e(self):
        nump = 801
        self.write('STRT')
        # pause((nump - 1) / fmax + 2);
        time.sleep(36);
        self.write('DSPB? 0')
        data = self.query(nump);
        spectrumCH1 = data
        self.write('DSPB? 1')
        data = self.query(nump);
        spectrumCH2 = data

        return spectrumCH1, spectrumCH2
