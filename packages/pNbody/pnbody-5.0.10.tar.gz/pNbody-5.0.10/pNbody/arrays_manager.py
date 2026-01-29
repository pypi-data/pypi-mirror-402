#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      arrays_manager.py
#  brief:     Defines the arrays manager class
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


class ArrayManagerCL():
  """
  This class simplify the management of arrays in pNbody.
  It defines which arrays will be loaded or written.   
  
  The arrays managed are defined by a dictionary (self.arrays_props) with the following structure
  
      arrays_props = {}
      arrays_props["pos"] =  {                            # pos is the name of the array : self.pos
                        "h5name"  :     "Coordinates",    # name in the file
                        "dtype"   :     np.float32,       # dtype of the array
                        "dim"     :     3,                # dimention of the array
                        "ptypes"  :     all_ptypes,       # particle types
                        "read"    :     True,             # must be loaded ?
                        "write"   :     True,             # must be written ?
                        "default" :     0,                # default values 
                        "loaded"  :     False             # has been loaded or not
                      }

  """
  
  def __init__(self,ntpe,verbose):
    """
    ntpe    : number of particle types
    verbose : verbose mode
    """
    
    self.ntpe    = ntpe
    self.verbose = verbose
    
    # init arrays_props
    self.arrays_props = {}
  
  def info(self):
    """
    Provides some info on the object
    """
    print("Currently loaded arrays:")
    for key in self.arrays_props:
      if self.array_is_loaded(key):
        print(key)
    
  def isUsed(self):
    """
    Return if the class is used or not
    """
    if len(self.arrays_props) == 0:
      return False
    else:
      return True  
      
  def setArraysProperties(self,props):
    """
    Set all arrays properties into the class
    props : the arrays properties, see the class documentation    
    """
    self.arrays_props = props
    
  def arrays(self):
    return self.arrays_props.keys()

  def array_is_loaded(self,name):
    """Return if the array called name is loaded or not."""
    return self.arrays_props[name]["loaded"]
  
  def array_set_loaded(self,name):
    """Set an array called name to be loaded"""
    self.arrays_props[name]["loaded"]  = True     
  
  def array_set_unloaded(self,name):
    """Set an array called name to be not loaded"""
    self.arrays_props[name]["loaded"]  = False 
    
  def array_h5_key(self,name):
    """Get the name an array called name will have in a file"""
    return self.arrays_props[name]["h5name"]
    
  def array_default_value(self,name):
    """Get default value of an array called name."""
    return self.arrays_props[name]["default"]      
    
  def array_dtype(self,name):
    """Get the dtype of an array called name."""
    return self.arrays_props[name]["dtype"]      

  def array_ptypes(self,name):
    """Get the ptypes of an array called name."""
    return self.arrays_props[name]["ptypes"]
      
  def array_dimension(self,name):
    """Get the dimentions an array called name."""
    return self.arrays_props[name]["dim"]   
  
  def array_read(self,name):
    """Get if an array called name must be read or not."""
    return self.arrays_props[name]["read"] 

  def array_write(self,name):
    """Get if an array called name must be written or not."""
    return self.arrays_props[name]["write"] 
    

  def setReadableArraysFromHDFH5File(self,fname,arrays=None,ptypes=None):
    '''
    Set arrays to be readable or not according to their presence 
    in the hdf5 file 
    
    arrays : a list of array to read
    ptypes : a list of particle type to read
    '''
    
    from . import h5utils
  
    if ptypes is None:
      ptypes = list(range(self.ntpe))
      
    
    # open the file
    fd = h5utils.openFile(fname)
        
  
    # loop over all arrays flagged as read=True in self.arrays_props
    for name in self.arrays_props.keys():
      
      # skip array not in arrays if the latter is provided
      if arrays is not None:
        if not name in arrays:
          self.arrays_props[name]["read"]=False
      
      if self.array_read(name):
    
        h5_key        = self.array_h5_key(name)
        flag = 0
  
        # loop over particle types
        for i_type in ptypes:
          PartType = "PartType%d" % i_type
          
          # if the dataset is present
          if PartType in fd:
            if h5_key in fd[PartType].keys():   
              flag = 1
          
        # if no dataset is found, 
        if flag==0:
          self.arrays_props[name]["read"]=False
        
    
    fd.close()  



    

