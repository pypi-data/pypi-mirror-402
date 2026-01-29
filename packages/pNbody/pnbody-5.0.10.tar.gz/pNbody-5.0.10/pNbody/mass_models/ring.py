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
ring model

Lass & Blitzer 1982
see also galpy RingPotential.py (Bovy)

"""

import numpy as np
from scipy import special


def Potential(M, R0, R, z, G=1.):
    """
    Shell Potential
    """
    
    m= 4.*R*R0/((R+R0)**2+z**2)
    P = - 2*G*M/np.pi/np.sqrt( (R0 + R)**2 + z**2 ) *special.ellipk(m)
  
    return P
    
    
    
def dPotential(M, R0, R, z, G=1.):
    """
    Shell first derivative of Potential
    """
    
    m= 4.*R*R0/((R+R0)**2+z**2)
    dP = G*M/np.pi/R/np.sqrt( (R0 + R)**2 + z**2 ) * ( m* (R**2-R0**2-z**2)/(4*(1-m)*R*R0)* special.ellipe(m) + special.ellipk(m) )
    
    return dP
    
    
    
    
        
    
    
    
    
    
