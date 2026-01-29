#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      einasto.py
#  brief:     Defines einastro profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
Einasto model
"""

import numpy as np

def Potential(rho0, a, r, m=6.,G=1.):
    """
    Potential
    
    Parameters
    ----------
    rho0 : specific density
    a    : scale length
    r    : radius
    m    : power (default=6)
    G    : gravitational constant (default=1)
    """
    pass
    

def Density(rho0, a, r, m=6.,G=1.):
    """
    Density
    
    Parameters
    ----------
    rho0 : specific density
    a    : scale length
    r    : radius
    m    : power (default=6)
    G    : gravitational constant (default=1)
    """
    return rho0 * np.exp(-(2*m)*((r/a)**(1./m)-1))
    

def Vcirc(rho0, a, r, m=6., G=1.):
    """
    Circular velocity
    
    Parameters
    ----------
    rho0 : specific density
    a    : scale length
    r    : radius
    m    : power (default=6)
    G    : gravitational constant (default=1)
    """
    pass

