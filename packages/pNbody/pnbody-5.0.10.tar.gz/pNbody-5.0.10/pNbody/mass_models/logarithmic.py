#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      logarithmic.py
#  brief:     Defines logarithmic potential
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np


def Potential(v0, Rc, q, R, z, G=1.):
    return 0.5*v0**2 * np.log(Rc**2 + R**2+z**2/q**2)


def Vcirc(v0, Rc, q, R, G=1.):
    return v0 * np.sqrt(R**2/(Rc**2+R**2))
        

def Density(v0, Rc, q, R, z, G=1.):
    return v0**2/(4*np.pi*G*q**2) * ( (2*q**2+1)*Rc**2 + R**2 + (2-1/q**2)*z**2 )/(Rc**2 + R**2 + z**2/q**2)**2



def Omega(v0, Rc, q, R, G=1.):
    """
    Omega
    """
    return np.sqrt( v0**2/(Rc**2 + R**2)  )


def Kappa(v0, Rc, q, R, G=1.):
    """
    Kappa
    """
    return np.sqrt(  2*v0**2/(Rc**2 + R**2)*(2 - R**2/(Rc**2 + R**2)) )
    
    
    
