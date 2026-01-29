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
import tarfile
import glob
import os
from pNbody.Isochrones.main import  IsochronesGrid, IsochroneBlock


def ReadOneIsochrone(f,default_keys=None):

  needtoclose=False
  
  # open if not a file descriptor  
  if type(f)==str:
    f = open(f)
    needtoclose=True
  
  # read header
  f.readline()
  line = f.readline()
  #print(line)
  
  for i in range(2):
    f.readline()
      
  header = f.readline()
  if type(header)==bytes:
    header = header.decode("utf-8")
  
  string = "[M/H] ="
  idx = header.find(string)
  MH    = float(header[idx+len(string):idx+len(string)+9])
  
  string = "Age (Myr) ="
  idx = header.find(string)
  Age   = float(header[idx+len(string):-1])
  
  #string = "Y ="
  #idx = header.find(string)
  #Y   = float(header[idx+len(string):idx+len(string)+11])
    
  f.readline()
  header = f.readline()
  if type(header)==bytes:
    header = header.decode("utf-8")
  keys = header.split()[1:]
  
  # change Mini to initial_mass
  idx = keys.index("M/Mo(ini)")
  keys[idx] = "initial_mass"

  # make a dict
  keys = {x: i for i,x in enumerate(keys)}
  
  
  # read the data
  data = np.loadtxt(f)
  
  # close file
  if needtoclose:
    f.close()

  # return
  return data, MH, Age, keys
  
  
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
    '''
    Loop over all files and store the content in a list of 
    isochrones blocks.
    '''
    
    # loop over all files
    for filename in self.filenames:
      
      print(filename)

      tar = tarfile.open(filename)
      members = tar.getmembers()
      
      for member in members:
        f = tar.extractfile(member)
        
        # read   
        data, MH, Age, keys = ReadOneIsochrone(f,default_keys=None)

        # convert to a block object
        MB = self.toIsochroneBlock(data,MH,Age,keys)
        self.MBs.append(MB)


    # define keys
    self.keys = self.MBs[0].keys



  def toIsochroneBlock(self,data,MH,Age,keys):
    """
    Convert raw data from a BastI file into an isochrones block
    """
  
    MB = IsochroneBlock(data=data,keys=keys)
    
    # min/max stellar mass in solar masses
    MB.Mmin = min(MB.get("initial_mass"))
    MB.Mmax = max(MB.get("initial_mass"))
    MB.MH   =     MH
    # age in Myr
    MB.Age  =     Age
    
    return MB


