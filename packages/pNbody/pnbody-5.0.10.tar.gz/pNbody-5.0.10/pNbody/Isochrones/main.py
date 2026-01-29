#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      BastI.py
#  brief:     
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
import os
from scipy import interpolate


database_directory=None
default_keys=None



###########################################################
# 
# Isochrone block class
#
###########################################################


class IsochroneBlock():
  """
  This class contains isochrone data, i.e., data for a list of stars of
  different masses, but with the same metallicity and age.
  """
    
  def __init__(self,data=None,keys=None,MH=None,Age=None,Mmin=None,Mmax=None):
    
    self.data = data
    self.keys = keys
    
    self.Mmin = Mmin    # minimum stellar mass
    self.Mmax = Mmax    # maximal stellar mass
    self.MH   = MH      # metallicity
    self.Age  = Age     # age

  
  def get(self,key):
    "get the values corresponding to a key (a column)"
    return self.data[:,self.keys[key]]




###########################################################
# 
# The main Isochrone class
#
###########################################################


class IsochronesGrid():
  """
  
  self.M is a numpy 2D matrix containing isochrones data (self.M[i,j]) for 
  a given metallicity and age.
  
  The Metallicity and Ages considered for the matrix is:
  
  self.binsMH  : in log10[M/H]
  self.binsAge : in Myr
  
  """
  
  def __init__(self,dirname=database_directory,default_keys=default_keys,filename=None):
    
    # make some parmeters global
    self.dirname      = dirname
    self.filename     = filename
    self.default_keys = default_keys
    
    # init the data base (the grid)
    self.Init() 
     



  def organizeDB(self):
    """
    Create the self.M matrix from the isochrones blocks
    """
    
    # compute min/max MH and Ages
    self.binsMH = []
    self.binsAge = []
    
    for mb in self.MBs:
      if mb.MH not in self.binsMH:
        self.binsMH.append(mb.MH)
      if mb.Age not in self.binsAge:
        self.binsAge.append(mb.Age)

    self.binsAge = np.array(self.binsAge)
    self.binsMH  = np.array(self.binsMH)
    self.binsAge.sort()
    self.binsMH.sort()
    
    self.M = np.empty((len(self.binsAge),len(self.binsMH)),dtype="O")
    
    # loop again and fill the matrix
    for mb in self.MBs:
      i = self.binsAge.tolist().index(mb.Age)
      j = self.binsMH.tolist().index(mb.MH)
      self.M[i,j] = mb

  def FillDBGaps(self):
    """
    Fill missing isochrones with the nearest one
    """
    pass
    
  
  
    
  def getMHbinsNumber(self):
    return len(self.binsMH)
    
  def getAgebinsNumber(self):
    return len(self.binsAge)     
  
  
  def getAgeIndex(self,Age):  
    '''
    determine the index for a given Age
    '''
    return np.fabs(self.binsAge - Age).argmin()

  def getAgeIndexes(self,Age):  
    '''
    determine the indexes bracketing a given Age
    '''
    idx = np.fabs(self.binsAge - Age).argmin()
    dd = Age - self.binsAge[idx]
    n = len(self.binsAge)-1
   
    if dd < 0:
      idx1 = idx - 1
      idx2 = idx
    else:
      idx2 = idx + 1
      idx1 = idx  

    idx1 = np.clip(idx1,0,n)
    idx2 = np.clip(idx2,0,n)
   
    return idx1,idx2

  def getMHIndex(self,MH):  
    '''
    determine the index for a given MH
    '''
    return np.fabs(self.binsMH - MH).argmin()

  def getMHIndexes(self,MH):  
    '''
    determine the indexes bracketing a given MH
    '''
    idx = np.fabs(self.binsMH - MH).argmin()
    dd = MH - self.binsMH[idx]
    n = len(self.binsMH)-1
   
    if dd < 0:
      idx1 = idx - 1
      idx2 = idx
    else:
      idx2 = idx + 1
      idx1 = idx  

    idx1 = np.clip(idx1,0,n)
    idx2 = np.clip(idx2,0,n)
   
    return idx1,idx2


  def getMaxStellarMass(self,Age,MH): 
    '''
    for a given Age and MH, get the maximal stellar mass
    '''
    # get the indexes of the table
    i = self.getAgeIndex(Age)
    j = self.getMHIndex(MH)
    # get the table
    M = self.M[i,j]  
    return M.Mmax  
    
  
  def getMassIndexes(self,Mass,i,j):
    '''
    From i (Age) and j (MH), and Mass the mass, 
    return the two indexes bracketing the mass. 
    '''
    # get the table
    M = self.M[i,j]     

    Masses = M.data[:,M.keys['initial_mass']]
    n = len(Masses)-1
    
    # a numpy array
    if type(Mass)==np.ndarray:
      idx2 = Masses.searchsorted(Mass)
      idx1 = idx2-1
      return idx1, idx2
       
    # a scalar  
    else:
      # here we need to find two masses
      idx = np.fabs(Masses - Mass).argmin()
      dd = Mass - Masses[idx]

      if dd < 0:
        idx1 = idx - 1
        idx2 = idx
      else:
        idx2 = idx + 1
        idx1 = idx  
      
      idx1 = np.clip(idx1,0,n)
      idx2 = np.clip(idx2,0,n)
      
      return idx1,idx2
      
      

  def interpolateMassAndValue(self,Mass,i,j,key):
    '''
    From i (Age) and j (MH), return the interpolated key
    for a given mass Mass
    '''
    
    # get the tables and mass indexes
    M = self.M[i,j] 
    
    k1,k2 = self.getMassIndexes(Mass,i,j)
   
    # get values
    M1 = M.data[k1,M.keys['initial_mass']]
    M2 = M.data[k2,M.keys['initial_mass']]
    V1 = M.data[k1,M.keys[key]]
    V2 = M.data[k2,M.keys[key]]
   
    # linear interpolation
    if type(Mass)==np.ndarray:
      V = np.where(V1!=V2,(M1 - Mass)/(M1-M2) * (V2-V1) + V1,V1)      
    else:  
      if M1 != M2:
        V = (M1 - Mass)/(M1-M2) * (V2-V1) + V1 
      else:
        V = V1
      
    return V    



  def get(self,Age,MH,Mass,key=None,mode="masslininterp"):
    """
    For a given Age, MH, Mass, return the value given
    by the key key.
    
    mode provides different ways of interpolating tables.
    masslininterp interpolates over masses and  
    """
    
    if mode=="nearest":
      '''
      use nearest value for the Age, MH and Mass
      '''
    
      # get the indexes of the table
      i = self.getAgeIndex(Age)
      j = self.getMHIndex(MH)
      # get the table
      M = self.M[i,j]
    
    
      Masses = M.data[:,M.keys['initial_mass']]
      idx = np.fabs(Masses - Mass).argmin()
    
      if key is not None:
        val = M.data[idx,M.keys[key]]   
        
      return val
      
    if mode=="masslininterp":
      '''
      use nearest value for the Age and MH,
      interpolate the mass
      '''
      # get the indexes of the table
      i = self.getAgeIndex(Age)
      j = self.getMHIndex(MH)
      # get the table
      #M = self.M[i,j]
      
      # interpolate the mass
      v = self.interpolateMassAndValue(Mass,i,j,key)
      return v    
    
    
    
    
    elif mode=="Agelininterp":
      
     # get the indexes and values
     i1,i2 = self.getAgeIndexes(Age)
     Age1  = self.binsAge[i1]
     Age2  = self.binsAge[i2] 
      
     # get the nearest metallicity
     j = self.getMHIndex(MH)
     
     # interpolate the Age
     v1 = self.interpolateMassAndValue(Mass,i1,j,key)
     v2 = self.interpolateMassAndValue(Mass,i2,j,key)
     val = (Age1 - Age)/(Age1-Age2) * (v2-v1) + v1 
     return val        


    elif mode=="MHlininterp":
      
    # interpolate only on MH
      
     # get the indexes and values
     j1,j2 = self.getMHIndexes(MH)
     MH1  = self.binsMH[j1]
     MH2  = self.binsMH[j2] 
     
     # get the nearest metallicity
     i = self.getAgeIndex(Age)

     
     # special case : if we are between -2.5 and -2 in MH, 
     # the isochrones are strongly different for the high mass end (wd)
     # do a nearest interpolation
     if j1==3 and j2==4:
       # get the indexes of the table
       i = self.getAgeIndex(Age)
       j = self.getMHIndex(MH)
       # get the table
       M = self.M[i,j]
       Masses = M.data[:,M.keys['initial_mass']]
       idx = np.fabs(Masses - Mass).argmin()
       if key is not None:
         val = M.data[idx,M.keys[key]]   
       return val
     
     else:
       # interpolate the MH
       v1 = self.interpolateMassAndValue(Mass,i,j1,key)
       v2 = self.interpolateMassAndValue(Mass,i,j2,key)
       val = (MH1 - MH)/(MH1-MH2) * (v2-v1) + v1 
       return val  

    
    
    elif mode=="lininterp":
      
      # get the indexes and values
      i1,i2 = self.getAgeIndexes(Age)
      Age1  = self.binsAge[i1]
      Age2  = self.binsAge[i2]
            
      j1,j2 = self.getMHIndexes(MH)
      MH1   = self.binsMH[j1]
      MH2   = self.binsMH[j2]   
      
      # MH1=MH2 and Age1=Age2 -> not interpolation
      if j1==j2 and i1==i2: 
        v = self.interpolateMassAndValue(Mass,i1,j1,key)
        return v
        
      # MH1=MH2 -> interpolate only in Age
      if j1==j2: 
        v1 = self.interpolateMassAndValue(Mass,i1,j1,key)
        v2 = self.interpolateMassAndValue(Mass,i2,j1,key)
        val = (Age1 - Age)/(Age1-Age2) * (v2-v1) + v1 
        return val
      
      # Age1=Age2 -> interpolate only in MH  
      if i1==i2:
        v1 = self.interpolateMassAndValue(Mass,i1,j1,key)
        v2 = self.interpolateMassAndValue(Mass,i1,j2,key)
        val = (MH1 - MH)/(MH1-MH2) * (v2-v1) + v1 
        return val
      
      
      # special case : if we are between -2.5 and -2 in MH, 
      # the isochrones are strongly different for the high mass end (wd)
      # we then only interpolate in Age
      if j1==3 and j2==4:
        # get the nearest metallicity
        j = self.getMHIndex(MH)
        v1 = self.interpolateMassAndValue(Mass,i1,j,key)
        v2 = self.interpolateMassAndValue(Mass,i2,j,key)
        val = (Age1 - Age)/(Age1-Age2) * (v2-v1) + v1 
        return val        
        
        
        
      # here we can perform a bilinear interpolation
      
      # get the four values
      v11 = self.interpolateMassAndValue(Mass,i1,j1,key)
      v12 = self.interpolateMassAndValue(Mass,i1,j2,key)
      v21 = self.interpolateMassAndValue(Mass,i2,j1,key)
      v22 = self.interpolateMassAndValue(Mass,i2,j2,key)
      
      #if np.isfinite(v11) == False:
        #print(v11,Age1,MH1,Mass)
        #exit()

      # if np.isfinite(v12) == False:
        # print(v12,Age1,MH2,Mass)
        # exit()
        
      # if np.isfinite(v21) == False:
        # print(v21,Age2,MH1,Mass)
        # exit()
        
      # if np.isfinite(v22) == False:
        # print(v22,Age2,MH2,Mass)
        # exit()

      # bilinear interpolation
      x = np.array([Age1,Age2])
      y = np.array([MH1,MH2])
      xx, yy = np.meshgrid(x, y)
      z = np.array([[v11,v21],[v12,v22]])
      f = interpolate.interp2d(x, y, z)
      val =  f(Age,MH)[0]
      
      # in case something goes wrong
      if np.isfinite(val) == False:
        print("!!! bad value : val = %g"%val)
        print(Age,MH,Mass)
        print(Age1,Age2,MH1,MH2)
        exit()
            
            
      return val


  def getKeys(self):
    """
    return the list of the keys
    """
    return self.keys

  def checkKeyExists(self,key):
    """
    check if the key key is the key list
    """
    for k in self.getKeys():
      if k == key:
        return True
    
    raise NameError("key %s does not exists in DB.\nUse one given in the following list: \n%s"%(key,str(list(self.getKeys().keys()))))  



