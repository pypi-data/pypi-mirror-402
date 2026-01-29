###########################################################################################
#  package:   Mockimgs
#  file:      noise.py
#  brief:     noise functions
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np

def get_std_for_SB_limit(SBlimit,p,area=100,zp=0,sn=3):
  """
  Compute the standard deviation of a Gaussian distribution (noise) 
  that must be applied on pixels to get a given SB limit computed
  in a given area.
  
  SBlimit  : desired SB limit
  p        : pixel sizein arsecond
  area     : area in arcsecond^2
  zp       : zero point
  sn       : signal to noise
  """
  
  # compute sigma
  sigma = p * (np.sqrt(area)/sn) * 10**(-(SBlimit-zp)/2.5)
  
  return sigma





