#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libmiyamoto.py
#  brief:     Defines exponential profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from scipy.special import iv,kv
from scipy.integrate import quad


def Potential(Sigma0,Rd,Rmax,R,z,G=1.0):
    """
    Exponential Potential
    """
    
    def integrand(a,Sigma0,Rd,R,z):
      sqp = np.sqrt(z**2 + (a+R)**2)
      sqm = np.sqrt(z**2 + (a-R)**2)
      I1 = (a+R)/sqp
      I2 = (a-R)/sqm
      I3 = Sigma0*a*kv(1,a/Rd)
      I4 = np.sqrt(R**2-a**2-z**2 + (sqp*sqm))
    
      return (I1-I2)/I4 * I3
     
     
    if type(R)==np.ndarray and type(z)==np.ndarray:
      
      Is = np.zeros(R.shape)
      
      for i in range(R.shape[0]):
        print(i,R.shape[0])
        for j in range(R.shape[1]):

          I = quad(integrand, 0, Rmax, args=(Sigma0,Rd,R[i,j],z[i,j]+1e-5)) 
          
          Is[i,j] = I[0]
                
      return -2*np.sqrt(2)*G*Is    
          
    else:
      I = quad(integrand, 0, Rmax, args=(Sigma0,Rd,R,z)) 
      return -2*np.sqrt(2)*G * I[0]
    
    


def Vcirc(Sigma0,Rd,R,G=1.0):
    """
    Exponential Circular velocity
    """
    
    y = R/(2*Rd)
    B = iv(0,y)*kv(0,y) - iv(1,y)*kv(1,y)
  
    return np.sqrt(4*np.pi*G*Sigma0*Rd * y**2 * B)



def dRVcirc2(Sigma0,Rd,R,G=1.0):
    """
    Radial derivative of the square of the Exponential Circular velocity
    """
    
    y = R/(2*Rd)
    B = iv(0,y)*kv(0,y) - iv(1,y)*kv(1,y)
    
    C1 = kv(0,y) * (iv(1,y) + iv(-1,y))
    C2 = iv(0,y) * (kv(1,y) + kv(-1,y))
    C3 = kv(1,y) * (iv(2,y) + iv(0,y))
    C4 = iv(1,y) * (kv(2,y) + kv(0,y))
    
    C = 0.5*(C1 - C2 - C3 + C4)
  
    return 2*np.pi*G*Sigma0  * ( ( 2*y*B ) + y**2 * C)


def Kappa(Sigma0,Rd,R,G=1.0):
    """
    Radial picycle frequency
    """
    return np.sqrt(Kappa2(Sigma0,Rd,R,G))
    
def Kappa2(Sigma0,Rd,R,G=1.0):
    """
    Square of the Radial picycle frequency
    """
    Vc2 = Vcirc(Sigma0,Rd,R,G)**2
    R2 = R*R
    return dRVcirc2(Sigma0,Rd,R,G)/R + 2*Vc2/R2  


def SurfaceDensity(Sigma0,Rd,R,G=1.0):
    """
    Exponential Density
    """

    return Sigma0*np.exp(-R/Rd)

def Mass(Sigma0,Rd,R,G=1.0):
    """
    Exponential Mass inside R
    """

    return 2*np.pi*Sigma0*Rd**2 * (1- np.exp(-R/Rd)*(1+R/Rd))


