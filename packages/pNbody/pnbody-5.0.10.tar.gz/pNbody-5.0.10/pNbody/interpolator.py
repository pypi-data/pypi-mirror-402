###########################################################################################
#  package:   Mockimgs
#  file:      interpolator.py
#  brief:     intgerpolator class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
import scipy
import scipy.interpolate


class SSPInterpolator():
  """
  This is a class designed to interpolate value related to single stellar populations (SSP).
  Basically, it interpolates (and extrapolate) a 2d table that depends on ages and metallicities
  """

  def __init__(self,Mat,Ages,Zs,order=1,s=0, extrapolate=False):
    '''
    Mat : a 2d matrix of size nA, nZ
    
    Ages        : a vector of size nA
    Z           : a vector of size nZ
    order       : interpolation order
    s           : smoothing 
    extrapolate : extrapolate or not 
    
    '''
    self.Mat = Mat
    self.Ages = Ages
    self.Zs   = Zs
    
    # extrapolate/interpolate...
    self.ExtrapolateMatrix(order=order,s=s, extrapolate=extrapolate)
    self.CreateInterpolator()
    self.Extrapolate2DMatrix()    
    
  def CreateInterpolator(self):
    """
    from the matrix self.Mat, create a spline interpolator
    """
    self.spl = scipy.interpolate.RectBivariateSpline(self.Zs, self.Ages, self.Mat,kx=1,ky=1,s=0)  
  
  
  def ExtrapolateMatrix(self, order=1, zmin=-5, zmax=2, nz=50, s=0, extrapolate=True):
    """
    extrapolate the matrix self.Mat in 1d (using spline), along the Z axis
    The function create a new self.Mat and self.Zs
    """

    # if extrapolated is true, we extrapolate values further out
    # elsewhere we use the neareast value (keep the value constant)
    if extrapolate:
      ext=0 
    else:
      ext=3   

    xx = np.linspace(zmin, zmax, nz)

    newMat = np.zeros((len(xx), len(self.Ages)))

    for i in np.arange(len(self.Ages)):

        Ls = self.Mat[:, i]

        # 1d spline interpolation
        x = self.Zs
        y = Ls

        tck = scipy.interpolate.splrep(x, y, k=order, s=s)
        yy = scipy.interpolate.splev(xx, tck, ext=ext)

        newMat[:, i] = yy

    self.Zs = xx
    self.Mat = newMat



  def Extrapolate2DMatrix(self,zmin=-10,zmax=2,nz=256,agemin=None,agemax=None,nage=1024):
    """
    create the big matrix self.Mat by interpolatin/extrapolating
    """
    if agemin is None:
        agemin = min(self.Ages)
    if agemax is None:
        agemax = max(self.Ages)
    
    self.Zs = np.linspace(zmin, zmax, nz)
    self.Ages = 10**np.linspace(np.log10(agemin), np.log10(agemax), nage)
    
    # extrapolate    
    self.Mat = self.spl(self.Zs, self.Ages)
    
  
  
  def Get(self,Ages,Zs):
    '''
    get values from the interpolated Matrix
    '''
    i = self.Zs.searchsorted(Zs)
    j = self.Ages.searchsorted(Ages)
    i = i.clip(0, len(self.Zs) - 1)
    j = j.clip(0, len(self.Ages) - 1)
    return self.Mat[i, j]
  
  
  def GetAgeIndexes(self, Ages):
    """
    Get the indexes of the nearest values of self.Ages from Ages
    """
    return self.Ages.searchsorted(Ages)

  def GetZIndexes(self, Zs):
    """
    Get the indexes of the nearest values of self.Zs from Zs
    """
    return self.Zs.searchsorted(Zs)


