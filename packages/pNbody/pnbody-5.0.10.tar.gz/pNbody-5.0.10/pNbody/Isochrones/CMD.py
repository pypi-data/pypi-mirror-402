#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      CMD.py
#  brief:     
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
import tarfile
import glob
import os
from pNbody.Isochrones.main import  IsochronesGrid, IsochroneBlock



def read_CMD(filename,MBs=[],default_keys=None):
  """
  read one CMD file
  http://stev.oapd.inaf.it/cmd
  
  and return it content as an array
  
  filename      : name of the file to read
  default_keys  : default keys to read. If None, ignore

  """
  
  # find the header and parse it
  f = open(filename,'r')
  while(True):
    line = f.readline()
    if line[:6] == "# Zini":
      break
  f.close()
  
  keys = line[1:].split()
  # change Mini to initial_mass
  idx = keys.index("Mini")
  keys[idx] = "initial_mass"
  
  # make a dict
  keys = {x: i for i,x in enumerate(keys)}
  

  if default_keys is not None:
    new_keys = {}
    tmp_keys = []
    for i,k in enumerate(default_keys):
      new_keys[k] = i
      tmp_keys.append(keys[k])
    keys = new_keys  
  else:
    tmp_keys = []
    for i,k in enumerate(keys):
      tmp_keys.append(keys[k])

    
  # read the complete data
  data = np.loadtxt(filename,comments="#",usecols=tmp_keys)
  
  MH     = data[:,keys["MH"]]
  Age    = 10**data[:,keys["logAge"]]/1e6  # in Myr
  
  # find the bins
  binsMH  = np.unique(MH)
  binsAge = np.unique(Age)
  
  
  M = np.empty((len(binsAge),len(binsMH)),dtype="O")
  
  
  for i in range(len(binsAge)):
    for j in range(len(binsMH)):

      # create a mist block
      dataij = data[(MH==binsMH[j]) & (Age==binsAge[i])]
      
      MB = IsochroneBlock(data=dataij,keys=keys)
      
      # min/max stellar mass in solar masses
      MB.Mmin = min(MB.get("initial_mass"))
      MB.Mmax = max(MB.get("initial_mass"))
      MB.MH   = binsMH[j]    
      # age in Myr
      MB.Age  = binsAge[i]/1e6       
      
      M[i,j] = MB
              
  return M,binsMH,binsAge,keys
  


###########################################################
# 
# Isochrone Grid
#
###########################################################

class Grid(IsochronesGrid):
  
  def Init(self):

    self.M,self.binsMH,self.binsAge,self.keys = read_CMD(self.filename,default_keys=self.default_keys)  


