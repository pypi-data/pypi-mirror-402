#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      gen_2_slopes.py
#  brief:     Defines generalized two slopes profile (two powers density models)
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
Generalized two slopes profile based on the density : 
    \rho(r) =  \frac{\rho_0}{( (r/r_s)^\alpha * (1 + r/r_s)**(\beta - \alpha) ) }
where \rho_0, r_s, \alpha and \beta are the parameters of the model. 
"""

import numpy as np
from scipy.integrate import quad
from scipy.optimize import fsolve

def c_from_dc(dc, c_guess=10):
    f = lambda c: (200/3)*c**3/(np.log(1+c) - c/(1+c)) - dc
    return fsolve(f, c_guess)[0]


class GEN2SLOPES():
  
  def __init__(self,alpha=1,beta=3,rho0=None,rs=None,c=None,M200=None,r200=None,H0=None,G=1.):
    """
    alpha is the inner slope
    beta  is the outer slope
    rho0  is the density at rs
    rs    is the specific radius
    c     is the concentration parameter
    M200  is the 'virial' mass
    rhoc  is the critical density of the Universe
    """
    
    self.alpha = alpha
    self.beta  = beta

    if (rho0 is not None) and (rs is not None):
      self.rho0 = rho0
      self.rs   = rs
      self.G    = G
      # compute c, r200, M200 if H0 is given 
      if H0 is not None:
        rhoc = 3*H0**2/(8*np.pi*G)      
        dc = self.rho0/rhoc
        self.c    = c_from_dc(dc)
        self.rhoc = rhoc
        self.r200 = self.c * self.rs
        self.M200 = 100 * H0**2 * self.r200**3 / self.G
        
    elif (c is not None) and (M200 is not None) and (H0 is not None): 
      rhoc = 3*H0**2/(8*np.pi*G)      
      r200 = np.cbrt(10*M200*G*H0)/(10*H0)
      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))
      
      # in this mode, those variabes are the ones used
      self.rho0 = dc*rhoc 
      self.rs   = r200/c
      self.G    = G
      
      # in this mode, those variables will be useless
      self.rhoc = rhoc
      self.r200 = r200
      self.M200 = M200
      self.c    = c

    elif (c is not None) and (rs is not None) and (H0 is not None): 
      self.c  = c
      self.rs = rs
      self.G  = G

      
      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))
      self.r200 = c * rs
      self.M200 = 100 * H0**2 * self.r200**3 / self.G
      
      r200 = np.cbrt(10*self.M200*G*H0)/(10*H0)
      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))
      rhoc = 3*H0**2/(8*np.pi*G)
      self.rho0 = dc*rhoc 

      # in this mode, those variables will be useless
      self.rhoc = rhoc

      
    elif (c is not None) and (r200 is not None) and (H0 is not None): 
      self.c  = c
      self.G  = G
      self.r200 = r200

      self.rs = self.r200/self.c
      
      self.M200 = 100 * H0**2 * self.r200**3 / self.G      
      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))

      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))
      rhoc = 3*H0**2/(8*np.pi*G)
      self.rho0 = dc*rhoc 

      # in this mode, those variables will be useless
      self.rhoc = rhoc

      print(">>>>>>>>")

      



      
      
  def info(self):
    print("NFW parameters")
    print("--------------")
    print("  alpha = %g"%self.alpha)
    print("  beta  = %g"%self.beta)
    print("  rs    = %g"%self.rs)
    print("  rho0  = %g"%self.rho0)
    print("  G     = %g"%self.G)
    if hasattr(self,'c'):    
      print("  c     = %g"%self.c)
    if hasattr(self,'rhoc'):  
      print("  rhoc  = %g"%self.rhoc)
    if hasattr(self,'M200'):      
      print("  M200  = %g"%self.M200)
    if hasattr(self,'r200'):      
      print("  r200  = %g"%self.r200)
    


  def __mass_integral(self,r):
    """Integral function for the mass function (not vectorized)."""
    return  quad(lambda u: u**(2-self.alpha) / (1 + u)**(self.beta-self.alpha) , 0, r/self.rs)[0]

  def __pot_integral(self, r):
    """Integral function for the potential function (not vectorized)."""
    return  quad(lambda u: u**(1-self.alpha) / (1 + u)**(self.beta-self.alpha) , r, np.inf)[0]
      
  def Potential(self,r):
    """
    return the Potential at a given radius r
    """
    raise Exception("Potential : this function provide an erroneous potential.")    
    M_r = self.CumulativeMass(r)
    integral_vec = np.vectorize(self.__pot_integral)
    return - self.G*M_r/r - 4*np.pi*self.G*self.rho0*self.rs**2*integral_vec(r)

  def dPotential(self,r):
    """
    return the first derivative of the Potential at a given radius r
    """
    if r==0:
      return 0
    
    Mr = self.CumulativeMass(r)
    return self.G*Mr/r**2  
  
  def CumulativeMass(self, r):
    """
    return the Cumulative mass at a given radius r
    """
    integral_vec = np.vectorize(self.__mass_integral)
    return   4 * np.pi * self.rho0 * self.rs**3 * integral_vec(r)

  def Density(self, r):
    """
    return the Density at a given radius r
    """
    return self.rho0 / ( (r/self.rs)**self.alpha * (1 + r/self.rs)**(self.beta - self.alpha) )

  def Vcirc(self, r):
    """
    return the circular velocity at a given radius r
    """
    Mr = self.CumulativeMass(r)
    return np.sqrt(self.G*Mr/r)





##############################################
# The old implementation
##############################################



##########################################################
# Utility functions
#########################################################

def __mass_integral(rho0, r_s, alpha, beta, r, G=1.):
    """Integral function for the mass function (not vectorized)."""
    return  quad(lambda u: u**(2-alpha) / (1 + u)**(beta-alpha) , 0, r/r_s)[0]

def __pot_integral(rho0, r_s, alpha, beta, r, G=1.):
    """Integral function for the potential function (not vectorized)."""
    return  quad(lambda u: u**(1-alpha) / (1 + u)**(beta-alpha) , r, np.inf)[0]

#########################################################
# Main content
#########################################################

def Potential(rho0, r_s, alpha, beta, r, G=1.):
    """
    Potential
    """
    M_r = CumulativeMass(rho0, r_s, alpha, beta, r, G=1.)
    integral_vec = np.vectorize(__pot_integral)
    return - G*M_r/r - 4*np.pi*G*rho0*r_s**2*integral_vec(rho0, r_s, alpha, beta, r, G)

def CumulativeMass(rho0, r_s, alpha, beta, r, G=1.):
    """
    Cumulative mass
    """
    integral_vec = np.vectorize(__mass_integral)
    return   4 * np.pi * rho0 * r_s**3 * integral_vec(rho0, r_s, alpha, beta, r, G)

def Density(rho0, r_s, alpha, beta, r, G=1.):
    """
    Density
    """
    return rho0 / ( (r/r_s)**alpha * (1 + r/r_s)**(beta - alpha) )
    
def Vcirc(rho0, r_s, alpha, beta, r, G=1.):
    """
    Circular velocity
    """
    Mr = CumulativeMass(rho0, r_s, alpha, beta, r, G=1.)
    return np.sqrt(G*Mr/r)
