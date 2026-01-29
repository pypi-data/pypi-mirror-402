#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      isochrone.py
#  brief:     Defines isochrone profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
isochrone model
"""

import numpy as np


def Potential(M, b, r, G=1.):
    """
    Potential
    """
    return -G * M / (b + np.sqrt(r**2 + b**2))


def Density(M, b, r, G=1.):
    """
    Density
    """
    a = np.sqrt(b**2+r**2)
    return M* (3*(b+a)*a**2 - r**2*(b+3*a))/( 4*np.pi * (b+a)**3 * a**3 )
    


def Vcirc(M, b, r, G=1.):
    """
    circular velocity
    """
    a = np.sqrt(b**2+r**2)
    return np.sqrt(G * M * r**2 / ( a*(b+a)**2) )
