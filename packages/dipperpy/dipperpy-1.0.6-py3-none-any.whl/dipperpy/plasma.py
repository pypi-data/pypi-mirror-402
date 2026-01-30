################################################################################
#
# Main subprograms for dipper package
#
################################################################################

import sqlite3
import numpy as np
import dipperpy as dp
from scipy.interpolate import CubicSpline
from scipy import interpolate, special
from matplotlib import pyplot as plt
from astropy.io import ascii
import scipy.special as sp
import time
import copy
import sys
import math

################################################################################
################################################################################
#                              CLASS
################################################################################
################################################################################
class plasma:

    # following should be replaced by input file
    uu=1.66e-24
    geometry='1D'
    ndepth=20
    te=8000. + np.arange(0,ndepth)
    nne=5.e9 +te*0.
    meanm=1.e-2
    fulldepth=1.e9
    nnh= meanm/1.3625/uu/ndepth/fulldepth + te*0.
    rho = nnh*1.3625*uu
    vturb=1.e6 + te*0.
    b=1.e1 + te*0.
    boundaries=['thin','thin']

    def __init__(self):
        pass




    def hminus(nh,pe):   #   PGJ dev
        #
        # returns opacity in inverse cm
        # for input nh and electron pressure (cgs)
        # as a function of wavelength in cm
        #
        print("hminus - warning constant value assumed with wavelength")
        return nh*pe/10.**24.8 # a mean value only


print(plasma.geometry)
print(plasma.nne)
print(plasma.nnh)
print(plasma.boundaries)

#print(hminus(self,nnh,bk*te*nne))
print(plasma.hminus(plasma.nnh,dp.dipall.bk*plasma.te*plasma.nne))
