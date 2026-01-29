###########################################################################################
#  package:   Mockimgs
#  file:      telescope.py
#  brief:     telescope class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import astropy.units
from astropy import units as u

class Telescope():
  '''
  Define the telescope class.
  '''
  
  def __init__(self,name=None,focal=None): 
       
    self.name  = name
    self.set_focal(focal)
    
  def info(self):
    """
    give info on the telescope
    """  
    print("telescope name     : %s"%self.name)


  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters    
    """
    params = {}
    if fmt=="fits":
      params["TELNAME"]            = (self.name,"Telescope name")
    else:
      params["telescope_name"]     = self.name

    if fmt=="fits":
      if self.focal is None:
        params["FOCAL"]              = str(None)
      else:  
        params["FOCAL"]              = (self.focal.to(u.cm).value,"Telescope focal in cm")
    else:
      params["telescope_focal"]    = self.focal
    
    return params


      
  def get_focal(self):
    """
    return the telescope focal
    """    
    return self.focal
      

  def set_focal(self,focal):
    """
    set the telescope focal
    
    focal : an astropy quantity in unit length
    """   
    if focal is not None:
      if type(focal) != astropy.units.quantity.Quantity:
        raise TypeError("focal must be of type astropy.units.quantity.Quantity") 
    
    self.focal = focal
    
    
    
    
    
