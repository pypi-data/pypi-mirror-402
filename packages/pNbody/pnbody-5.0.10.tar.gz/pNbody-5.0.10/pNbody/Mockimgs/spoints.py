###########################################################################################
#  package:   Mockimgs
#  file:      spoints.py
#  brief:     spoints class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from .scoords import sCoords
from astropy import units as u

class sPoints():
  
  def __init__(self,x,y,ref):
    """
    x : list of x coordinates (astropy units.quantity.Quantity)
    y : list of x coordinates (astropy units.quantity.Quantity)
    """
    
    if type(x) != u.quantity.Quantity:
      raise TypeError("x must be of type astropy.units.quantity.Quantity")

    if type(y) != u.quantity.Quantity:
      raise TypeError("y must be of type astropy.units.quantity.Quantity")
    
    self.xs = sCoords(x,ref=ref)
    self.ys = sCoords(y,ref=ref)
      
      
  def x(self,mode=None,unit=None,focal=None,distance=None):
    
    # some conventions to guarantee backwards compatibility
    if   mode=="angle"    : mode="sky"
    elif mode=="detector" : mode="focal plane"
    elif mode=="phys"     : mode="universe"
    
    xs = self.xs.change_ref(mode,focal=focal,distance=distance)
      
    if unit is not None:
      xs = xs.to(unit)
    
    return xs
      

  def y(self,mode=None,unit=None,focal=None,distance=None):
    
    # some conventions to guarantee backwards compatibility
    if   mode=="angle"    : mode="sky"
    elif mode=="detector" : mode="focal plane"
    elif mode=="phys"     : mode="universe"
    
    ys = self.ys.change_ref(mode,focal=focal,distance=distance)
      
    if unit is not None:
      ys = ys.to(unit)
    
    return ys     


      

