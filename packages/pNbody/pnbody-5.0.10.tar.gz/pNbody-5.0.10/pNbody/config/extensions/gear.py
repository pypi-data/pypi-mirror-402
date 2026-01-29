import os
import sys
import types

import numpy as np

from pNbody import parameters, units, ctes, cosmo
from pNbody import thermodyn
from pNbody.libutil import getLOS

class _NbodyMyGear:
  
  
  def isComovingIntegrationOn(self):
    """
    return true if the file has been runned using
    the comoving integration scheme
    (obsolete)
    """
    return self.comovingintegration

  def setComovingIntegrationOn(self):
    """
    (obsolete)
    """
    self.comovingintegration = True

  def setComovingIntegrationOff(self):
    """
    (obsolete)
    """
    self.comovingintegration = False

  def ComovingIntegrationInfo(self):
    """
    (obsolete)
    """
    if self.isComovingIntegrationOn():
      self.message("ComovingIntegration")
      self.message("  on  (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
    else:
      self.message("ComovingIntegration")
      self.message(" off")


  def isCosmoRun(self):
    """
    return true if the run is a cosmological run
    """
    return self.doComovingToProperConversion()   


    
  def HubbleFactorCorrectionInfo(self):    
    if self.doHubbleFactorCorrection():
      self.message("  on  (h=%5.3f)"%(self.hubbleparam))
    else:
      self.message("  off")
      
 
  def doHubbleFactorCorrection(self):
      """
      return true if we need to correct from the Hubble factor
             false instead
      """
      return self.hubblefactorcorrection
       
            
  def HubbleFactorCorrectionOn(self):
      """
      enable Hubble factor correction
      """
      self.hubblefactorcorrection  = True   
      
      
  def HubbleFactorCorrectionOff(self):
      """
      disable Hubble factor correction
      """
      self.hubblefactorcorrection  = False



  def ComovingToProperConversionInfo(self):
    if self.doComovingToProperConversion():
      self.message("  on  (a=%5.3f)"%(self.atime))
    else:
      self.message("  off")
      
      
  def doComovingToProperConversion(self):
      """
      return true if we need want to convert from comoving to proper coordinates
             false instead
      """
      return self.comovingtoproperconversion

    
  def ComovingToProperConversionOn(self):
      """
      enable conversion from comoving to proper coordinates 
      """
      self.comovingtoproperconversion  = True   
      
      
  def ComovingToProperConversionOff(self):
      """
      disable conversion from comoving to proper coordinates 
      """
      self.comovingtoproperconversion  = False      
      



  def UnitsConversionFactor(self,units,mode=None):
      """
      return the unit conversion factor
      (not considering the Hubble parameter nor the scaling factor)
      """

      funit=1.0
      
      if units is not None:
      
        if type(units) in [str, bytes]:
          from pNbody import units as u
          units = u.GetUnitsFromString(units)
      
        funit = self.localsystem_of_units.convertionFactorTo(units)
      
      self.message("factor = %g"%funit)
        
      return funit  
        


  def ScaleFactorConversionFactor(self,a=None,mode=None):

      funit = 1.0

      if a is None:
        a = self.atime

      if self.doComovingToProperConversion():
        
        self.message("converting to physical units (a=%s)"%(a))

        if   mode=="pos":  
          funit = funit * a
        elif mode=="mass":
          pass
        elif mode=="rho":
          funit = funit / a**3   
        elif mode=="u":
          # for swift
          if self.utype=="swift":
            funit = funit / a**2   
          else:
            pass   
        elif mode=="u_init":                  # specific energy that contains no a (used for swift) 
          pass      
        elif mode=="vel":                     # we no longer consider the  self.pos*Ha*a term
          if self.utype=="swift":       
            pass
          if self.utype=="auriga" or  self.utype=="gear":
            funit = funit *np.sqrt(a)
        else:
          pass 

        self.message("factor=%g"%(funit))

      return funit


  def HubbleConversionFactor(self,h=None,mode=None):

      funit = 1.0

      if h is None:
        h = self.hubbleparam

      if self.doHubbleFactorCorrection():
        self.message("apply hubble factor (h=%5.3f)"%(h))
   
        if mode=="pos":  
          funit = funit / h
        elif mode=="mass":
          funit = funit / h
        elif mode=="rho":
          funit = funit * h**2  
        elif mode=="u":
          pass      
        elif mode=="u_init":
          pass    
        elif mode=="vel":
          pass    
        elif mode=="time":
          funit = funit / h                                      
        else:
          pass  

        self.message("factor=%g"%(funit))

        
      return funit

        

  def ConversionFactor(self,units,a=None,h=None,mode=None):
      """
      return the unit conversion factor
      (not considering the Hubble parameter nor the scaling factor)
      """
      
      
      if a is None:
        a = self.atime
      
      if h is None:
        h = self.hubbleparam
      
      
      # do the unit conversion        
      funit = self.UnitsConversionFactor(units,mode=mode)
   
   
      # compute the comoving to proper conversion factor
      funit = funit * self.ScaleFactorConversionFactor(a=a,mode=mode)
 

      # compute the Hubble parameter factor
      funit = funit * self.HubbleConversionFactor(h=h,mode=mode)

   

      return funit
        




  def spec_info(self):
    """
    Write spec info
    """	
    infolist = []
    infolist.append("")
    #infolist.append("nzero               : %s"%self.nzero)	
    #infolist.append("npart               : %s"%self.npart)		
    #infolist.append("massarr             : %s"%self.massarr)       
    infolist.append("atime               : %s"%self.atime)		
    infolist.append("redshift            : %s"%self.redshift)       
    infolist.append("flag_sfr            : %s"%self.flag_sfr)       
    infolist.append("flag_feedback       : %s"%self.flag_feedback)  
    if self.has_var("nall"):
      infolist.append("nall                : %s"%self.nall)		
    infolist.append("flag_cooling        : %s"%self.flag_cooling)   
    infolist.append("num_files           : %s"%self.num_files)      
    infolist.append("boxsize             : %s"%self.boxsize)        
    infolist.append("omega0              : %s"%self.omega0)  	
    infolist.append("omegalambda         : %s"%self.omegalambda)    
    infolist.append("hubbleparam         : %s"%self.hubbleparam)   
    infolist.append("flag_age            : %s"%self.flag_age)
    infolist.append("flag_metals         : %s"%self.flag_metals)
    infolist.append("nallhw              : %s"%self.nallhw)
    #infolist.append("flag_entr_ic        : %s"%self.flag_entr_ic) 
    infolist.append("critical_energy_spec: %s"%self.critical_energy_spec) 


    infolist.append("")
    if self.has_array('u'):
      infolist.append("len u               : %s"%len(self.u))
      infolist.append("u[0]                : %s"%self.u[0])
      infolist.append("u[-1]               : %s"%self.u[-1])
    if self.has_array('rho'):  
      infolist.append("len rho             : %s"%len(self.rho))
      infolist.append("rho[0]              : %s"%self.rho[0])
      infolist.append("rho[-1]             : %s"%self.rho[-1])  
    if self.has_array('rsp'):  
      infolist.append("len rsp             : %s"%len(self.rsp))
      infolist.append("rsp[0]              : %s"%self.rsp[0])
      infolist.append("rsp[-1]             : %s"%self.rsp[-1]) 
    if self.has_array('opt'):  
      infolist.append("len opt             : %s"%len(self.opt))
      infolist.append("opt[0]              : %s"%self.opt[0])
      infolist.append("opt[-1]             : %s"%self.opt[-1])     
    if self.has_array('opt2'):  
      infolist.append("len opt2            : %s"%len(self.opt2))
      infolist.append("opt2[0]             : %s"%self.opt2[0])
      infolist.append("opt2[-1]            : %s"%self.opt2[-1])     
    if self.has_array('erd'):  
      infolist.append("len erd             : %s"%len(self.erd))
      infolist.append("erd[0]              : %s"%self.erd[0])
      infolist.append("erd[-1]             : %s"%self.erd[-1]) 
    if self.has_array('dte'):  
      infolist.append("len dte             : %s"%len(self.dte))
      infolist.append("dte[0]              : %s"%self.dte[0])
      infolist.append("dte[-1]             : %s"%self.dte[-1]) 

    if self.has_array('tstar'):  
      infolist.append("len tstar           : %s"%len(self.tstar))
      infolist.append("tstar[0]            : %s"%self.tstar[0])
      infolist.append("tstar[-1]           : %s"%self.tstar[-1])

    if self.has_array('idp'):
      infolist.append("len idp             : %s"%len(self.idp))
      infolist.append("idp[0]              : %s"%self.idp[0])
      infolist.append("idp[-1]             : %s"%self.idp[-1])
      
    return infolist  



  def select(self, *arg, **kw):
      """
      Return an N-body object that contain only particles of a
      certain type:
      """

      index = self.getParticleMatchingDict()
      
      # this allows to write nb.select(('gas','disk'))
      if len(arg) == 1:
          if isinstance(arg[0], tuple):
              arg = arg[0]

      tpes = arg

      # create the selection vector
      c = np.zeros(self.nbody)

      for tpe in tpes:
          if isinstance(tpe, str):
              if tpe not in index:
                  self.message("unknown type, do nothing %s" % (tpe),verbosity=0,color='r')
                  return self
              else:
                  i = index[tpe]
                  c = c + (self.tpe == i)

          elif isinstance(tpe, int):

              c = c + (self.tpe == tpe)

      return self.selectc(c)



  def subdis(self,mode='dd',val=None):
    """
    Equivalent of select
    """
    return self.select(mode)




  def MetalsH(self):
    """
    Return the metalicity of each particle.
    
    By default, use the variable self.metals    
    """
    # use the function specific to the format if it exists.
    if hasattr(self,"_MetalsH"):
      return self._MetalsH()

    if not self.has_array('metals'):
      raise ValueError("the array 'metals' is not defined")

    elt = "Metals"
    idx = self.ChimieElements.index(elt)
    return np.log10(self.metals[:,idx] / self.ChimieSolarMassAbundances[elt] + 1.0e-20)
    

  

  def Fe(self):
    """
    metallicity Fe
    """
    elt = "Fe"
    idx = self.ChimieElements.index(elt)
    return np.log10(self.metals[:,idx] / self.ChimieSolarMassAbundances[elt] + 1.0e-20)



  def Mg(self):
    """
    magnesium
    """
    elt = "Mg"
    idx = self.ChimieElements.index(elt)
    return np.log10(self.metals[:,idx] / self.ChimieSolarMassAbundances[elt] + 1.0e-20)



  def O(self):
    """
    Oxygen
    """
    elt = "O"
    idx = self.ChimieElements.index(elt)
    return np.log10(self.metals[:,idx] / self.ChimieSolarMassAbundances[elt] + 1.0e-20)


  def Ba(self):
    """
    Barium
    """
    elt = "Ba"
    idx = self.ChimieElements.index(elt)
    return np.log10(self.metals[:,idx] / self.ChimieSolarMassAbundances[elt] + 1.0e-20)


  def MgFe(self):
    elt1 = "Mg"
    elt2 = "Fe"
    idx1 = self.ChimieElements.index(elt1)
    idx2 = self.ChimieElements.index(elt2)
    eps = 1e-20
    return np.log10((self.metals[:,idx1]+eps)/(self.metals[:,idx2]+eps) / self.ChimieSolarMassAbundances[elt1] * self.ChimieSolarMassAbundances[elt2])

  def CaFe(self):
    elt1 = "Ca"
    elt2 = "Fe"
    idx1 = self.ChimieElements.index(elt1)
    idx2 = self.ChimieElements.index(elt2)
    eps = 1e-20
    return np.log10((self.metals[:,idx1]+eps)/(self.metals[:,idx2]+eps) / self.ChimieSolarMassAbundances[elt1] * self.ChimieSolarMassAbundances[elt2])


  def BaFe(self):
    elt1 = "Ba"
    elt2 = "Fe"
    idx1 = self.ChimieElements.index(elt1)
    idx2 = self.ChimieElements.index(elt2)
    eps = 1e-20
    return np.log10((self.metals[:,idx1]+eps)/(self.metals[:,idx2]+eps) / self.ChimieSolarMassAbundances[elt1] * self.ChimieSolarMassAbundances[elt2])


  def SiFe(self):
    elt1 = "Si"
    elt2 = "Fe"
    idx1 = self.ChimieElements.index(elt1)
    idx2 = self.ChimieElements.index(elt2)
    eps = 1e-20
    return np.log10((self.metals[:,idx1]+eps)/(self.metals[:,idx2]+eps) / self.ChimieSolarMassAbundances[elt1] * self.ChimieSolarMassAbundances[elt2])



  def AbRatio(self,elt1,elt2):
    """
    return [X/Y]
    """

    if elt2=="H":
      idx1 = self.ChimieElements.index(elt1)
      return np.log10(self.metals[:,idx1] / self.ChimieSolarMassAbundances[elt1] + 1.0e-20)
    else:
      idx1 = self.ChimieElements.index(elt1)
      idx2 = self.ChimieElements.index(elt2)
      eps = 1e-20
      return np.log10((self.metals[:,idx1]+eps)/(self.metals[:,idx2]+eps) / self.ChimieSolarMassAbundances[elt1] * self.ChimieSolarMassAbundances[elt2])







  #################################################################
  # physical values (with correct unit conversion)
  #################################################################


  
  def Pos(self,a=None,h=None,units=None):
    '''
    return the position of the particles in physical units
    '''
    funit=self.ConversionFactor(units,a=a,h=h,mode='pos')
    return self.pos*funit     
  

  def Rxyz(self,a=None,h=None,units=None,center=None):
    """
    return the radius of each particles in physical units, i.e.
    correct it from the scaling factor and h if necessary (i.e. comoving integration is on)
    """
    self.message("... compute Rxyz()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='pos')
    return self.rxyz(center=center) * funit



  def Rxy(self,a=None,h=None,units=None,center=None):
    """
    return the radius of each particles in physical units, i.e.
    correct it from the scaling factor and h if necessary (i.e. comoving integration is on)
    """
    self.message("... compute Rxy()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='pos')
    return self.rxy() * funit
      

  def SphRadius(self,a=None,h=None,units=None):
    """
    return the sph radius of each particles in physical units, i.e.
    correct it from the scaling factor and h if necessary (i.e. comoving integration is on)
    """
    self.message("... compute Hsml()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='pos')
    return self.rsp * funit


  def Vel(self,a=None,h=None,units=None):
    '''
    return the velocity of the particles in physical units
    
    we no longer consider the expansion of the universe, i.e.
    
      Hubble     = ctes.HUBBLE.into(self.localsystem_of_units)
      OmegaLambda= self.omegalambda
      Omega0     = self.omega0
      pars = {"Hubble":Hubble,"OmegaLambda":OmegaLambda,"Omega0":Omega0}
      Ha =  cosmo.Hubble_a(self.atime,pars=pars)
      
      v_exp = self.pos*Ha*a
      
          
    '''
    self.message("... compute Vel()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='vel')
    return self.vel * funit
    

  def Mass(self,a=None,h=None,units=None):
    """
    return the mass of the particles in physical units, i.e.
    correct it from the scaling factor and h if necessary
    """
    self.message("... compute Mass()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='mass')
    return self.mass * funit

  def TotalMass(self,a=None,h=None,units=None):
    """
    return the mass of the particles in physical units, i.e.
    correct it from the scaling factor and h if necessary
    """
    self.message("... compute TotalMass()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='mass')
    return self.mass_tot * funit


  def InitialMass(self,a=None,h=None,units=None):
    '''
    return the initial mass of stellar particles in physical units, i.e.
    correct it from the scaling factor and h if necessary
    '''
    self.message("... compute InitialMass()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='mass')
    return self.minit * funit



  def Rho(self,a=None,h=None,units=None):
    '''
    return the mass density of gas particles in physical units, i.e.
    correct it from the scaling factor and h if necessary
    '''
    self.message("... compute Rho()")
    funit=self.ConversionFactor(units,a=a,h=h,mode='rho')
    return self.rho * funit

  def InternalEnergy(self,a=None,h=None,units=None):
    '''
    return the internal energy of gas particles in physical units, i.e.
    correct it from the scaling factor and h if necessary
    '''
    self.message("... compute InternalEnergy()")
      
    if self.has_array("u"):
      funit=self.ConversionFactor(units,a=a,h=h,mode='u')
      return self.u * funit
    elif  self.has_array("u_init"):
      funit=self.ConversionFactor(units,a=a,h=h,mode='u_init')
      return self.u_init * funit
    else:
      raise Exception("neither self.u nor nb.u_init are defined.")
      
        

  def GasMeanWeight(self):
    '''
    Return the mean molecular weight of the gas
    
    Note: (1) we don't consider the presence of metals here
          (2) the density could be omitted.
    '''
    self.message("... compute MeanWeight()")
    

    if self.has_array("XHDI"):                                           #grackle3
      self.message("... found info for grackle mode=3")
      rho    = self.rho
      nHI    = self.XHI    * rho
      nHII   = self.XHII   * rho
      nHeI   = self.XHeI   * rho / 4
      nHeII  = self.XHeII  * rho / 4
      nHeIII = self.XHeIII * rho / 4
      nH2I   = self.XH2I   * rho / 2
      nH2II  = self.XH2II  * rho / 2
      nHDI   = self.XHDI   * rho / 3
      nel    = nHII + nHeII + 2 * nHeIII + nH2II
      n      = nHI + nHII + nHeI + nHeII + nHeIII + nH2I + nH2II + nHDI + nel
      mu = rho/n
      return mu

    elif self.has_array("XH2I"):                                         #grackle2
      self.message("... found info for grackle mode=2")
      rho    = self.rho
      nHI    = self.XHI    * rho
      nHII   = self.XHII   * rho
      nHeI   = self.XHeI   * rho / 4
      nHeII  = self.XHeII  * rho / 4
      nHeIII = self.XHeIII * rho / 4
      nH2I   = self.XH2I   * rho / 2
      nH2II  = self.XH2II  * rho / 2
      nel    = nHII + nHeII + 2 * nHeIII + nH2II
      n      = nHI + nHII + nHeI + nHeII + nHeIII + nH2I + nH2II + nel
      mu = rho/n
      return mu

    elif self.has_array("XHI"):                                           #grackle1
      self.message("... found info for grackle mode=1")
      rho    = self.rho
      nHI    = self.XHI    * rho
      nHII   = self.XHII   * rho
      nHeI   = self.XHeI   * rho / 4
      nHeII  = self.XHeII  * rho / 4
      nHeIII = self.XHeIII * rho / 4
      nel    = nHII + nHeII + 2 * nHeIII
      n      = nHI + nHII + nHeI + nHeII + nHeIII + nel
      mu = rho/n
      return mu

    else:
      mu = thermodyn.MeanWeight(xi,ionisation)
      return mu



  def GasMeanWeightDD(self):
    '''
    Return the mean molecular weight of the gas
    '''
    self.message("... compute MeanWeight()")
    
    from astropy import units as u
    from astropy import constants as c

    # hydrogen mass in gram
    mH_in_g = c.m_p.to(u.g).value

    if self.has_array("XHDI"):                                           #grackle3
      self.message("... found info for grackle mode=3")
      rho = self.Rho(units='g/cm3')
      nHI = self.XHI * rho / (mH_in_g)
      nHII = self.XHII * rho / (mH_in_g)
      nHeI = self.XHeI * rho / (4 * mH_in_g)
      nHeII = self.XHeII * rho / (4 * mH_in_g)
      nHeIII = self.XHeIII * rho / (4 * mH_in_g)
      nH2I = self.XH2I * rho / (2 * mH_in_g)
      nH2II = self.XH2II * rho / (2 * mH_in_g)
      nHDI = self.XHDI * rho / (3 * mH_in_g)
      nel = nHII + nHeII + 2 * nHeIII + nH2II
      mu = ((nHI + nHII) + (nHeI + nHeII + nHeIII) * 4 + (nH2I + nH2II) * 2 + nHDI * 3) / (nHI + nHII + nHeI + nHeII + nHeIII + nH2I + nH2II + nHDI + nel)
      return mu

    elif self.has_array("XH2I"):                                         #grackle2
      self.message("... found info for grackle mode=2")
      rho = self.Rho(units='g/cm3')
      nHI = self.XHI * rho / (mH_in_g)
      nHII = self.XHII * rho / (mH_in_g)
      nHeI = self.XHeI * rho / (4 * mH_in_g)
      nHeII = self.XHeII * rho / (4 * mH_in_g)
      nHeIII = self.XHeIII * rho / (4 * mH_in_g)
      nH2I = self.XH2I * rho / (2 * mH_in_g)
      nH2II = self.XH2II * rho / (2 * mH_in_g)
      nel = nHII + nHeII + 2 * nHeIII + nH2II
      mu = ((nHI + nHII) + (nHeI + nHeII + nHeIII) * 4 + (nH2I + nH2II) * 2) / (nHI + nHII + nHeI + nHeII + nHeIII + nH2I + nH2II + nel)
      return mu

    elif self.has_array("XHI"):                                           #grackle1
      self.message("... found info for grackle mode=1")
      rho = self.Rho(units='g/cm3')
      nHI = self.XHI * rho / (mH_in_g)
      nHII = self.XHII * rho / (mH_in_g)
      nHeI = self.XHeI * rho / (4 * mH_in_g)
      nHeII = self.XHeII * rho / (4 * mH_in_g)
      nHeIII = self.XHeIII * rho / (4 * mH_in_g)
      nel = nHII + nHeII + 2 * nHeIII
      mu = ((nHI + nHII) + (nHeI + nHeII + nHeIII) * 4) / (nHI + nHII + nHeI + nHeII + nHeIII + nel)
      return mu

    else:
      mu = thermodyn.MeanWeight(xi,ionisation)
      return mu


  def T(self,a=None,h=None,units=None):
    '''
    u does not depends on a nor h
    '''
    self.message("... compute T()")
    
    from astropy import units as u
    from astropy import constants as c
    
    k_in_erg_K = c.k_B.to(u.erg/u.K).value
    
    mh         = ctes.PROTONMASS.into(self.localsystem_of_units)
    gamma      = self.unitsparameters.get('gamma')

    if self.has_array("XHI"):
      mu = self.GasMeanWeight()
      u = self.InternalEnergy(a=a,h=h,units='erg')
      T = mu * (gamma - 1.0) * u * mh / k_in_erg_K
      return T

    else:

      gamma      = self.unitsparameters.get('gamma')
      xi         = self.unitsparameters.get('xi')
      ionisation = self.unitsparameters.get('ionisation')
      mu         = thermodyn.MeanWeight(xi,ionisation)
      mh         = ctes.PROTONMASS.into(self.localsystem_of_units)
      k          = ctes.BOLTZMANN.into(self.localsystem_of_units)
      
      
      thermopars = {"k":k,"mh":mh,"mu":mu,"gamma":gamma}
      
      # compute internal energy
      u = self.InternalEnergy(a=a,h=h,units=units)
      
      # this is the old implementation, avoid the computation of the ionization state
      #T = where((u>0),(gamma-1.)* (mu*mh)/k * u,0)
      
      # this is the new implementation, but may take much more time
      T = np.where((u>0),thermodyn.Tru(u,thermopars),0)
      
      return T



    
  def ScaleFactor(self,units=None,t=None,params=None,mode=None):
    """
    return the scaling factor

    params={}
    params['OmegaLambda']  = 0.685
    params['Omega0']       = 0.315
    params['HubbleParam']  = 0.673    
   
    for a given t in Gyr:
      nb.ScaleFactor(t=t,units="Gyr",params=params)
      
    if t is taken from nb
      nb.ScaleFactor(params=params)
   
    """
    # use the function specific to the format if it exists.
    if hasattr(self,"_ScaleFactor"):
      return self._ScaleFactor()


    
    self.message("... compute ScaleFactor()")
    
    if self.isComovingIntegrationOn():
      return self.atime
    
  
    else:
  
  
      # do the unit conversion        
      funit = self.UnitsConversionFactor(units,mode=mode)
  
            
      if params==None:
        self.message("please, provides cosmological parameters",verbosity=0,color='r')
        self.message("like ",verbosity=0,color='r')      
        self.message("params={}",verbosity=0,color='r')
        self.message("params['OmegaLambda']  = 0.685",verbosity=0,color='r')
        self.message("params['Omega0']       = 0.315",verbosity=0,color='r')      
        self.message("params['HubbleParam']  = 0.673",verbosity=0,color='r')
        self.message("  ",verbosity=0,color='r')
        sys.exit()
      
        
      if t is None:
        t = self.atime  
     
      atime = t  / funit

      # add hubble parameter
      Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
      params['Hubble']      = Hubble     
      
      a = cosmo.a_CosmicTime(atime,pars=params,a0=0.5)
      
      return a
  
  

  def Redshift(self,age=None):
    """
    return the redshift of the current snapshot
    """
    # use the function specific to the format if it exists.    
    if hasattr(self,"_Redshift"):
      return self._Redshift()

    
    
    if self.has_var("redshift"):
      return self.redshift
    
    self.error("The variable .redshift is not defined.") 
  
    
    
    from pNbody import cosmo

    if age==None:
      age = self.tstar


    if self.isComovingIntegrationOn():
      redshift= cosmo.Z_a(age)
    else:    
      Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
      pars = {"Hubble":Hubble,"HubbleParam":self.hubbleparam,"OmegaLambda":self.omegalambda,"Omega0":self.omega0}            
      
      a = cosmo.a_CosmicTime(age*0.73,pars=pars)
      redshift= cosmo.Z_a(a)

    return   redshift



    


  def Time(self,units=None,a=None,t=None,params=None):
    """
    return the current time (cosmic time) in some units.
    
    By default, the value is taken from the variable self.time if the latter is available.
    
    
    nb.Time()                           # in code unit, using self.atime          
    nb.Time(a=0.5)                      # in code unit, forcing self.atime=a
    nb.Time(units="Gyr")                # in Gyr
    nb.Time(units="Gyr",a=0.5)          # in Gyr, forcing self.atime=a
    nb.Time(units="Gyr",a=[0.1,1])      # in Gyr, forcing self.atime=a
    
    nb.Time(units="Gyr",t=[1000])       # in Gyr, using t as the unit time (for self.isComovingIntegrationOff()==True only)
    nb.Time(units="Gyr",t=[1000,2000])  # in Gyr, using t as the unit time (for self.isComovingIntegrationOff()==True only)   
    
    in case self.isComovingIntegrationOff() and a is given, we need
    to have the cosmological parameter in params, like
    
    params={}
    params['OmegaLambda']  = 0.685
    params['Omega0']       = 0.315     
    params['HubbleParam']  = 0.673   
    
    
    """
    # use the function specific to the format if it exists.
    if hasattr(self,"_Time"):
      return self._Time(a=a,t=t,units=units)


    ###########################################
    # this is the old part (should be removed)

    self.message("... compute Time()")
    
    
    if type(a)==list:
      atime = np.array(a)

    if type(t)==list:
      t = np.array(t)    
    
    if a is not None:
      atime = a
    else:
      
      if t is not None:
        atime = t
      else:  
       atime = self.atime  
    
    
    # do the unit conversion        
    funit = self.UnitsConversionFactor(units,mode="time")  
    
      
    if self.isComovingIntegrationOn():
      
    
      if units is not None:
        
        Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
        pars = {"Hubble":Hubble,"HubbleParam":self.hubbleparam,"OmegaLambda":self.omegalambda,"Omega0":self.omega0}
        
        time = cosmo.CosmicTime_a(atime,pars)
        # correct from the Hubble parameter (as H0 is allways in units of h)
        if self.hubbleparam != 0:
          time = time/self.hubbleparam        
        return time*funit
      
      else:
        return atime
    
    
    else:
    
      if a is not None:       # use the scaling factor : no comoving integration but a is given
      
        if params==None:
          self.message("please, you must provides cosmological parameters")
          self.message("like ")      
          self.message("params={}")
          self.message("params['OmegaLambda']  = 0.685")
          self.message("params['Omega0']       = 0.315")      
          self.message("params['HubbleParam']  = 0.673")
          self.message("  ")
          sys.exit()
                
        Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
        params['Hubble']      = Hubble
     
        time = cosmo.CosmicTime_a(a=atime,pars=params) / params['HubbleParam']

        return time*funit
      
      else:                   # no comoving integration, use t
      
        return atime*funit

  
  def CosmicTime(self,age=None,t=None,units=None):
    """
    This is an alias for StellarFormationTime
    (for compatibility reasons)
    """
    return self.StellarFormationTime(a=age,t=t,units=units)
    
    


  def StellarFormationTime(self,a=None,t=None,units=None):
    '''
    Time at which a stellar particle formed in some given units.
    By default, the function assume nb.tstar to contain the
    scale factor or time of particles. 
    '''
    # use the function specific to the format if it exists.
    if hasattr(self,"_StellarFormationTime"):
      return self._StellarFormationTime(a=a,t=t,units=units)

    self.message("StellarFormationTime()")
    
    if not self.has_array("tstar"):
      raise ValueError("the array 'tstar' is not defined")
        
    a = self.tstar

    return self.Time(a=a,units=units)
  
  

  def StellarAge(self,a=None,t=None,units=None):
    '''
    Return the Age of a particle in some given units.
    By default, the function assume nb.tstar to contain the
    scale factor or time of particles. 
    '''
    # use the function specific to the format if it exists.
    if hasattr(self,"_StellarAge"):
      return self._StellarAge(a=a,units=units)
    
    self.message("compute StellarAge()")

    if not self.has_array("tstar"):
      raise ValueError("the array 'tstar' is not defined")
        
    astar = self.tstar
    tstar= self.Time(a=astar,units=units)
    tnow = self.Time(a=a,units=units)

    return tnow-tstar    

    
    

  def LuminositySpec(self,tnow=None,band="V"):
    """
    compute specific luminosity, per unit of Msol
    This is the new version, using units correctly

    tnow is given in code units
    """

    # initialize SSP
    from pNbody.SSP import libvazdekis
    # vazdekis_kb_mu1.3.txt : krupa 01 revisited
    self.LObj = libvazdekis.VazdekisLuminosities(os.path.join(parameters.OPTDIR,'SSP','vazdekis_kb_mu1.3.txt'),band)
    self.LObj.ExtrapolateMatrix(order=1,s=0)
    self.LObj.CreateInterpolator()
    self.LObj.Extrapolate2DMatrix()


    # Compute Age (tnow must be the scaling factor)
    Ages = self.StellarAge(units="Gyr",a=tnow)
    
    # get the metallicity
    MHs   = self.MetalsH()

    
    # compute luminosities using LObj
    L  = self.LObj.Luminosities(MHs,Ages)

    return L




  def Luminosity(self,tnow=None,band="V",model=None):
    '''
    Luminosity per particle in solar luminosity unit
    '''
    
    if model is None:
    
      mass = self.Mass(units="Msol")
      return self.LuminositySpec(tnow,band)*mass
    
    
    else:
      
      from pNbody.Mockimgs import luminosities
      
      # Initial SSP mass
      InitialMass = self.InitialMass(units="Msol")
      
      # Compute Age (tnow must be the scaling factor)
      Ages = self.StellarAge(units="Gyr",a=tnow)
      
      # get the metallicity
      MHs   = self.MetalsH()

      # get the model
      '''
      if model == "BastI":
        LuminosityModel = luminosities.LuminosityModel("BastI_L")
        L = LuminosityModel.Luminosities(InitialMass,Ages,MHs,current_mass=False)
      '''
      
      if model == "CMD":
        LuminosityModel = luminosities.LuminosityModel("CMD_L")
        L = LuminosityModel.Luminosities(InitialMass,Ages,MHs,current_mass=False)
      else:      
        LuminosityModel = luminosities.LuminosityModel(model)
        ML =  LuminosityModel.MassToLightRatio(Ages,MHs)
        L = self.Mass(units="Msol") / ML
      
      return L

  def TotalLuminosity(self,tnow=None,band="V",model=None):
    """
    Total Luminosity (sum self.Luminosity) in solar luminosity.
    """
    return self.Luminosity(tnow=tnow,band=band,model=model).sum()

    

  def Magnitudes(self,filter=None,tnow=None):
    '''
    return a Magnitudes per particle
    
    tnow allows to shift the stellar ages
    '''
    
    from pNbody.Mockimgs import filters

    if filter is None:
      filter = filters.default
    
    Filter = filters.Filter(filter)  
     
    # Initial SSP mass
    InitialMass = self.InitialMass(units="Msol")
    
    # Compute Age (tnow must be the scaling factor)
    Ages = self.StellarAge(units="Gyr",a=tnow)
    
    # get the metallicity
    MHs   = self.MetalsH()
    
    # compute the luminosity
    Mags = Filter.Magnitudes(InitialMass,Ages,MHs,current_mass=False)
    
    return Mags
    
  def TotalMagnitude(self,filter=None,tnow=None):
    '''
    return the total magnitude of the system
    
    tnow allows to shift the stellar ages
    '''
    
    mags = self.Magnitudes(filter=filter,tnow=tnow)
    # convert to flux
    F = np.sum(10**(-mags/2.5))
    # convert to magnitude
    return -2.5 * np.log10(F)  

  def Magnitude(self,filter=None,tnow=None):
    '''
    return the total magnitude of the system
    (alias for TotalMagnitude)
    tnow allows to shift the stellar ages
    '''
    return self.TotalMagnitude(filter=filter,tnow=tnow)



  """
  def RGB(self,tnow=None,u_mass=1.e10,u_time=4.7287e6):
    '''
    Compute the number of stars in each particle which are climbing the red giant branch, assuming a Kroupa IMF.
    '''
    from pNbody.SSP import libbastitime

    self.NRGB = libbastitime.BastiRGB(os.path.join(parameters.OPTDIR,'SSP','basti'))

    if self.tstar is None:
      return np.array([],np.float32)
    if tnow is None:
      tnow = self.atime

    Ages = (tnow-self.tstar)*u_time*1.0e-9
    Zs   = self.Fe()
    N = self.mass*u_mass*self.NRGB.RGBs(Zs,Ages)

    return(N)
  """




  # the following methods have not been tested with the Swift format





  def TotalKineticEnergy(self,a=None,h=None,units=None):
    '''
    return the mass of the particles

    a : scaling factor
    h : hubble parameter
    units : output units


    different cases :

      comoving integration      (self.comovingintegration==True)
      
        !!! we assume that  vel = w=sqrt(a)*xp 

        1) convert into physical coorinates
        2) if a=1 -> stay in comoving (in this case, we can also use nb.rho)

      non comoving integration (self.comovingintegration==False)

        1) do not convert
        2) if I want to force a behavior : put a=0.1 ->

    
    '''

    # set factor unit
    funit=1.0
    if units is not None:

      if type(units) in [str, bytes]:
        from pNbody import units as u
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)

    if self.isComovingIntegrationOn():
      self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
      return self.Ekin()*self.atime/self.hubbleparam *funit
    else:
      return self.Ekin()*funit



  def TotalPotentialEnergy(self,a=None,h=None,units=None):
    '''
    return the mass of the particles

    a : scaling factor
    h : hubble parameter
    units : output units


    different cases :

      comoving integration      (self.comovingintegration==True)
      
        1) convert into physical coorinates
        2) if a=1 -> stay in comoving (in this case, we can also use nb.rho)

      non comoving integration (self.comovingintegration==False)

        1) do not convert
        2) if I want to force a behavior : put a=0.1 ->

    
    '''

    # set factor unit
    funit=1.0
    if units is not None:

      if type(units) in [str, bytes]:
        from pNbody import units as u
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)

    if self.isComovingIntegrationOn():
      self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
      return self.Epot()/self.atime/self.hubbleparam *funit
    else:
      return self.Epot()*funit








  def FormationGasDensity(self,a=None,h=None,units=None):
    '''
    return the density of particles.

    a : scaling factor
    h : hubble parameter
    units : output units


    different cases :

      comoving integration      (self.comovingintegration==True)

        1) convert into physical coorinates
        2) if a=1 -> stay in comoving (in this case, we can also use nb.rho)

      non comoving integration (self.comovingintegration==False)

        1) do not convert
        2) if I want to force a behavior : put a=0.1 ->

    '''

    self.message("... compute FormationGasDensity()")

    # set factor unit
    funit=1.0
    if units is not None:

      if type(units) in [str, bytes]:
        from pNbody import units as u
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)

    if self.isComovingIntegrationOn():
      self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
      return self.rhostar/self.tstar**3*self.hubbleparam**2 *funit
    else:
      return self.rhostar*funit




  def TJeans(self,a=None,h=None,units=None,Hsml=None,Softening=None,SofteningMaxPhys=None):
    '''
    Jeans temperature for a given density and Hsml.
    The Jean temperature is the temperature corresponding to
    the Jeans pressure floor for a given density and resolution (Hsml).

    '''

    if self.verbose > 1 :
      self.message("... compute TJeans()")

    gamma      = self.unitsparameters.get('gamma')
    xi         = self.unitsparameters.get('xi')
    ionisation = self.unitsparameters.get('ionisation')
    mu         = thermodyn.MeanWeight(xi,ionisation)
    mh         = ctes.PROTONMASS.into(self.localsystem_of_units)
    k          = ctes.BOLTZMANN.into(self.localsystem_of_units)
    G  = ctes.GRAVITY.into(self.localsystem_of_units)
    self.message("Gravity constant = %g"%G)

    NJ = 10	# Jeans Mass factor

    rho    = self.Rho(a=a,h=h,units=units)

    if Hsml==None and Softening==None and SofteningMaxPhys==None:
      Hsml   = self.SphRadius(a=a,h=h,units=units)
    else:

      self.message("Hsml in TJeans:")

      if Softening!=None and SofteningMaxPhys!=None:
        self.message("     using Softening = %g and  SofteningMaxPhys = %g"%(Softening,SofteningMaxPhys))
        Hsml = self.ComputeSofteningCosmo(Softening,SofteningMaxPhys)

      else:
        Hsml = Hsml

      self.message("     using Hsml = %g (in physical units)"%Hsml)


    '''
    uJeans = 4./pi * NJ**(2./3.) * Hsml**2 * rho * G * (gamma-1)**(-1) * gamma**(-1)



    thermopars = {"k":k,"mh":mh,"mu":mu,"gamma":gamma}

    # this is the old implementation, avoid the computation of the ionization state
    #T = where((self.u>0),(gamma-1.)* (mu*mh)/k * self.u,0)

    # this is the new implementation, but may take much more time
    #TJeans = where((uJeans>0),thermodyn.Tru(uJeans,thermopars),0)
    '''

    TJeans = (mu*mh)/k * 4./np.pi * G/gamma * NJ**(2./3.) * Hsml**(2) * rho

    return TJeans




  def Tff(self,units=None):

    self.message("... compute Tff()")
    
    G = ctes.GRAVITY.into(self.localsystem_of_units)

    Tff   = np.sqrt(3*np.pi/(32*G*self.Rho()))

    if units is not None:

      if type(units) in [str, bytes]:
        from pNbody import units as u
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)
      Tff = Tff*funit

    if self.isComovingIntegrationOn():
      self.message("in Tff isComovingIntegrationOn is not implemented")
      sys.exit()


    return Tff.astype(np.float32)



  """
  def Pressure(self,units=None):

    self.message("... compute Pressure()")

    gamma      = self.unitsparameters.get('gamma')
    mu         = 1. # not needed here : thermodyn.MeanWeight(xi,ionisation)
    mh         = ctes.PROTONMASS.into(self.localsystem_of_units)
    k          = ctes.BOLTZMANN.into(self.localsystem_of_units)

    thermopars = {"k":k,"mh":mh,"mu":mu,"gamma":gamma}
    rho = self.Rho()

    P =	thermodyn.Pru(rho,self.u,thermopars)

    return P.astype(np.float32)
  """


  """
  def SoundSpeed(self,units=None):

    self.message("... compute SoundSpeed()")

    gamma      = self.unitsparameters.get('gamma')
    #mu         = 1. # not needed here : thermodyn.MeanWeight(xi,ionisation)
    #mh         = ctes.PROTONMASS.into(self.localsystem_of_units)
    #k          = ctes.BOLTZMANN.into(self.localsystem_of_units)

    #thermopars = {"k":k,"mh":mh,"mu":mu,"gamma":gamma}
    #rho = self.Rho()

    #P =	thermodyn.Pru(rho,self.u,thermopars)
    #C = np.sqrt(gamma*P/rho)

    C = np.sqrt(gamma*(gamma-1)*self.u)


    if units is not None:

      if type(units) in [str, bytes]:
        from pNbody import units as u
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)
      C = C*funit

    return C.astype(np.float32)
  """

  """
  def CourantTimeStep(self,units=None):

    self.message("... compute CourantTimeStep()")

    C = self.SoundSpeed()
    dt = self.SphRadius()/C

    return dt
  """











  """
  def sfr(self,dt):
    '''
    star formation rate per particle

    all units are in code units
    '''

    sfr = np.where( (self.atime-self.tstar) < dt, self.mass/dt ,0 )

    return sfr
  """


  def toProperUnits(self,a=None,h=None):
     """
     convert from comobile units to proper units (keeping the current units), i.e,
     correct only from the scaling factor and from the Hubble parameter
     
     Note that only the main quantities are converted.
     """
     
     # here we could also loop over self.get_list_of_arrays() (see Cosmo2Iso)
     
     self.pos  = self.Pos().astype(np.float32)
     self.vel  = self.Vel().astype(np.float32)
     self.mass = self.Mass().astype(np.float32) 
     
     if self.has_array('rho'):
       self.rho  = self.Rho().astype(np.float32)
     
     if self.has_array('u'):
       self.u    = self.InternalEnergy().astype(np.float32) 
       
     if self.has_array('minit'):  
       self.minit = self.InitialMass().astype(np.float32)
       
     if self.has_array('rsp'):  
       self.rsp = self.SphRadius().astype(np.float32)
              

     # disable conversions
     self.hubblefactorcorrection=False
     self.comovingtoproperconversion=False




  def toPhysicalUnits(self,a=None,h=None):
     """
     convert from comobile units to physical units
     correct from the scaling factor and
     from the hubble parameter
     
     !!! this function should be replaced by toProperUnits
     """
     
     self.warning("consider using toProperUnits instead of toPhysicalUnits")

     if self.isComovingIntegrationOn():

       if a is None:
         a = self.atime
       if h is None:
         h = self.hubbleparam

       self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(a,h))

       Hubble     = ctes.HUBBLE.into(self.localsystem_of_units)
       OmegaLambda= self.omegalambda
       Omega0     = self.omega0

       self.message("                                 (HubbleCte  =%5.3f)"%Hubble)
       self.message("                                 (OmegaLambda=%5.3f)"%OmegaLambda)
       self.message("                                 (Omega0     =%5.3f)"%Omega0)


       pars = {"Hubble":Hubble,"OmegaLambda":OmegaLambda,"Omega0":Omega0}

       Ha =  cosmo.Hubble_a(a,pars=pars)

       self.vel = self.pos*Ha*a + self.vel*np.sqrt(a)
       self.pos = self.pos*a/h
       self.mass= self.mass/h

       if self.has_array('u'):
         self.u   = self.u
       if self.has_array('rho'):
         self.rho = self.rho/a**3 * h**2




  def Cosmo2Iso(self,GadgetParameterFile1=None,GadgetParameterFile2=None):

    """
    This function is deprecated
    """
    
    from pNbody import units
    from pNbody import iofunc as io
    from pNbody import cosmo
  
  
    a = self.atime

    # unit options
    unit_params1 = io.read_params(GadgetParameterFile1) 

    unit_params2 = io.read_params(GadgetParameterFile2) 
    local_units_2 = units.Set_SystemUnits_From_Params(unit_params2)
    if 'HubbleParam' in unit_params2:
      local_units_2.CorrectFromHubbleParameter(unit_params2['HubbleParam'])


    # set some parameters
    Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
    
    cosmo.Omega0     = unit_params1['Omega0']
    cosmo.OmegaLambda= unit_params1['OmegaLambda']
    cosmo.HubbleParam= unit_params1["HubbleParam"]
    cosmo.Hubble     = Hubble
    cosmo.setdefault()      # this set defaultpars

    # compute some factors

    Ha = cosmo.Hubble_a(a,pars=cosmo.defaultpars)

    pos = self.pos
    vel = self.vel
    
    

    for ar in self.get_list_of_arrays():

      if ar == "pos":
        self.pos = pos * a

      elif ar == "vel":
        self.vel = vel*np.sqrt(a) + pos*a*Ha     
            
      elif ar == "mass":
        pass
        
      elif ar == "u":
        pass
         
      elif ar == "rho":
        self.rho = self.rho / a**3

      elif ar == "rsp":
        self.rsp = self.rsp * a

      elif ar == "tpe":
        pass

      elif ar == "num":
        pass
        
      elif ar == "minit":
        pass   

      else:
        self.message("skipping %s"%ar)


    # compute the time 
    hubbleparam = unit_params1["HubbleParam"]
    omegalambda = unit_params1["OmegaLambda"]
    omega0      = unit_params1["Omega0"]

    units = local_units_2.UnitTime
    funit = self.localsystem_of_units.convertionFactorTo(units)
    Hubble = ctes.HUBBLE.into(self.localsystem_of_units)
    pars = {"Hubble":Hubble,"HubbleParam":hubbleparam,"OmegaLambda":omegalambda,"Omega0":omega0} 
    age_beg = cosmo.CosmicTime_a(self.atime,pars) / hubbleparam * funit


    self.atime = age_beg

    # kill comobile flag
    self.comovingintegration= False
    self.omega0=0
    self.omegalambda=0















  def ChangeUnits(self,GadgetParameterFile1=None,GadgetParameterFile2=None):
  
    from pNbody import iofunc as io
    
    # define local units  
    
    cosmo_corrections = [] 


    if GadgetParameterFile1!=None:
      unit_params1 = io.read_params(GadgetParameterFile1) 
      local_units_1 = units.Set_SystemUnits_From_Params(unit_params1)    
      if 'HubbleParam' in unit_params1:
        local_units_1.CorrectFromHubbleParameter(unit_params1['HubbleParam'])
      
      ccorrect=False
      if 'Omega0' in unit_params1:
        if unit_params1['Omega0'] !=0:
          ccorrect=unit_params1
      cosmo_corrections.append(ccorrect)
          


    if GadgetParameterFile2!=None:  
      unit_params2 = io.read_params(GadgetParameterFile2) 
      local_units_2 = units.Set_SystemUnits_From_Params(unit_params2)
      if 'HubbleParam' in unit_params2:
        local_units_2.CorrectFromHubbleParameter(unit_params2['HubbleParam'])
      
      ccorrect=False
      if 'Omega0' in unit_params2:
        if unit_params2['Omega0'] !=0:
          ccorrect=unit_params2
      cosmo_corrections.append(ccorrect)


    UnitLengthRatio     = local_units_1.convertionFactorTo(local_units_2.UnitLength)
    UnitVelocityRatio   = local_units_1.convertionFactorTo(local_units_2.UnitVelocity)
    UnitMassRatio       = local_units_1.convertionFactorTo(local_units_2.UnitMass)
    UnitEnergySpecRatio = local_units_1.convertionFactorTo(local_units_2.UnitEnergy)/local_units_1.convertionFactorTo(local_units_2.UnitMass)
    UnitDensityRatio    = local_units_1.convertionFactorTo(local_units_2.UnitDensity)
    UnitTimeRatio       = local_units_1.convertionFactorTo(local_units_2.UnitTime)

    # check
    if unit_params1['HubbleParam'] != self.hubbleparam:
      
      self.warning("unit_params1['HubbleParam'] = %f"%(unit_params1['HubbleParam'])) 
      self.warning("is different from")
      self.warning("self.hubbleparam            = %f"%(self.hubbleparam))
      sys.exit()


    for a in self.get_list_of_arrays():

      if a == "pos":
        self.pos = self.pos * UnitLengthRatio

      elif a == "vel":
        self.vel = self.vel * UnitVelocityRatio
        
      elif a == "mass":
        self.mass = self.mass * UnitMassRatio
        
      elif a == "u":
        self.u = self.u* UnitEnergySpecRatio
         
      elif a == "rho":
        self.rho = self.rho * UnitDensityRatio

      elif a == "rsp":
        self.rsp = self.rsp * UnitLengthRatio

      elif a == "tpe":
        pass

      elif a == "num":
        pass
        
      elif a == "minit":
        self.minit = self.minit * UnitMassRatio    

      elif a == "tstar":
        tpe = 1
        idx = np.compress(self.tpe==tpe,np.arange(self.nbody))    
        nbs = self.select(tpe)
        ct =  nbs.CosmicTime(units=local_units_2.UnitTime)   
        np.put(self.tstar,idx,ct) 
            
      elif  a== "thtsnii":
        tpe = 0
        idx = np.compress(self.tpe==tpe,np.arange(self.nbody))    
        nbg = self.select(tpe)
        ct =  nbg.CosmicTime(units=local_units_2.UnitTime,age=nbg.thtsnii)   
        np.put(self.thtsnii,idx,ct) 
      
      elif  a== "thtsnia":
        tpe = 0
        idx = np.compress(self.tpe==tpe,np.arange(self.nbody))    
        nbg = self.select(tpe)
        ct =  nbg.CosmicTime(units=local_units_2.UnitTime,age=nbg.thtsnia)   
        np.put(self.thtsnia,idx,ct) 


      else:
        self.message("skipping %s"%a)


    if 'HubbleParam' in unit_params2:
      self.hubbleparam = unit_params2['HubbleParam']  
      

    self.UnitLength_in_cm         = local_units_2.get_UnitLength_in_cm()
    self.UnitMass_in_g            = local_units_2.get_UnitMass_in_g()
    self.Unit_time_in_cgs         = local_units_2.get_UnitTime_in_s()
    self.UnitVelocity_in_cm_per_s = local_units_2.get_UnitVelocity_in_cm_per_s()
    
    self.localsystem_of_units     = local_units_2
  




  def TimeStepLevel(self):
    """
    return the timestep level in log2
    """

    return (np.log10(self.opt1)/np.log10(2)).astype(int)



  def dLdt(self):
    from pNbody import cooling

    if self.metals is None:
      FeH = np.zeros(self.nbody).astype(np.float32)
    else:
      FeH = self.metals[:,self.ChimieElements.index('Fe')]

    l = cooling.get_lambda_from_Density_EnergyInt_FeH(self.rho,self.u,FeH)
    dLdt = self.mass * l/self.rho

    return dLdt.astype(np.float32)


  def GetVirialRadius(self,X=200,Rmin=0.5,Rmax=200.,imax=20,center=None,inCodeUnits=True):
    """
    Compute the virial radius and virial mass and return them.
    The virial radius is defined to be the radius of a sphere with a mean density
    equal to X times the mean matter density of the Universe.
    
    X : parameters that defines the virial radius (default=200)
    Rmin : minimum radius for the bisection algorithm
    Rmax : maximial radius for the bisection algorithm
    imax : maximal iterations to improve Rmin and Rmax
    center : 3D array: center for the virial radius determination
    inCodeUnits : if True, return the virial radius and virial mass in code units
    if False, in proper units (a and h corrected).

    if X=='BN'

      use the Bryan Norman 1998 convention, where
      the overdensity X is redshift dependant:

       x=Omega_m_z(z,om,ol)-1
       X = 18*np.pi**2 +82*x-39*x
    
    """

    from scipy.optimize import bisect as bisection

    # get local units
    system_of_units = self.localsystem_of_units


    if hasattr(self,"hubbleparam"):
      HubbleParam = self.hubbleparam
    else:
      raise Exception("self.hubbleparam is not defined.")

    if hasattr(self,"omega0"):
      Omega0 = self.omega0
    else:
      raise Exception("self.omega0 is not defined.")

    if hasattr(self,"omegalambda"):
      OmegaLambda = self.omegalambda
    else:
      raise Exception("self.omegalambda is not defined.")       
 
    # compute the critical density
    G=ctes.GRAVITY.into(system_of_units)
    H0 = ctes.HUBBLE.into(system_of_units)*self.hubbleparam

    self.message("G=%g H0=%g"%(G,H0))
    
    # get the scale factor
    atime = self.ScaleFactor()
    
    # compute H(a) : in code units, corrected from h
    Ha = H0 * (Omega0 / (atime*atime*atime) + (1 - Omega0 - OmegaLambda) / (atime*atime) + OmegaLambda)


    if X=="BN":
      z = self.Redshift()
      E2 = Omega0 * (1 + z)**3 + OmegaLambda
      Om = Omega0*(1+z)**3 / E2
      x  = Om-1
      X  = 18*np.pi**2 +82*x-39*x


    # compute the density in code units (no h,a dependency)
    rhoc = pow(Ha,2)*3/(8*np.pi*G)  # density in proper unit (not comobile)
    rhoX = float(rhoc*X*Omega0)
    
    self.message("rhoX =%g     (code units (a,h corrected), X=%g)"%(rhoX,X))


    ############################
    # find rX using bisection 
    ############################

    # convert to physical units
    rs = self.Rxyz(center=center) 
    ms = self.Mass()
    
    def getRes(r):
      c = rs < r
      M = sum(np.compress(c,ms))
      V    = 4/3.*np.pi*r**3  # r is scaled w.r.t. rs so no h,a dependency
      self.message("r=%g M/V=%g rhoX=%g"%(r,M/V,rhoX))
      return M/V - rhoX
    
    
    def TestRminRmax(rmin,rmax):
      rhoX_Rmin = getRes(Rmin) + rhoX
      rhoX_Rmax = getRes(Rmax) + rhoX 
      
      txt =   "Rmin = %7.3f"%Rmin + " Rmax = %7.3f"%Rmax + " rhoX_Rmin = %8.6e"%rhoX_Rmin + " rhoX_Rmax = %8.6e"%rhoX_Rmax + " rhoX = %8.6e"%rhoX
      self.message(txt)  
      
      if rhoX_Rmin==0:                            # Rmin is too small, no particles found
        return 1
      if rhoX_Rmin > rhoX and rhoX_Rmax < rhoX:   # Rmin and Rmax are fine
        return 0
      else:
        return -1
    
    
    # setup an adequate Rmin and Rmax
    for i in range(imax+1):
      res = TestRminRmax(Rmin,Rmax)
      if   res==0:  # Rmin and Rmax are fine
        break
      elif res==-1:
        Rmax = Rmin
        Rmin = Rmin/2.
      elif res==+1:
        #Rmin = Rmax/2
        Rmin = Rmin + Rmin*0.25
      
    if i==imax:
      rhoX_Rmin = getRes(Rmin) + rhoX
      rhoX_Rmax = getRes(Rmax) + rhoX 
      self.warning("failed to find adequate Rmin and Rmax after %d itterations."%i)
      self.warning("Rmin      = %g"%Rmin)
      self.warning("Rmax      = %g"%Rmax)
      self.warning("rhoX(Rmin)= %g"%rhoX_Rmin)
      self.warning("rhoX(Rmax)= %g"%rhoX_Rmax)
      self.warning("rhoX      = %g"%rhoX)
      return 0,0
      
      

    rX = bisection(getRes, Rmin, Rmax, args = (), xtol = 0.001, maxiter = 400)
    self.message("rx : %g (code units, a, h corrected)"%(rX))

    

    c = rs < rX
    MX = sum(np.compress(c,ms))

    
    # reintroduce a and h
    fp = self.ConversionFactor(units=None,mode='pos')
    fm = self.ConversionFactor(units=None,mode='mass')
      
    rXc = rX/fp
    MXc = MX/fm
    
    
    # in code units
    self.message("")
    self.message("Virial radius : r%d = %g (code units)"%(X,rXc),color="b")
    self.message("Virial mass   : M%d = %g (code units)"%(X,MXc),color="b")    
    

    # in kpc and Msol, h and a corrected
    fp = self.UnitsConversionFactor("kpc",mode='pos')
    fm = self.UnitsConversionFactor("Msol",mode='mass')
    
    self.message("")
    self.message("Virial radius : r%d = %g [kpc  proper]"%(X,rX*fp),color="b")
    self.message("Virial mass   : M%d = %g [Msol proper]"%(X,MX*fm),color="b")

      
    if inCodeUnits:
      return rXc,MXc
    else:
      return rX,MX
    





  def GetVirialRadiusOld(self,X=200,Rmin=0.5,Rmax=100.,center=None,omega0=None,inCodeUnits=False):

    from scipy.optimize import bisect as bisection


    # define local units
    system_of_units = self.localsystem_of_units

    if omega0==None:
      omega0 = self.omega0


    G=ctes.GRAVITY.into(system_of_units)
    H = ctes.HUBBLE.into(system_of_units)
    HubbleParam = self.hubbleparam

    rhoc = pow(H,2)*3/(8*np.pi*G)
    rhoX = rhoc*X * omega0

    self.message("rhoX      (code units, dX=%g)"%X,rhoX)



    # output system of units (the mass units is the hydrogen mass)
    Unit_atom = ctes.PROTONMASS.into(units.cgs)*units.Unit_g
    Unit_atom.set_symbol('atom')
    out_units = units.UnitSystem('local',[units.Unit_cm,Unit_atom,units.Unit_s,units.Unit_K])

    funit = system_of_units.convertionFactorTo(out_units.UnitDensity)

    if self.isComovingIntegrationOn():
      atime = self.atime
    else:
      atime = 1.0

    self.message("rhoX =%g     (code units (a,h corrected), X=%g)"%(rhoX,X))

    self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(atime,HubbleParam))
    rhoXu = rhoX/HubbleParam**2 *funit
    self.message("rhoX      (atom/cm^3)",rhoXu)
    self.message("log10rhoX (atom/cm^3)",np.log10(rhoXu))

    ############################
    # find rX using bissectrice
    ############################

    #if center!=None:
    #  self.translate(-center)
    #self.histocenter()


    rs = self.rxyz(center=center)

    def getRes(r):

      nb_s = self.selectc(rs<r)
      M    = sum(nb_s.mass)
      V    = 4/3.*np.pi*r**3

      # move to physical units
      M = M/HubbleParam
      V = V*( atime/HubbleParam )**3
      
      return M/V - rhoX


    rX = bisection(getRes, Rmin, Rmax, args = (), xtol = 0.001, maxiter = 400)


    nb_s = self.selectc(self.rxyz(center=center)<rX)
    MX    = sum(nb_s.mass)
    V    = 4/3.*np.pi*rX**3


    out_units = units.UnitSystem('local',[units.Unit_kpc,units.Unit_Msol,units.Unit_s,units.Unit_K])
    fL = system_of_units.convertionFactorTo(out_units.UnitLength)
    fM = system_of_units.convertionFactorTo(out_units.UnitMass)

    self.message("")
    self.message("Virial radius : r%d = %g [kpc/h comobile]"%(X,rX*fL))
    self.message("Virial mass   : M%d = %g [Msol/h]"%(X,MX*fM))

    self.message("")
    self.message("Virial radius : r%d = %g [kpc]"%(X,rX*fL/HubbleParam*atime))
    self.message("Virial mass   : M%d = %g [Msol]"%(X,MX*fM/HubbleParam))


    if inCodeUnits:
      return rX,MX
    else:
      return rX*fL/HubbleParam*atime,MX*fM/HubbleParam




    
    
  def XLightRadius(self,X=0.5,rmin=0,rmax=None,center=None,omega0=None,units=None,tnow=None):
    """
    Return the virial radius in physical units
    """
     
    from scipy.optimize import bisect as bisection
    from pNbody import units as u
     
     
    self.L = self.Luminosity(tnow=tnow)
    Ltot = sum(self.L)
    rs       = self.rxyz(center=center)
    
    if rmin==None:
      rmin = min(rs)
    
    if rmax==None:  
      rmax = 1.1*max(rs)
  
    def getL(r):
      nb_s = self.selectc(rs<r)
      L    = sum(nb_s.L)
      return X - L/Ltot 

    Rt = bisection(getL, rmin, rmax, args = (), xtol = 0.001, maxiter = 400)

    # set factor unit
    funit=1.0
    if units is not None:

      if type(units) in [str, bytes]:
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)


    
    if self.isComovingIntegrationOn():
      self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
      Rt = Rt*funit/self.hubbleparam*self.atime    
    else:
      Rt = Rt*funit
    
    
    return Rt




    
  def MeanXLightRadius(self,angles=None,axiss=None,X=0.5,rmin=0.0,rmax=None,center=None,omega0=None,units=None,tnow=None,tend=None):
    """
    Return the virial radius in physical units
    """
     
    from scipy.optimize import bisect as bisection
    from pNbody import units as u
    import copy
    
    
    if self.nbody<=1:
      nb.warning("Warning : only %d particles !!!"%(self.nbody))
      return 0.0,0.0,0.0,0.0,0.0,0.0
    
    rmin_ini = rmin
    rmax_ini = rmax
    
    if angles is None or axiss is None:
      angles = [0]
      axiss  = ['y']    


    
    self.L = self.Luminosity(tnow=tend)
    Ltot = sum(self.L)

   
    RXs = np.zeros(len(angles))
    LXs = np.zeros(len(angles))
    LX_ends = np.zeros(len(angles))
   
   
    # loop over different line of sight
    for i in range(len(angles)):
    
      rmax = rmax_ini
      rmin = rmin_ini
      
      nbss = copy.deepcopy(self)
            
      angle = angles[i]
      axis  = axiss[i] 
    
      nbss.rotate(angle=angle,axis=axis)
   
      rs       = nbss.rxy()
        
      if rmin==None:    
        rmin = min(rs)  
                        
      if rmax==None:    
        rmax = 1.1*max(rs)      
                
  
      def getL(r):
        nb_s = nbss.selectc(rs<r)
        L    = np.sum(nb_s.L)
        return X - L/Ltot 
        
      RX = bisection(getL, rmin, rmax, args = (), xtol = 0.001, maxiter = 400)

      nb_s = nbss.selectc(rs<RX)
    
      RXs[i]      = RX
      LXs[i]      = sum(nb_s.L)
      LX_ends[i]  = sum(nb_s.Luminosity(tnow=tend))


    # set factor unit
    funit=1.0
    if units is not None:

      if type(units) in [str, bytes]:
        units = u.GetUnitsFromString(units)

      funit = self.localsystem_of_units.convertionFactorTo(units)
      self.message("... factor units = %g"%funit)


    
    if self.isComovingIntegrationOn():
      self.message("    converting to physical units (a=%5.3f h=%5.3f)"%(self.atime,self.hubbleparam))
      RXs = RXs*funit/self.hubbleparam*self.atime    
    else:
      RXs = RXs*funit


    return RXs.mean(),RXs.std(),LXs.mean(),LXs.std(),LX_ends.mean(),LX_ends.std()




  def CylindricalProfileAndMaxRadius(self,rmin=0.0,rmax=None,nr=64,unitLength='kpc',tend=None):
    """
    Return the profile and extention radius in physical units
    """
     
    from pNbody import libgrid
    from pNbody import units as u
    import copy
    
    
    if self.nbody<=5:
      nb.warning("Warning : only %d particles !!!"%(self.nbody))
      return 0,0,0,0,0



    # ensure comobile conversions
    nb = copy.deepcopy(self)
    nb.pos  = nb.Pos()
    nb.mass = nb.Mass()


    nb.L = self.Luminosity(tnow=tend)


    # grid division		       
    rc = 1
    f	  = lambda r:np.log(r/rc+1.)
    fm    = lambda r:rc*(np.exp(r)-1.)
    

    if rmax==None:  
      rmax = 1.1*max(nb.rxy())

    
    # 
    G = libgrid.Cylindrical_2drt_Grid(rmin=rmin,rmax=rmax,nr=nr,nt=1,g=f,gm=fm)
    
    x,t  = G.get_rt()
    y  = np.reshape(G.get_SurfaceValMap(nb,nb.LuminositySpec()),nr)          # in Lsol/(unitlength)

    # units conversion
    fx = nb.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitLength))
    x = x*fx

    c = (x>0)*(y>0)
    x = np.compress(c,x)
    y = np.compress(c,y)
    
    x = np.log10(x)
    y = np.log10(y)
    
    ##########################
    # profile fitting
    
    from scipy.optimize import leastsq
  
  
    def KingPlus(p,r):
      I0 = p[0]
      rc = p[1]
      a  = p[2]
      c  = p[3]
      return np.log10( I0/( 1+(10**r/rc)**2 )**a  + c)


    errfunc = lambda p, x, y: KingPlus(p, x) - y  

    # Now, fit
    p0 = [max(10**y), 1, 3 , min(10**y)] # Initial guess for the parameters
    p1, success = leastsq(errfunc, p0, args=(x,y))
    y1 = KingPlus(p1,x)
  
    
    p2 = copy.deepcopy(p1)
    p2[3] = 0  
    y2 = KingPlus(p2,x)
    
    e = np.fabs((y1-y2)/y1)
    c = ( e ) > 5e-3 
    xx = np.compress(c,x)
    
    if len(xx)>0:       
      Rmax = 10**np.min(xx)
    else:               # if there is no significant floor
      Rmax = np.max(x)   
    
    return x,y,y1,y2,Rmax








  def meanCylindricalProfileAndMaxRadius(self,rmin=0.0,rmax=None,nr=64,unitLength='kpc',tend=None,angles=None,axiss=None):
    """
    Return the mean profile and extention radius in physical units
    """
    
      
    from pNbody import libgrid
    from pNbody import units as u
    import copy
    
    
    if self.nbody<=5:
      nb.warning("Warning : only %d particles !!!"%(self.nbody))
      return 0,0,0,0,0,0

    if angles==None or axiss==None:
      angles = [0]
      axiss  = ['y']    


    # ensure comobile conversions
    nb = copy.deepcopy(self)
    nb.pos  = nb.Pos()
    nb.mass = nb.Mass()

    nb.L = self.Luminosity(tnow=tend)
    nb.l = self.LuminositySpec(tnow=tend)
    
    # grid division		       
    rc = 1
    f	  = lambda r:np.log(r/rc+1.)
    fm    = lambda r:rc*(np.exp(r)-1.)
    


    y1s = np.zeros(nr)        
    y2s = np.zeros(nr)
    ns  = np.zeros(nr)
    

    if rmax==None:  
        rmax = 1.1*max(nb.rxyz())    
    

    # loop over different line of sight
    for i in range(len(angles)):


      nbsr = copy.deepcopy(nb)
      
      angle = angles[i]
      axis  = axiss[i] 
    
      nbsr.rotate(angle=angle,axis=axis)

    
      # 
      G = libgrid.Cylindrical_2drt_Grid(rmin=rmin,rmax=rmax,nr=nr,nt=1,g=f,gm=fm)
    
      x,t  = G.get_rt()
      y  = np.reshape(G.get_SurfaceValMap(nbsr,nbsr.l),nr)          # in Lsol/(unitlength)

      # units conversion
      fx = nbsr.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitLength))
      x = x*fx
            
      y1s = y1s + y
      y2s = y2s + y*y 
      ns = ns   + np.where(y>0,1,0)  
          
    
    # remove odd values
    c = ns > 0
    y1s = np.compress(c,y1s)
    y2s = np.compress(c,y2s)
    ns  = np.compress(c,ns)
    x   = np.compress(c,x)
           
    # compute the mean
    y = y1s / ns
    # compute the std
    Ey = np.sqrt(  y2s/ns  - (y**2)  )
        
    
    ##########################
    # now fit
    c = (x>0)*(y>0)
    x = np.compress(c,x)
    y = np.compress(c,y)
    Ey = np.compress(c,Ey)
    
    Ep = np.log10(y+Ey)
    Em = np.log10(y-Ey)
    
    x = np.log10(x)
    y = np.log10(y)
    
    Eyp = Ep - y
    Eym = y  - Em
    

    ##########################
    # profile fitting

    from scipy.optimize import leastsq


    def KingPlus(p,r):
      I0 = p[0]
      rc = p[1]
      a  = p[2]
      c  = p[3]
      return np.log10( I0/( 1+(10**r/rc)**2 )**a  + c)


    errfunc = lambda p, x, y: KingPlus(p, x) - y  

    # Now, fit
    p0 = [max(10**y), 1, 3 , min(10**y)] # Initial guess for the parameters
    p1, success = leastsq(errfunc, p0, args=(x,y))
    y1 = KingPlus(p1,x)

    p2 = copy.deepcopy(p1)
    p2[3] = 0  
    y2 = KingPlus(p2,x)

    e = np.fabs((y1-y2)/y1)
    c = ( e ) > 5e-3 
    xx = np.compress(c,x)

    if len(xx)>0:       
      Rmax = 10**np.min(xx)
    else:               # if there is no significant floor
      Rmax = np.max(x)       
        

    return x,y,Eyp,Eym,y1,y2,Rmax



    
  def ModeFeH(self):
    """
    Return the FeH mode
    """
    
    from pNbody import libgrid
    

    x = self.Fe()
    
    # do the 1d histogram
    G = libgrid.Generic_1d_Grid(-4,0.5,40)
    #y = G.get_MassMap(x,nb.mass)/sum(nb.mass)		# mass weighted
    y = G.get_MassMap(x,np.ones(self.nbody))/self.nbody
    x = G.get_r()

    i = np.argmax(y)
    Fe = x[i]
    
    return Fe

  def ModeFeHFit(self):
    """
    Return the FeH mode computed with a fit of the MDF using the instantaneous mixing model 
    """
    
    #auxiliary function
    def AnalyticalMDF(fe,a,p):
	    """
	    Analytical model for the metallicity distribution function of a dwarf galaxy
	    (see 'Nucleosynthesis and chemical evolution of galaxies', Pagel 2009, eq (8.20))
	    fe, the metallicity values
	    a, the amplitude of the MDF
	    p, which describes the position of the peak
	    """
	    
	    return a*10**fe*np.exp(-10**fe/p)
    
    from scipy.optimize import curve_fit
    from pNbody import libgrid
    
    fe = self.Fe()

    # do the 1d histogram
    G = libgrid.Generic_1d_Grid(min(fe) - 2, max(fe) + 2, int(9*(4 + max(fe) - min(fe))))
    y = G.get_MassMap(fe, np.ones(self.nbody))/self.nbody
    #y = G.get_MassMap(x,self.mass)/sum(self.mass)		# mass weighted
    x = G.get_r()

    try:
        popt, pcov = curve_fit(AnalyticalMDF, x, y, method = 'dogbox', bounds = ([1e-10, 10**(min(fe) - 0.1)], [np.inf, 10**(max(fe) + 0.1)]))
        # fitted mode
        fe_fit = np.log10(popt[1])
        # error on the fitted parameter given by the covariance matrix
        error = np.sqrt(np.diag(pcov))[1]/(popt[1]*np.log(10))
        
    except RuntimeError: # if the fit failed
        nb.warning("Warning : The fit procedure failed, returning median of the metallicity instead")
        # return median and standard deviation
        fe_fit = np.median(fe)
        error = np.std(fe)
        
    return [fe_fit, error] # return mode and error

  def MeanVelocityDispersion(self,r,angles=None,axiss=None,units=None):
    """
    Return the mean velocity dispersion in a cylindrical region (in km/s)
    """
    import copy
        

    
    
    if angles is None or axiss is None:
      angles = [0]
      axiss  = ['y']    
          
    nb = self.selectc(self.Rxy(units="kpc")<r)


    if nb.nbody<=1:
      nb.warning("Warning : only %d particles !!!"%(self.nbody))
      return 0.0,0.0,0.0
    
    
    sigmas = np.zeros(len(angles))    
        
    # loop over different line of sight
    for i in range(len(angles)):
      
      nbss = copy.deepcopy(nb)
      
      angle = angles[i]
      axis  = axiss[i] 
          
      nbss.rotate(angle=angle,axis=axis)
    
      vz = nbss.Vel(units=units)[:,2]
      m  = nbss.mass	  
      vzm = sum(vz*m)/sum(m)
    
      sigmavz2 = sum(m*vz**2)/sum(m) - vzm**2
      sigmavz  = np.sqrt(sigmavz2) 
    
      sigmas[i] = sigmavz
    
    
    return sigmas,sigmas.mean(),sigmas.std()   
    
    
    
  def StarFormationvsTime(self,tmin=0,tmax=14,nt=500,unitsTime="Gyr",unitsMass="Msol"):
    """
    Return the star formation rate as a function of time
    """

    from pNbody import libgrid
    
    # do the 1d histogram
    G = libgrid.Generic_1d_Grid(tmin,tmax,nt)
    
    x = self.StellarFormationTime(units=unitsTime)   
    y = G.get_MassMap(x,self.Mass(units=unitsMass))	
    x = G.get_r()

    dt = (x[1:]-x[:-1])*1e9 # Gyrs to yrs
    dMdt = y[:-1] / dt 
    
    y = dMdt
    x = x[1:]

    return x,y


  def StellarMassvsTime(self,tmin=0,tmax=14,nt=500,unitsTime="Gyr",unitsMass="Msol"):
    """
    Return the stellar mass as a function of time
    """

    from pNbody import libgrid
    

    # do the 1d histogram
    G = libgrid.Generic_1d_Grid(tmin,tmax,nt)
    
    x = self.StellarFormationTime(units=unitsTime)   
    y = G.get_MassMap(x,self.Mass(units=unitsMass))	
    x = G.get_r()
    
    y = np.add.accumulate(y)
    
    return x,y



  def CircularVelocityvsRadius(self,rmin=0,rmax=10,nr=64,unitVelocity="km/s",unitLength="kpc"):
    """
    Return the circular velocity as a function of radius
    """

    from pNbody import libgrid
    from pNbody import ctes
    from pNbody import units as u
    import copy
    
    # ensure comobile conversions
    nb = copy.deepcopy(self)
    nb.pos  = nb.Pos()
    nb.mass = nb.Mass()

    # grid division		       
    rc = 1.0
    f	  = lambda r:np.log(r/rc+1.)
    fm    = lambda r:rc*(np.exp(r)-1.)
      
    Gcte = ctes.GRAVITY.into(self.localsystem_of_units)
    G = libgrid.Spherical_1d_Grid(rmin=rmin,rmax=rmax,nr=nr,g=f,gm=fm)
    
    x  = G.get_r()
    M  = G.get_MassMap(nb)
    M = np.add.accumulate(M)
   
    y = np.sqrt(Gcte * M/x)

    # comoving conversion
    #if nb.isComovingIntegrationOn():
    #  nb.message( "	 converting to physical units (a=%5.3f h=%5.3f)"%(nb.atime,nb.hubbleparam))
    #  x = x*nb.atime/nb.hubbleparam	      # length  conversion


    fx = nb.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitLength))
    fy = nb.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitVelocity))
   
    x = x*fx
    y = y*fy

    return x,y




  def LOSVelocityvsRadius(self,rmin=0,rmax=10,nr=64,unitVelocity="km/s",unitLength="kpc",angles=None,axiss=None):
    """
    Return the line of sight velocity as a function of radius
    """

    from pNbody import libgrid
    from pNbody import ctes
    from pNbody import units as u
    import copy


    if self.nbody<=1:
      nb.warning("Warning : only %d particles !!!"%(self.nbody))
      return 0.0,0.0,0.0


    if angles is None or axiss is None:
      angles = [0]
      axiss  = ['y']    


    # ensure comobile conversions
    nb = copy.deepcopy(self)
    nb.pos  = nb.Pos()
    nb.vel  = nb.Vel()
    nb.mass = nb.Mass()

    # grid division		       
    rc = 1.0
    f	  = lambda r:np.log(r/rc+1.)
    fm    = lambda r:rc*(np.exp(r)-1.)


    G = libgrid.Cylindrical_2drt_Grid(rmin=rmin,rmax=rmax,nr=nr,nt=1,g=f,gm=fm)

    x,t  = G.get_rt()
    
    y1s = np.zeros(nr)    
    y2s = np.zeros(nr)
    ns  = np.zeros(nr)

    # loop over different line of sight
    for i in range(len(angles)):


      nbsr = copy.deepcopy(nb)
      
      angle = angles[i]
      axis  = axiss[i] 
    
      nbsr.rotate(angle=angle,axis=axis)
    
    
      y  = G.get_SigmaValMap(nbsr,nbsr.Vz())   
      y = np.sum(y,axis=1)  	  

      #x,y = pt.CleanVectorsForLogX(x,y)
      #x,y = pt.CleanVectorsForLogY(x,y)
       
      y1s = y1s + y
      y2s = y2s + y*y 
      ns = ns   + np.where(y>0,1,0)
       
    
    # remove odd values
    c = ns > 0
    y1s = np.compress(c,y1s)
    y2s = np.compress(c,y2s)
    ns  = np.compress(c,ns)
    x   = np.compress(c,x)
           
    # compute the mean
    ym = y1s / ns
    # compute the std
    Ey = np.sqrt(  y2s/ns  - (ym**2)  )
        
        
    fx = nb.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitLength))
    fy = nb.localsystem_of_units.convertionFactorTo(u.GetUnitsFromString(unitVelocity))
   
    x = x*fx
    ym = ym*fy
    Ey = Ey*fy
    
        
    return x,ym,Ey



  def FevsLuminosityEvolution(self,tend=None,units=None):
    """
    For different time, compute the final luminosity and metallicity
    """

    from pNbody import libgrid
    
    self.Ages = self.StellarAge(units=units)   
    self.L = self.Luminosity(tnow=tend)

    dt = 0.25 # gyr
    ts = np.arange(0,14+dt,dt)
    
    
    Ages = []
    Lvs  = []
    FeHs = []
    FeHms = []
    
    
    
    for i in range(len(ts)-1):
      t1 = ts[i]
      t2 = ts[i+1]
    
      t = 0.5*(t1+t2)
       
       
      ##############################
      # select for Luminosity
      ##############################
      
      c = (self.Ages>=t) #* (Ages<=tmax)
      nbs = self.selectc(c)
    
      # compute the luminosity
      #nbs.L = nbs.Luminosity(tnow=1.0)
      L = np.sum(nbs.L)
      
            
      Ages.append(t)
      Lvs.append( L )
      
      ##############################
      # select for Metallicity
      ##############################
      
      c = (self.Ages>=t) * (self.Fe()>-20)

      nbs = self.selectc(c)
  
  
      if nbs.nbody > 0:

      	# compute the mode
      	x = nbs.Fe()
	    
      	# do the 1d histogram
      	G = libgrid.Generic_1d_Grid(-4,0.5,40)
      	#y = G.get_MassMap(x,nbs.mass)/sum(nbs.mass)	    # mass weighted
      	y = G.get_MassMap(x,np.ones(nbs.nbody))/nbs.nbody
      	x = G.get_r()

      	Fe_mode = x[np.argmax(y)]
      	Fe_mean = nbs.Fe().mean()

      else:
        Fe_mode = -20
        Fe_mean = -20
      
      FeHs.append(Fe_mode)
      FeHms.append(Fe_mean)

   
    Ages  = np.array(Ages)
    Lvs   = np.array(Lvs)
    FeHs  = np.array(FeHs)
    FeHms = np.array(FeHms)
    
    
    return Ages,Lvs,FeHs,FeHms







  def CylindricalHalfMassFromPlummer(self,nlos=30,npb1=10,npb2=30,rmode='uniform',plot=False):
    """
    Compute the half mass or light from a model
    """
    import copy
    from pNbody import libgrid
    from scipy.optimize import leastsq
    
    xs = np.zeros(0)
    ys = np.zeros(0)
    
    if nlos>1:      
      los = getLOS(nlos,seed=0)
    else:
      los = np.array([0,0,1])
      
    for j in range(len(los)):
                      
      # copy the model
      nbc = copy.deepcopy(self)
    
      # rotate
      if nlos > 1:
        nbc.align(axis=los[j])
        
      # compute the radius
      r0 = nbc.Rxy()
    
      # define the grid
      G = libgrid.CylindricalIrregular_1dr_Grid(r0,npb1,rmode=rmode)
      x = G.get_R()
      y = G.get_SurfaceDensity(nbc.Mass())
            
      xs     = np.concatenate((xs,x))
      ys     = np.concatenate((ys,y))          
    
    
    if nlos > 1:
      G = libgrid.CylindricalIrregular_1dr_Grid(xs,npb2)
      x = G.get_R()
      mean,std = G.get_MeanAndStd(ys)
      y = mean
  
    ##########################
    # fit a Plummer
    
    def Plummer2DSdens(p,r):
      h  = p[0]
      I0 = p[1]
      return  I0* h**2/(h**2 + r**2)**2
      
    errfunc = lambda p, x, y: Plummer2DSdens(p, x) - y  

    # Now, fit
    p0 = [0.1*max(x), y[0]] # Initial guess for the parameters
    p1, success = leastsq(errfunc, p0, args=(x,y))
    yf = Plummer2DSdens(p1,x)    
    R12 = p1[0]
       
    if plot:   
      from matplotlib import pyplot as pt
      pt.plot(x,y)
      pt.plot(x,yf)
      pt.loglog()
      pt.show()

    return R12






  def CylindricalHalfMassFromIntegratedMass(self,nlos=30,npb1=10,npb2=30,rmode='uniform',plot=False,accurate=False,units="kpc"):
    """
    Compute the half mass or light from a model

    nlos : the number of line of sight over which we average
    npb1 : the number of bins to compute the profile

    return 
       R12   the half light radius
       R12e  the error (std) on the half light radius

    """
    import copy
    from pNbody import libgrid
    from scipy.optimize import leastsq
    
    xs = np.zeros(0)
    ys = np.zeros(0)
    Rs = np.zeros(0)
    
    if nlos>1:      
      los = getLOS(nlos,seed=0)
    else:
      los = [np.array([0,0,1])]
      
    for j in range(len(los)):
                            
      # copy the model
      nbc = copy.deepcopy(self)
    
      # rotate
      if nlos > 1:
        nbc.align(axis=los[j])
        
      # compute the radius
      r0 = nbc.Rxy(units=units)
      
      # define the grid
      G = libgrid.CylindricalIrregular_1dr_Grid(r0,npb1,rmode=rmode)
      x = G.get_R()      
      y = G.get_IntegratedSum(nbc.Mass())
      
      xs     = np.concatenate((xs,x))
      ys     = np.concatenate((ys,y))

      # compute r12 with this los
      # used to get std
      y = y/y[-1]
      y = np.fabs(0.5-y)
      idx = np.argmin(y)
      R12 = x[idx]
      Rs = np.concatenate((Rs,[R12]))
    
    
    if nlos > 1:
      G = libgrid.CylindricalIrregular_1dr_Grid(xs,npb2)
      x = G.get_R()
      mean,std = G.get_MeanAndStd(ys)
      y = mean
      
  
  
    # normalize
    y = y/y[-1]
    y = np.fabs(0.5-y)
    
    idx = np.argmin(y)
    
    R12  = x[idx]

    if len(Rs)==0:
      R12e = 0
    else:  
      R12e = Rs.std()
    
    if accurate:
      # improve by computing interpolating a quadratic
      xq = np.array([x[idx-1],x[idx],x[idx+1]])
      yq = np.array([y[idx-1],y[idx],y[idx+1]])

      def Quadratic(p,x):
        a = p[0]
        b = p[1]
        c = p[2]
        return  a*x**2 + b*x + c
      
      errfunc = lambda p, xq, yq: Quadratic(p, xq) - yq  

      # Now, fit
      p0 = [1,1,0] # Initial guess for the parameters
      p1, success = leastsq(errfunc, p0, args=(xq,yq))
      a = p1[0]
      b = p1[1]
    
      R12 = -b/(2*a)
    
      if plot:  
        xqf = np.linspace(min(xq),max(xq),1000)
        yqf = Quadratic(p1,xqf)    

        pt.scatter(xq,yq)
        pt.plot(xqf,yqf)
        pt.show()  


    if plot:   
      from matplotlib import pyplot as pt
      pt.plot(x,y)
      pt.loglog()
      pt.show()

    return R12,R12e



  def CylindricalHalfMass(self,Rmax=10,nlos=30,nr=64,plot=False,units="kpc",npb2=30):
    """
    Compute the half mass or light from a model

    nlos : the number of line of sight over which we average
    nr   : the number of bins to compute the profile

    return 
       R12   the half light radius
       R12e  the error (std) on the half light radius

    """
    import copy
    from pNbody import libgrid

    # grid division
    rc = 1
    def f(r): return np.log(r / rc + 1.)
    def fm(r): return rc * (np.exp(r) - 1.)
    
    if nlos>1: 
      xs = np.zeros((nlos,nr))
      ys = np.zeros((nlos,nr))
      Rs = np.zeros(nlos)
    else:
      xs = np.zeros(0)
      ys = np.zeros(0)
      Rs = np.zeros(0)
    
    if nlos>1:      
      los = getLOS(nlos,seed=0)
    else:
      los = [np.array([0,0,1])]
      
    for j in range(len(los)):
                            
      # copy the model
      nbc     = copy.deepcopy(self)
      nbc.pos = nbc.Pos(units=units)

      # rotate
      if nlos > 1:
        nbc.align(axis=los[j])
              
      
      # define the grid
      G = libgrid.Cylindrical_2drt_Grid(rmin=0, rmax=Rmax, nr=nr, nt=1, g=f, gm=fm)
      x, t = G.get_rt()
      y = G.get_MassMap(nbc)
      y = np.add.accumulate(y)
      y = y.ravel()

      if plot:
        from matplotlib import pyplot as pt
        pt.plot(x,y/y[-1])
                  
      xs[j]     = x
      ys[j]     = y


      # compute r12 with this los
      # used to get std
      y = y/y[-1]
      y = np.fabs(0.5-y)
      idx = np.argmin(y)
      R12 = x[idx]
      Rs[j] = R12

    if plot:
      pt.show() 

    if nlos > 1:
      y = ys.mean(axis=0)
      ystd = ys.std(axis=0)
      x = xs[0]

    if plot:   
      from matplotlib import pyplot as pt
      pt.plot(x,y/y[-1])
      pt.show()

      
    # normalize
    y = y/y[-1]
    y = np.fabs(0.5-y)
    
    idx = np.argmin(y)
    R12  = x[idx]

    if len(Rs)==0:
      R12e = 0
    else:  
      R12e = Rs.std()
    

    return R12,R12e


  def CylindricalEllipticity(self,nlos=30):
    """
    Compute the ellipticty of a model

    nlos : the number of line of sight over which we average

    return 
       e   the ellipticity
       ee  the error (std) on the ellipticity

    """
    import copy
    
    if nlos>1: 
      es = np.zeros(nlos)
    else:
      es = np.zeros(0)
    
    if nlos>1:      
      los = getLOS(nlos,seed=0)
    else:
      los = [np.array([0,0,1])]
      
    for j in range(len(los)):
                            
      # copy the model
      nbc     = copy.deepcopy(self)

      # rotate
      if nlos > 1:
        nbc.align(axis=los[j])
                  
      es[j]     = nbc.ellipticity_2D()


    if nlos > 1:
      e = es.mean(axis=0)
      estd = es.std(axis=0)


    return e,estd
  

  def CylindricalLOSVelocityDispertion(self,Rmax=-1,nlos=32,units="km/s"):
    """
    Compute the los velocity dispersion.

    Rmax : the 2D radius in which the velocity dispersion will be computed, in kpc
    nlos : the number of line of sight over which we average
    units: the output units ("km/s")

    return 
         Sigma  : the velocity dispersion in a given radius
         Sigmae : 

    """
    import copy
    from pNbody import libgrid
    
    sigmas = np.zeros(0)
    
    if nlos>1:      
      los = getLOS(nlos,seed=0)
    else:
      los = [np.array([0,0,1])]
      
    for j in range(len(los)):
                            
      # copy the model
      nbc = copy.deepcopy(self)

      if Rmax >0 -1:
        nbc = nbc.selectc(nbc.Rxy(units="kpc") < Rmax)
    
      # rotate
      if nlos > 1:
        nbc.align(axis=los[j])

      # line of sight velocities  
      vlos = nbc.Vel(units=units)[:,0]

      # velocity dispersion 
      sigma = vlos.std()

      # keep
      sigmas = np.concatenate((sigmas,[sigma]))
    
    sigma_mean = sigmas.mean()
    sigma_std  = sigmas.std()

    return sigma_mean, sigma_std
      


##########################################
#
# Abundances
#
##########################################



  def XH(self):
    """
    return hydrogen mass fraction
    """
    if not self.has_array('XHI'):
      raise Exception("self.XHI is not defined.")
    if not self.has_array('XHII'):
      raise Exception("self.XHII is not defined.")      
      
    return self.XHI + self.XHII
      

  def XHe(self):
    """
    return helium mass fraction
    """    
    if not self.has_array('XHeI'):
      raise Exception("self.XHeI is not defined.")
    if not self.has_array('XHeII'):
      raise Exception("self.XHeII is not defined.")
    if not self.has_array('XHeIII'):
      raise Exception("self.XHeIII is not defined.")
      
    return self.XHeI + self.XHeII + self.XHeIII
      

  def XH2(self):
    """
    return H2 mass fraction
    """    
    if not self.has_array('XH2I'):
      raise Exception("self.XH2I is not defined.")
    if not self.has_array('XH2II'):
      raise Exception("self.XH2II is not defined.")    
    
    return self.XH2I + self.XH2II





  def MH(self):
    return self.XH()  * self.mass

  def MHe(self):
    return self.XHe() * self.mass

  def MH2(self):
    return self.XH2() * self.mass


