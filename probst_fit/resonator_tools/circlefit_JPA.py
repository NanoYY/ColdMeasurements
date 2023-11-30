import numpy as np
import scipy.optimize as spopt
from scipy import stats

class circleJPAfit(object):
    '''
    contains all the circlefit procedures
    see http://scitation.aip.org/content/aip/journal/rsi/86/2/10.1063/1.4907935
    arxiv version: http://arxiv.org/abs/1410.3365
    '''
    def _remove_cable_delay(self,f_data,z_data, delay):
        return z_data/np.exp(2j*np.pi*f_data*delay)

    def _center(self,z_data,zc):
        return z_data-zc

    def _dist(self,x):
        np.absolute(x,x)
        c = (x > np.pi).astype(np.int)
        return x+c*(-2.*x+2.*np.pi)

    def _periodic_boundary(self,x,bound):
        return np.fmod(x,bound)-np.trunc(x/bound)*bound # ???????????????????????????????