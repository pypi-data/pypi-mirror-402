#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      __init__.py
#  brief:     
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
import sys, os
import time

from . import BastI
from . import CMD
from . import MIST

database_directory=None
default_keys=None


#'''
#
## setup database directory
#if "PNBODY_ISOCHRONE_DEFAULT_DATABASE" in os.environ:
#  database_directory = os.environ["PNBODY_ISOCHRONE_DEFAULT_DATABASE"]
#else:
#  raise NameError("Environnement variable %s not defined ! Please define it."%("PNBODY_ISOCHRONE_DEFAULT_DATABASE"))
#
## setup database directory
#if "PNBODY_ISOCHRONE_LIBRARY_NAME" in os.environ:
#  filter_system = os.environ["PNBODY_ISOCHRONE_LIBRARY_NAME"]
#else:
#  raise NameError("Environnement variable %s not defined ! Please define it."%("PNBODY_ISOCHRONE_LIBRARY_NAME"))
#
#'''
#
## default keys of the database
##default_keys = ["log10_isochrone_age_yr","initial_mass","log_Teff","log_L","[Fe/H]_init","SDSS_u","SDSS_g","SDSS_r","SDSS_i","SDSS_z"]
#default_keys = None
#
##if not os.path.isdir(database_directory):
##   raise NameError("directory %s not found !"%(database_directory))
# 
#database_directory=None
#def getDatabaseDirectory():
#  return database_directory
#


def Isochrones(dirname=database_directory,default_keys=default_keys,filename=None):
  
  if filename is not None:
    if os.path.isfile(filename):
      return CMD.Grid(filename=filename,default_keys=default_keys)
    else:
      raise NameError("The file %s does not exists !"%filename)
  
  else:
    
    if os.path.isdir(dirname):
      if os.path.basename(dirname)[:4] == "MIST":
        return MIST.Grid(dirname=dirname,default_keys=default_keys)
      else:
        return BastI.Grid(dirname=dirname,default_keys=default_keys)
    
    else:
      raise NameError("The directoy %s does not exists !"%dirname)
    
    






