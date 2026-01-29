#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      h5utils.py
#  brief:     Defines usefull function related to the hdf5 format
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from . import mpi
import h5py
import numpy as np

try:
    from mpi4py import MPI
except BaseException:
    MPI = None

def openFile(fname,mode='r'):
    """
    open an hdf5 file
    """
    if mpi.mpi_NTask() > 1:
        fd = h5py.File(fname,mode,driver="mpio",comm=MPI.COMM_WORLD)
    else:
        fd = h5py.File(fname,mode)

    return fd

def closeFile(fd):
    """
    close an hdf5 file
    """
    mpi.mpi_barrier()
    fd.close()


def get_particles_limits(size):
    """ Gives the limits for a thread.
    In order to get the particles, slice them like this pos[start:end].
    :param int i: Particle type
    :returns: (start, end)
    """
    nber = float(size) / mpi.mpi_NTask()
    start = int(mpi.mpi_ThisTask() * nber)
    end = int((mpi.mpi_ThisTask() + 1) * nber)
    return start, end    


def get_particles_limits_from_npart(npart_i):
    """ Gives the limits for a thread.
    In order to get the particles, slice them like this pos[start:end].
    :param npart_tot_i: total particle of type i
    :returns: (start, end)
    """
    nber = float(npart_i) / mpi.mpi_NTask()
    start = int(mpi.mpi_ThisTask() * nber)
    end = int((mpi.mpi_ThisTask() + 1) * nber)
    return start, end
        


def get_npart_from_dataset(fname,key,ntype,ptypes=None):
  '''
  Get an array containing the number of particles for each particle type
  from the block named key.
  
  fname  : the file name
  key    : the block to read
  ntype  : number of particle types 
  '''

  if ptypes is None:
    ptypes = list(range(ntype))
    
  h5_key = key 
  
  # open the file
  fd = openFile(fname)    
  
  npart = np.zeros(ntype,np.uint32)
  
  # loop over particle types
  for i_type in ptypes:
    PartType = "PartType%d" % i_type
    
    if PartType in fd:
      block = fd[PartType]
      
      # if the dataset is present
      if h5_key in fd[PartType].keys():
        
        data_lenght   = block[h5_key].len()
      
        idx0=0
        idx1=data_lenght
        if mpi.mpi_NTask() > 1:
          idx0, idx1 = get_particles_limits(data_lenght)
        
        npart[i_type] = idx1-idx0   
        
      else:
        raise error.FormatError("%s is not in the file."%(h5_key))     
  
  
  # close the file
  closeFile(fd)
  
  return npart
