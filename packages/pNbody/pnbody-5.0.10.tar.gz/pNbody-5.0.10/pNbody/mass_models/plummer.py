#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      plummer.py
#  brief:     Defines plummer profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
plummer model
"""

import numpy as np


def Potential(M, a, r, G=1.):
    """
    Plummer Potential
    """
    return -G * M / np.sqrt(r**2 + a**2)


def dPotential(M, a, r, G=1.):
    """
    Plummer first derivative of Potential
    """
    return G * M * r * (r**2 + a**2)**(-3. / 2.)


def CumulativeMass(M, a, r, G=1.):
    """
    Plummer cumulative mass
    """
    return M * r**3 / (r**2 + a**2 )**(3./2.)


def TotalMass(M, a, G=1.):
    """
    Plummer total mass
    """
    return M 
    


def Vcirc(M, a, r, G=1.):
    """
    Plummer circular velocity
    """
    return np.sqrt(G * M * r**2 * (r**2 + a**2)**(-3. / 2.))


def Density(M, a, r, G=1.):
    """
    Plummer Density
    """
    return (3. * M / (4. * np.pi * a**3)) * (1 + (r / a)**2)**(-5. / 2.)


def LDensity(M, a, r, G=1.):
    """
    Plummer Linear Density
    """
    return (4 * np.pi * r**2) * (3. * M / (4. * np.pi * a**3)) * \
        (1 + (r / a)**2)**(-5. / 2.)


def Sigma(M, a, r, G=1.):
    """
    Return sigma (radial) from Jeans equation : 1/rho Int( rho * drPhi * dr )
    """
    sigma = 1. / (8 * np.pi * Density(G, M, a, r)) * \
        G * M**2 * a**2 / (r**2 + a**2)**3
    return np.sqrt(sigma)
