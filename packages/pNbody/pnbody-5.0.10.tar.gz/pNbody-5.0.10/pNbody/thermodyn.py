#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      thermodyn.py
#  brief:     thermodynamics functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import numpy as np
from . import ctes
from . import units
from . import iofunc as pnio

from pNbody import thermodynlib

##########################################################################
#
# THERMODYNAMIC RELATIONS
#
##########################################################################

# defaults parameters in cgs
defaultpars = {
    "k": ctes.BOLTZMANN,
    "mh": ctes.PROTONMASS,
    "mu": 2,
    "gamma": 5 / 3.,
    "G": ctes.GRAVITY}


# tabulation of the mean weight (from Grackle)
nt = 10
tt = np.array([1.0e+01, 1.0e+02, 1.0e+03, 1.0e+04, 1.3e+04,
            2.1e+04, 3.4e+04, 6.3e+04, 1.0e+05, 1.0e+09])
mt = np.array([1.18701555,
            1.15484424,
            1.09603514,
            0.9981496,
            0.96346395,
            0.65175895,
            0.6142901,
            0.6056833,
            0.5897776,
            0.58822635])


###################
def old_MeanWeightT(T):
    ###################
    """
    mean molecular weight as a function of the Temperature
    """

    if isinstance(T, np.ndarray):

        mu = np.zeros(len(T))
        for i in range(len(T)):
            mu[i] = MeanWeightT(T[i])

    else:

        logt = np.log(T)
        ttt = np.exp(logt)

        if ttt < tt[0]:
            j = 1
        else:
            for j in range(1, nt):
                if (ttt > tt[j - 1]) and (ttt <= tt[j]):
                    break

        slope = np.log(mt[j] / mt[j - 1]) / np.log(tt[j] / tt[j - 1])
        mu = np.exp(slope * (logt - np.log(tt[j])) + np.log(mt[j]))

    return mu


###################
def MeanWeightT(T):
    ###################
    """
    mean molecular weight as a function of the Temperature
    """

    return thermodynlib.MeanWeightT(T)


###################
def UNt(T):
    ###################
    """
    UN(T) = energy normalized as a function of T
          = T/mu(T)
    """

    return T / MeanWeightT(T)



# tabulation of the normalized energy vs T
unr = UNt(tt)


###################
def Tun(UN):
    ###################
    """
    T(UN) = temperature vs energy normalized

    inverse of UNt(U)

    """

    if isinstance(UN, np.ndarray):

        T = np.zeros(len(UN))
        for i in range(len(UN)):
            T[i] = Tun(UN[i])

    else:

        logu = np.log(UN)
        uuu = np.exp(logu)

        if uuu < unr[0]:
            j = 1
        else:
            for j in range(1, nt):
                if (uuu > unr[j - 1]) and (uuu <= unr[j]):
                    break

        slope = np.log(tt[j] / tt[j - 1]) / np.log(unr[j] / unr[j - 1])
        T = np.exp(slope * (logu - np.log(unr[j])) + np.log(tt[j]))

    return T


###################
def Prt(rho, T, pars=defaultpars):
    ###################
    """
    P(rho,T)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    mu = float(pars['mu'])

    mumh = mu * mh

    return k * T / (mumh / rho)


###################
def Trp(rho, P, pars=defaultpars):
    ###################
    """
    T(rho,P)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    mu = float(pars['mu'])

    mumh = mh * mu

    return (mumh / rho) / k * P


###################
def Art(rho, T, pars=defaultpars):
    ###################
    """
    A(rho,T)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    mu = float(pars['mu'])
    gamma = float(pars['gamma'])

    mumh = mu * mh

    return k / mumh * rho**(1. - gamma) * T

###################
def Tra(rho, A, pars=defaultpars):
    ###################
    """
    T(rho,A)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    mu = float(pars['mu'])
    gamma = float(pars['gamma'])

    mumh = mu * mh

    return mumh / k * rho**(gamma - 1.) * A


###################
def Urt(T, pars=defaultpars):
    ###################
    """
    U(rho,T)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    gamma = float(pars['gamma'])

    U = UNt(T) / (gamma - 1.) * k / mh		# new, using the tabulated mu

    return U


###################
def Tru(U, pars=defaultpars):
    ###################
    """
    T(rho,U)
    """

    k = float(pars['k'])
    mh = float(pars['mh'])
    gamma = float(pars['gamma'])

    UN = (gamma - 1) * mh / k * U
    # T = Tun(UN)				# new, using the tabulated mu
    T = thermodynlib.Tun(UN)		# new, using the tabulated mu + C version

    return T


###################
def Tmuru(U, pars=defaultpars):
    ###################
    """
    T(rho,U)/mu  = UN
    """

    k = float(pars['k'])
    gamma = float(pars['gamma'])
    mh = float(pars['mh'])

    Tmu = (gamma - 1.) * mh / k * U

    return Tmu


###################
def Pra(rho, A, pars=defaultpars):
    ###################
    """
    P(rho,A)
    """

    gamma = float(pars['gamma'])

    return rho**gamma * A


###################
def Arp(rho, P, pars=defaultpars):
    ###################
    """
    A(rho,P)
    """

    gamma = float(pars['gamma'])

    return rho**-gamma * P


###################
def Pru(rho, U, pars=defaultpars):
    ###################
    """
    P(rho,U)
    """

    gamma = float(pars['gamma'])

    return (gamma - 1.) * rho * U


###################
def Urp(rho, P, pars=defaultpars):
    ###################
    """
    U(rho,P)
    """

    gamma = float(pars['gamma'])

    return 1. / (gamma - 1.) * (1 / rho) * P


###################
def Ura(rho, A, pars=defaultpars):
    ###################
    """
    U(rho,A)
    """

    gamma = float(pars['gamma'])

    return 1. / (gamma - 1.) * rho**(gamma - 1.) * A


###################
def Aru(rho, U, pars=defaultpars):
    ###################
    """
    A(rho,U)
    """

    gamma = float(pars['gamma'])

    return (gamma - 1.) * rho**(1. - gamma) * U


###################
def SoundSpeed_ru(U, pars=defaultpars):
    ###################
    """
    Sound Speed
    Cs(rho,U)
    """

    gamma = float(pars['gamma'])

    return np.sqrt((gamma - 1.) * gamma * U)


###################
def SoundSpeed_rt(T, pars=defaultpars):
    ###################
    """
    Sound Speed
    Cs(rho,T)
    """

    gamma = float(pars['gamma'])

    U = Urt(T, pars)

    return np.sqrt((gamma - 1.) * gamma * U)

###################
def JeansLength_ru(rho, U, pars=defaultpars):
    ###################
    """
    Jeans Length
    L_J(rho,U)
    """

    G = float(pars['G'])

    Cs = SoundSpeed_ru(U, pars)

    return Cs * np.sqrt(np.pi / (G * rho))


###################
def JeansLength_rt(rho, T, pars=defaultpars):
    ###################
    """
    Jeans Length
    L_J(rho,T)
    """

    G = float(pars['G'])

    Cs = SoundSpeed_rt(T, pars)

    return Cs * np.sqrt(np.pi / (G * rho))


###################
def JeansMass_ru(rho, U, pars=defaultpars):
    ###################
    """
    Jeans Mass
    M_J(rho,T)
    """

    G = float(pars['G'])

    Cs = SoundSpeed_ru(U, pars)

    return (np.pi**(5 / 2.) * Cs**3) / (6 * G**(3 / 2.) * np.sqrt(rho))


###################
def JeansMass_rt(rho, T, pars=defaultpars):
    ###################
    """
    Jeans Mass
    M_J(rho,T)
    """

    G = float(pars['G'])

    Cs = SoundSpeed_rt(T, pars)

    return (np.pi**(5 / 2.) * Cs**3) / (6 * G**(3 / 2.) * np.sqrt(rho))


###################
def MeanWeight(Xi, ionized=0):
    ###################
    """
    old version
    """

    if ionized:
        return 4. / (8. - 5. * (1. - Xi))
    else:
        return 4. / (1. + 3. * Xi)


###################
def ElectronDensity(rho, pars):
    ###################
    """
    Electron density for a mixture of H + He
    """

    Xi = float(pars['Xi'])
    mh = float(pars['mh'])
    ionisation = float(pars['ionisation'])

    if ionisation:
        return rho.astype(float) / mh * (Xi + (1 - Xi) / 2.)
    else:
        return rho.astype(float) * 0


#############################
def Lambda(rho, u, localsystem, thermopars, coolingfile):
    #############################
    """
    This corresponds to Lambda normalized

    Ln = L / nh 2

    nh = (xi*rho/mh)
    """

    UnitLength_in_cm = units.PhysCte(1, localsystem.UnitDic['m']).into(units.cgs)
    UnitTime_in_s = units.PhysCte(1, localsystem.UnitDic['s']).into(units.cgs)
    UnitMass_in_g = units.PhysCte(1, localsystem.UnitDic['kg']).into(units.cgs)

    UnitEnergy_in_cgs = UnitMass_in_g * UnitLength_in_cm**2 / UnitTime_in_s**2

    metalicity = thermopars['metalicity']
    hubbleparam = thermopars['hubbleparam']

    # compute cooling time
    logT, logL0, logL1, logL2, logL3, logL4, logL5, logL6 = pnio.read_cooling(
        coolingfile)

    if metalicity == 0:
        logL = logL0
    elif metalicity == 1:
        logL = logL1
    elif metalicity == 2:
        logL = logL2
    elif metalicity == 3:
        logL = logL3
    elif metalicity == 4:
        logL = logL4
    elif metalicity == 5:
        logL = logL5
    elif metalicity == 6:
        logL = logL6

    # compute gas temp
    logTm = np.log10(Tru(rho, u, thermopars))
    c = ((logTm >= 4) * (logTm < 8.5))
    u = np.where(c, u, 1)
    rho = np.where(c, rho, 1)
    # recompute gas temp
    logTm = np.log10(Tru(rho, u, thermopars))

    # get the right L for a given mT
    logLm = np.take(logL, np.searchsorted(logT, logTm))
    Lm = 10**logLm

    # transform in user units
    Lm = Lm / UnitEnergy_in_cgs / UnitLength_in_cm**3 * UnitTime_in_s

    L = Lm * hubbleparam

    return L


#############################
def CoolingTime(rho, u, localsystem, thermopars, coolingfile):
    #############################

    UnitLength_in_cm = units.PhysCte(1, localsystem.UnitDic['m']).into(units.cgs)
    UnitTime_in_s = units.PhysCte(1, localsystem.UnitDic['s']).into(units.cgs)
    UnitMass_in_g = units.PhysCte(1, localsystem.UnitDic['kg']).into(units.cgs)

    UnitEnergy_in_cgs = UnitMass_in_g * UnitLength_in_cm**2 / UnitTime_in_s**2

    ProtonMass = thermopars['mh']
    Xi = thermopars['Xi']
    metalicity = thermopars['metalicity']
    hubbleparam = thermopars['hubbleparam']

    # compute cooling time
    logT, logL0, logL1, logL2, logL3, logL4, logL5, logL6 = pnio.read_cooling(
        coolingfile)

    if metalicity == 0:
        logL = logL0
    elif metalicity == 1:
        logL = logL1
    elif metalicity == 2:
        logL = logL2
    elif metalicity == 3:
        logL = logL3
    elif metalicity == 4:
        logL = logL4
    elif metalicity == 5:
        logL = logL5
    elif metalicity == 6:
        logL = logL6

    # compute gas temp
    logTm = np.log10(Tru(rho, u, thermopars))
    c = ((logTm >= 4) * (logTm < 8.5))
    u = np.where(c, u, 1)
    rho = np.where(c, rho, 1)
    # recompute gas temp
    logTm = np.log10(Tru(rho, u, thermopars))

    # get the right L for a given mT
    logLm = np.take(logL, np.searchsorted(logT, logTm))
    Lm = 10**logLm

    # transform in user units
    Lm = Lm / UnitEnergy_in_cgs / UnitLength_in_cm**3 * UnitTime_in_s

    L = Lm * hubbleparam

    tc = (ProtonMass)**2 / (L * Xi**2) * u / rho
    tc = np.where(c, tc, 0)

    return tc, c
