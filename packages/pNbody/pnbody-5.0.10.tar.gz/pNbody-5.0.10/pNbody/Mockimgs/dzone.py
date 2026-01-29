###########################################################################################
#  package:   Mockimgs
#  file:      dzone.py
#  brief:     dzone class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u


class Dzone():
  '''
  Define the Dzone class.
  A Dzone is a zone on a detector
  '''
  def __init__(self,detector,xs,ys):
    """
    xs,ys a list of points with unit length
    
    focal    : the telescope focal, this allow to convert x,y from the focal plane
               to angle
    distance : the distance to an object, this allow to convert x,y from the focal plane
               to distances
    
    """
    
    # close the zone
    self.xs = np.concatenate((xs,[xs[0]]))
    self.ys = np.concatenate((ys,[ys[0]]))
    
    # detector
    self.detector = detector
    
    
  
  def x(self,mode=None,unit=None):
    """
    get x values
    
    mode : the mode [None,angle,phys]
    """
    if mode is None or mode=="detector":
      val = self.xs
      
    elif mode=="angle":
      val =  self.detector.toAngle(self.xs)
      
    elif mode=="phys":
      val =  self.detector.toDistance(self.xs)     
    
    if unit is not None:
      val = val.to(unit)
    
    return val  
  
  
  def y(self,mode=None,unit=None):
    """
    get y values
    
    mode : the mode [None,angle,phys]
    """
    if mode is None or mode=="detector":
      val = self.ys
      
    elif mode=="angle":
      val =  self.detector.toAngle(self.ys)
      
    elif mode=="phys":
      val =  self.detector.toDistance(self.ys)     
    
    if unit is not None:
      val = val.to(unit)
    
    return val  







