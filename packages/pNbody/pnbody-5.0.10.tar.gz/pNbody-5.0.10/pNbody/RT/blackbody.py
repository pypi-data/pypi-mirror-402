###########################################################################################
#  package:   RT
#  file:      blackbody.py
#  brief:     blackbody usefull routines
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Mladen Ivkovic <mladen.ivkovic@durham.ac.uk>
#
# This file is part of pNbody.
###########################################################################################

# ------------------------------------------
# Blackbody spectrum related functions.
# ------------------------------------------

import numpy as np


def B_nu(nu, T, kB, h_planck, c):
    """
    Return the blackbody energy density for
    a temperature T and frequency nu
    """
    res = 2.0 * h_planck * nu ** 3 / c ** 2 / (np.exp(h_planck * nu / kB / T) - 1.0)
    return res


def B_l(l, T, kB, h_planck, c):
    """
    Return the blackbody energy density for
    a temperature T and wavelength l
    """
    res = 2.0 * h_planck * c ** 2 / l ** 5 / (np.exp(h_planck * c / l / kB / T) - 1.0)
    return res




def B_nu_over_h_nu(nu, T, kB, h_planck, c):
    return B_nu(nu, T, kB, h_planck, c) / (h_planck * nu)


def nu_peak(T, kB, h_planck):
    """
    Return the (approximate) frequency where the peak of the
    blackbody energy density spectrum should be
    """
    return 2.82144 * kB * T / h_planck



