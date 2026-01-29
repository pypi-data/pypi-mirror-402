###########################################################################################
#  package:   Mockimgs
#  file:      utils.py
#  brief:     some useful routines
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from scipy.spatial.transform import Rotation



def convert_rsp_options_to_parameters(opt):
  '''
  convert argparse rsp options to parameters
  stored in a dictionary 
  '''
  rsp_opts = {}
  rsp_opts["mode"] = opt.rsp_mode
  rsp_opts["val"]  = opt.rsp_val
  rsp_opts["max"]  = opt.rsp_max
  rsp_opts["sca"]  = opt.rsp_sca  
  rsp_opts["fac"]  = opt.rsp_fac  
  return rsp_opts
  


def align(pos,axis,axis_ref=[0,0,1]):
  """
  rotate the model with a rotation that align axis with axis_ref
  
  pos      : a set of positions
  axis     : the axis
  axis_ref : the reference axis
  """
  axis1 = axis_ref
  axis2 = axis

  a1 = np.array(axis1, float)
  a2 = np.array(axis2, float)

  a3 = np.array([0, 0, 0], float)
  a3[0] = a1[1] * a2[2] - a1[2] * a2[1]
  a3[1] = a1[2] * a2[0] - a1[0] * a2[2]
  a3[2] = a1[0] * a2[1] - a1[1] * a2[0]

  n1 = np.sqrt(a1[0]**2 + a1[1]**2 + a1[2]**2)
  n2 = np.sqrt(a2[0]**2 + a2[1]**2 + a2[2]**2)
  angle = -np.arccos(np.inner(a1, a2) / (n1 * n2))

  if angle==0:
    return pos
    
  # set the norm of a3 to be angle
  norm = np.sqrt(a3[0]**2 + a3[1]**2 + a3[2]**2)
  a3 = a3/norm*angle  
    
  # create the rotation matix
  R = Rotation.from_rotvec(a3)
  
  # do the rotation
  pos = R.apply(pos)
  
  return pos

  
