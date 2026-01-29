
#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      pseudoisothermal.py
#  brief:     Defines pseudo-isothermal profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
pseudo-isothermal model
"""

import numpy as np


def Potential(rho0, a, r, G=1.):
    """
    Potential
    """
    return 4*np.pi*G*rho0*a**2*(0.5*np.log(a**2+r**2) + a/r * np.arctan(r/a))


def Density(rho0, a, r, G=1.):
    """
    Density
    """
    return rho0 * 1/(1+(r**2/a**2))
    


def Vcirc(rho0, a, r, G=1.):
    """
    circular velocity
    """
        
    return np.sqrt(4*np.pi*G*rho0*a**2 * (1-a/r * np.arctan(r/a)))
    
    
