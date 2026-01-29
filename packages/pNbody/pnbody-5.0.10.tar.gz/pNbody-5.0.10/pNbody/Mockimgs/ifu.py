###########################################################################################
#  package:   Mockimgs
#  file:      ifu.py
#  brief:     ifu class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u
from .detector import Detector
from .spoints import sPoints

class IFU(Detector):
  '''
  Define the CCD class.
  '''
  def __init__(self,name,size=None):    
        
    self.name  = name
    self.size  = size

    # define the sensible ccd zone
    self.defineSensibleZones()


  def info(self):
    """
    gives info on the ifu
    """
    print("ifu name              : %s"%self.name) 
    print("ifu size              : %s"%self.size)   
    

  def defineSensibleZones(self):
    """
    set the sensible zone in size units
    
    self.sZone is a list of tupple
    """
    
    unit = self.size.unit
    ref  = self.size.ref
    
    xmin = -self.size[0].value/2.
    xmax = +self.size[0].value/2.
    ymin = -self.size[1].value/2.
    ymax = +self.size[1].value/2.  
    
    xs = np.array([xmin,xmax,xmax,xmin,xmin])*unit
    ys = np.array([ymin,ymin,ymax,ymax,ymin])*unit
    
    pts = sPoints(xs,ys,ref)
    self.sZones = [pts]
    
  
  
      
      
        


