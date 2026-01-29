#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      nfw.py
#  brief:     Defines nfw profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
nfw model
"""

import numpy as np


class NFW():
  
  def __init__(self,rho0=None,rs=None,c=None,M200=None,H0=None,G=1.):
    """
    rho0 is the density at rs
    rs   is the specific radius
    c    is the concentration parameter
    M200 is the 'virial' mass
    rhoc is the critical density of the Universe
    """
    
    if (rho0 is not None) and (rs is not None):
      self.rho0 = rho0
      self.rs   = rs
      self.G    = G
      self.c    = None
    elif (c is not None) and (M200 is not None) and (H0 is not None): 
      rhoc = 3*H0**2/(8*np.pi*G)      
      r200 = np.cbrt(10*M200*G*H0)/(10*H0)
      dc = (200/3) * c**3/( np.log(1+c) - (c/(1+c)))       
      self.rho0 = dc*rhoc 
      self.rs   = r200/c
      self.G    = G
      self.c    = c
      
      self.rhoc = rhoc
      self.r200 = r200
      self.M200 = M200

  
  def info(self):
    print("NFW parameters")
    print("--------------")
    print("  c    = %g"%self.c)
    print("  rhoc = %g"%self.rhoc)
    print("  M200 = %g"%self.M200)
    print("  r200 = %g"%self.r200)
    print("  rs   = %g"%self.rs)
    print("  rho0 = %g"%self.rho0)
    
    
  def Potential(self,r):
    """
    return the Potential at a given radius r
    """
    return -4*np.pi*self.G*self.rho0*self.rs**2 * np.log(1+r/self.rs)/(r/self.rs)
    
  def CumulativeMass(self,r):
    """
    return the Cumulative mass at a given radius r
    """
    return   4*np.pi*self.rho0*self.rs**3 *   ( np.log(1+r/self.rs) - (r/self.rs)/(1+r/self.rs) )     
    
  def Density(self,r):
    """
    return the Density at a given radius r
    """
    return self.rho0 / ( (r/self.rs)**1 * (1+(r/self.rs))**2  )
  

  def Vcirc(self,r):
    """
    return the circular velocity at a given radius r
    """
    Mr = 4*np.pi*self.rho0*self.rs**3 * (   np.log(1+r/self.rs) - (r/self.rs)/(1+r/self.rs)       )
    return np.sqrt(self.G*Mr/r)
      
  
  def Kappa2(self,r):
      """
      return Kappa2 at a given radius r
      """
      kappa2 = -(self.rs/r**3)*np.log(1+r/self.rs) + (1/r**2)*(1./(1+r/self.rs)) - (1/(self.rs*r))*(1./(1+r/self.rs))**2
      kappa2 = -4*np.pi*self.G*self.rho0*self.rs**2  * kappa2
      return kappa2
  
  
  def Kappa(self, r):
      """
      return the Radial epicycle frequency at a given radius r
      """
      return np.sqrt(self.Kappa2(r))
  


##############################################
# The old implementation
##############################################



def Potential(rho0, a, r, G=1.):
    """
    Potential
    """
    return -4*np.pi*G*rho0*a**2 * np.log(1+r/a)/(r/a)

def CumulativeMass(rho0, a, r, G=1.):
    """
    Cumulative mass
    """
    return   4*np.pi*rho0*a**3 *   ( np.log(1+r/a) - (r/a)/(1+r/a) ) 

def dPotential(rho0, a, r, G=1.):
    """
    First derivative of the potential
    """
    Mr = 4*np.pi*rho0*a**3 * (   np.log(1+r/a) - (r/a)/(1+r/a)       )
    return G*Mr/r**2
  

def Density(rho0, a, r, G=1.):
    """
    Density
    """
    return rho0 / ( (r/a)**1 * (1+(r/a))**2  )
    

def Vcirc(rho0, a, r, G=1.):
    """
    circular velocity
    """
        
    Mr = 4*np.pi*rho0*a**3 * (   np.log(1+r/a) - (r/a)/(1+r/a)       )
    return np.sqrt(G*Mr/r)
    

def Kappa2(rho0, a, r, G=1.):
    """
    Kappa2 
    """
    
    kappa2 = -(a/r**3)*np.log(1+r/a) + (1/r**2)*(1./(1+r/a)) - (1/(a*r))*(1./(1+r/a))**2
    kappa2 = -4*np.pi*G*rho0*a**2  * kappa2

    return kappa2


def Kappa(rho0, a, r, G=1.):
    """
    Radial epicycle frequency
    """
    return np.sqrt(Kappa2(rho0, a, r, G))
