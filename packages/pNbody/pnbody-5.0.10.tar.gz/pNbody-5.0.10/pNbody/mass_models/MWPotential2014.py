#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      MWPotential2014.py
#  brief:     Defines a Milky Way like potential based on the one from galpy
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from scipy.special import gamma, gammainc
from astropy import units as u
from astropy.constants import G as G_a

from pNbody.mass_models import miyamoto as mn
from pNbody.mass_models import nfw
from pNbody.mass_models import powerSphericalCutoff as psc

from scipy.special import gamma, gammainc

##########################################################
# Utility functions
#########################################################


def __miyamoto_nagai_Vcirc(M, a, b, R, z, G=1.0):
    """
    Computes the velocity for the Miyamoto-Nagai potential.

    Parameters
    ----------
    M : double
        Mass of the disk.
    a : double
        Radial scale length.
    b : double
        z scale length.
    R : double, array
        The cylindrical radius.
    z : double, array
        The z coordinate.
    G : double, optional
        Newton gravitationial constant. The default is 1.0.

    Returns
    -------
    double, array
        The velocity.

    """
    factor = G*M/(R**2 + (a + np.sqrt(z**2 + b**2))**2)**1.5
    part_R = R**2
    part_z = z**2 * (a + np.sqrt(z**2 + b**2))/np.sqrt(z**2 + b**2)
    return np.sqrt(factor*(part_R + part_z))


def MW_time_evolution_factor(time, slope=0.09):
    """Time dependent multiplicative factor to change the mass off the
    MWPotential as time evolves. We assume a linear growth in time. This is
    roughly valid during the last 10 Gyr. """
    return slope*time + 1


#########################################################
# Main content
#########################################################

def Potential(rho0, r_s, M, a, b, alpha, r_c, amplitude, r_1, f_1, f_2, f_3, R, z, G=1.0):
    """
    Potential
    """
    r = np.sqrt(R**2 + z**2)
    phi_NFW = nfw.Potential(rho0, r_s, r, G)
    phi_MN = mn.Potential(M, a, b, R, z, G)
    phi_PSC = psc.Potential(alpha, r_c, amplitude, r_1, r, G)
    return f_1*phi_NFW + f_2*phi_MN + f_3*phi_PSC


def Density(rho0, r_s, M, a, b, alpha, r_c, amplitude, r_1, f_1, f_2, f_3, R, z, G=1.0):
    """
    Density
    """
    r = np.sqrt(R**2 + z**2)
    rho_NFW = nfw.Density(rho0, r_s, r, G)
    rho_MN = mn.Density(M, a, b, R, z, G)
    rho_PSC = psc.Density(alpha, r_c, amplitude, r_1, r, G)
    return f_1*rho_NFW + f_2*rho_MN + f_3*rho_PSC


def Vcirc(rho0, r_s, M, a, b, alpha, r_c, amplitude, r_1, f_1, f_2, f_3, R, z, G=1.0):
    """
    Circular velocity
    """
    r = np.sqrt(R**2 + z**2)
    v_circ_NFW = nfw.Vcirc(rho0, r_s, r, G)
    v_circ_MN = __miyamoto_nagai_Vcirc(M, a, b, R, z, G)
    v_circ_PSC = psc.Vcirc(alpha, r_c, amplitude, r_1, r, G)
    v_circ_tot = np.sqrt(f_1*v_circ_NFW**2 + f_2 *
                         v_circ_MN**2 + f_3*v_circ_PSC**2)
    return v_circ_tot


def GradPot(rho_0, r_s, M, a, b, alpha, r_c,
            amplitude,  r_1, f_1, f_2, f_3, position, time, G=1):
    """Gradient of MW potential in carthesian coordinates. For orbit integration."""

    # Treat cases for the shape of position (a numpy vector or a 3n numpy array)
    # if We have an array 3xn of positions
    if len(position.shape) > 1 and position.shape[1] > 1:
        x = position[0, :]
        y = position[1, :]
        z = position[2, :]
    else:  # If we have a vector [x y z], we have len(shape)=1
        x = position[0]
        y = position[1]
        z = position[2]

    # Convenient variables
    r = np.linalg.norm(position, axis=0)
    R = np.sqrt(x**2 + y**2)

    # NFW componenent
    M_NFW = 4*np.pi*rho_0*r_s**3 * (np.log(1 + r/r_s) - r/(r + r_s))
    d_Phi_NFW_dr = G * M_NFW/r**2
    grad_phi_NFW = d_Phi_NFW_dr * np.array([x/r, y/r, z/r])

    # MN component
    d_Phi_dR = G*M*R / (R**2 + (a + np.sqrt(z**2 + b**2))**2)**1.5
    d_Phi_dz = G*M*z / \
        (R**2 + (a + np.sqrt(z**2 + b**2))**2)**1.5 * \
        (1 + a / np.sqrt(z**2 + b**2))
    grad_phi_MN = np.array([d_Phi_dR * x/R, d_Phi_dR * y/R,  d_Phi_dz])

    # Bulge component
    M_bulge = 2*np.pi*amplitude*r_1**alpha * \
        r_c**(3.0-alpha) * gammainc(1.5-alpha /
                                    2, r**2/r_c**2)*gamma(1.5-alpha/2)
    d_phi_bulge_dr = G * M_bulge/r**2
    grad_phi_bulge = d_phi_bulge_dr*np.array([x/r, y/r, z/r])

    # Total gradient
    grad_Phi = f_1*grad_phi_NFW + f_2*grad_phi_MN + f_3*grad_phi_bulge
    return grad_Phi


def MWPotential2014_parameters():
    """
    Returns the parameters of the potential MWPotential2014 given by Bovy in his 
    paper: galpy: A Python Library for Galactic Dynamics, Jo Bovy (2015), 
    Astrophys. J. Supp., 216, 29 (arXiv/1412.3451). The units are kpc, 1e10*M_sun
    and km/s.

    Returns
    -------
    params : Dictionnary
        The parameters of the potential corresponding to the Milky Way.

    """
    unit_length = 1*u.kpc
    unit_mass = 1e10*u.M_sun
    unit_mass = unit_mass.to(unit_mass)
    unit_time = 3.086e16*u.s
    # unit_velocity = unit_length/unit_time
    G = G_a.to(unit_length**3 * unit_mass**(-1) * unit_time**(-2))

    # NFW parameters
    r_s = 16*unit_length
    M_200 = 147.4103154277408*unit_mass
    r_200 = 157.1744550043975*unit_length
    c = r_200/r_s
    log_c200_term = np.log(1 + c) - c / (1. + c)
    rho_0 = M_200 / (4 * np.pi * r_s**3 * log_c200_term)
    rho_0 = rho_0.to(unit_mass/unit_length**3)
    rho_c = M_200/(200*4/3*np.pi*r_200**3)
    H_0 = np.sqrt(8*np.pi*G/3 * rho_c).to(1/unit_time)

    # MN parameters
    M_disk = 6.8
    a = 3.0
    b = 0.280

    # PSC parameters
    alpha = 1.8
    r_c = 1.9
    amplitude = 1.0
    r_1 = 1.0

    # Potential contribution
    f_1 = 0.4367419745056084
    f_2 = 1.002641971008805
    f_3 = 0.022264787598364262

    # Defines the dictionnary
    params = {"rho_0": rho_0.value, "r_s": r_s.value, "M_disk": M_disk, "a": a, "b": b, "alpha": alpha,
              "r_c": r_c, "amplitude": amplitude, "r_1": r_1, "f_1": f_1, "f_2": f_2, "f_3": f_3, "c": c.value,
              "M_200": M_200.value, "r_200": r_200.value, "rho_c": rho_c.value, "H_0": H_0.value}
    return params
