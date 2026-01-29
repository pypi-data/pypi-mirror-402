###########################################################################################
#  package:   Mockimgs
#  file:      lib.py
#  brief:     some useful routines
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u

from .. import message

def FluxToSurfaceBrightness(FluxMap,object_distance,ccd_pixel_area):
  """
  Convert a mass/luminosity/flux to a surface brightness map
  
  FluxMap         : the flux map (numpy.array)
  object_distance : distance to the object (astropy.units.quantity)
  ccd_pixel_area  : ccd pixel area (astropy.units.quantity)
  
  """
    
  # compute the absolute magnitude in each pixel (as before we ignore the zero point)
  c = FluxMap==0
  FluxMap = np.where(FluxMap==0,1e-40, FluxMap)        
  MagMap = np.where(c,0,-2.5*np.log10(FluxMap))
  
  
  # compute the apparent magnitude in each pixel
  # Mpc -> 10pc
  d = object_distance.to(10*u.pc).value
  magMap = MagMap + 5*np.log10(d)
  
  # compute the surface brightness in each pixel 
  SBMap = np.where(MagMap==0, 100, magMap + 2.5*np.log10(ccd_pixel_area.to(u.arcsec**2).value) )
  
  return SBMap
       


def FilterFluxMap(FluxMap,filter_opts={'mode':None},verbose=0):
  """
  Filter the flux map
  
  FluxMas      : the flux map (numpy.array)
  filter_opts  : filter options
  """

  
  if filter_opts['mode'] == "psf-convolution":
    """
    if a fits file is given as a psf, convolve with it
    """
    from astropy.io import fits
    from scipy import ndimage
    from astropy.convolution import convolve_fft
        
    psf_filename      = filter_opts["psf_filename"]
    image_pixel_scale = filter_opts["image_pixel_scale"]
    
    message.message("convolving with",verbose=verbose,verbosity=1,level=0,color='b')
    message.message("image_pixel_scale = %g"%image_pixel_scale,verbose=verbose,verbosity=1,level=0,color='b')    
    
    # open the psf fits file
    psf      = fits.open(psf_filename)
    psf_data = psf[0].data
    
    psf_header = psf[0].header
    
    if "PIXELSCL" in psf_header:
      psf_pixel_scale=psf_header["PIXELSCL"]
    else:
      message.message("PIXELSCL keywork is missing in %s"%opt.psf_filename,verbose=1,verbosity=0,level=0,color='r')
      message.message("STOP !",verbose=1,verbosity=0,level=0,color='r')
      exit()    
    
    # check if pixel scale agree
    scale_factor = psf_pixel_scale/image_pixel_scale
    message.message("scale_factor = %g"%scale_factor,verbose=verbose,verbosity=1,level=0,color='b')
          
    # new size of the psf
    psf_new_shape = (int(scale_factor*psf_data.shape[0]),int(scale_factor*psf_data.shape[1]))
    
    # rescale the pdf
    psf_data = ndimage.zoom(psf_data, scale_factor, output=None, order=3, mode='constant', cval=-1, prefilter=True)
    
    # do the convolution
    FluxMap = convolve_fft(FluxMap, psf_data, boundary='fill',fill_value=0.0, allow_huge=True, normalize_kernel=True)


  #if filter_opts is not None:
    # here, we should do something
    
    #if opt.convolve=="gaussian":   
    #  print("Convolving with a gaussian...")
    #  psf = opt.psf/opt.ccd_pixel_size[0]
    #  psf_map = gaussian_filter(L_map.shape[0],psf)
    #elif opt.convolve=="square":   
    #  print("Convolving with a square...")
    #  psf_map = square_filter(int(opt.psf))
    #        
    ## convolve
    #L_map = signal.convolve2d(L_map, psf_map, mode='same', boundary='fill', fillvalue=0)
  #  pass
  
  return FluxMap

