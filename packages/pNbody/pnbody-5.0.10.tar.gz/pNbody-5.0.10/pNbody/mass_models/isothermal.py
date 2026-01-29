#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      isothermal.py
#  brief:     Defines isothermal profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
isothermal model
"""

import numpy as np


def Potential(rho0, a, r, G=1.):
    """
    Potential
    """
    return 4*np.pi * G * rho0 * a**2 * np.log(r/a)


def Density(rho0, a, r, G=1.):
    """
    Density
    """
    return rho0 * a**2/r**2
    


def Vcirc(rho0, a, r, G=1.):
    """
    circular velocity
    """
        
    def vc():
      return 4*np.pi*G*rho0*a**2
    
    
    if type(r) == np.ndarray:
      return np.ones(len(r)) * vc()
    
    else:
      return vc()
    
    
