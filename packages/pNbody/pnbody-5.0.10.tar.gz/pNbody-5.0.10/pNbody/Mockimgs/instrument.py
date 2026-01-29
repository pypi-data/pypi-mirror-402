###########################################################################################
#  package:   Mockimgs
#  file:      instrument.py
#  brief:     instrument class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from astropy import units as u
import numpy as np
import pickle
import datetime
import os
import socket
import pNbody
from . import filters
from . import lib


class Instrument():
  '''
  Define the Instrument class.
  An instrument is composed of a telescope, a detector (ccd) and a filter.
  '''
  def __init__(self,name=None,telescope=None,ccd=None,ifu=None,mos=None,filter_type=None,obs_object=None,mapping_method=None):
    
    self.name              = name
    self.telescope         = telescope
    
    self.ccd               = ccd
    if ccd is not None:
      self.ccd.instrument  = self
      
    self.ifu               = ifu
    if ifu is not None:
      self.ifu.instrument  = self  

    self.mos               = mos
    if mos is not None:
      self.mos.instrument  = self  
    
    self.filter            = filter_type
    
    self.object            = obs_object
    if obs_object is not None:
      self.object.instrument = self
        
    # send the telescope focal to the CCD is the latter is defined
    if self.ccd is not None:
      if self.telescope is not None:
        if self.telescope.focal is not None:
          self.ccd.set_focal(self.telescope.focal)
    
    # ccd mapping method  : spline or gauss or gauss_old
    if mapping_method is None:
        self.mapping_method = "gauss"


  def info(self):
    """
    get info on the instrument
    """
    print("name               : %s"%self.name)
    print("fov                : [%s,%s]"%(self.fov()[0].to(u.degree),self.fov()[1].to(u.degree)))
    self.telescope.info()
    self.ccd.info()
    self.filter.info()
    if self.object is not None:
      self.object.info()
      

  def fov(self):
    """
    get the instrument (ccd) field of view
    """    
    return self.ccd.fov
  
  
  def change_fov(self,fov):
    """
    Use only a subset of the available fov
    
    fov : new field of view
    """
    
    # define the field of view
    self.ccd.change_fov(fov)
    
  def get_arcsec_to_pixel_factors(self):
    """
    return the factor to convert arcsec to pixels
    """
    return self.ccd.get_arcsec_to_pixel_factors()

  def getFocal(self):
    """
    return the telescope focal if defined
    """
    if self.telescope is not None:
      return self.telescope.get_focal()
    else:
      raise ValueError("no telsecope defined. Cannot get the telescope focal.")
      
  def getObject(self):
    """
    return the object
    """
    if self.object is not None:
      return self.object
    else:
      raise ValueError("no object defined.")    


  def add_object(self,obj):
    """
    add an object to observe
    """
    self.object = obj
    self.ccd.set_extension_in_spatial_length(self.object.distance)
    
  def set_object_for_exposure(self,getAgeMH=False):
    """
    Open the N-body model and eventually compute missing quantities. 
    Rotate according to a given los.
    Scale according to a given distance.
    """
    self.object.open(getAgeMH=getAgeMH)    
    self.object.set_for_exposure()
    
    
    
  def set_filter(self,filtername):
    """
    set the filter
    
    filtername : name of the filter, e.g. : "BastI_GAIA_G"
                 of filter object  , e.g. : filters.Filter("BastI_GAIA_G")
        
    """
    
    if type(filtername) is str:
      self.filter = filters.Filter(filtername)
    else:
      self.filter = filtername 

  def set_mapping_method(self,mapping_method):
    """
    Set the kernel used to map particles to the CCD.

    mapping_method: 'gauss_old', 'gauss', 'spline'
    """
    self.mapping_method = mapping_method
    return

  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters
    """
    params = {}
    
    if fmt=="fits":
      params["NAME"]             = (self.name,"Instrument name")    
    else:  
      params["name"]             = self.name    

    # add telescope
    params.update(self.telescope.get_parameters(fmt)) 
    
    # add filter
    params.update(self.filter.get_parameters(fmt)) 
    
    # add object
    params.update(self.object.get_parameters(fmt))    
    
    # add ccd
    params.update(self.ccd.get_parameters(fmt))
    
    return params


  def ComputeIDsMap(self):  
    """
    Compute a map containing the IDs of particles that fall into pixels.
    
    It return a 2D matrix containing a list of IDs of particles.
    """
    
    # get the nbody model
    nb = self.object

    # compute the map
    IDsMap = self.ccd.IDsMap(nb.pos,nb.num)

    return IDsMap
    

    
  
  def ComputeFluxMap(self,magFromField=None):  
    """
    Compute a luminosity of flux map.
    Here the nbody model is supposed
    to be in the right units
    
    It return a 2D matrix containing either a fluxes or masses or luminosities
    
    If magFromField is not none, the magnitude is not computed but taken form the
    nbody object with the field name magFromField.
    """
    
    # get the nbody model
    nb = self.object
    
    # set map bins
    binsx = np.linspace(self.ccd.xmin,self.ccd.xmax,self.ccd.nx())
    binsy = np.linspace(self.ccd.ymin,self.ccd.ymax,self.ccd.ny())
    
    # get the magnitude per stellar particle

    if magFromField is None:
      # compute the magnitude for the defined filter:
      M = self.filter.Magnitudes(nb.mass,nb.age,nb.mh)     
    else:
      # take the magnitude from the hdf5 file
      M = getattr(nb,magFromField)
      
                
              
    # convert to flux (ignore the zero point)
    F = 10**(-M/2.5)
      
    # store in the mass field
    nb.mass = F.astype(np.float32) 
    
    
    # store the total mass
    total_mass = nb.mass.sum()

    # create the map
    if self.mapping_method is "gauss_old":
      raise ValueError("The mapping method gauss_old is not longer supported. Please, use spline or gauss instead.")
    
    elif self.mapping_method is "spline":
      FluxMap = self.ccd.MapUsingSpline(nb.pos,nb.mass,nb.rsp)
    
    elif self.mapping_method is "gauss":
      FluxMap = self.ccd.MapUsingGauss(nb.pos,nb.mass,nb.rsp)

  
    
    # compute total flux 
    total_flux = np.sum(np.ravel(FluxMap))
    
    # compute difference
    flux_diff = np.fabs(total_flux-total_mass)/total_mass
    #print("Flux difference : %g %%"%(flux_diff*100))
    
      
    # make it global
    self.FluxMap = FluxMap
    
    return self.FluxMap
  

  def FilterFluxMap(self,filter_opts={'mode':None}):
    """
    Filter the flux map
  
    FluxMas      : the flux map (numpy.array)
    filter_opts  : filter options
    """
    

    if hasattr(filter_opts,'psf_filename'):
      if filter_opts.psf_filename is not None:
        # redefine filter_opts
        opts = {}
        opts["mode"]              = "psf-convolution"
        opts["psf_filename"]      = filter_opts.psf_filename
        opts["image_pixel_scale"] = self.ccd.pixel_fov[0].to(u.arcsec).value        
        self.FluxMap = lib.FilterFluxMap(self.FluxMap,opts)
      
    
    return self.FluxMap
    

  def SurfaceBrightnessMap(self):
    """
    Convert a mass/luminosity/flux to a surface brightness map
    """
    
    # compute the map
    self.SBMap = lib.FluxToSurfaceBrightness(self.FluxMap,self.object.distance,self.ccd.pixel_area)
    
    return self.SBMap
    

  def getFluxMap(self):
    """
    return the current flux map
    """
    return self.FluxMap    
    
    
  def getSurfaceBrightnessMap(self):
    """
    return the current surface brightness map
    """
    return self.SBMap  


  def saveFitsImage(self,image,filename,units=None,comments=None,compress=True):
    """
    save a fits image
    
    image       : name of the image
    filename    : output file name
    units       : pixel units (str)
    comments    : additional comments (list)
    
    """
    from astropy.io import fits
    import os

    hdu = fits.PrimaryHDU(image)
    
    # add pixel unit
    hdu.header["UNITS"]     = (units,"pixel units")
    
    # add date
    hdu.header["TIME"]      = (str(datetime.datetime.now()),"creation time")
    
    # add user
    try:
      hdu.header["USER"]      = (os.getlogin(),"creator name")
    except:
      if "USER" in os.environ:
        hdu.header["USER"]      = (os.environ['USER'],"creator name")
      else:
        hdu.header["USER"]      = ('unknown',"creator name")  

    # add hostname
    try:
      hdu.header["HOSTNAME"]  = (socket.gethostname(),"hostname")
    except:
      hdu.header["HOSTNAME"]  = ('unknown',"hostname")
        
    # add user
    try:
      hdu.header["GITTAG"]    = (pNbody.__version__,"pNbody git tag")
    except:
      hdu.header["GITTAG"]    = ("unknown","pNbody git tag")
            
  
    #add other info 
    params = self.get_parameters(fmt="fits")
    for key in params:
      hdu.header[key] = params[key]
  
    # add comments
    if comments is not None:
      for comment in comments:
        hdu.header["COMMENT"]   = comment
    
    
    if os.path.isfile(filename):
      os.remove(filename)
    
    hdu.writeto(filename)    
    
    if compress:
      import gzip
      import shutil
      
      with open(filename, 'rb') as f_in:
        with gzip.open("%s.gz"%filename, 'wb') as f_out:
          shutil.copyfileobj(f_in, f_out)
      
      os.remove(filename)



  def draw(self,ax,mode=None,unit=None):
    """
    draw using matplotlib
    """    
    if self.ccd is not None:
      self.ccd.draw(ax,mode,unit)
      
    if self.ifu is not None:  
      self.ifu.draw(ax,mode,unit)

    if self.mos is not None:  
      self.mos.draw(ax,mode,unit)
    
    if self.object is not None:
      self.object.draw(ax,mode,unit)
    







