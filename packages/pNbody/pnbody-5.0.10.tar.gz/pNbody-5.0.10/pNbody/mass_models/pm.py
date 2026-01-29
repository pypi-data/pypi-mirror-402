#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      pm.py
#  brief:     Defines point mass profile
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
point mass model
"""

import numpy as np


def Potential(M, r, G=1.):
    """
    Potential
    """
    return -G * M / np.sqrt(r**2)


def dPotential(M, r, G=1.):
    """
    first derivative of Potential
    """
    return G * M * r * (r**2)**(-3. / 2.)

def Density(M, r, G=1.):
    """
    Density
    """
    if type(r) == np.ndarray:
      return np.zeros(len(r)) 
    else:
      return 0
    
    
def Vcirc(M, r, G=1.):
    """
    circular velocity
    """
    return np.sqrt(G * M / r)


