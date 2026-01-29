###########################################################################################
#  package:   Mockimgs
#  file:      los.py
#  brief:     line of sight class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from .. import iofunc as io
from .utils import align
from .parameters import Parameters



def get_axes(n=7,random=False,irand=None):

  if irand is not None:
    np.random.seed(irand)
  
  if random:
    random2 = np.random.random(n)
    random3 = np.random.random(n)
  else:

    # this is another way to define n1 and n2
    # n2 = int(1 + np.sqrt(1-0.5*(3-n)))
    # n1 = 2*(n2-1)
    # from the requirement that n = 2*n2**2 -4*n2 + 3 
    # which comes from  n = n1*n2 - (n1-1)
        
    n = int(np.sqrt(n/2))
    #n1 = 2*n   
    n1 = n      
    n2 = n+1
    #random2 = np.linspace(0,1,n1+1)[:-1]   
    random2 = np.linspace(0,1,n1+1)[:-1]/2  # limit to pi
    
    random3 = np.linspace(0,0.5,n2)    
    random2,random3 = np.meshgrid(random2,random3)
    random2 = random2.ravel()
    random3 = random3.ravel()
    
    # keep only one 90 deg in theta
    random2 = random2[(n1-1):]
    random3 = random3[(n1-1):]
    

  phi = random2 * np.pi * 2.
  costh = 1. - 2. * random3

  sinth = np.sqrt(1. - costh**2)

  x = sinth * np.cos(phi)
  y = sinth * np.sin(phi)
  z = costh
  
  pos = np.transpose(np.array([x, y, z]))
  
  return pos


def get_axes_from_grid(n_phi,n_theta,d_phi,d_theta,los):
  """
  get a list of axes centred on los and 
  equally distributed in azimuth and elevation 
  
  n_phi   :   number of divisions in azimuthal angle
  n_theta :   number of divisions in elevation angle
  d_phi   :   azimuthal variation in degree [-d_phi,-d_phi]
  d_theta :   elevation variation in degree [-d_theta,-d_theta]
  
  """
  
  thetas = np.pi/180 * np.linspace(-d_theta,d_theta,n_theta)
  phis   = np.pi/180 * np.linspace(-d_phi  ,d_phi  ,n_phi)
  
  # the ref axis is 1,0,0
  axes = []
  for theta in thetas:
    for phi in phis:
      x = np.cos(theta)*np.cos(phi)
      y = np.cos(theta)*np.sin(phi)
      z = np.sin(theta)
      axes.append([x,y,z])
  
  # convert to numpy array
  pos = np.array(axes)
  # rotate to centre the final direction
  pos = align(pos,axis=los,axis_ref=[1,0,0])
  # back to a list
  axes = pos.tolist()
  
  return axes





  

def SetLineOfSights(n=1,random=False,irand=None):

  if n==1:
    los_axes=[[0,0,1]]
  else:    
    los_axes = get_axes(n,random,irand)  
    
  return los_axes


class LineOfSights():
  """
  A line of sights object
  
  not that a line of sight of [1,0,0] means that the observer
  is in [1,0,0] and look towards [-1,0,0] 
  
  parameters
  ----------
  
  n         : the number of line of sight
  random    : if the line of sight are random or not
  irand     : the random seed
  los       : explicitly provide a line of sight
  
  
  """
  def __init__(self,opt=None,params=None,parameter_file=None):
    
    # init default parameters
    self._init_default_parameters()
    
    # 1: set parameters from a yml file
    if parameter_file is not None:
      pdic = io.ReadYaml(parameter_file,'LineOfSights')
      self._p.update_from_dic(pdic) 

    # 2: set parameters from the dictionary params
    if params is not None:
      self._p.update_from_dic(params) 

    # 3: set parameters from options
    if opt is not None:
      self._p.update_from_options(opt,skip_None=True) 
    
    
    
    # init idx
    self.idx = -1
        
    # treat different cases
    
    # create from a grid
    if self._p.grid is not None:
      n_phi   = self._p.grid["n_phi"]
      n_theta = self._p.grid["n_theta"]
      d_phi   = self._p.grid["d_phi"]
      d_theta = self._p.grid["d_theta"] 
      los     = self._p.los     
      self.axes = get_axes_from_grid(n_phi,n_theta,d_phi,d_theta,los)
      return  
  
    # if the line of sight is given
    if self._p.los is not None:
      # use the los which is provided
      self.axes=[self._p.los]
      return
    
    # only one line of sight is needed
    if self._p.nlos==None or self._p.nlos==1:
      self.axes=[[0,0,1]]
      return
      
    # instead, get either random axes or axes on an hemisphere  
    self.axes = get_axes(self._p.nlos,random=self._p.random_los,irand=self._p.irand)  
    
    
    
  def _init_default_parameters(self):
    '''
    define parameters as well as their default value
    '''
    self._p = Parameters()
    self._p.nlos        = None      # number of line of sights
    self._p.random_los  = False     # random line of sights
    self._p.irand       = 0         # random seed
    self._p.los         = None      # line of sight
    self._p.grid        = None      # grid parameters to generate a los
  
  def print_parameters(self):
    print(self._p)  

    
  def __iter__(self):
    return self

  def __next__(self):
    if self.idx == len(self.axes)-1:
      raise StopIteration
    self.idx = self.idx + 1
    return self.axes[self.idx]

  def info(self):
    for ax in self.axes:
      print(ax)
  
  def n(self):
    """
    return the number of line of sights
    """
    return len(self.axes)  
  
  def list(self):
    """
    return the list of line of sight
    """
    return self.axes
        
  def get(self):
    """
    return the next line of sight
    """
    return self.axes[self.idx]
    
    


  
