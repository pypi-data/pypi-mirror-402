###########################################################################################
#  package:   Mockimgs
#  file:      detector.py
#  brief:     detector class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u


class Detector():
  '''
  Define the Detector class.
  '''
  def __init__(self,name):    

    self.name       = name
    self.instrument = None

    # define the sensible
    self.defineSensibleZones()
    

  def info(self):
    """
    gives info on the detector
    """
    print("detector name              : %s"%self.name)

  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters    
    """
    params = {}
    params["detector_name"]           = self.detector
    return params  
  
  
  
  def getFocal(self):
    """
    if defined, get the instrument focal
    """
    if self.instrument is not None:
      return self.instrument.getFocal()
    else:
      raise ValueError("no instrument defined. Cannot get the telescope focal.")
    
  def getDistance(self):
    """
    if defined, get the object distance
    """
    if self.instrument is not None:
      obj = self.instrument.getObject()
      return obj.getDistance()
    else:
      raise ValueError("no object defined. Cannot get the object distance.")

  
  def toDistance(self,x):
    """
    convert distances in the ccd
    to physical distances, assuming some focal and distance
    """
    focal    = self.getFocal()
    distance = self.getDistance()
    return x/focal*distance
    
  
  def toAngle(self,x):  
    """
    get the factor to convert distances in the ccd
    to angle, assuming some focal    
    """
    focal    = self.getFocal()
    return np.arctan(x/focal)
      
  

  def defineSensibleZones(self):
    """
    set the sensible zone
    """
    xs = np.array([-1,1,1,-1])*u.mm
    ys = np.array([-1,-1,1,1])*u.mm    
    self.sZones = [Dzone(self,xs,ys)]
    
    
  def getSensibleZones(self):
    """
    return the sensible zones
    """  
    return self.sZones
  
  def draw(self,ax,mode=None,unit=None):
    """
    draw the detector
    """
    self.drawSensibleZones(ax,mode,unit)  
    
    
  def drawSensibleZones(self,ax,mode=None,unit=None):  
    """
    draw the sensible zones
  
    ax : matplotlib axis
    """
    
    focal    = self.getFocal()
    distance = self.getDistance()
    
    for sz in self.getSensibleZones():
      
      xs = sz.x(mode=mode,unit=unit,focal=focal,distance=distance)
      ys = sz.y(mode=mode,unit=unit,focal=focal,distance=distance)
      
      ax.scatter(xs,ys,c='k')
      
            
      
      
    
    
    
    


    
    
    
