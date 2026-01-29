#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      profiles.py
#  brief:     Defines different halo profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


from pNbody import *
import numpy as np

from scipy import integrate
from scipy import optimize
from scipy import special
from scipy.integrate import quad


###############################
# A New Family of Models for Spherical Stellar Systems
###############################
#
# http://arxiv.org/abs/1003.0259
#

###############################
# Plummer profile
###############################


def plummer_profile(r, rc, rho0=1.):
    """
    Plummer profile
    rho = 1/(1+(r/rc)**2)**(5/2)
    """
    return rho0 / (1 + (r / rc)**2)**(5. / 2.)


def plummer_mr(r, rc, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = 1/(1+(r/rc)**2)**(5/2)
    """
    return (4. / 3.) * np.pi * rho0 * rc**3 * r**3 / (r**2 + rc**2)**(3. / 2.)


###############################
# generic2c
###############################


def generic2c_mr(r, rs, a, b, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = 1/( (r/rs)**a * (1+r/rs)**(b-a) )
    """
    if not is_scipy:
        raise Exception("scipy is needed for these function")

    a = float(a)
    b = float(b)

    aa = b - a
    bb = -a + 3
    cc = 4 - a
    z = -r / rs

    return rho0 * 4 * np.pi * (r / rs)**(-a) * r**3 * \
        special.hyp2f1(aa, bb, cc, z) / bb


def generic2c_profile(r, rs, a, b, rho0=1.):
    """
    generic2c profile
    rho = 1/( (r/rs)**a * (1+r/rs)**(b-a) )

    """
    a = float(a)
    b = float(b)

    return rho0 / ((r / rs)**a * (1 + r / rs)**(b - a))


###############################
# Hernquist profile
###############################


def hernquist_profile(r, rs, rho0=1.):
    """
    hernquist profile
    rho = 1/( (r/rs) * (1+r/rs)**3 )

    """
    return rho0 / ((r / rs) * (1 + r / rs)**3)


def hernquist_mr(r, rs, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = 1/( (r/rs) * (1+r/rs)**3 )
    """
    return 4 * np.pi * rho0 * rs**3 * 0.5 * (r / rs)**2 / (1 + r / rs)**2


def hernquist_mR(R, rs, rho0=1):
    """
    Mass in the projected radius R for the distribution
    rho = 1/( (r/rs) * (1+r/rs)**3 )

    (Hernquist 90, Eq. 37)

    Warning : the function diverges in r=0 and r/rs=1.
    Warning : it is badly implemented for arrays
    """

    if isinstance(R, np.ndarray):

        def X(s):

            Y = np.zeros(len(s), float)
            for i in range(len(s)):

                if s[i] <= 1:
                    Y[i] = 1. / np.sqrt(1. - s[i]**2) * \
                        np.log((1. + np.sqrt(1. - s[i]**2)) / s[i])
                else:
                    Y[i] = 1. / np.sqrt(s[i]**2 - 1.) * np.arccos(1. / s[i])

            return Y

    else:

        def X(s):

            if s <= 1:
                Y = 1. / np.sqrt(1. - s**2) * np.log((1. + np.sqrt(1. - s**2)) / s)
            else:
                Y = 1. / np.sqrt(s**2 - 1.) * np.arccos(1. / s)

            return Y

    s = R / rs

    return rho0 * s**2 / (1 - s**2) * (X(s) - 1.)


###############################
# jaffe
###############################


def jaffe_profile(r, rs, rho0=1.):
    """
    jaffe profile
    rho = 1/( (r/rs)**2 * (1+r/rs)**2 )

    """
    return rho0 / ((r / rs)**2 * (1 + r / rs)**2)


def jaffe_mr(r, rs, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = 1/( (r/rs)**2 * (1+r/rs)**2 )
    """
    return 4 * np.pi * rho0 * rs**3 * (r / rs) / (1 + r / rs)


###############################
# NFW profile
###############################

def nfw_profile(r, rs, rho0=1.):
    """
    NFW profile
    rho = rho0/((r/rs)*(1+r/rs)**2)
    """
    return rho0 / ((r / rs) * (1 + r / rs)**2)


def nfw_mr(r, rs, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = rho0/((r/rs)*(1+r/rs)**2)
    """
    return 4 * np.pi * rho0 * rs**3 * (np.log(1. + r / rs) - r / (rs + r))


###############################
# NFWg profile
###############################

def nfwg_profile(r, rs, gamma, rho0=1.):
    """
    NFW modified profile
    rho = rho0/((r/rs)**(gamma)*(1+(r/rs)**2)**(0.5*(3.-gamma)))
    """
    return rho0 / ((r / rs)**gamma * (1 + (r / rs)**2)**(0.5 * (3. - gamma)))


def nfwg_mr(r, rs, gamma, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = rho0/((r/rs)**(gamma)*(1+(r/rs)**2)**(0.5*(3.-gamma)))
    """
    if not is_scipy:
        raise Exception("scipy is needed for these function")

    aa = 1.5 - 0.5 * gamma
    cc = 2.5 - 0.5 * gamma
    z = -r**2 / rs**2
    return rho0 * 2 * np.pi * (r / rs)**-gamma * r**3 * \
        special.hyp2f1(aa, aa, cc, z) / aa


  # def rho(r,rs,gamma):
  #   return 1/(  (r/rs)**(gamma)  * (1+(r/rs)**2)**(0.5*(3.-gamma))  )
  #
  # def rhor2(r,rs,gamma):
  #   return 4*pi*r**2 /(  (r/rs)**(gamma)  * (1+(r/rs)**2)**(0.5*(3.-gamma))  )
  #
  # def Mr(r,rs,gamma):
  #   return quad(rhor2, 0, r, args=(rs,gamma), tol=1.e-3, maxiter=50)
  #
  #
  # Rs = r
  #
  #
  # if type(Rs)==ndarray:
  #
  #   Mrs = np.zeros(len(Rs))
  #   ntot = len(Rs)
  #
  #   for i in xrange(len(Rs)):
  #     Mrs[i] =  Mr(Rs[i],rs,gamma)[0]
  #     print Rs[i],Mrs[i],i,'/',ntot
  #
  #   return Mrs*rho0
  #
  # else:
  #   return Mr(Rs,rs,gamma)[0]*rho0



###############################
# NFW softened profile
###############################

def nfws_profile(r, rhos, rs, r0):
    """
    NFW softened profile
    rho = rhos/(((r+r0)/rs)*(1+r/rs)**2)
    """
    return rhos / (((r + r0) / rs) * (1 + r / rs)**2)


def nfws_mr(r, rhos, rs, r0):
    """
    Mass in the radius r for the distribution
    rho = rhos/((r/rs)*(1+r/rs)**2)
    """

    if r0 == 0:
        return nfw_mr(r, rhos, rs)

    # r=R
    rsr = rs + r
    rs0 = rs - r0
    rr0 = r + r0

    lnrr0 = np.log(rr0)
    lnrsr = np.log(rsr)

    I1 = 4 * np.pi * rhos * rs**3 * (r0**2 * lnrr0 * rsr + rs**2 * lnrsr *
                                  rsr - 2 * r0 * rs * lnrsr * rsr + rs**2 * rs0) / (rsr * rs0**2)

    # r=0
    rsr = rs
    rs0 = rs - r0
    rr0 = r0

    lnrr0 = np.log(rr0)
    lnrsr = np.log(rsr)

    I2 = 4 * np.pi * rhos * rs**3 * (r0**2 * lnrr0 * rsr + rs**2 * lnrsr *
                                  rsr - 2 * r0 * rs * lnrsr * rsr + rs**2 * rs0) / (rsr * rs0**2)

    return I1 - I2


###############################
# Burkert profile
###############################


def burkert_profile(r, rs, rho0=1.):
    """
    Burkert profile
    rhob = rho0 / ( ( 1 + r/rs  ) * ( 1 + (r/rs)**2  ) )

    A. Burkert, Astrophys. J. 447 (1995) L25.
    """

    return rho0 / ((1 + r / rs) * (1 + (r / rs)**2))


def burkert_mr(r, rs, rho0=1.):
    """
    Burkert profile
    rhob = rho0 / ( ( 1 + r/rs  ) * ( 1 + (r/rs)**2  ) )

    A. Burkert, Astrophys. J. 447 (1995) L25.
    """

    return 4 * np.pi * rho0 * rs**3 * \
        (0.25 * np.log((r / rs)**2 + 1) - 0.5 * np.arctan(r / rs) + 0.5 * np.log((r / rs) + 1))


###############################
# Pseudo-isothermal profile
###############################

def pisothm_profile(r, rs, rho0=1.):
    """
    Pseudo-isothermal profile
    rho = 1/(1+(r/rs)**2)
    """
    return rho0 / (1 + (r / rs)**2)


def pisothm_mr(r, rs, rho0=1.):
    """
    Mass in the radius r for the distribution
    rho = 1/(1+(r/rs)**2)
    """
    return 4 * np.pi * rho0 * rs**3 * (r / rs - np.arctan(r / rs))


###############################
# King profile
###############################


def king_profile(r, rs, rt):
    """
    King profile
    (see King 62)
    """

    x = np.sqrt((1 + (r / rs)**2) / (1 + (rt / rs)**2))

    return 1 / x**2 * (np.arccos(x) / x - np.sqrt(1 - x**2))


def king_profile_Rz(R, z, rs, rt):
    """
    King profile in cylindrical coord (needed for surface density computation)
    (see King 62)
    """

    r = np.sqrt(R**2 + z**2)
    x = np.sqrt((1 + (r / rs)**2) / (1 + (rt / rs)**2))

    res = 1 / x**2 * (np.arccos(x) / x - np.sqrt(1 - x**2))
    return np.where(r > rt, 0, res)


def king_surface_density_old(R, rs, rt):
    """
    Obsolete implementation
    """

    if not is_scipy:
        raise Exception("scipy is needed for these function")

    def Integrant(r, R, rs, rt):
        return 2 * king_profile(r, rs, rt) * r / (np.sqrt(r**2 - R**2))

    Sigma = np.zeros(len(R))
    for i in range(len(R)):

        tol = 1.e-1
        Sigma[i], e = integrate.quad(
            Integrant, R[i], rt, args=(
                R[i], rs, rt), tol=tol, maxiter=100)
        if e > tol:
            print(("Error in % =", 100 * e / Sigma[i]))

    return Sigma


def king_surface_density(R, rs, rt):
    """
    Surface density of King profile
    (see King 62)
    """

    if not is_scipy:
        raise Exception("scipy is needed for these function")

    def Integrant(z, R, rs, rt):
        return 2 * king_profile_Rz(R, z, rs, rt)

    Sigma = np.zeros(len(R))
    for i in range(len(R)):
        tol = 1.e-5
        Sigma[i], e = integrate.quad(
            Integrant, 0, rt, args=(
                R[i], rs, rt), tol=tol, maxiter=200)

    return Sigma


def king_Rc(rs, rt):
    """
    Core radius
    Find R such that

    Sigma(Rc) = Sigma(0)/2.
    """

    if not is_scipy:
        raise Exception("scipy is needed for these function")

    Sigma0 = king_surface_density([0], rs, rt)[0]

    def Fct(R, rs, rt):
        return king_surface_density([R], rs, rt)[0] - Sigma0 / 2

    Rc = optimize.bisect(
        Fct,
        a=0,
        b=0.99 * rt,
        args=(
            rs,
            rt),
        xtol=1e-3,
        maxiter=500)

    return Rc
