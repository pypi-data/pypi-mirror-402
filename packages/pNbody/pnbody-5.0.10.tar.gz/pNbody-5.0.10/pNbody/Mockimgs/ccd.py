###########################################################################################
#  package:   Mockimgs
#  file:      ccd.py
#  brief:     ccd class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u
from  .. import mapping as mapping
from .detector import Detector
from .dzone import Dzone


class CCD(Detector):
  '''
  Define the CCD class.
  '''
  def __init__(self,name,shape=None,size=None,pixel_size=None,fov=None,focal=None):    
    
    #super().__init__(name)
        
    self.name       = name
    self.shape      = shape
    self.size       = size
    self.pixel_size = pixel_size
    self.fov        = fov
    self.focal      = focal
    
    self.xmin_kpc   = 1*u.kpc
    self.xmax_kpc   = 1*u.kpc
    self.ymin_kpc   = 1*u.kpc
    self.ymax_kpc   = 1*u.kpc
    
    self.units      = None  # pixel output units
  
    # initialize  
    self.init()
    
    

  def init(self):
    """
    Initialize all necessary quantities
    """

    # shape must be defined
    if self.shape is None:
      raise ValueError("The CCD shape must always be defined if ") 
    
    self.set_sizeOrpixel_size()

    if self.fov is not None:
      # compute the focal
      self.set_focal_from_fov()
      self.set_pixel_fov() # must be before the next line

    else:  
      # define a default focal length if needed 
      if self.focal is None:
        self.focal = 1000*u.mm
      
      # now that the focal is known, we can set the fov
      self.set_fov_from_focal()
      self.set_pixel_fov()
      
  
    # final stuffs
    self.set_pixel_area()
    self.set_extension()

    
    # define the sensible ccd zone (in case we want to draw it)
    self.defineSensibleZones()    



  
  
  def set_size(self):
    """
    set size from pixel_size and shape
    """
    self.size = [self.pixel_size[0]*self.shape[0],self.pixel_size[1]*self.shape[1]]

  def set_pixel_size(self):
    """
    set size from pixel_size and shape
    """
    self.pixel_size = [self.size[0]/self.shape[0],self.size[1]/self.shape[1]]

  def set_sizeOrpixel_size(self): 
    '''
    set pixel_size from size or
    set size from pixel_size
    '''
    if self.size is None and self.pixel_size is None:
     raise ValueError("The CCD size of pixel_size must be defined") 
    else:
      if self.size is not None:
        self.set_pixel_size()
      else:
          self.set_size()


  def set_focal(self,focal):
    """
    set the focal and ignore the the fov
    """
    self.focal = focal
    self.fov   = None
    
    self.init()
    
  def change_fov(self,fov):
    """
    change the field of view, by modifying the shape
    """    
    f = fov[0].to(u.deg).value/self.fov[0].to(u.deg).value
    
    # note that all quantities are propertly defined at this stage
    
    # scale the shape
    self.shape[0] = int(self.shape[0] * f)
    self.shape[1] = int(self.shape[1] * f)
    
    # compute the new size from the pixel_size
    self.set_size() 
    
    # kill the fov : it will be recomputed at init
    self.fov = None

    
    self.init()  
        
  
  def set_focal_from_fov(self):
    """
    set the focal from the field of view and size
    """

    if self.fov is None:
      raise ValueError("The fov must be defined.") 
    
    if self.size[0] != self.size[1]:
      raise ValueError("size[0] but be equal to size[1]")

    if self.fov[0] != self.fov[1]:
      raise ValueError("fov[0] but be equal to fov[1]")
      
  
    self.focal =   self.size[0]/np.tan(self.fov[0])



  def set_pixel_fov(self):
    """
    set the pixel field of view
    needs the focal to be defined
    """
    if self.focal is None:
      raise ValueError("The focal must be defined.")  
    self.pixel_fov  = [np.arctan(self.pixel_size[0]/self.focal),np.arctan(self.pixel_size[1]/self.focal)]
    
    
  def set_fov_from_focal(self):
    """
    set the field of view from the focal
    """
    if self.focal is None:
      raise ValueError("The focal must be defined.") 
    
    self.fov        = [np.arctan(self.size[0]      /self.focal),np.arctan(self.size[1]      /self.focal)]
      
      

  def set_pixel_area(self):
    """
    set the pixel area
    needs pixel_fov to be defined
    """
    self.pixel_area = self.pixel_fov[0]*self.pixel_fov[1]


  def set_extension(self):  
    """
    set the ccd extension in angle
    """
    self.xmin = -self.fov[0]/2.
    self.xmax = +self.fov[0]/2.
    self.ymin = -self.fov[1]/2.
    self.ymax = +self.fov[1]/2.   
    


  def set_extension_in_spatial_length(self,object_distance):
    """
    set the ccd extension in spatial length
    
    distance : distance to the observed object
    """ 
    self.xmin_kpc = object_distance*np.tan(self.xmin)
    self.xmax_kpc = object_distance*np.tan(self.xmax)
    self.ymin_kpc = object_distance*np.tan(self.ymin)
    self.ymax_kpc = object_distance*np.tan(self.ymax)
    


  
  def info(self):
    """
    gives info on the ccd
    """
    print("ccd name              : %s"%self.name)
    print("ccd shape             : [%d,%d]"%(self.shape[0],self.shape[1]))    
    print("ccd fov               : [%s,%s]"%(self.fov[0].to(u.degree),self.fov[1].to(u.degree)))
    print("ccd focal used (cm)   : %s"%(self.focal.to(u.cm)))
    print("ccd size              : [%s,%s]"%(self.size[0],self.size[1]))
    print("ccd pixel size        : %s %s"%(self.pixel_size[0],self.pixel_size[1]))
    print("ccd pixel fov(arcsec) : %s %s"%(self.pixel_fov[0].to(u.arcsec),self.pixel_fov[1].to(u.arcsec)))  
    print("ccd xmin xmax (deg)   : %s %s"%(self.xmin.to(u.deg),self.xmax.to(u.deg)))
    print("ccd ymin ymax (deg)   : %s %s"%(self.ymin.to(u.deg),self.ymax.to(u.deg)))
    print("ccd xmin xmax (kpc)   : %s %s"%(self.xmin_kpc.to(u.kpc),self.xmax_kpc.to(u.kpc)))
    print("ccd ymin ymax (kpc)   : %s %s"%(self.ymin_kpc.to(u.kpc),self.ymax_kpc.to(u.kpc)))  
  
  
  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters    
    """
    params = {}
    if fmt=="fits":
      params["CCDNAME"]            = (self.name,"CCD name")
    else:
      params["ccd_name"]           = self.name
                                  
    if fmt=="fits":                
      params["FOVX"]               = (self.fov[0].to(u.degree).value,"CCD field of view in deg.")
      params["FOVY"]               = (self.fov[1].to(u.degree).value,"CCD field of view in deg.")
    else:                          
      params["ccd_fov"]            = self.fov
                                  
    if fmt=="fits":                
      params["NX"]                 = (self.shape[0],"CCD number of pixels in x")
      params["NY"]                 = (self.shape[1],"CCD number of pixels in y")               
    else:                          
      params["ccd_shape"]          = self.shape
                                  
    if fmt=="fits":                
      params["PIXSIZEX"]           = (self.pixel_size[0].to(u.micron).value,"CCD pixel size in microns in x")
      params["PIXSIZEY"]           = (self.pixel_size[1].to(u.micron).value,"CCD pixel size in microns in y")
    else:                          
      params["ccd_pixel_size"]     = self.pixel_size
                                  
    if fmt=="fits":                
      params["PIXFOVX"]            = (self.pixel_fov[0].to(u.arcsec).value,"CCD pixel field of view x in arcsec")
      params["PIXFOVY"]            = (self.pixel_fov[1].to(u.arcsec).value,"CCD pixel field of view y in arcsec")
    else:                          
      params["ccd_pixel_fov"]      = self.pixel_fov
    
    if fmt=="fits":
      params["PIXAREA"]            = (self.pixel_area.to(u.arcsec**2).value,"CCD pixel area in arcsec^2")
    else:
      params["ccd_pixel_area"]     = self.pixel_area
        
    if fmt=="fits":
      params["XMIN"]               = (self.xmin.to(u.arcsec).value, "CCD xmin in arcsec")
      params["XMAX"]               = (self.xmax.to(u.arcsec).value, "CCD xmax in arcsec")
      params["YMIN"]               = (self.ymin.to(u.arcsec).value, "CCD ymin in arcsec")
      params["YMAX"]               = (self.ymax.to(u.arcsec).value, "CCD ymax in arcsec")
      params["XMINKPC"]            = (self.xmin_kpc.to(u.kpc).value,"CCD xmin in kpc")
      params["XMAXKPC"]            = (self.xmax_kpc.to(u.kpc).value,"CCD xmax in kpc")
      params["YMINKPC"]            = (self.ymin_kpc.to(u.kpc).value,"CCD ymin in kpc")
      params["YMAXKPC"]            = (self.ymax_kpc.to(u.kpc).value,"CCD ymax in kpc")
    else:
      params["ccd_xmin"]           = self.xmin
      params["ccd_xmax"]           = self.xmax
      params["ccd_ymin"]           = self.ymin
      params["ccd_ymax"]           = self.ymax      
      params["ccd_xmin_kpc"]       = self.xmin_kpc.to(u.kpc)
      params["ccd_xmax_kpc"]       = self.xmax_kpc.to(u.kpc)
      params["ccd_ymin_kpc"]       = self.ymin_kpc.to(u.kpc)
      params["ccd_ymax_kpc"]       = self.ymax_kpc.to(u.kpc)    
    
    return params
  
  def nx(self):
    """
    return the number of pixels along the x axis
    """
    return self.shape[0]

  def ny(self):
    """
    return the number of pixels along the y axis
    """
    return self.shape[1]  
    
  


  def get_arcsec_to_pixel_factors(self):
    """
    return the factor to convert arcsec to pixels
    """
    return(1/self.pixel_fov[0].to(u.arcsec).value,1/self.pixel_fov[1].to(u.arcsec).value)
    

  def IDsMap(self,pos,num):
    """
    create a map containing the IDs of particles falling into pixels
    coordinates = pos : in arsec
    num               : id of particles
    """
      
    # factor to pixels
    fx,fy = self.get_arcsec_to_pixel_factors()
    
    # to pixels:
    pos[:,0] = pos[:,0]*fx
    pos[:,1] = pos[:,1]*fy
    
    # convert to [0,1]
    pos[:,0] = pos[:,0]/self.nx()*2
    pos[:,1] = pos[:,1]/self.ny()*2
    pos[:,0] = (pos[:,0] + 1)/2.
    pos[:,1] = (pos[:,1] + 1)/2.
         
    # set all quantities to float32 
    pos  = pos.astype(np.float32)
    num  = num.astype(np.int64)

    Map = mapping.mkmap2dn_IDs(pos,num,(self.nx(),self.ny()))
    Map = np.rot90(Map)       
    
    return Map

  
  
  def MapUsingGauss(self,pos,amp,rsp):
    """
    create a map (using a gaussian kernel) from points with 
    coordinates = pos : in arsec
    amplitude   = amp
    size        = rsp
    """
      
    # factor to pixels
    fx,fy = self.get_arcsec_to_pixel_factors()
    
    # to pixels:
    pos[:,0] = pos[:,0]*fx
    pos[:,1] = pos[:,1]*fy
    rsp      = rsp*fx
    
    # convert to [0,1]
    pos[:,0] = pos[:,0]/self.nx()*2
    pos[:,1] = pos[:,1]/self.ny()*2
    pos[:,0] = (pos[:,0] + 1)/2.
    pos[:,1] = (pos[:,1] + 1)/2.
    
    rsp = np.clip(rsp, 0, 100)  # trim in pixels
     
    # set all quantities to float32 
    pos  = pos.astype(np.float32)
    rsp  = rsp.astype(np.float32)
    amp  = amp.astype(np.float32)
    tmp  = np.ones(amp.size).astype(np.float32)
    
    Map = mapping.mkmap2dnsph(pos,amp,tmp,rsp,(self.nx(),self.ny()))
    Map = np.rot90(Map)       
    
    return Map  




  def MapUsingSpline(self,pos,amp,rsp):
    """
    create a map (using a gaussian kernel) from points with 
    coordinates = pos : in arsec
    amplitude   = amp
    size        = rsp
    """
    
    # factor to pixels
    fx,fy = self.get_arcsec_to_pixel_factors()
    
    # convert to pixels
    pos[:,0] = pos[:,0]*fx
    pos[:,1] = pos[:,1]*fy
    rsp      = rsp*fx

    # shift towards the center of the ccd
    pos[:,0] = pos[:,0]+ self.nx()/2
    pos[:,1] = pos[:,1]+ self.ny()/2
    
    
    rsp = np.clip(rsp, 0, 100)  # trim in pixels
     
    # set all quantities to float32 
    pos  = pos.astype(np.float32)
    rsp  = rsp.astype(np.float32)
    amp  = amp.astype(np.float32)
    
    Map = mapping.mkmap2d_splcub(pos,amp,rsp,(self.nx(),self.ny()))
    Map = np.rot90(Map)       
    
    return Map      


  def defineSensibleZones(self):
    """
    set the sensible zone in size units
    
    self.sZone is a list of tupple
    """
    
    unit = self.size[0].unit
    
    xmin = -self.size[0].value/2.
    xmax = +self.size[0].value/2.
    ymin = -self.size[1].value/2.
    ymax = +self.size[1].value/2.  
    
    xs = np.array([xmin,xmax,xmax,xmin])*unit
    ys = np.array([ymin,ymin,ymax,ymax])*unit
    
    self.sZones = [Dzone(self,xs,ys)]
  


  def draw(self,ax,mode=None,unit=None):
    """
    draw the detector
    """
    for sz in self.getSensibleZones():      
      xs = sz.x(mode,unit)
      ys = sz.y(mode,unit)
      ax.plot(xs,ys,c='k')        
    

    




