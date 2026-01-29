#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libmiyamoto.py
#  brief:     Defines Miyamoto profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np



def Potential(M, a, R, z, G=1.):
    """
    Kuzmin Potential
    """
    return -G * M / np.sqrt(R**2 + (a + np.sqrt(z**2))**2)


def Vcirc(M, a, R, G=1.):
    """
    Kuzmin Circular velocity
    """
    return np.sqrt(G * M / (R**2 + a**2)**1.5 * R**2)


def Omega(M, a, R, G=1.):
    """
    Kuzmin-Nagai Omega
    """
    return np.sqrt(G * M / R**3)


def Kappa(M, a, R, G=1.):
    """
    Kuzmin Kappa
    """

    r2 = R * R
    x = np.sqrt(r2 + a**2)
    return np.sqrt(G * M * (-3. * r2 / x**5 + 4. / x**3))


def SurfaceDensity(M, a, R, G=1.):
    """
    Kuzmin Density
    """

    R2 = R * R

    return a*M/(2*np.pi) / (R2 + a**2)**(3/2.)




def dR_Potential(M, a, R, z, G=1.):
    """
    first derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return G * M * R / R2azb2**(3.0 / 2.0)


def d2R_Potential(M, a, R, z, G=1.):
    """
    second derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return -3 * G * M * R2 * \
        R2azb2**(-5.0 / 2.0) + G * M * R2azb2**(-3.0 / 2.0)


def dz_Potential(M, a, R, z, G=1.):
    """
    first derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return G * M * z * (a + zb) / (R2azb2**(3.0 / 2.0) * zb)


def d2z_Potential(M, a, R, z, G=1.):
    """
    second derivative in R
    """

    R2 = R * R
    z2 = z * z
    zb2 = z**2
    zb = np.sqrt(zb2)
    azb = a + zb
    azb2 = azb**2

    R2azb2 = R2 + azb2

    c1 = -3 * z2 * azb2 / (R2azb2**(5.0 / 2.0) * zb2)
    c2 = z2 / (R2azb2**(3.0 / 2.0) * zb2)
    c3 = -  z2 * azb / (R2azb2**(3.0 / 2.0) * zb**3.0)
    c4 = azb / (R2azb2**(3.0 / 2.0) * zb)

    return G * M * (c1 + c2 + c3 + c4)





