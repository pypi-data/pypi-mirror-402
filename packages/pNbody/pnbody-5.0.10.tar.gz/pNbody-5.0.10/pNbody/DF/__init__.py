#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      ic.py
#  brief:     generating initial conditions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


'''
This method is strongly inspired from the nbodpy code from Errani:
https://rerrani.github.io/code.html
https://github.com/rerrani/nbopy
'''


from pNbody import *
import numpy as np
from scipy.integrate import quad


class DistributionFunction():
  
  def __init__(self,Rmin=1e-2,Rmax=100,Rinf=np.inf,NR=1e4,NE=1e4,fctDensity=None,fctCumulativeMass=None,fctPotential=None,TotalMass=None,G=1.,EPSREL=1e-6):
          
    
    self.Rmin   = Rmin        # maximum sampled radius
    self.Rmax   = Rmax        # minimum sampled radius  
    self.Rinf   = Rinf        # maximal radius consdered to compute the total mass
    self.NR     = NR          # number of radius bins
    self.NE     = NE          # number of energy bins
    self.EPSREL = EPSREL      # integration relative precision  
    self.fctDensity        = fctDensity
    self.fctPotential      = fctPotential
    self.fctCumulativeMass = fctCumulativeMass
    self.TotalMass         = TotalMass
    self.G                 = G           # gravitational constant

    # initialize 
    self.Init()

    # compute Psi array
    self.setPsi()
    
    # compute Nu array  (normalized rho)
    self.setNu()

    # define the distribution function
    self.setDFfct()
    
    # define energy bins
    self.setEnergyBins()
    
    
    
  def Init(self):
    '''
    Perform initialization
    '''
    
    # set the radial bins
    self.setRadialBins()
    
    # a one variable function (of R)
    self.computeTotalMass()
    
    # define the cumulative mass function
    self.setCumulativeMassfct()
    
    # define the potential function
    self.setPotentialfct()
          
    # compute the cumulative mass
    self.computeCumulativeMass()
    
  
  def setRadialBins(self,log=True):  
    '''
    define a list of radius
    '''
    if log:
      self.R = np.logspace(np.log10(self.Rmin),np.log10(self.Rmax),num=int(self.NR))      
    else:
      self.R = np.linspace(self.Rmin,self.Rmax,num=int(self.NR))     

  def setEnergyBins(self,log=False):  
    '''
    define a list of energy, from max(Psi) (R=Rmin) to Emax/NE  (avoid E=0)
    '''
        
    # compute most-bound/least-bound energy
    self.Emax = self.psi[0]
    self.Emin = self.Emax/float(self.NE)
    
    if log:
      self.E = np.logspace(np.log10(self.Emin),np.log10(self.Emax),num=int(self.NE))      
    else:
      self.E = np.linspace(self.Emin,self.Emax,num=int(self.NE))    


  
  def computeTotalMass(self):
    ''' 
    compute the total mass function by numerical integration
    '''
    if self.TotalMass is None:
      self.Mtot =  4 * np.pi * quad( lambda r: r*r * self.fctDensity(r) , 0., self.Rinf)[0] 
    else:
      self.Mtot = self.TotalMass

  def setCumulativeMassfct(self):
    ''' 
    define the "normalized" cumulative mass function (direct integration)
    '''
    if self.fctCumulativeMass is None:
      self.fctMr = np.vectorize(lambda x: 4*np.pi *  quad( lambda r: r*r * self.fctDensity(r)/self.Mtot , 0., x)[0]  )
    else:
      self.fctMr = lambda r:self.fctCumulativeMass(r)/self.Mtot
        
  
  def computeCumulativeMass(self):
    '''
    compute the "normalized" cumulative mass
    '''     
    self.Mcum = self.fctMr(self.R)
    
    

        
  def setPotentialfct(self):
    ''' 
    define the potential function (it is faster to use quad instead of fctMr)
    '''
    
    if self.fctPotential is None:
       # self.fctPotential  = np.vectorize(lambda x: -4*np.pi*self.G*quad( lambda r: r*r * self.fctDensity(r)/self.Mtot , 0., x)[0]/x 
                                                   # -4*np.pi*self.G*quad( lambda r: r   * self.fctDensity(r)/self.Mtot , x, self.Rinf)[0])
       self.fctPotential  = np.vectorize(lambda x: -4*np.pi*self.G*quad( lambda r: r*r * self.fctDensity(r) , 0., x)[0]/x 
                                                   -4*np.pi*self.G*quad( lambda r: r  * self.fctDensity(r) , x, self.Rinf)[0])
        
  
  def setPsi(self):
    '''
    set Psi (array), the relative potential
    '''
    self.psi = -self.fctPotential(self.R)
  
  def setNu(self):
    '''
    set Nu (array), the probability (normalized density)
    '''
    self.nu  =   self.fctDensity(self.R) / self.Mtot
      
    
    
  def setDFfct(self):
    ''' 
    define the distribution function through the Eddington formula.
    Note that we assume dnu/dpsi equal to 0.
    '''
      
    # compute gradients
    dndp   = np.gradient(self.nu,   self.psi)
    d2nd2p = np.gradient(dndp, self.psi)
    
    self.dndp   = dndp
    self.d2nd2p = d2nd2p
        
    if np.fabs(dndp[-1]) > 1e-5:
      print("WARNING: dnu/dpsi = %g > 1e-6\n"%dndp[-1])
      exit()

    # this fuction is very steep : we should integrate its log    
    #fctp =  lambda p:  np.interp(p, self.psi[::-1], d2nd2p[::-1]) / np.sqrt(e-p)
    self.fctDF = np.vectorize( lambda e: 1./(np.sqrt(8)*np.pi*np.pi) * (quad( lambda p:  np.interp(p, self.psi[::-1], d2nd2p[::-1]) / np.sqrt(e-p) , 0., e,  epsrel=self.EPSREL)[0]  ) )
    
     
  def computeDF(self):
    '''
    Compute the DF using the set of relative energies self.E
    '''
    self.DF = self.fctDF(self.E)
    
    
 
  def checkDF(self):
    '''
    check whether DF is physical - if not, check for rounding errors in integration, try increasing/decreasing NR, NE
    '''
    if np.any (self.DF < 0) : 
      print("DF < 0 !!!" )
      sys.exit(0)
    
    return True
    

  def clean(self):
    '''
    clean DF
    '''
    
    if np.any (self.DF < 0) : 
      pass
    else:
      return
     
    c = self.DF < 0
    
    print("INFO: {0:d} energy bins out of {1:d} have negative values".format(c.sum(),len(self.DF)))
    
    subDF = np.compress(c,self.DF)
    subE  = np.compress(c,self.E)
    
    self.DF = np.where(c,0,self.DF)

    
    
    
    
  def dPdr(self,e,r):  
    '''
    phase space volume element per energy accessible at given energy e and fixed radius r
    sqrt( 2(psi-e) ) r^2
    see BT, integrand of Eq 4.56
    '''  
    return np.sqrt( 2.*(np.interp(r, self.R, self.psi) - e )) * r*r     
    

  def PLikelihood(self,e,r):
    '''
    likelihood of a particle to have an energy E at a fixed radius
    dP/dr * DF(e)
    '''
    return np.interp(e,self.E,self.DF) * self.dPdr(e,r)
  
  
  def computePLikelihoodForR(self,R):
    '''
    compute the energy probability distribution 
    for a given radius
    '''

    # compute Psi for a given radius
    Epsi = np.interp(R,self.R,self.psi)
    
    # keep only the accessible energies for this radius
    #allowed = np.where (self.E <=  Epsi )[0]
    condition = self.E <=  Epsi
    Eallowed = np.compress (condition, self.E)
    
    # compute the maximum likelihood for this radius
    return self.PLikelihood(Eallowed,R),Eallowed
    

  def computeMaxLikelihood(self):
    '''
    for each radius in self.R, compute the maximum likelihood
    '''
    self.maxPLikelihood = np.zeros(int(self.NR))
    # loop over radii
    for i,R in enumerate(self.R):
      # compute the maximum likelihood for this radius
      PLikelihood,E = self.computePLikelihoodForR(R)
      
      # compute the maximum likelihood for this radius
      maxPLikelihood = PLikelihood.max()

      # and add 10% tolerance
      self.maxPLikelihood[i]=1.1* maxPLikelihood
    
    
  def sample(self,N,Ndraw,irand=0):
    '''
    N      : number of particles to draw
    Ndraw  : number of random numbers drawn at a time 
    
    return pos and vel
    '''
    np.random.seed(irand)
    
    xx = np.zeros(int(N))
    yy = np.zeros(int(N))
    zz = np.zeros(int(N))
    vx = np.zeros(int(N))
    vy = np.zeros(int(N))
    vz = np.zeros(int(N))    
    
    n=0             # current number of generated 'particles'
    Efails = 0      # rejection sampling failures in Energy

    # "normalized" cumulative mass
    Mcum = self.Mcum
    
    # compute the number of particles inside Rmin
    Nin  = int(N *      4 * np.pi * quad( lambda r: r*r * self.fctDensity(r)/self.Mtot , 0., self.Rmin)[0] )
    # compute the number of particles outside Rmax
    Nout = int(N * (1 - 4 * np.pi * quad( lambda r: r*r * self.fctDensity(r)/self.Mtot , 0., self.Rmax)[0] ) )
    
    if Nin > 0:
      print("INFO: out of %i particles there are %i part. with R < Rmin (%.2f per cent)"%(N,Nin, 100.*Nin/float(N) ) )
    if Nout > 0:
      print("INFO: out of %i particles there are %i part. with R > Rmax (%.2f per cent)"%(N,Nout,100.*Nout/float(N) ) )
        

    # while we still need to generate 'particles'..
    while (n < N):

      # random number between fraction of particles within  min. sampled radius Rmin 
      #                   and fraction of particles outside max. sampled radius Rmax
      randMcum = Nin/float(N)  + (1.-(Nin+Nout)/float(N)) * np.random.rand(int(Ndraw))

      # inverse the cumulative mass function to get a list of radius between Rmin and Rmax 
      # that sample the density rho(r)
      randR = np.interp(randMcum ,Mcum ,self.R)      

      
      # compute the relative potential
      psiR = np.interp(randR ,self.R ,self.psi)
      
      # random relative energy between 0 and psiR
      randE = np.random.rand(int(Ndraw)) * psiR  
      
      # likelihood for E at given R
      rhoE  = self.PLikelihood(randE,randR)
      
      # draw a random number between 0 and the max likelihood for each radius
      randY = np.random.rand(int(Ndraw)) * np.interp(randR,self.R,self.maxPLikelihood) 
      
      # record the index of the failed points
      Missidx = np.where(randY > rhoE)[0]        
      Efails += len(Missidx)
      
      #print("Efails = %d"%Efails)

      # repeat sampling at fixed R till we got all the energies we need
      loop=0
      while len(Missidx):
        loop=loop+1
        randE[Missidx] = np.random.rand(len(Missidx)) * psiR[Missidx]  
        rhoE[Missidx]  = self.PLikelihood(randE[Missidx],randR[Missidx])
        randY[Missidx] = np.random.rand(len(Missidx)) * np.interp(randR[Missidx],self.R, self.maxPLikelihood)
        Missidx = np.where(randY > rhoE)[0]
        Efails += len(Missidx)
        
        #print("loop=%3d Efails = %d"%(loop,Efails))
      

      # final check (this should never happen)
      okEidx = np.where(randY <= rhoE)[0]
      if len(okEidx) != int(Ndraw):             
        print("Particles went missing. Exit." )
        sys.exit(0)

      # Let's select as many R,E combinations as we're still missing to get N particles in total
      missing = int(N) - int(n)
      if len(okEidx) <= missing: 
        arraxIdx = n + np.arange(0,len(okEidx))
      else: 
        arraxIdx = n + np.arange(0,missing)
        okEidx = okEidx[:missing]      
      
      n += len(okEidx)


      # spherical symmetric model, draw random points on sphere
      Rtheta  = np.arccos (2. * np.random.rand(len(okEidx)) - 1.)
      Rphi    = np.random.rand(len(okEidx)) * 2*np.pi
      
      # isotropic velocity dispersion, draw random points on sphere
      Vtheta  = np.arccos (2. * np.random.rand(len(okEidx)) - 1.)
      Vphi    = np.random.rand(len(okEidx)) * 2*np.pi
      V =  np.sqrt( 2.*(psiR[okEidx] - randE[okEidx] ))  
      
      # spherical to cartesian coordinates 
      xx[arraxIdx] = randR[okEidx] * np.sin(Rtheta) * np.cos(Rphi)
      yy[arraxIdx] = randR[okEidx] * np.sin(Rtheta) * np.sin(Rphi)
      zz[arraxIdx] = randR[okEidx] * np.cos(Rtheta) 
      
      vx[arraxIdx] = V * np.sin(Vtheta) * np.cos(Vphi)
      vy[arraxIdx] = V * np.sin(Vtheta) * np.sin(Vphi)
      vz[arraxIdx] = V * np.cos(Vtheta)

    self.pos = np.transpose(np.array([xx, yy, zz]))
    self.vel = np.transpose(np.array([vx, vy, vz]))

    M = self.Mtot
    self.mass = self.Mtot*np.ones(len(self.pos))/len(self.pos)    




  def save(self,name,ftype,ptype,u):   
    '''
    save the model
    '''
    if name is not None:
      M = self.Mtot
            
      mass = M*np.ones(len(self.pos))/len(self.pos)
      nb = Nbody(status='new',p_name=name,pos=self.pos,vel=self.vel,mass=mass,ftype=ftype)
      
      # add units
      nb.UnitLength_in_cm         = u["UnitLength_in_cm"]
      nb.UnitMass_in_g            = u["UnitMass_in_g"]           
      nb.UnitVelocity_in_cm_per_s = u["UnitVelocity_in_cm_per_s"]
      nb.Unit_time_in_cgs         = u["Unit_time_in_cgs"]
    
      # additional stuffs
      nb.massarr=None
      nb.nzero = None
      nb.setComovingIntegrationOff()
      
      # particle type
      nb.set_tpe(ptype)
      
      # cvcenter
      nb.cvcenter()
      
      # write
      nb.write()
    
    
    
    
    
    
    
