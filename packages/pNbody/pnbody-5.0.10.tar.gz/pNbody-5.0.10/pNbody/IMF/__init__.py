#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      IMF/__init__.py
#  brief:     IMF routines
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from pNbody import pychem
import numpy as np

# define a default IMF
# modified Kroupa 2001
imf_default_params = {}
imf_default_params["Mmax"] = 50.                     # maximal imf mass in Msol
imf_default_params["Mmin"] = 0.05                    # minimal imf mass in Msol
imf_default_params["as"] = [0.7,-0.8,-1.7,-1.3]      # imf slope in a given mass range
imf_default_params["ms"] = [0.08,0.5,1.0]            # mass range for the imf slope


class IMF:
  
  def __init__(self,params=imf_default_params,M0=10000,seed=0):
    """
    params : a set of parameters defining the IMF
    M0     : the IMF total mass in solar mass
    seed   : a random seed

    Note all quantities are in solar mass
    """
    # set default parameters
    pychem.set_parameters(params)

    # make global 
    self.M0 = M0
    self.seed = seed
    self.params = params
    
    # init random seed
    self.setRandomSeed(seed)

  def info(self):
    """
    print some info 
    """

    mmin = self.getMinMass()
    mmax = self.getMaxMass()
    N = self.getNumberOfStarsInMassInterval(mmin,mmax)    

    print("IMF mass in solar mass")
    print("M0 = %g\n"%(self.M0))

    print("Total number of stars in the IMF")
    print("N = %d\n"%(N))
    
    print("IMF minimal and maximal masses in solar mass")
    print("mmin = %g"%(mmin))
    print("mmax = %g\n"%(mmax))

    print("IMF slopes")
    print("as = %s\n"%(self.params["as"]))

    print("IMF masses ranges")
    print("ms = %s\n"%(self.params["ms"]))
    
    print("Current random seed")
    print("seed = %d\n"%(self.seed))    
    
    

  def setRandomSeed(self,seed=None):
    """
    init the random seed
    
    seed : the random seed. If none, use the default value
    """
    if seed is None:
      seed = self.seed
    else:
      seed = seed
      
    self.seed = seed  
    pychem.imf_init_seed(seed)
   
    
    
  def getMaxMass(self):
    """
    return the maximal IMF mass in Msol
    """
    mass = pychem.get_Mmax()
    return mass

  def getMinMass(self):
    """
    return the minimal IMF mass in Msol
    """
    mass = pychem.get_Mmin()
    return mass

  def setTotalMass(self,M0):
    """
    set the IMF total mass in Msol
    """
    self.M0 = M0
  
  def getTotalMass(self):
    """
    get the IMF total mass in Msol
    """
    return self.M0
    
  def getNumberOfStarsInMassInterval(self,mmin,mmax):
    """
    return the number of stars in a given mass range defined by:
    mmin : lower mass bound
    mmax : upper mass bound
    """
    if mmin < self.getMinMass():
      raise ValueError("mmin=%g is smaller than the IMF minimal mass=%g"%(mmin,self.getMinMass()))

    if mmax > self.getMaxMass():                                                                       
      raise ValueError("mmax=%g is smaller than the IMF maximal mass=%g"%(mmax,self.getMaxMass()))

    # compute the number of stars per mass between m1 and m2 (dep on M0)
    # N this is thus the number of stars in a particle of mass M0
    N      = int(pychem.get_imf_N(np.array([mmin]),np.array([mmax]))*self.M0)

    return N

  def getStellarMassInMassInterval(self,mmin,mmax):
    """
    return the stellar mass in a given mass range defined by:
    mmin : lower mass bound
    mmax : upper mass bound
    """
    if mmin < self.getMinMass():
      raise ValueError("mmin=%g is smaller than the IMF minimal mass=%g"%(mmin,self.getMinMass()))

    if mmax > self.getMaxMass():                                                                       
      raise ValueError("mmax=%g is smaller than the IMF maximal mass=%g"%(mmax,self.getMaxMass()))
    
    # compute the number of stars per mass between m1 and m2 (dep on M0)
    # N this is thus the number of stars in a particle of mass M0
    M      = pychem.get_imf_M(np.array([mmin]),np.array([mmax]))*self.M0

    return M
  
  def getTotalNumberOfStars(self):
    """
    get the total number of stars in the IMF
    """
    mmin = self.getMinMass()
    mmax = self.getMaxMass()
    N = self.getNumberOfStarsInMassInterval(mmin,mmax)
    return N
    
  def Sample(self): 
    """
    return a set of star mass, that sample the IMF
    By default the masses are sorted.
    """
    
    N = self.getTotalNumberOfStars()
    
    # compute the masses
    MassesFullIMF = pychem.imf_sampling(N,self.seed)
    MassesFullIMF.sort()

    return MassesFullIMF


  def getOneStar(self,f=None): 
    """
    return one start mass (that sample the IMF)

    f : random number if None, one is randomly picked between [0,1]
    """

    if f is None:    
      # get one stellar mass
      mass = pychem.imf_sampling_single()
    else:
      mass = pychem.imf_sampling_single_from_random(f)
      
    return mass

  

  def Sample2Parts(self,Mt=1,Msp=20): 
    """
    sample the IMF with macro particles below a given mass and with
    individual stars above.
    
    Mt  minimal discrete mass (minimal_discrete_mass_Msun)
    Msp mass of stellar particles (stellar_particle_mass_Msun)
    """

    if Mt < self.getMinMass():
      raise ValueError("Mt=%g is smaller than the IMF minimal mass=%g"%(Mt,self.getMinMass()))

    if Mt > self.getMaxMass():                                                                       
      raise ValueError("Mt=%g is smaller than the IMF maximal mass=%g"%(Mt,self.getMaxMass()))


    
    
  def Sample2Parts(self,Mt=1,Msp=20): 
    """
    sample the IMF with macro particles below a given mass and with
    individual stars above.

    Mt  minimal discrete mass (minimal_discrete_mass_Msun)
    Msp mass of stellar particles (stellar_particle_mass_Msun)

    The routine returns:

    masses_d  : the list of discrete stars  
    masses_sp : the list of stellar particles (macro particles)
    """

    if Mt < self.getMinMass():
      raise ValueError("Mt=%g is smaller than the IMF minimal mass=%g"%(Mt,self.getMinMass()))

    if Mt > self.getMaxMass():                                                                       
      raise ValueError("Mt=%g is smaller than the IMF maximal mass=%g"%(Mt,self.getMaxMass()))

    
    mmin = self.getMinMass()
    mmax = self.getMaxMass()
    
    # total mass in the continuous part
    Mc = self.getStellarMassInMassInterval(mmin,Mt)
    
    # total mass in the discrete part
    Md = self.getStellarMassInMassInterval(Mt,mmax)

    # total number of stars in the continuous part
    Nc = self.getNumberOfStarsInMassInterval(mmin,Mt)
    
    # total number of stars in the discrete part
    Nd = self.getNumberOfStarsInMassInterval(Mt,mmax)

    # total number of stellar particles in the contiuous part
    Nsp = Mc/Msp
    
    # probability to get one stellar particle (in the continuous part)
    Pc = Nsp/(Nsp + Nd)

    # probability to get one individual star
    Pd = 1 - Pc    

    # integer values
    Nd  = int(Nd)
    Nsp = int(Nsp)
    
    # sample Nd particles in the discrete part
    # get the fraction of stars less massive than Mt
    f1 = self.getNumberOfStarsInMassInterval(mmin,Mt)/self.getNumberOfStarsInMassInterval(mmin,mmax)

    # sample an imf in the probability fraction range [f1,1]
    Masses_d = pychem.imf_sampling_with_boundaries(Nd,self.seed,f1,1)
    Masses_d.sort()
    
    # get Nsp particles in the continuous part
    Masses_sp = np.ones(Nsp)*Msp

    return Masses_d,Masses_sp


