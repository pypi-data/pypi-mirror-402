###########################################################################################
#  package:   Mockimgs
#  file:      spectra.py
#  brief:     filter class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import sys
import os
import numpy as np

from astropy import units as u
from astropy import constants as c
from scipy import integrate

# absolute magnitude factor 4*np.pi*((10*u.pc.to(u.cm))**2)  = 1.1964951828635063e+40 cm2

class Spectra():
  '''
  Define a spectra class.
  A spectra is characterised by a quantity (luminosity or transmission) given as a function
  of the wavelength (by default in angstrom)
  '''

  def __init__(self):  
    pass
    
  
  def resample(self,wavelength=None,lmin=1e1,lmax=1e7,n=1000000,units=u.angstrom):
    """
    resample data over a different wavelength range
    """
    
    if wavelength is None:
      logmin = np.log10(lmin)
      logmax = np.log10(lmax)
      wavelength = np.logspace(logmin,logmax,n)
    
    # interpolate data
    if type(self.data) is np.ndarray:
      data = np.interp(wavelength,self.wavelength.value,self.data)
      self.data       = data
    else:
      data = np.interp(wavelength,self.wavelength.value,self.data.value)
      self.data       = data*  self.data.unit
    
    self.wavelength = wavelength*units
    
    
    
    
  def get_wavelength(self,units=u.angstrom):
    """
    get the wavelength
    """
    return self.wavelength.to(units)
  
  
  def get_data(self,units=u.erg/u.s/u.angstrom):
    """
    get the data
    """
    if units is None:
      return self.data
    else:  
      return self.data.to(units)    
  
  def get_luminosity(self):
    """
    compute the luminosity, i.e., the integral under the data curve
    """
    from scipy import integrate
    I = integrate.simpson(self.data, self.wavelength)  
    return I
  

  
class SED(Spectra):
  '''
  Define a Spectral Energy Distribution class.
  The class is inherited from the Spectra class
  '''  
  
  def __init__(self,sed,wavelength):  
    
    if type(sed)   is np.ndarray:
      self.data        = sed * u.erg/u.s/u.angstrom
    elif type(sed) is u.quantity.Quantity:
      self.data        = sed
    else:
      raise(ValueError)
    
    if type(wavelength)   is np.ndarray:
      self.wavelength        = wavelength * u.angstrom
    elif type(wavelength) is u.quantity.Quantity:
      self.wavelength        = wavelength
    else:
      raise(ValueError)
  
  def mean_ST_flux(self,f):
    """
    compute the mean flux using the Willmer 2018 prescription
    f is a 
    """

    if not np.all(self.wavelength==f.wavelength):
      raise ValueError('self.wavelength must be identical to f.wavelength')
     
    F = self.absolute_flux
    R = f.data
    l = self.wavelength
  
    I1 = integrate.simpson(F*R*l,l)
    I2 = integrate.simpson(  R*l,l)
  
    flm = I1/I2 * u.erg/u.s/u.cm**2/u.AA
    
    return flm
    
  def mean_AB_flux(self,f):
    """
    compute the mean flux using the Willmer 2018 prescription
    f is the response 
    """

    if not np.all(self.wavelength==f.wavelength):
      raise ValueError('self.wavelength must be identical to f.wavelength')
     
    F = self.absolute_flux
    R = f.data
    l = self.wavelength
    
    F  = F.to(u.erg/(u.s*u.cm**2*u.cm)).value     # to erg/(s*cm**2*cm)
    l  = l.to(u.cm).value                         # to cm
    cc = c.c.to(u.cm/u.s).value                   # to cm/s

    I1 = integrate.simpson(F*R*l,l)
    I2 = integrate.simpson(  R*cc/l,l)  
    flm = I1/I2  * u.erg/u.s/u.cm**2/u.Hz        # give new appropriate units    
    
    return flm    
    
    
    
  
  def STMagnitude(self,f):
    """
    compute ST magnitude
    f is the filter "SED"
    See Bessell and Murphy 2012 for the origin of 21.10
    """

    # compute the mean flux
    flm = self.mean_ST_flux(f)

    # prevent 0 flux
    flm = np.where(flm==0,1e-50*flm.unit,flm)
    
    # compute the AB magnitude
    mag = -2.5* np.log10(flm.value) - 21.10
      
    return mag
    
  def ABMagnitude(self,f):
    """
    convert the flux in [u.erg/u.s/u.cm**2/u.AA]
    in AB magnitude using the filter "f"
    """

    # compute the mean flux (integral of f with the filter response)
    flm = self.mean_AB_flux(f)
    
    # prevent 0 flux
    flm = np.where(flm==0,1e-50*flm.unit,flm)

    # compute the AB magnitude
    mag = -2.5* np.log10(flm.value) - 48.6
      
    return mag

  def BolometricLuminosity(self):
    """
    from the intrinsic luminosity [erg/s/angstrom]
    compute the bolometric Luminosity [erg/s]
    """

    l = self.get_wavelength()     # in Angstrom
    f = self.data                 # in erg /(s Angstrom)
    
    funit = (1*u.erg/u.s/u.Angstrom).cgs.unit
    lunit = (1*u.Angstrom).cgs.unit
    
    if f.cgs.unit != funit:
      raise ValueError('f must be in units of %s'%funit)
    if l.cgs.unit != lunit:
      raise ValueError('l must be in units of %s'%lunit)
      
    I = integrate.simpson(f,l)    # erg/s
    I = I*u.erg/u.s    
    
    return I
    
    
  def Luminosity(self,f):
    """
    from the intrinsic luminosity [erg/s/angstrom]
    compute the luminosity [erg/s] in a given filter f
    """
    SED = self.multiply_with_filter(f)
    I = SED.BolometricLuminosity()
    return I


  def toAbsoluteFlux(self):
    """
    copy the current intensity stored in the .data variable to the
    .absolute_flux variable
    u.erg/u.s/u.cm**2/u.AA
    """
    self.absolute_flux = self.data
            
  
  
  def computeAbsoluteFlux(self):
    """
    convert intrinsic luminosity [erg/s/angstrom] 
    into absolute flux [u.erg/u.s/u.cm**2/u.AA],
    i.e. move the source at 10pc.
    """
    
    # compute the flux at a distance of 10 pc
    d = 10*u.pc
    d = d.to(u.cm)

    self.absolute_flux = self.data/(4*np.pi * d**2)
    self.absolute_flux.to(u.erg/u.s/u.cm**2/u.AA)
    
    
  
  
  def multiply_with_filter(self,f):
    """
    multiply the SED with a given filter
    both must have the same wavelength range
    """
    
    if not np.all(self.wavelength==f.wavelength):
      raise ValueError('self.wavelength must be identical to f.wavelength')
    
    data = self.data * f.data
    
    return SED(data,self.wavelength)
    
    

  def get_wavelength(self,units=u.angstrom):
    """
    get the wavelength
    """
    return self.wavelength.to(units)
  
  def get_sed(self,units=u.erg/u.s/u.angstrom):
    """
    get the sed
    """
    return self.get_data(units=units)
    
    
    
    
