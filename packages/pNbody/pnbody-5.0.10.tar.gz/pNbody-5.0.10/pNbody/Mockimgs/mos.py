###########################################################################################
#  package:   Mockimgs
#  file:      mos.py
#  brief:     mos class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from astropy import units as u
from .detector import Detector
from .spoints import sPoints

import numpy as np

class MOS(Detector):
  '''
  Define the MOS class.
  Multi Object Spectroscopy
  '''
  def __init__(self,name,fov):    
        
    self.name = name
    self.fov  = fov
    
    self.defineSensibleZones()

  def info(self):
    """
    gives info on the mos
    """
    print("mos name              : %s"%self.name) 
    print("mos fov               : %s"%self.fov)   


  def defineSensibleZones(self):
    """
    set the sensible zone here in fov unit
    
    self.sZone is a list of tupple
    """
    
    r    = self.fov.value
    unit = self.fov.unit
    ref  = self.fov.ref
    
    theta =  np.linspace(0,2*np.pi,100)
    xs = r*np.cos(theta)*unit
    ys = r*np.sin(theta)*unit
        
    pts = sPoints(xs,ys,ref)
    self.sZones = [pts]



