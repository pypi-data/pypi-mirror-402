#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      MIST.py
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


def read_mesa_iso(filename,MBs=[],default_keys=None):
  """
  read one mesa iso file
  and return it content as an array
  
  filename      : name of the file to read
  default_keys  : default keys to read. If None, ignore
  
  """

  def read_block(f):
    
    # read block header
    f.readline()
    line = f.readline()
    line = line.split("=")[1]
    line = line.split()
    nrows = int(line[0])
    ncols = int(line[1])
    f.readline()
    
    # keys
    keys = f.readline()
    keys = keys.split()[1:]
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
   
    # read 
    data = np.loadtxt(f,max_rows=nrows,usecols=tmp_keys)
    
    # skip the last line
    f.readline()
    
    return data,keys
  
  def toMistBlock(data,keys):
    "convert an array to a MistBlock object"
    
    
    MB = IsochroneBlock(data=data,keys=keys)
    
    # min/max stellar mass in solar masses
    MB.Mmin = min(MB.get("initial_mass"))
    MB.Mmax = max(MB.get("initial_mass"))
    MB.MH   =     MB.get("[Fe/H]_init")[0]
    # age in Myr
    MB.Age  =     10**MB.get("log10_isochrone_age_yr")[0] / 1e6
    
    return MB
  

  
  print("reading: ",filename)
  f = open(filename,'r')
  f.seek(0,2)
  size = f.tell()
  f.seek(0,0)
    
  # skip file header
  for i in range(9):
    f.readline()
  
  # loop over all blocks
  nblocks = 0
  while True:
    try:
      # read the block
      data,keys = read_block(f)
            
      # convert to a block object
      MB = toMistBlock(data,keys)
      MBs.append(MB)
      
      nblocks = nblocks + 1
    except:
      break
  
  return MBs



###########################################################
# 
# Isochrone Grid
#
###########################################################

class Grid(IsochronesGrid):
  
  def Init(self):

    # get all files
    self.filenames = glob.glob(os.path.join(self.dirname,"*"))

    # list of Isocrhones blocks
    self.MBs = []    
        
    # read all the tar file and fill the isochrones list
    self.readAll() 
    
    # create the DB (self.M) from the isochrones list
    self.organizeDB()


  def readAll(self):
    "read the data base by looping over files"
    
    for filename in self.filenames:  
      self.MBs = read_mesa_iso(filename,MBs=self.MBs,default_keys=self.default_keys)

    # define keys
    self.keys = self.MBs[0].keys







