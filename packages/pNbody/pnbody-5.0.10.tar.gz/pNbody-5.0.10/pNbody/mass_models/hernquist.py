#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      hernquist.py
#  brief:     Defines hernquist profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
hernquist model
"""

import numpy as np

def Potential(rho0, a, r, G=1.):
    """
    Potential
    """
    return -4*np.pi*G*rho0*a**2 * 1/(2*(1+(r/a)))



def CumulativeMass(rho0, a, r, G=1.):
    """
    Hernquist cumulative mass
    """
    return   4*np.pi*rho0*a**3 *   0.5*(r/a)**2/(1+(r/a))**2

def TotalMass(rho0, a, G=1.):
    """
    Hernquist total mass
    """
    return   4*np.pi*rho0*a**3 *   0.5
    

def Density(rho0, a, r, G=1.):
    """
    Density
    """
    return rho0 / ( (r/a)**1 * (1+(r/a))**3  )
    

def Vcirc(rho0, a, r, G=1.):
    """
    circular velocity
    """
        
    Mr = 4*np.pi*rho0*a**3 * (  (r/a)**2 / (2*(1+r/a)**2)  )
    return np.sqrt(G*Mr/r)
    

