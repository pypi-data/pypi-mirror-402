#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      homosphere.py
#  brief:     Defines homogeneous sphere profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
homogeneous mass model
"""

import numpy as np

def getRho(M, R):
    """
    return the sphere density
    """
    return M/(4/3.*np.pi * R**3)


def Potential(M, R, r,G=1.):
    """
    Potential
    """
    rho = getRho(M, R)
    
    def pot_int(r):
      return 2/3.*np.pi * G * rho * r**2  - 2*np.pi * G * rho * R**2
    
    def pot_ext(r):
      return -G*M/r
    
    
    if type(r) == np.ndarray:
      return np.where(r<R, pot_int(r), pot_ext(r)) 
    
    else:
      if r<R:
        return pot_int(r)
      else:
        return pot_ext(r)
        
        
def Density(M, R, r,G=1.):
    """
    Density
    """
    rho = getRho(M, R)
    
    def dens_int(r):
      return rho
    
    def dens_ext(r):
      return 0
    
    
    if type(r) == np.ndarray:
      return np.where(r<R, dens_int(r), dens_ext(r)) 
    
    else:
      if r<R:
        return dens_int(r)
      else:
        return dens_ext(r)    
    
    


def Vcirc(M, R, r, G=1.):
    """
    Circular Velocity
    """
    rho = getRho(M, R)
    

    def vc_int(r):
      return np.sqrt(4/3.*np.pi*G*rho)*r
    
    def vc_ext(r):
      return np.sqrt(4/3.*np.pi*G*rho*R**3/r)
    
    
    if type(r) == np.ndarray:
      return np.where(r<R, vc_int(r), vc_ext(r)) 
    
    else:
      if r<R:
        return vc_int(r)
      else:
        return vc_ext(r)   


