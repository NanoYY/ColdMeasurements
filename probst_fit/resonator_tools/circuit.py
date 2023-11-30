import warnings
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as spopt
from numpy import ndarray
from scipy.constants import hbar
from scipy.interpolate import splrep, splev

from .utilities import  plotting, save_load, Watt2dBm, dBm2Watt
from .circlefit import circlefit
from .calibration import calibration



##
## z_data_raw denotes the raw data
## z_data denotes the normalized data
##

class reflection_port(circlefit, save_load, plotting, calibration):
    '''
    normal direct port probed in reflection
    '''
    z_data_raw: ndarray

    def __init__(self, f_data=None, z_data_raw=None):
        self.porttype = 'direct'
        self.fitresults = {}
        self.z_data = None
        if f_data is not None:
            self.f_data = np.array(f_data)
        else:
            self.f_data = None
        if z_data_raw is not None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data = None
        self.phasefitsmooth = 3

    def _S11(self, f, fr, k_c, k_i):
        '''
        use either frequency or angular frequency units
        for all quantities
        k_l=k_c+k_i: total (loaded) coupling rate
        k_c: coupling rate
        k_i: internal loss rate
        '''
        return ((k_c - k_i) + 2j * (f - fr)) / ((k_c + k_i) - 2j * (f - fr))

    def get_delay(self, f_data, z_data, delay=None, ignoreslope=True, guess=True):
        '''
        ignoreslope option not used here
        retrieves the cable delay assuming the ideal resonance has a circular shape
        modifies the cable delay until the shape Im(S21) vs Re(S21) is circular
        see "do_calibration"
        '''
        maxval = np.max(np.absolute(z_data))
        z_data = z_data / maxval
        A1, A2, A3, A4, fr, Ql = self._fit_skewed_lorentzian(f_data, z_data)
        if self.df_error / fr > 0.001 or self.dQl_error / Ql > 0.1:
            # print "WARNING: Calibration using Lorentz fit failed, trying phase fit..."
            A1 = np.mean(np.absolute(z_data))
            A2 = 0.
            A3 = 0.
            A4 = 0.
            # fr = np.mean(f_data)
            f = splrep(f_data, np.unwrap(np.angle(z_data)), k=5, s=self.phasefitsmooth)
            fr = f_data[np.argmax(np.absolute(splev(f_data, f, der=1)))]
            Ql = 1e4
        if ignoreslope == True:
            A2 = 0.
        else:
            A2 = 0.
            # z_data = (np.absolute(z_data)-A2*(f_data-fr)) * np.exp(np.angle(z_data)*1j)  #usually not necessary
        if delay is None:
            if guess == True:
                delay = self._guess_delay(f_data, z_data)
            else:
                delay = 0.
            delay = self._fit_delay(f_data, z_data, delay, maxiter=200)
        params = [A1, A2, A3, A4, fr, Ql]
        return delay, params

    def do_calibration(self, f_data, z_data, ignoreslope=True, guessdelay=True, fixed_delay=None):
        '''
        calculating parameters for normalization
        '''
        delay, params = self.get_delay(f_data, z_data, ignoreslope=ignoreslope, guess=guessdelay,
                                       delay=fixed_delay)
        z_data = (z_data - params[1] * (f_data - params[4])) * np.exp(
            2. * 1j * np.pi * delay * f_data)
        xc, yc, r0 = self._fit_circle(z_data)
        zc = complex(xc, yc)
        fitparams = self._phase_fit(f_data, self._center(z_data, zc), 0., np.absolute(params[5]),
                                    params[4])
        theta, Ql, fr = fitparams
        beta = self._periodic_boundary(theta + np.pi, np.pi)  ###
        offrespoint = complex((xc + r0 * np.cos(beta)), (yc + r0 * np.sin(beta)))
        alpha = self._periodic_boundary(np.angle(offrespoint) + np.pi, np.pi)
        # a = np.absolute(offrespoint)
        # alpha = np.angle(zc)
        a = r0 + np.absolute(zc)
        return delay, a, alpha, fr, Ql, params[1], params[4]

    def do_normalization(self, f_data, z_data, delay, amp_norm, alpha, A2, frcal):
        '''
        transforming resonator into canonical position
        '''
        return (z_data - A2 * (f_data - frcal)) / amp_norm * np.exp(
            1j * (-alpha + 2. * np.pi * delay * f_data))

    def circlefit(self, f_data, z_data, fr=None, Ql=None, refine_results=False, calc_errors=True):
        '''
        S11 version of the circlefit
        '''

        if fr is None: fr = f_data[np.argmin(np.absolute(z_data))]
        if Ql is None: Ql = 1e6
        xc, yc, r0 = self._fit_circle(z_data, refine_results=refine_results)
        phi0 = -np.arcsin(yc / r0)
        theta0 = self._periodic_boundary(phi0 + np.pi, np.pi)
        z_data_corr = self._center(z_data, complex(xc, yc))
        theta0, Ql, fr = self._phase_fit(f_data, z_data_corr, theta0, Ql, fr)
        # print "Ql from phasefit is: " + str(Ql)
        Qi = Ql / (1. - r0)
        Qc = 1. / (1. / Ql - 1. / Qi)

        results = {"Qi": Qi, "Qc": Qc, "Ql": Ql, "fr": fr, "theta0": theta0}

        # calculation of the error
        p = [fr, Qc, Ql]
        # chi_square, errors = rt.get_errors(rt.residuals_notch_ideal,f_data,z_data,p)
        if calc_errors == True:
            chi_square, cov = self._get_cov_fast_directrefl(f_data, z_data, p)
            # chi_square, cov = rt.get_cov(rt.residuals_notch_ideal,f_data,z_data,p)

            if cov is not None:
                errors = np.sqrt(np.diagonal(cov))
                fr_err, Qc_err, Ql_err = errors
                # calc Qi with error prop (sum the squares of the variances and covariaces)
                dQl = 1. / ((1. / Ql - 1. / Qc) ** 2 * Ql ** 2)
                dQc = - 1. / ((1. / Ql - 1. / Qc) ** 2 * Qc ** 2)
                Qi_err = np.sqrt((dQl ** 2 * cov[2][2]) + (dQc ** 2 * cov[1][1]) + (
                        2 * dQl * dQc * cov[2][1]))  # with correlations
                errors = {"Ql_err": Ql_err, "Qc_err": Qc_err, "fr_err": fr_err,
                          "chi_square": chi_square, "Qi_err": Qi_err}
                results.update(errors)
            else:
                print("WARNING: Error calculation failed!")
        else:
            # just calc chisquared:
            fun2 = lambda x: self._residuals_notch_ideal(x, f_data, z_data) ** 2
            chi_square = 1. / float(len(f_data) - len(p)) * (fun2(p)).sum()
            errors = {"chi_square": chi_square}
            results.update(errors)

        return results

    def autofit(self, electric_delay=None):
        '''
        automatic calibration and fitting
        '''
        delay, amp_norm, alpha, fr, Ql, A2, frcal = \
            self.do_calibration(self.f_data, self.z_data_raw, ignoreslope=True, guessdelay=False,
                                fixed_delay=electric_delay)
        self.z_data = self.do_normalization(self.f_data, self.z_data_raw, delay, amp_norm, alpha,
                                            A2, frcal)
        self.fitresults = self.circlefit(self.f_data, self.z_data, fr, Ql, refine_results=False,
                                         calc_errors=True)
        self.fitresults["delay"] = delay
        self.fitresults["a"] = amp_norm
        self.fitresults["alpha"] = alpha
        self.z_data_sim = A2 * (self.f_data - frcal) + self._S11_directrefl(self.f_data,
                                                                            fr=self.fitresults[
                                                                                "fr"],
                                                                            Ql=self.fitresults[
                                                                                "Ql"],
                                                                            Qc=self.fitresults[
                                                                                "Qc"], a=amp_norm,
                                                                            alpha=alpha,
                                                                            delay=delay)



    def _S11_directrefl(self, f, fr=7e9, Ql=900, Qc=1000., a=1., alpha=0., delay=.0):
        '''
        full model for notch type resonances
        '''
        return a * np.exp(complex(0, alpha)) * np.exp(-2j * np.pi * f * delay) * (
                2. * Ql / Qc - 1. + 2j * Ql * (fr - f) / fr) / (1. - 2j * Ql * (fr - f) / fr)

    def get_single_photon_limit(self, unit='dBm'):
        '''
        returns the amout of power in units of W necessary
        to maintain one photon on average in the cavity
        unit can be 'dbm' or 'watt'
        '''
        if self.fitresults != {}:
            fr = self.fitresults['fr']
            k_c = 2 * np.pi * fr / self.fitresults['Qc']
            k_i = 2 * np.pi * fr / self.fitresults['Qi']
            if unit == 'dBm':
                return Watt2dBm(1. / (4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2)))
            elif unit == 'watt':
                return 1. / (4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2))

        else:
            warnings.warn('Please perform the fit first', UserWarning)
            return None

    def get_photons_in_resonator(self, power, unit='dBm'):
        '''
        returns the average number of photons
        for a given power (defaul unit is 'dbm')
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults != {}:
            if unit == 'dBm':
                power = dBm2Watt(power)
            fr = self.fitresults['fr']
            k_c = 2 * np.pi * fr / self.fitresults['Qc']
            k_i = 2 * np.pi * fr / self.fitresults['Qi']
            return 4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2) * power
        else:
            warnings.warn('Please perform the fit first', UserWarning)
            return None

class notch_port(circlefit, save_load, plotting, calibration):
    '''
    notch type port probed in transmission as basic class and
    the modification for tail-type resonator probed in reflection based on: https://arxiv.org/abs/2203.09247v1
    '''

    def __init__(self, f_data=None, z_data_raw=None):
        self.porttype = 'notch'
        self.fitresults = {}
        self.z_data = None
        if f_data is not None:
            self.f_data = np.array(f_data)
        else:
            self.f_data = None
        if z_data_raw is not None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data_raw = None

    def get_delay(self, f_data, z_data, delay=None, ignoreslope=True, guess=False):
        '''
        retrieves the cable delay assuming the ideal resonance has a circular shape
        modifies the cable delay until the shape Im(S21) vs Re(S21) is circular
        see "do_calibration"
        '''
        maxval = np.max(np.absolute(z_data))
        z_data = z_data / maxval
        A1, A2, A3, A4, fr, Ql = self._fit_skewed_lorentzian(f_data, z_data)
        if ignoreslope == True:
            A2 = 0.
        else:
            A2 = 0.
            # z_data = (np.absolute(z_data)-A2*(f_data-fr)) * np.exp(np.angle(z_data)*1j)  #usually not necessary
        if delay is None:
            if guess == True:
                delay = self._guess_delay(f_data, z_data)
            else:
                delay = 0.
            delay = self._fit_delay(f_data, z_data, delay, maxiter=200)
        params = [A1, A2, A3, A4, fr, Ql]
        return delay, params

    def do_calibration(self, f_data, z_data, ignoreslope=True, guessdelay=True):
        '''
        performs an automated calibration and tries to determine the prefactors a, alpha, delay
        fr, Ql, and a possible slope are extra information, which can be used as start parameters for subsequent fits
        see also "do_normalization"
        the calibration procedure works for transmission line resonators as well
        '''
        delay, params = self.get_delay(f_data, z_data, ignoreslope=ignoreslope, guess=guessdelay)
        z_data = (z_data - params[1] * (f_data - params[4])) * np.exp(
            2. * 1j * np.pi * delay * f_data)
        xc, yc, r0 = self._fit_circle(z_data)
        zc = complex(xc, yc)
        fitparams = self._phase_fit(f_data, self._center(z_data, zc), 0., np.absolute(params[5]),
                                    params[4])
        theta, Ql, fr = fitparams
        beta = self._periodic_boundary(theta + np.pi, np.pi)
        offrespoint = complex((xc + r0 * np.cos(beta)), (yc + r0 * np.sin(beta)))
        alpha = np.angle(offrespoint)
        a = np.absolute(offrespoint)

        return delay, a, alpha, fr, Ql, params[1], params[4]

    def do_normalization(self, f_data, z_data, delay, amp_norm, alpha, A2, frcal):
        '''
        removes the prefactors a, alpha, delay and returns the calibrated data, see also "do_calibration"
        works also for transmission line resonators
        '''
        return (z_data - A2 * (f_data - frcal)) / amp_norm * np.exp(
            1j * (-alpha + 2. * np.pi * delay * f_data))

    def circlefit(self, f_data, z_data, fr=None, Ql=None, refine_results=False, calc_errors=True):
        '''
        performs a circle fit on a frequency vs. complex resonator scattering data set
        Data has to be normalized!!
        INPUT:
        f_data,z_data: input data (frequency, complex S21 data)
        OUTPUT:
        outpus a dictionary {key:value} consisting of the fit values, errors and status information about the fit
        values: {"phi0":phi0, "Ql":Ql, "absolute(Qc)":absQc, "Qi": Qi, "electronic_delay":delay, "complexQc":complQc, "resonance_freq":fr, "prefactor_a":a, "prefactor_alpha":alpha}
        errors: {"phi0_err":phi0_err, "Ql_err":Ql_err, "absolute(Qc)_err":absQc_err, "Qi_err": Qi_err, "electronic_delay_err":delay_err, "resonance_freq_err":fr_err, "prefactor_a_err":a_err, "prefactor_alpha_err":alpha_err}
        for details, see:
            [1] (not diameter corrected) Jiansong Gao, "The Physics of Superconducting Microwave Resonators" (PhD Thesis), Appendix E, California Institute of Technology, (2008)
            [2] (diameter corrected) M. S. Khalil, et. al., J. Appl. Phys. 111, 054510 (2012)
            [3] (fitting techniques) N. CHERNOV AND C. LESORT, "Least Squares Fitting of Circles", Journal of Mathematical Imaging and Vision 23, 239, (2005)
            [4] (further fitting techniques) P. J. Petersan, S. M. Anlage, J. Appl. Phys, 84, 3392 (1998)
        the program fits the circle with the algebraic technique described in [3], the rest of the fitting is done with the scipy.optimize least square fitting toolbox
        also, check out [5] S. Probst et al. "Efficient and reliable analysis of noisy complex scatterung resonator data for superconducting quantum circuits" (in preparation)
        '''
        if fr is None: fr = f_data[np.argmin(np.absolute(z_data))]
        if Ql is None: Ql = 1e6
        xc, yc, r0 = self._fit_circle(z_data, refine_results=refine_results)
        phi0 = -np.arcsin(yc / r0)
        theta0 = self._periodic_boundary(phi0 + np.pi, np.pi)
        z_data_corr = self._center(z_data, complex(xc, yc))
        theta0, Ql, fr = self._phase_fit(f_data, z_data_corr, theta0, Ql, fr)
        # print "Ql from phasefit is: " + str(Ql)
        absQc = Ql / (2. * r0)
        complQc = absQc * np.exp(1j * ((-1.) * phi0))
        Qc = 1. / (
                1. / complQc).real  # here, taking the real part of (1/complQc) from diameter correction method
        Qi_dia_corr = 1. / (1. / Ql - 1. / Qc)
        Qi_no_corr = 1. / (1. / Ql - 1. / absQc)

        results = {"Qi_dia_corr": Qi_dia_corr, "Qi_no_corr": Qi_no_corr, "absQc": absQc,
                   "Qc_dia_corr(Re{Qc})": Qc, "Ql": Ql, "fr": fr, "theta0": theta0, "phi0": phi0}

        # calculation of the error
        p = [fr, absQc, Ql, phi0]
        # chi_square, errors = rt.get_errors(rt.residuals_notch_ideal,f_data,z_data,p)
        if calc_errors == True:
            chi_square, cov = self._get_cov_fast_notch(f_data, z_data, p)
            # chi_square, cov = rt.get_cov(rt.residuals_notch_ideal,f_data,z_data,p)

            if cov is not None:
                errors = np.sqrt(np.diagonal(cov))
                fr_err, absQc_err, Ql_err, phi0_err = errors
                # calc Qi with error prop (sum the squares of the variances and covariaces)
                dQl = 1. / ((1. / Ql - 1. / absQc) ** 2 * Ql ** 2)
                dabsQc = - 1. / ((1. / Ql - 1. / absQc) ** 2 * absQc ** 2)
                Qi_no_corr_err = np.sqrt((dQl ** 2 * cov[2][2]) + (dabsQc ** 2 * cov[1][1]) + (
                        2 * dQl * dabsQc * cov[2][1]))  # with correlations
                # calc Qi dia corr with error prop
                dQl = 1 / ((1 / Ql - np.cos(phi0) / absQc) ** 2 * Ql ** 2)
                dabsQc = -np.cos(phi0) / ((1 / Ql - np.cos(phi0) / absQc) ** 2 * absQc ** 2)
                dphi0 = -np.sin(phi0) / ((1 / Ql - np.cos(phi0) / absQc) ** 2 * absQc)
                ##err1 = ( (dQl*cov[2][2])**2 + (dabsQc*cov[1][1])**2 + (dphi0*cov[3][3])**2 )
                err1 = ((dQl ** 2 * cov[2][2]) + (dabsQc ** 2 * cov[1][1]) + (
                        dphi0 ** 2 * cov[3][3]))
                err2 = (dQl * dabsQc * cov[2][1] + dQl * dphi0 * cov[2][3] + dabsQc * dphi0 *
                        cov[1][3])
                Qi_dia_corr_err = np.sqrt(err1 + 2 * err2)  # including correlations
                errors = {"phi0_err": phi0_err, "Ql_err": Ql_err, "absQc_err": absQc_err,
                          "fr_err": fr_err, "chi_square": chi_square,
                          "Qi_no_corr_err": Qi_no_corr_err, "Qi_dia_corr_err": Qi_dia_corr_err}
                results.update(errors)
            else:
                print("WARNING: Error calculation failed!")
        else:
            # just calc chisquared:
            fun2 = lambda x: self._residuals_notch_ideal(x, f_data, z_data) ** 2
            chi_square = 1. / float(len(f_data) - len(p)) * (fun2(p)).sum()
            errors = {"chi_square": chi_square}
            results.update(errors)

        return results

    def autofit(self, calc_errors = False, return_norm_data = False):
        '''
        automatic calibration and fitting
        '''
        delay, amp_norm, alpha, fr, Ql, A2, frcal = \
            self.do_calibration(self.f_data, self.z_data_raw, ignoreslope=True, guessdelay=True)
        self.z_data = self.do_normalization(self.f_data, self.z_data_raw, delay, amp_norm, alpha,
                                            A2, frcal)

        self.fitresults = self.circlefit(self.f_data, self.z_data, fr, Ql, refine_results=False,
                                         calc_errors=calc_errors)
        self.fitresults["delay"] = delay
        self.fitresults["a"] = amp_norm
        self.fitresults["alpha"] = alpha
        self.z_data_sim = A2 * (self.f_data - frcal) + self._S21_notch(self.f_data,
                                                                       fr=self.fitresults["fr"],
                                                                       Ql=self.fitresults["Ql"],
                                                                       Qc=self.fitresults["absQc"],
                                                                       phi=self.fitresults["phi0"],
                                                                       a=amp_norm, alpha=alpha,
                                                                       delay=delay)
        # if return_norm_data: return z_data

    def _S21_notch(self, f, fr=10e9, Ql=900, Qc=1000., phi=0., a=1., alpha=0., delay=.0):
        '''
        full model for notch type resonances
        '''
        return a * np.exp(complex(0, alpha)) * np.exp(-2j * np.pi * f * delay) * (
                1. - Ql / Qc * np.exp(1j * phi) / (1. + 2j * Ql * (f - fr) / fr))

    def get_single_photon_limit(self, unit='dBm', diacorr=True):
        '''
        returns the amout of power in units of W necessary
        to maintain one photon on average in the cavity
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults != {}:
            fr = self.fitresults['fr']
            if diacorr:
                k_c = 2 * np.pi * fr / self.fitresults['Qc_dia_corr(Re{Qc})']
                k_i = 2 * np.pi * fr / self.fitresults['Qi_dia_corr']
            else:
                k_c = 2 * np.pi * fr / self.fitresults['absQc']
                k_i = 2 * np.pi * fr / self.fitresults['Qi_no_corr']
            if unit == 'dBm':
                return Watt2dBm(1. / (4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2)))
            elif unit == 'watt':
                return 1. / (4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2))
        else:
            warnings.warn('Please perform the fit first', UserWarning)
            return None

    def get_photons_in_resonator(self, power, unit='dBm', diacorr=True):
        '''
        returns the average number of photons
        for a given power in units of W
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults != {}:
            if unit == 'dBm':
                power = dBm2Watt(power)
            fr = self.fitresults['fr']
            if diacorr:
                k_c = 2 * np.pi * fr / self.fitresults['Qc_dia_corr(Re{Qc})']
                k_i = 2 * np.pi * fr / self.fitresults['Qi_dia_corr']
            else:
                k_c = 2 * np.pi * fr / self.fitresults['absQc']
                k_i = 2 * np.pi * fr / self.fitresults['Qi_no_corr']
            return 4. * k_c / (2. * np.pi * hbar * fr * (k_c + k_i) ** 2) * power
        else:
            warnings.warn('Please perform the fit first', UserWarning)
            return None

    def tail_port(self, f_data, z_data, plot=False, refine_results=False):
        '''
        The modification is based on the affine frequency transformation with respect to the resonant frequency.
        If we compare the formulas for notch-port and tail-port:
        Notch port: a * np.exp(np.complex(0, alpha)) * np.exp(-2j * np.pi * f * delay) * (
                    1. - Ql / Qc * np.exp(1j * phi) / (1. + 2j * Ql * (f - fr) / fr))
        Tail-port: a * np.exp(np.complex(0, alpha)) * np.exp(-2j * np.pi * f * delay) * (
                    1. - Ql / Qc * np.exp(1j * phi) / (1. - 2j * Ql * (f - fr) / fr))
        So the only difference is in the sing in the denominator,hence the transformation f_new = -f_raw + 2 * fr will
            bring us to notch-port resonator. Finally a back transformation is made.

        :param f_data: full numpy array of frequencies in Hz
        :param z_data: complex S-parameter numpy array
        '''

        def freq_transform (freqs, S_data):
            '''
            :param freqs: full numpy array of frequencies in Hz
            :param S_data: complex S-parameter numpy array
            :return: numpy array of reformed to notch-port frequencies in Hz, complex S-parameter numpy array, base reflection frequency (fr_guess) in Hz
            '''
            if len(freqs)==0: print("frequency array is empty")
            elif len(S_data)==0: print("S-array is empty")

            num_res = np.argmax(np.angle(S_data)) # the number of the array element that corresponds to the extremum of the phase function (assumed resonance)
            fr_guess = freqs[num_res]             # the guess resonant frequency (used for reverse conversion)
            freqs = -freqs + 2 * fr_guess         # affine frequency transformation
            return freqs, S_data, fr_guess

        def back_freq_transform (freqs, fr_guess):
            '''
            :param freqs: full numpy array of frequencies in Hz
            :param fr_guess: the guess resonant frequency
            :return: numpy array of reformed back to tail-port basis frequencies in Hz
            '''
            f_data = -freqs + 2 * fr_guess
            return f_data


        f_data, S_data, fr_guess = freq_transform(f_data, z_data)  # transformed data now can be used for standard notch-port fitting.

        # For some reason, the automatic fit does not work on its own, so the first step is copied to this function without changes from _fit_circle.
        # If it works - don't touch it.  ¯\_ (ツ)_/¯


        def calc_moments (z_data):
            xi = z_data.real
            xi_sqr = xi * xi
            yi = z_data.imag
            yi_sqr = yi * yi
            zi = xi_sqr + yi_sqr
            Nd = float(len(xi))
            xi_sum = xi.sum()
            yi_sum = yi.sum()
            zi_sum = zi.sum()
            xiyi_sum = (xi * yi).sum()
            xizi_sum = (xi * zi).sum()
            yizi_sum = (yi * zi).sum()
            return np.array([[(zi * zi).sum(), xizi_sum, yizi_sum, zi_sum], \
                             [xizi_sum, xi_sqr.sum(), xiyi_sum, xi_sum], \
                             [yizi_sum, xiyi_sum, yi_sqr.sum(), yi_sum], \
                             [zi_sum, xi_sum, yi_sum, Nd]])

        M = calc_moments(z_data)

        a0 = ((M[2][0] * M[3][2] - M[2][2] * M[3][0]) * M[1][1] - M[1][2] * M[2][0] * M[3][1] - M[1][0] * M[2][1] *
              M[3][2] + M[1][0] * M[2][2] * M[3][1] + M[1][2] * M[2][1] * M[3][0]) * M[0][3] + (
                     M[0][2] * M[2][3] * M[3][0] - M[0][2] * M[2][0] * M[3][3] + M[0][0] * M[2][2] * M[3][3] - M[0][
                 0] * M[2][3] * M[3][2]) * M[1][1] + (
                     M[0][1] * M[1][3] * M[3][0] - M[0][1] * M[1][0] * M[3][3] - M[0][0] * M[1][3] * M[3][1]) * \
             M[2][2] + (-M[0][1] * M[1][2] * M[2][3] - M[0][2] * M[1][3] * M[2][1]) * M[3][0] + (
                     (M[2][3] * M[3][1] - M[2][1] * M[3][3]) * M[1][2] + M[2][1] * M[3][2] * M[1][3]) * M[0][0] + (
                     M[1][0] * M[2][3] * M[3][2] + M[2][0] * (M[1][2] * M[3][3] - M[1][3] * M[3][2])) * M[0][1] + (
                     (M[2][1] * M[3][3] - M[2][3] * M[3][1]) * M[1][0] + M[1][3] * M[2][0] * M[3][1]) * M[0][2]
        a1 = (((M[3][0] - 2. * M[2][2]) * M[1][1] - M[1][0] * M[3][1] + M[2][2] * M[3][0] + 2. * M[1][2] * M[2][1] -
               M[2][0] * M[3][2]) * M[0][3] + (
                      2. * M[2][0] * M[3][2] - M[0][0] * M[3][3] - 2. * M[2][2] * M[3][0] + 2. * M[0][2] * M[2][
                  3]) * M[1][1] + (-M[0][0] * M[3][3] + 2. * M[0][1] * M[1][3] + 2. * M[1][0] * M[3][1]) * M[2][
                  2] + (-M[0][1] * M[1][3] + 2. * M[1][2] * M[2][1] - M[0][2] * M[2][3]) * M[3][0] + (
                      M[1][3] * M[3][1] + M[2][3] * M[3][2]) * M[0][0] + (
                      M[1][0] * M[3][3] - 2. * M[1][2] * M[2][3]) * M[0][1] + (
                      M[2][0] * M[3][3] - 2. * M[1][3] * M[2][1]) * M[0][2] - 2. * M[1][2] * M[2][0] * M[3][
                  1] - 2. * M[1][0] * M[2][1] * M[3][2])
        a2 = ((2. * M[1][1] - M[3][0] + 2. * M[2][2]) * M[0][3] + (2. * M[3][0] - 4. * M[2][2]) * M[1][1] - 2. *
              M[2][
                  0] * M[3][2] + 2. * M[2][2] * M[3][0] + M[0][0] * M[3][3] + 4. * M[1][2] * M[2][1] - 2. * M[0][
                  1] * M[1][
                  3] - 2. * M[1][0] * M[3][1] - 2. * M[0][2] * M[2][3])
        a3 = (-2. * M[3][0] + 4. * M[1][1] + 4. * M[2][2] - 2. * M[0][3])
        a4 = -4.

        def func (x):
            return a0 + a1 * x + a2 * x * x + a3 * x * x * x + a4 * x * x * x * x

        def d_func (x):
            return a1 + 2 * a2 * x + 3 * a3 * x * x + 4 * a4 * x * x * x

        x0 = spopt.fsolve(func, 0., fprime=d_func)

        def solve_eq_sys (val, M):
            # prepare
            M[3][0] = M[3][0] + 2 * val
            M[0][3] = M[0][3] + 2 * val
            M[1][1] = M[1][1] - val
            M[2][2] = M[2][2] - val
            return np.linalg.svd(M)

        U, s, Vt = solve_eq_sys(x0[0], M)

        A_vec = Vt[np.argmin(s), :]

        xc = -A_vec[1] / (2. * A_vec[0])
        yc = -A_vec[2] / (2. * A_vec[0])
        # the term *sqrt term corrects for the constraint, because it may be altered due to numerical inaccuracies during calculation
        r0 = 1. / (2. * np.absolute(A_vec[0])) * np.sqrt(
            A_vec[1] * A_vec[1] + A_vec[2] * A_vec[2] - 4. * A_vec[0] * A_vec[3])
        if refine_results:
            print("agebraic r0: " + str(r0))
            xc, yc, r0 = self._fit_circle_iter(z_data, xc, yc, r0)
            r0 = self._fit_circle_iter_radialweight(z_data, xc, yc, r0)
            print("iterative r0: " + str(r0))

        S_data = np.real(S_data) - xc + 1j * (np.imag(S_data) + yc)

        # The function was copied to this place, then again my code
        # Next, a filtering algorithm is implemented that removes point outliers.

        factor = 0.2 # You can vary this factor to discard more noise, although I would recommend using it only for oint outliers. Base 0.2
        S_data_filtered = S_data[0:3]
        f_data_filtered = f_data[0:3]
        for i in range(3, len(f_data) - 3):
            r1 = np.abs(np.real(S_data[i - 3: i - 1]))
            r2 = np.abs(np.imag(S_data[i - 3: i - 1]))

            avg_re = np.mean(r1)
            avg_im = np.mean(r2)
            if (np.abs(np.abs(np.real(S_data[i])) - avg_re) < factor) or (
                    np.abs(np.abs(np.imag(S_data[i])) - avg_im) < factor):
                S_data_filtered = np.append(S_data_filtered, S_data[i])
                f_data_filtered = np.append(f_data_filtered, f_data[i])
        S_data_filtered = np.append(S_data_filtered, S_data[len(f_data) - 3:])
        f_data_filtered = np.append(f_data_filtered, f_data[len(f_data) - 3:])


        port1 = notch_port(f_data_filtered, S_data_filtered) # Finally notch-port fitting, f_data_filtered in Hz
        port1.autofit()
        # port1.plotall()

        fitresults = port1.fitresults
        f_tail = back_freq_transform(f_data_filtered, fr_guess)


        def S11_tail (f, fr=6e9, Ql=900, Qc=1000., phi=0., a=1., alpha=0., delay=.0):
            '''
            full model for tail type resonances
            1/Ql=1/Qi+1/Re{Qc}, where Qc is complex. Ql < Re{Qc}
            '''
            return a * np.exp(complex(0, alpha)) * np.exp(-2j * np.pi * f * delay) * (
                    1. - Ql / Qc * np.exp(1j * phi) / (1. - 2j * Ql * (f - fr) / fr))

        S_fit = S11_tail(f_tail,
                          fr=back_freq_transform(fitresults["fr"], fr_guess),
                          Ql=fitresults["Ql"],
                          Qc=fitresults["absQc"],
                          phi=fitresults["phi0"],
                          a=fitresults["a"], alpha=fitresults["alpha"],
                          delay=fitresults["delay"])

        def plotall (f, S, S_fit):
            real = S.real
            imag = S.imag
            real2 = S_fit.real
            imag2 = S_fit.imag
            fig = plt.figure(figsize=(15, 5))
            plt.suptitle('Tail-port resonator fit')
            fig.canvas.set_window_title("Resonator fit")
            plt.subplot(131)
            plt.plot(real, imag, label='rawdata')
            plt.plot(real2, imag2, label='fit')
            plt.xlabel('Re(S21)')
            plt.ylabel('Im(S21)')
            plt.legend()
            plt.subplot(132)
            plt.plot(f * 1e-9, np.absolute(S), label='rawdata')
            plt.plot(f * 1e-9, np.absolute(S_fit), label='fit')
            plt.xlabel('f (GHz)')
            plt.ylabel('Amplitude')
            plt.legend()
            plt.subplot(133)
            plt.plot(f * 1e-9, np.unwrap(np.angle(S)), label='rawdata')
            plt.plot(f * 1e-9, np.unwrap(np.angle(S_fit)), label='fit')
            plt.xlabel('f (GHz)')
            plt.ylabel('Phase')
            plt.legend()
            # plt.gcf().set_size_inches(15,5)
            plt.tight_layout()
            plt.show()

        if plot: plotall(f_tail, S_data_filtered, S_fit)

        return f_tail, S_fit, fitresults



class transmission_port(circlefit, save_load, plotting):
    '''
    a class for handling transmission measurements
    '''

    def __init__(self, f_data=None, z_data_raw=None):
        self.porttype = 'transm'
        self.fitresults = {}
        if f_data is not None:
            self.f_data = np.array(f_data)
        else:
            self.f_data = None
        if z_data_raw is not None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data = None

    def _S21(self, f, fr, Ql, A):
        return A ** 2 / (1. + 4. * Ql ** 2 * ((f - fr) / fr) ** 2)

    def fit(self):
        self.ampsqr = (np.absolute(self.z_data_raw)) ** 2
        p = [self.f_data[np.argmax(self.ampsqr)], 1000., np.amax(self.ampsqr)]
        popt, pcov = spopt.curve_fit(self._S21, self.f_data, self.ampsqr, p)
        errors = np.sqrt(np.diag(pcov))
        self.fitresults = {'fr': popt[0], 'fr_err': errors[0], 'Ql': popt[1], 'Ql_err': errors[1],
                           'Ampsqr': popt[2], 'Ampsqr_err': errors[2]}

class resonator(object):
    '''
    Universal resonator analysis class
    It can handle different kinds of ports and assymetric resonators.
    '''

    def __init__(self, ports={}, comment=None):
        '''
        initializes the resonator class object
        ports (dictionary {key:value}): specify the name and properties of the coupling ports
            e.g. ports = {'1':'direct', '2':'notch'}
        comment: add a comment
        '''
        self.comment = comment
        self.port = {}
        self.transm = {}
        if len(ports) > 0:
            for key, pname in ports.items():
                if pname == 'direct':
                    self.port.update({key: reflection_port()})
                elif pname == 'notch':
                    self.port.update({key: notch_port()})
                else:
                    warnings.warn("Undefined input type! Use 'direct' or 'notch'.", SyntaxWarning)
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)

    def add_port(self, key, pname):
        if pname == 'direct':
            self.port.update({key: reflection_port()})
        elif pname == 'notch':
            self.port.update({key: notch_port()})
        else:
            warnings.warn("Undefined input type! Use 'direct' or 'notch'.", SyntaxWarning)
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)

    def delete_port(self, key):
        del self.port[key]
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)

    def get_Qi(self):
        '''
        based on the number of ports and the corresponding measurements
        it calculates the internal losses
        '''
        pass

    def get_single_photon_limit(self, port):
        '''
        returns the amout of power necessary to maintain one photon
        on average in the cavity
        '''
        pass

    def get_photons_in_resonator(self, power, port):
        '''
        returns the average number of photons
        for a given power
        '''
        pass

    def add_transm_meas(self, port1, port2):
        '''
        input: port1
        output: port2
        adds a transmission measurement
        connecting two direct ports S21
        '''
        key = port1 + " -> " + port2
        self.port.update({key: transm()})
        pass

class batch_processing(object):
    '''
    A class for batch processing of resonator data as a function of another variable
    Typical applications are power scans, magnetic field scans etc.
    '''

    def __init__(self, porttype):
        '''
        porttype = 'notch', 'direct', 'transm'
        results is an array of dictionaries containing the fitresults
        '''
        self.porttype = porttype
        self.results = []

    def autofit(self, cal_dataslice=0):
        '''
        fits all data
        cal_dataslice: choose scatteringdata which should be used for calibration
        of the amplitude and phase, default = 0 (first)
        '''
        pass

class coupled_resonators(batch_processing):
    '''
    A class for fitting a resonator coupled to a second one
    '''

    def __init__(self, porttype):
        self.porttype = porttype
        self.results = []
