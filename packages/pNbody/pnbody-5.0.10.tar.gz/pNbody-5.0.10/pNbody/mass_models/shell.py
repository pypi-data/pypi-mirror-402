#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      shell.py
#  brief:     Defines shell profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
shell model
"""

import numpy as np


def Potential(M, R, r, G=1.):
    """
    Shell Potential
    """
    
    P1 = -G * M / R     # r < R
    P2 = -G * M / r     # r > R
    
    
    return np.where(r<R,P1,P2)
    
    
    
def dPotential(M, R, r, G=1.):
    """
    Shell first derivative of Potential
    """
    
    dP1 = 0              # r < R
    dP2 = G * M / r**2   # r > R
    
    return np.where(r<R,dP1,dP2)
    
    
    
    
        
    
    
    
    
    
