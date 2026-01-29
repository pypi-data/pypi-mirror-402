#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libmiyamoto.py
#  brief:     Defines Miyamoto profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
import scipy.integrate as integrate
import sys



def ComputeCircularVelocity2(V,a,Rmax,R,G=1):
  
  if R==0:
    return 0
  
  def Integrant(x):
    return -2*(V**2)/np.pi *(-x/( np.sqrt(Rmax**2-x**2)*( np.sqrt(Rmax**2-x**2) + np.sqrt(Rmax**2+a**2) )  ) - x/(x**2 + a**2))  * x/np.sqrt(R**2 -x**2)

  result = integrate.quad(Integrant, 0, R,epsrel=1e-6)  
  return result[0]



def Vcirc2(V, a, Rmax, R, G=1.):
    """
    Mestel Circular velocity
    """
    
    if Rmax is None:
      V2 = V**2 * (1- a/np.sqrt(a**2 + R**2))
    else:
      raise("we should use ComputeCircularVelocity2")
      sys.exit()
       
    return V2
    

def Vcirc(V, a, Rmax, R, G=1.):
    """
    Mestel Circular velocity
    """
    
    return np.sqrt(Vcirc2(V, a, Rmax, R, G=G))




def SurfaceDensity(V, a, Rmax, R, G=1.):
    """
    pseudo-Mestel Surface Density
    """

    return   V**2/(2*np.pi*G) /np.sqrt(R**2+ a**2)




def Omega2(V, a, Rmax, R, G=1.):
    """
    Omega2
    """
    Om2 = Vcirc2(V, a, Rmax, R, G=G) / R**2
    return Om2


def Omega(V, a, Rmax, R, G=1.):
    """
    Omega
    """
    return np.sqrt(Omega2(V, a, Rmax, R, G=G))



def Kappa2(V, a, Rmax, R, G=1.):
    """
    Kappa2
    """
    K2 =  V**2 * a /(R**2+a**2)**(3/2.)    +   2*Vcirc2(V, a, Rmax, R, G=G) / R**2
    return K2


def Kappa(V, a, Rmax, R, G=1.):
    """
    Kappa
    """
    return np.sqrt(Kappa2(V, a, Rmax, R, G=G))





