import numpy as np
import time
from datetime import datetime, timedelta
from scipy.io import savemat
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft, fftshift, ifftshift

# file_store
import os
import scipy.io as sio


def find_nearest_index(array, value):
    return (np.abs(array - value)).argmin()


def create_non_linear_distribution(min_value, max_value, n_points, lin=False):

    if lin:
        return np.linspace(min_value, max_value, n_points)
    else:
        power_lin = 1
        n_points = 1 + n_points // 2  # Ensure n_points is adjusted correctly

        if np.mod(n_points, 2) == 0:  # Even n_points
            part1 = np.linspace(0, 1, n_points - 1, endpoint=True) ** power_lin
            part2 = -np.linspace(0, 1, n_points, endpoint=True) ** power_lin
            indices = np.concatenate((part1[1:], part2))
        else:  # Odd n_points
            part1 = np.linspace(0, 1, n_points, endpoint=True) ** power_lin
            part2 = -np.linspace(0, 1, n_points, endpoint=True) ** power_lin
            indices = np.concatenate((part1[1:], part2))

        non_linear_values = (max_value + min_value) / 2 + (max_value - min_value) * indices / 2

        return np.sort(non_linear_values)


def stats():
    """
    Prints duration of previous sweeps for reference
    """
    print('31-41-41 --> 3:52')
    print('41-51-61 --> 9:21')
    print('41-21-51 --> 3:21')


class TWPA_best_gain:
    def __init__(self, file_path, file_name, vna, anapico, dc,
                 min_pump_power=-5, max_pump_power=12,
                 min_pump_freq=9e9, max_pump_freq=13.5e9,
                 min_dc=0.5, max_dc=3,
                 steps_pump_power=81, steps_pump_freq=1001, steps_dc=201,
                 gain_threshold=13,
                 vna_band_fast=500, vna_nop_fast=20,  # for fast gain sweep
                 vna_band_slow=10, vna_nop_slow=101, fft_avgs=10, vna_power=-10,
                 dry_run=False,
                 temp=9):  # for noise measurements

        self.start_time = datetime.now()
        self.file_path = file_path
        self.file_name = file_path + '\\' + file_name + self.start_time.strftime(r'%Y-%m-%d-%H-%M-%S') + '.mat'

        self.min_pump_power = min_pump_power
        self.max_pump_power = max_pump_power
        self.steps_pump_power = steps_pump_power
        self.min_pump_freq = min_pump_freq
        self.max_pump_freq = max_pump_freq
        self.steps_pump_freq = steps_pump_freq
        self.min_dc = min_dc
        self.max_dc = max_dc
        self.steps_dc = steps_dc

        self.vna_band_fast = vna_band_fast
        self.vna_nop_fast = vna_nop_fast
        self.vna_band_slow = vna_band_slow
        self.vna_nop_slow = vna_nop_slow
        self.vna_power = vna_power
        self.fft_avgs = fft_avgs

        self.temp = temp

        self.database = self.create_database()

        self.best_gain_DC = []
        self.best_gain_pp = []
        self.best_gain_pf = []
        self.actual_gain = []

        self.gain_threshold = gain_threshold
        self.state = dict()

        if not dry_run:
            self.vna = vna
            self.anapico = anapico
            self.dc = dc
            self.setup_vna_fast_cw_sweep()

    def dump(self, print_it=False):
        """
        Function returns all pre-defined class attributes
        (all variables used in the code with the latest value read)
        Args:
            print_it: If True, prints class_attributes. Default: False
        Returns: list of all variables defined in class __init__

        """
        list_of_att = dict()
        for attribute, value in self.__dict__.items():
            list_of_att[attribute] = value
            if print_it:
                print(attribute, '=', value)
        return list_of_att

    def get_sweep_time(self):
        """
        Function to get VNA sweep time
        Returns: formatted_time

        """
        single_sweep_time = self.vna.get_sweep_time()
        full_time = self.steps_dc * (self.steps_pump_freq * self.steps_pump_power * single_sweep_time + 5.2)
        td = timedelta(seconds=full_time)
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{days:02d}d {hours:02d}h-{minutes:02d}m-{seconds:02d}s"
        return formatted_time

    def load_database(self, folder_address=None, file_name=None, last_one=False):
        """
        Function to load premeasured database as current database.
        Args:
            folder_address: folder, where the data is stored
            file_name: file name. not needed if last_one = True
            last_one: selects the last measured file

        Returns: none.

        """
        if last_one:
            files = os.listdir(folder_address)
            full_address = folder_address + "\\" + files[-1]
            mat = sio.loadmat(full_address)
            print('Database from the file \n  ', full_address, ' \nuploaded')
        else:
            full_address = folder_address + "\\" + file_name
            mat = sio.loadmat(full_address)
            print('Database from file \n  ', full_address, '\nuploaded')
        print(mat.keys())
        uploaded_pp = mat['database'][0]['pump_powers'][0][0]
        self.min_pump_power = min(uploaded_pp)
        self.max_pump_power = max(uploaded_pp)
        self.steps_pump_power = len(uploaded_pp)
        uploaded_pf = mat['database'][0]['pump_freqs'][0][0]
        self.min_pump_freq = min(uploaded_pf)
        self.max_pump_freq = max(uploaded_pf)
        self.steps_pump_freq = len(uploaded_pf)
        uploaded_DC = mat['database'][0]['volts'][0][0]
        self.min_dc = min(uploaded_DC)
        self.max_dc = max(uploaded_DC)
        self.steps_dc = len(uploaded_DC)
        self.create_database()
        self.database['data'] = mat['database'][0]['data'][0]
        return mat

    def setup_vna_fast_cw_sweep(self, vna_cw_freq=5e9):
        """
        Function to setup VNA for fast gain sweep.
        Args:
            vna_cw_freq: CW probe freq on VNA
            vna_power: power of probe signal

        Returns: none

        """
        self.vna.set_cw()
        self.vna.set_cw_freq(vna_cw_freq)
        self.vna.set_band(self.vna_band_fast)
        self.vna.set_nop(self.vna_nop_fast)
        self.vna.set_power(self.vna_power)

    def setup_vna_slow_cw_sweep(self, vna_cw_freq=5e9):
        """
        Function to setup VNA for noise measurements with low bandwidth.
        Args:
            vna_cw_freq: CW probe freq on VNA
            vna_power:  power of probe signal

        Returns: none

        """
        self.vna.set_cw()
        self.vna.set_cw_freq(vna_cw_freq)
        self.vna.set_band(self.vna_band_slow)
        self.vna.set_nop(self.vna_nop_slow)
        self.vna.set_power(self.vna_power)

    def create_database(self):
        """
        Creates class-related database for gain sweep. Does not contain noise data
        Returns: database dict: {power; freq; volts}

        """
        pump_powers = np.linspace(self.min_pump_power, self.max_pump_power, self.steps_pump_power)
        pump_freqs = np.linspace(self.min_pump_freq, self.max_pump_freq, self.steps_pump_freq)
        volts = np.linspace(self.min_dc, self.max_dc, self.steps_dc)

        data = np.zeros((self.steps_dc, self.steps_pump_freq, self.steps_pump_power))
        return {'pump_powers': pump_powers, 'pump_freqs': pump_freqs, 'volts': volts, 'data': data}

    def database_info(self):
        print("Database created at:", self.start_time.strftime(r'%Y-%m-%d %H:%M:%S'))

    def plot_database(self, index_dc=0, index_pf=0, index_pp=0):
        data = self.database['data']
        pump_freqs = self.database['pump_freqs']
        pump_powers = self.database['pump_powers']
        volts = self.database['volts']

        fig, ax = plt.subplots(1, 3, figsize=(25, 7))
        colors = ['#5bb6ff', '#0000a2', '#af39d7', '#ffffff']
        cmap = LinearSegmentedColormap.from_list('my_cmap', colors, N=256)

        # Plot fixed DC
        c1 = ax[0].pcolor(pump_freqs / 1e9, pump_powers, data[index_dc, :, :].T, cmap=cmap)
        ax[0].set_title(r'Bias, V')
        ax[0].set_xlabel(r'Pump freqs, GHz')
        ax[0].set_ylabel(r'Pump Powers, dB')
        fig.colorbar(c1, ax=ax[0], orientation='vertical')

        # Plot fixed pump freq
        c2 = ax[1].pcolor(volts, pump_powers, data[:, index_pf, :].T, cmap=cmap)
        ax[1].set_title(r'Bias, V')
        ax[1].set_xlabel(r'DC, V')
        ax[1].set_ylabel(r'Pump Powers, dB')
        fig.colorbar(c2, ax=ax[1], orientation='vertical')

        # Plot fixed pump power
        c3 = ax[2].pcolor(volts, pump_freqs / 1e9, data[:, :, index_pp].T, cmap=cmap)
        ax[2].set_title(r'Bias, V')
        ax[2].set_xlabel(r'DC, V')
        ax[2].set_ylabel(r'Pump freqs, GHz')
        fig.colorbar(c3, ax=ax[2], orientation='vertical')
        plt.show()

    def get_gain(self, mag_no_gain):
        mag_gain, _ = self.vna.get_data()
        return np.round(np.mean(mag_gain) - np.mean(mag_no_gain), 5)

    def get_noise(self):
        band = self.vna.get_band()
        nop = self.vna.get_nop()
        freq = np.linspace(-band / 2, band / 2, nop)

        fft_mags = np.ones((len(freq), self.fft_avgs))
        fft_phas = np.ones((len(freq), self.fft_avgs))

        for i in range(self.fft_avgs):
            mag, pha = self.vna.get_data()
            fft_mags[:, i] = abs(fftshift(fft(np.sqrt(np.power(10, mag / 10))))) ** 2    # /N**2 or "forward" normalization
            fft_phas[:, i] = abs(fftshift(fft(pha))) ** 2                                # /N**2 or forward normalization

        return freq, np.mean(fft_mags, axis=1), np.mean(fft_phas, axis=1)

    def sweep_database(self, dc_nop=21, pp_nop=7, pf_nop=201, conditional_gain_tr=-1,
                       dc_range=None, pf_range=None, pp_range=None,  lin=False):

        if dc_range is None:
            rough_dc = np.linspace(self.min_dc, self.max_dc, dc_nop)
        else:
            rough_dc = np.linspace(dc_range[0], dc_range[1], dc_nop)

        if pf_range is None:
            rough_pf = np.linspace(self.min_pump_freq, self.max_pump_freq, pf_nop)
        else:
            rough_pf = np.linspace(pf_range[0], pf_range[1], pf_nop)

        # will concentrate points near middle value
        if pp_range is None:
            rough_pp = create_non_linear_distribution(self.min_pump_power, self.max_pump_power, pp_nop, lin)
        else:
            rough_pp = create_non_linear_distribution(pp_range[0], pp_range[1], pp_nop, lin)

        if self.steps_dc == dc_nop: delta_dc = 0
        else: delta_dc = int(self.steps_dc // len(rough_dc))

        if self.steps_pump_freq == pf_nop: delta_pf = 0
        else: delta_pf = np.max(int(self.steps_pump_freq // len(rough_pf))-1)

        if self.steps_pump_power == pp_nop: delta_pp = 0
        else: delta_pp = np.max(int(self.steps_pump_power // len(rough_pp))-1)

        start_time = datetime.now()
        print('Script started at', start_time.strftime(r'_%Y-%m-%d %H:%M:%S'))

        self.dc.set_on()

        for i_dc, dc_voltage in enumerate(rough_dc):
            print("\n")
            start_DC_time = datetime.now()
            print("New DC set to", dc_voltage, "V", "at", start_DC_time.strftime(r'_%Y-%m-%d %H:%M:%S'), end='\n')
            self.dc.set_volt(dc_voltage)
            self.dc.set_on()
            time.sleep(5)

            self.anapico.set_off(1)
            mag_no_gain, _ = self.vna.get_data()
            self.anapico.set_on(1)

            dc_idx = find_nearest_index(self.database['volts'], dc_voltage)

            for pf_freq in rough_pf:
                pf_idx = find_nearest_index(self.database['pump_freqs'], pf_freq)

                for pp_power in rough_pp:

                    # finds position in database, where the new gain point is measured
                    pp_idx = find_nearest_index(self.database['pump_powers'], pp_power)

                    min_dc_idx = np.max([dc_idx - delta_dc, 0])
                    max_dc_idx = np.min([dc_idx + delta_dc, self.steps_dc - 1])

                    min_pf_idx = np.max([pf_idx - delta_pf, 0])
                    max_pf_idx = np.min([pf_idx + delta_pf, self.steps_pump_freq - 1])

                    min_pp_idx = np.max([pp_idx - delta_pp, 0])
                    max_pp_idx = np.min([pp_idx + delta_pp, self.steps_pump_power - 1])

                    if np.any(self.database['data'][min_dc_idx:max_dc_idx, min_pf_idx:max_pf_idx,
                              min_pp_idx:max_pp_idx]) > conditional_gain_tr:

                        self.anapico.set_freq(1, pf_freq)
                        self.anapico.set_power(1, pp_power)
                        time.sleep(10)
                        gain = self.get_gain(mag_no_gain)

                        dc_range = 'Range DC[{:.2f}] = [{:.2f}, {:.2f}]'.format(
                            np.round(dc_voltage, 3),
                            np.round(self.database['volts'][min_dc_idx], 4),
                            np.round(self.database['volts'][max_dc_idx], 4))

                        pf_range = 'PF[{:.2f}] = [{:.2f}, {:.2f}]'.format(
                            np.round(pf_freq / 1e9, 3),
                            np.round(self.database['pump_freqs'][min_pf_idx] / 1e9, 3),
                            np.round(self.database['pump_freqs'][max_pf_idx] / 1e9, 3))

                        pp_range = 'PP[{:.4f}] = [{:.2f}, {:.2f}]'.format(
                            np.round(pp_power, 2),
                            np.round(self.database['pump_powers'][min_pp_idx], 2),
                            np.round(self.database['pump_powers'][max_pp_idx], 2))

                        gain_info = '--> {:.3f}'.format(np.round(gain, 3))

                        print(f"{dc_range}, {pf_range}, {pp_range} {gain_info}",
                              end='\n' if gain > self.gain_threshold else '\r')

                        # Fill in the gain values efficiently
                        self.database['data'][min_dc_idx:max_dc_idx + 1, min_pf_idx:max_pf_idx + 1,
                        min_pp_idx:max_pp_idx + 1] = gain

                        if gain > self.gain_threshold:
                            self.best_gain_DC.append(dc_voltage)
                            self.best_gain_pp.append(pp_power)
                            self.best_gain_pf.append(pf_freq)
                            self.actual_gain.append(gain)

            self.state = {'best_gain_DC': self.best_gain_DC, 'best_gain_pp': self.best_gain_pp,
                          'best_gain_pf': self.best_gain_pf, 'best_gain': self.actual_gain,
                          'rough_dc': rough_dc, 'rough_pf': rough_pf, 'rough_pp': rough_pf,
                          'database': self.database}
            savemat(self.file_name, self.state)

        self.state = {'best_gain_DC': self.best_gain_DC, 'best_gain_pp': self.best_gain_pp,
                      'best_gain_pf': self.best_gain_pf, 'best_gain': self.actual_gain,
                      'rough_dc': rough_dc, 'rough_pf': rough_pf, 'rough_pp': rough_pf,
                      'database': self.database}

        self.dc.set_volt(0)
        self.dc.set_off()
        self.anapico.set_off(1)

        savemat(self.file_name, self.state)
        if len(self.best_gain_DC) > 0:
            print("\n")
            idx_max = np.argmax(self.actual_gain)
            print(
                f"Best gain found: DC={self.best_gain_DC[idx_max]:.2f}, PP={np.round(self.best_gain_pp[idx_max] / 1e9, 3):.2f}, "
                f"PF={self.best_gain_pf[idx_max]:.2f}: {self.actual_gain[idx_max]:.2f}")
        else:
            print("\n")
            print('No good gain point found')
        print(f"Run time: {datetime.now() - start_time}")

    def sweep_noise(self, gain_tr1=-1, gain_tr2=-1, gain_tr2_max=50, dc_range=None, pf_range=None, pp_range=None,
                    file_name='Noise_sweep', lin=False):

        start_time = datetime.now()
        file_name = self.file_path + '\\' + file_name + start_time.strftime(r'_%Y-%m-%d-%H-%M-%S') + '.mat'

        if dc_range is None:
            rough_dc = np.linspace(self.min_dc, self.max_dc, self.steps_dc)
        else:
            rough_dc = np.linspace(dc_range[0], dc_range[1], dc_range[2])

        if pf_range is None:
            rough_pf = np.linspace(self.min_pump_freq, self.max_pump_freq, self.steps_pump_freq)
        else:
            rough_pf = np.linspace(pf_range[0], pf_range[1], pf_range[2])

        # will concentrate points near middle value
        if pp_range is None:
            rough_pp = create_non_linear_distribution(self.min_pump_power, self.max_pump_power, self.steps_pump_power, lin)
        else:
            rough_pp = create_non_linear_distribution(pp_range[0], pp_range[1], pp_range[2], lin)

        # create new_mini_database
        data_mag = np.zeros((len(rough_dc), len(rough_pf), len(rough_pp), 2, self.vna_nop_slow))  # on/off noise
        data_pha = np.zeros((len(rough_dc), len(rough_pf), len(rough_pp), 2, self.vna_nop_slow))  # on/off noise
        data_gain = np.zeros((len(rough_dc), len(rough_pf), len(rough_pp)))  # gain

        database_noise = {'pump_powers': rough_pp, 'pump_freqs': rough_pf, 'volts': rough_dc, 'data_gain': data_gain,
                          'data_mag': data_mag, 'data_pha': data_pha}

        start_time = datetime.now()
        print('Script started at', start_time.strftime(r'%Y-%m-%d %H:%M:%S'))

        self.dc.set_on()

        for dc_idx, dc_voltage in enumerate(rough_dc):
            print("\n")
            start_DC_time = datetime.now()
            print("New DC set to", dc_voltage, "V", "at", start_DC_time.strftime(r'%Y-%m-%d %H:%M:%S'), end='\n')
            self.dc.set_volt(dc_voltage)
            self.dc.set_on()
            time.sleep(5)
            dc_idx_closest = find_nearest_index(self.database['volts'], dc_voltage)

            self.anapico.set_off(1)
            self.setup_vna_fast_cw_sweep()
            mag_no_gain, _ = self.vna.get_data()
            self.anapico.set_on(1)

            for pf_idx, pf_freq in enumerate(rough_pf):
                pf_idx_closest = find_nearest_index(self.database['pump_freqs'], pf_freq)

                for pp_idx, pp_power in enumerate(rough_pp):
                    pp_idx_closest = find_nearest_index(self.database['pump_powers'], pp_power)

                    check_gain = self.database['data'][dc_idx_closest, pf_idx_closest, pp_idx_closest]
                    data_gain[dc_idx, pf_idx, pp_idx] = check_gain

                    if check_gain > gain_tr1:

                        self.anapico.set_power(1, pp_power)
                        self.anapico.set_freq(1, pf_freq)
                        self.anapico.set_on(1)

                        self.setup_vna_fast_cw_sweep()
                        gain = self.get_gain(mag_no_gain)
                        data_gain[dc_idx, pf_idx, pp_idx] = gain
                        print(check_gain, '-->', gain, end="\r")
                        if gain_tr2 < gain < gain_tr2_max:  # measure noise
                            start_time = datetime.now()
                            print(f'   Noise sweep [{dc_idx, pf_idx, pp_idx}] with gain {gain} started at',
                                  start_time.strftime(r'%Y-%m-%d %H:%M:%S'), end='\n')

                            self.setup_vna_slow_cw_sweep()

                            self.anapico.set_off(1)
                            time.sleep(0.1)
                            freq_ref, fft_mag_ref, fft_pha_ref = self.get_noise()
                            self.anapico.set_on(1)
                            time.sleep(0.1)
                            freq, fft_mag, fft_pha = self.get_noise()

                            data_mag[dc_idx, pf_idx, pp_idx, 0] = fft_mag
                            data_mag[dc_idx, pf_idx, pp_idx, 1] = fft_mag_ref

                            data_pha[dc_idx, pf_idx, pp_idx, 0] = fft_pha
                            data_pha[dc_idx, pf_idx, pp_idx, 1] = fft_pha_ref

                            database_noise.update({'data_mag': data_mag, 'data_pha': data_pha, 'data_gain': data_gain,
                                                   'fft_freq': freq})
                            savemat(file_name, database_noise)

        database_noise.update({'data_mag': data_mag, 'data_pha': data_pha, 'data_gain': data_gain, 'fft_freq': freq})
        savemat(file_name, database_noise)
        print(f"Run time: {datetime.now() - start_time}")
