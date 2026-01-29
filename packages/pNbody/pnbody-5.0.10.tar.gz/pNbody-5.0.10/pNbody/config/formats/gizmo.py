###########################################################################################
#  package:   pNbody
#  file:      swift.py
#  brief:     SWIFT file format
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>, Loic Hausammann <loic_hausammann@hotmail.com>
#
# This file is part of pNbody.
###########################################################################################


##########################################################################
#
# GEAR HDF5 CLASS
#
##########################################################################

import numpy as np
import h5py

import pNbody
from pNbody import mpi, error, units

try:				# all this is useful to read files
    from mpi4py import MPI
except BaseException:
    MPI = None



class Nbody_gh5:
  
  
    def get_default_arrays_props(self):
      '''
      get the default properties of arrays considered
      
      "h5name"  :     name in the hdf5 file
      "dtype"   :     numpy dtype                       
      "dim"     :     dimention 
      "ptypes"  :     type of particles that store this property (useless for the moment)
      "read"    :     read it by default or not
      "write"   :     write it by default or not
      "default" :     default values of the components
      "loaded"  :     is the array currently loaded    
      
      # position must always be first, this is a convention
      '''
      
      all_ptypes = list(range(self.get_mxntpe()))
      
      aprops = {}
      
      aprops["pos"] =  {
                        "h5name"  :     "Coordinates", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     3, 
                        "ptypes"  :     all_ptypes,
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["vel"] =  {
                        "h5name"  :     "Velocities", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     3,
                        "ptypes"  :     all_ptypes, 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }
                      
      aprops["mass"] =  {
                        "h5name"  :     "Masses", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     all_ptypes, 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     1,
                        "loaded"  :     False
                      }

      aprops["num"] =  {
                        "h5name"  :     "ParticleIDs", 
                        "dtype"   :     np.uint32,                        
                        "dim"     :     1,
                        "ptypes"  :     all_ptypes, 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }
                          
      aprops["pot"] =  {
                        "h5name"  :     "Potentials", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     all_ptypes, 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["acc"] =  {
                        "h5name"  :     "Acceleration", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     3,
                        "ptypes"  :     all_ptypes, 
                        "read"    :     False,
                        "write"   :     False, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["rsp"] =  {
                        "h5name"  :     "SmoothingLengths", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["rsp_init"] =  {
                        "h5name"  :     "SmoothingLength", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }


      aprops["u"] =  {
                        "h5name"  :     "InternalEnergies", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["u_init"] =  {
                        "h5name"  :     "InternalEnergy", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["rho"] =  {
                        "h5name"  :     "Densities", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }
                      





      aprops["snii_thermal_time"] =  {
                        "h5name"  :     "SNII_ThermalTime", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["snia_thermal_time"] =  {
                        "h5name"  :     "SNIa_ThermalTime", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [0], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }


      aprops["softening"] =  {
                        "h5name"  :     "Softenings", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [1,2], 
                        "read"    :     False,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["minit"] =  {
                        "h5name"  :     "BirthMasses", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["tstar"] =  {
                        "h5name"  :     "BirthScaleFactors", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["tstar"] =  {
                        "h5name"  :     "StellarFormationTime",         # same as "BirthScaleFactors"
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }


      aprops["rhostar"] =  {
                        "h5name"  :     "BirthDensities", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }



      aprops["sp_type"] =  {
                        "h5name"  :     "StellarParticleType", 
                        "dtype"   :     np.int32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }


      aprops["idp"] =  {
                        "h5name"  :     "ProgenitorIDs", 
                        "dtype"   :     np.uint32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }



      aprops["age"] =  {
                        "h5name"  :     "StellarAge", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }
                      
      aprops["metals"] =  {
                        "h5name"  :     "Metallicity", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     15,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

      aprops["mh"] =  {
                        "h5name"  :     "MH", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }                   


      return aprops  
    
    
    
    def array_is_loaded(self,name):
      return self.arrays_props[name]["loaded"]

    def array_set_loaded(self,name):
      self.arrays_props[name]["loaded"]  = True     
  
    def array_set_unloaded(self,name):
      self.arrays_props[name]["loaded"]  = False 
      
    def array_h5_key(self,name):
      return self.arrays_props[name]["h5name"]
      
    def array_default_value(self,name):
      return self.arrays_props[name]["default"]      
      
    def array_dtype(self,name):
      return self.arrays_props[name]["dtype"]      

    def array_dimension(self,name):
      return self.arrays_props[name]["dim"]   

    def array_read(self,name):
      return self.arrays_props[name]["read"] 
        

  
    def get_npart_from_dataset(self,ptypes=None):
      '''
      Get npart from the block storing the positions
      '''

      if ptypes is None:
        ptypes = list(range(self.get_mxntpe()))
        
      h5_key = self.array_h5_key('pos')  
      
      if mpi.mpi_NTask() > 1:
          fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
      else:
          fd = h5py.File(self.p_name_global[0],'r')
      
      npart = np.zeros(self.get_mxntpe(),np.uint32)
      
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
              idx0, idx1 = self.get_particles_limits(data_lenght)
            
            npart[i_type] = idx1-idx0   
            
          else:
            raise error.FormatError("%s is not in the file."%(h5_key))     
      
      
      # close the file
      mpi.mpi_barrier()
      fd.close()
      
      return npart
      

    def set_readable_arrays(self,ptypes=None):
      '''
      Set the arrays to be readable or not according to their presence in the blocks
      '''

      if ptypes is None:
        ptypes = list(range(self.get_mxntpe()))
        
      
      if mpi.mpi_NTask() > 1:
          fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
      else:
          fd = h5py.File(self.p_name_global[0],'r')
      

      # loop over all arrays flagged as read=True in self.arrays_props
      for name in self.arrays_props.keys():
        
        # skip array if a list of array is provided in self.array
        if self.arrays is not None:
          if not name in self.arrays:
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
        
      
  
    def load(self,name=None,ptypes=None,force=False):
      '''
      Load array from the hdf5 file.
      This function relays on the info stored self.arrays_props
      Here, we assume that npart is known and correct
      '''
      
      if ptypes is None:
        ptypes = list(range(self.get_mxntpe()))
      
      if name not in self.arrays_props:
        self.warning("load error : %s not defined in self.arrays_props"%(name))
        return
      
      dtype         = self.array_dtype(name)
      h5_key        = self.array_h5_key(name)
      default_value = self.array_default_value(name)
      dim           = self.array_dimension(name)
      
      if mpi.mpi_NTask() > 1:
          fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
      else:
          fd = h5py.File(self.p_name_global[0],'r')
      
      

            
      if not self.array_is_loaded(name) or force:
        self.message("loading %s"%name)
      

        # erase existing instance
        try: 
          delattr(self,name)
        except AttributeError:
          pass

        
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
                idx0, idx1 = self.get_particles_limits(data_lenght)
                
              # sanity check
              if idx1-idx0 !=self.npart[i_type]:
                raise error.FormatError("npart[%d]=%d is not equal to idx1-idx0=%d"%(i_type,npart[i_type],idx1-idx0))                 
                
              # read             
              data = block[h5_key][idx0:idx1].astype(dtype)
              
            
            # if the dataset is not present, compute from default value
            else:
              if dim==1:
                data = (default_value * np.ones(self.npart[i_type])).astype(dtype)
              else:
                data = (default_value * np.ones((self.npart[i_type],dim))).astype(dtype)
           
            try:
              setattr(self, name, np.concatenate((getattr(self, name), data)))
            except AttributeError:
              setattr(self, name, data)
          
    
      
      
      # set it as loaded        
      self.array_set_loaded(name)

      # close the file 
      mpi.mpi_barrier()
      fd.close()
        

        
        
        
    def read_arrays(self,ptypes=None):    
      '''
      Read arrays that must be loaded.
      '''      
      
      if ptypes is None:
        ptypes = list(range(self.get_mxntpe()))      
      
      # loop over all arrays flagged as read=True in self.arrays_props
      for name in self.arrays_props.keys():
        if self.array_read(name) and not self.array_is_loaded(name):
          self.load(name,ptypes)
      
 
 

    def _init_spec(self):
        # create an empty header (in case the user is creating a dataset)
        self._header = []

    def get_excluded_extension(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        return []

    def getParticleMatchingDict(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        
        index = {
            'gas':    0,
            'halo':   1,
            'disk':   2,
            'sink':   3,
            'stars':  4,
            'bndry':  2,
            'stars1': 4,
            'halo1':  1}
        
        return index 

    def check_spec_ftype(self):
        try:
            if mpi.NTask > 1:
                fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
            else:
                fd = h5py.File(self.p_name_global[0])
            
            
            test1 = False
            test2 = False
            
            header = fd["Header"]
            if not "Compactify_Version" in header.attrs:
              test1 = True

            #test1 = "Units" not in fd
            #test1 = test1 or "Unit temperature in cgs (U_T)" not in fd["Units"].attrs
            #test2 = "PartType0/Offset" in fd
            
            
            fd.close()
            if test1 or test2:
                raise error.FormatError("gizmo")

        except IOError as e:
            self.warning("gizmo not recognized: %s" % e)
            raise error.FormatError("gizmo")

    def set_pio(self, pio):
        """ Overwrite function
        """
        pNbody.Nbody.set_pio(self, "no")

    def get_read_fcts(self):
        return [self.read_particles]

    def get_write_fcts(self):
        return [self.write_particles]

    def get_mxntpe(self):
        return 6

    def get_header_translation(self):
        """
        Gives a dictionnary containing all the header translation.
        If a new variable is possible in the HDF5 format, only the translation
        is required for the reader/writer.
        As h5py is not supporting dictionnary, they need special care when reading/writing.
        """
        # dict containing all the main header variables (=> easy acces)
        # e.g. self.npart will contain NumPart_ThisFile
        header_var = {}

        # Size variables
        header_var["Header/NumPart_ThisFile"] = "npart"
        header_var["Header/NumPart_Total"] =  "npart" #   "npart_tot" check what must be done properly here
        header_var["Header/NumPart_Total_HighWord"] = "nallhw"
        header_var["Header/MassTable"] = "massarr"
        header_var["Header/NumFilesPerSnapshot"] = "num_files"
        header_var["Header/BoxSize"] = "boxsize"
        header_var["Header/Flag_Entropy_ICs"] = "flag_entr_ics"
        header_var["Header/Compactify_Version"] = "version"
        
        

        # Physics
        #header_var["Header/Scale-factor"] = "atime"
        #header_var["Header/Time"] = "time"
        header_var["Header/Redshift"] = "redshift"
        header_var["Header/Time"]     = "atime"
        header_var["Header/Redshift"] = "redshift"
         
        

        # Cosmology
        #header_var["Cosmology/Omega_b"] = "omegab"
        header_var["Header/Omega0"]      = "omega0"
        header_var["Header/OmegaLambda"] = "omegalambda"
        header_var["Header/HubbleParam"] = "hubbleparam"
        header_var["Header/Cosmorun"] = "cosmorun"        


        # Units
        #header_var["Units/Unit velocity in cgs (U_V)"] = "UnitVelocity_in_cm_per_s"
        #header_var["Units/Unit length in cgs (U_L)"] = "UnitLength_in_cm"
        #header_var["Units/Unit mass in cgs (U_M)"] = "UnitMass_in_g"
        #header_var["Units/Unit time in cgs (U_t)"] = "Unit_time_in_cgs"
        #header_var["Units/Unit temperature in cgs (U_T)"] = "Unit_temp_in_cgs"
        #header_var["Units/Unit current in cgs (U_I)"] = "Unit_current_in_cgs"



        return header_var

    def get_list_header(self):
        """
        Gives a list of header directory from self.get_header_translation
        """
        list_header = []
        trans = self.get_header_translation()
        for key, tmp in list(trans.items()):
            directory = key.split("/")[0]
            if directory not in list_header:
                list_header.append(directory)
        return list_header

    def get_array_translation(self):
        """
        Gives a dictionnary containing all the header translation with the particles type
        requiring the array.
        If a new variable is possible in the HDF5 format, the translation,
        default value (function get_array_default_values) and dimension (function get_array_dimension)
        are required for the reader/writer.
        """
        # hdf5 names -> pNbody names
        # [name, partType, type] where partType is a list of particles with the datas
        # True means all, False means none
        # and type is the data type
        ntab = {}
        
        ###################
        # common data
        ntab["Acceleration"] = ["acc", True, np.float32]
        ntab["Coordinates"] = ["pos", True, np.float32]
        ntab["Velocities"] = ["vel", True, np.float32]
        ntab["ParticleIDs"] = ["num", True, np.uint32]
        ntab["Masses"] = ["mass", True, np.float32]
        
        
        ntab["Potentials"] = ["pot", True, np.float32]
        
        ###################
        # gas data
        ntab["SmoothingLength"] = ["rsp_init", [0], np.float32]       # needed for ICs...
        ntab["InternalEnergy"] = ["u_init", [0], np.float32]          # needed for ICs...

        ntab["SmoothingLengths"] = ["rsp", [0], np.float32]
        ntab["InternalEnergies"] = ["u", [0], np.float32]
        ntab["Densities"] = ["rho", [0], np.float32]
        
        #ntab["Pressure"] = ["p", [0], np.float32]
        #ntab["Entropy"] = ["a", [0], np.float32]
        

                
        ###################
        # dm data
        ntab["Softenings"]        = ["softening",   [1], np.float32]   
        
        ###################
        # bndry data
        ntab["Softenings"]        = ["softening",   [2], np.float32]             
        
        
        ###################
        # stars data
        ntab["BirthMasses"]          = ["minit",   [4], np.float32]
        ntab["BirthScaleFactors"]    = ["tstar",   [4], np.float32]        
        ntab["StellarFormationTime"] = ["tstar",   [4], np.float32]
        ntab["BirthDensities"]       = ["rhostar", [4], np.float32]
        ntab["MetalMassFractions"]   = ["metals", [4], np.float32]
        #ntab["SmoothedMetalMassFractions"] = ["metals", [4], np.float32]
        ntab["ProgenitorIDs"]        = ["idp", [4], np.uint32]
        
        ntab["StellarAge"]           = ["age",   [4], np.float32]
        ntab["MH"]                   = ["mh",    [4], np.float32]
         
        ntab["SmoothingLengths"] = ["rsp",    [4], np.float32]

        
        ntab["MagVIS"] = ["MagVIS",    [4], np.float32]
        ntab["MagY"] = ["MagY",    [4], np.float32]
        ntab["MagJ"] = ["MagJ",    [4], np.float32]
        
        
        return ntab

    def get_array_default_value(self):
        """
        Gives a dictionary of default value for pNbody's arrays
        """
        # default value
        dval = {}
        dval["p"] = 0.0
        dval["a"] = 0.0
        dval["acc"] = 0.0
        dval["pos"] = 0.0
        dval["vel"] = 0.0
        dval["num"] = 0.0
        dval["mass"] = 0.0
        dval["pot"] = 0.0
        dval["u"] = 0.0
        dval["rho"] = 0.0
        dval["metals"] = 0.0
        dval["opt1"] = 0.0
        dval["opt2"] = 0.0
        dval["rsp"] = 0.0
        dval["softening"] = 0.0
        dval["minit"] = 0.0
        dval["tstar"] = 0.0
        dval["rhostar"] = 0.0
        dval["idp"] = 0.0
        dval["rsp_stars"] = 0.0
        dval["rho_stars"] = 0.0
        dval["snii_thermal_time"] = 0.0
        dval["snia_thermal_time"] = 0.0
        dval["entropy"] = 0.0
        dval["p"] = 0.0
        
        dval["MagVIS"] = 0.0
        dval["MagY"] = 0.0
        dval["MagJ"] = 0.0 
               
        return dval

    def get_array_dimension(self):
        """
        Gives a dictionary of dimension for pNbody's arrays
        """
        # dimension
        vdim = {}
        vdim["pos"] = 3
        vdim["vel"] = 3

        vdim["p"] = 1
        vdim["a"] = 1
        vdim["acc"] = 3
        vdim["num"] = 1
        vdim["mass"] = 1
        vdim["pot"] = 1
        vdim["u"] = 1
        vdim["rho"] = 1
        vdim["opt1"] = 1
        vdim["opt2"] = 1
        vdim["rsp"] = 1
        vdim["softening"] = 1
        vdim["minit"] = 1
        vdim["tstar"] = 1
        vdim["rhostar"] = 1
        vdim["idp"] = 1
        vdim["rsp_stars"] = 1
        vdim["rho_stars"] = 1
        vdim["snii_thermal_time"] = 1
        vdim["snia_thermal_time"] = 1
        vdim["entropy"] = 1
        vdim["p"] = 1
        vdim["metals"] = self.ChimieNelements
        
        vdim["MagVIS"] = 1
        vdim["MagY"]   = 1
        vdim["MagJ"]   = 1 
                
        return vdim

    def get_default_spec_vars(self):
        """
        return specific variables default values for the class
        """

        return {'massarr': np.array([0, 0, 0, 0, 0, 0]),
                'atime': 0.,
                'redshift': 0.,
                'flag_sfr': 0,
                'flag_feedback': 0,
                'npart_tot': np.array([0, 0, self.nbody, 0, 0, 0]),
                'npart': np.array([0, 0, self.nbody, 0, 0, 0]),
                'flag_cooling': 0,
                'num_files': 1,
                'boxsize': 0.,
                'omega0': 0.,
                'omegalambda': 0.,
                'hubbleparam': 0.,
                'flag_age': 0.,
                'flag_metals': 0.,
                'nallhw': np.array([0, 0, 0, 0, 0, 0]),
                'flag_entr_ics': 0,
                'flag_chimie_extraheader': 0,
                'critical_energy_spec': 0.,
                'empty': 48 * '',
                'comovingintegration': True,
                'hubblefactorcorrection': False,
                'comovingtoproperconversion': True,
                'ChimieNelements': 0,
                'utype':"swift",
                'cosmorun': 1,
                'version': 0
                }

    def get_particles_limits_from_npart(self, i):
        """ Gives the limits for a thread.
        In order to get the particles, slice them like this pos[start:end].
        :param int i: Particle type
        :returns: (start, end)
        """
        nber = float(self.npart_tot[i]) / mpi.mpi_NTask()
        start = int(mpi.mpi_ThisTask() * nber)
        end = int((mpi.mpi_ThisTask() + 1) * nber)
        return start, end
        
    def get_particles_limits(self,size):
        """ Gives the limits for a thread.
        In order to get the particles, slice them like this pos[start:end].
        :param int i: Particle type
        :returns: (start, end)
        """
        nber = float(size) / mpi.mpi_NTask()
        start = int(mpi.mpi_ThisTask() * nber)
        end = int((mpi.mpi_ThisTask() + 1) * nber)
        return start, end        
        

    def set_local_value(self):
        N = mpi.mpi_NTask()
        if N == 1:
            return
        part = len(self.npart_tot)
        for i in range(part):
            s, e = self.get_particles_limits_from_npart(i)
            self.npart[i] = e - s

    def get_massarr_and_nzero(self):
        """
        return massarr and nzero

        !!! when used in //, if only a proc has a star particle,
        !!! nzero is set to 1 for all cpu, while massarr has a length of zero !!!
        """

        if self.has_var('massarr') and self.has_var('nzero'):
            if self.massarr is not None and self.nzero is not None:
                self.warning("warning : get_massarr_and_nzero : here we use massarr and nzero %s %s"%(self.massarr,self.nzero))
                return self.massarr, self.nzero

        massarr = np.zeros(len(self.npart), float)
        nzero = 0

        # for each particle type, see if masses are equal
        for i in range(len(self.npart)):
            first_elt = sum((np.arange(len(self.npart)) < i) * self.npart)
            last_elt = first_elt + self.npart[i]

            if first_elt != last_elt:
                c = (self.mass[first_elt] ==
                     self.mass[first_elt:last_elt]).astype(int)
                if sum(c) == len(c):
                    massarr[i] = self.mass[first_elt]
                else:
                    nzero = nzero + len(c)

        return massarr.tolist(), nzero

    def read_particles(self, f):
        """
        read gadget file
        """
                
        from copy import deepcopy
        import time
                
        # go to the end of the file
        if f is not None:
            f.seek(0, 2)

        if mpi.mpi_NTask() > 1:
            fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
        else:
            fd = h5py.File(self.p_name_global[0],'r')

        ################
        # read header
        ################
        self.message("reading header...")

        # set default values
        default = self.get_default_spec_vars()
        
        
        for key, i in list(default.items()):
            setattr(self, key, i)

        # get values from snapshot
        trans = self.get_header_translation()

        list_header = self.get_list_header()
        

        for name in list_header:
            if name not in fd:
                continue
                
            # e.g. create self.npart with the value
            # fd["Header"].attrs["NumPart_ThisFile"]
                        
            for key in fd[name].attrs:
                                                                    
              
                full_name = name + "/" + key
                if full_name not in list(trans.keys()):
                    trans[full_name] = full_name

                tmp = fd[name].attrs[key]
                if isinstance(tmp, bytes) and tmp == "None":
                    tmp = None
                if isinstance(tmp, bytes):
                    tmp = tmp.decode('utf-8')
                setattr(self, trans[full_name], tmp)
                
                self.message("%s %s >> %s %s"%(name,key,trans[full_name],tmp),verbosity=2)
                
        

        # additional stuffs
        # we assume its a cosmo run
        
        
        # additional stuffs
        if self.has_var('cosmorun'):
          if self.cosmorun==1:
            self.cosmorun=1
            self.HubbleFactorCorrectionOn()
            self.ComovingToProperConversionOn()
          else:
            self.cosmorun=0
            self.HubbleFactorCorrectionOff()
            self.ComovingToProperConversionOff()            
        else:   
          self.cosmorun=1
          self.HubbleFactorCorrectionOn()
          self.ComovingToProperConversionOn()                 


        
        # get local value from global ones
        self.set_local_value()
        
       

        
        
        
        ###############
        # read units
        ###############
        self.message("reading units...")

        # define system of units
        params = {}
        params['UnitLength_in_cm']         = 3.085678e21
        params['UnitVelocity_in_cm_per_s'] = 1.0e5
        params['UnitMass_in_g']            = 1.989e43
        self.localsystem_of_units = units.Set_SystemUnits_From_Params(params)
        
        mpi.mpi_barrier()
        fd.close()
        
        ################
        # read particles
        ################

                
        # get npart from the blocks
        self.npart = self.get_npart_from_dataset(ptypes=self.ptypes)
        
        # check that arrays are present
        self.set_readable_arrays(ptypes=self.ptypes)
        
        # load all arrays according to the information
        # provided by self.arrays_props
        self.read_arrays(ptypes=self.ptypes)
                

        # set tpe
        self.tpe = np.array([], np.int32)
        for i in range(len(self.npart)):
            self.tpe = np.concatenate((self.tpe, np.ones(self.npart[i]) * i))

        # compute nzero
        nzero = 0
        mass = np.array([])

        for i in range(len(self.npart)):
            if self.massarr[i] == 0:
                nzero = nzero + self.npart[i]
            else:
                self.warning("Massarr is not supported! Please specify the mass of all the particles!",verbosity=2)

        self.nzero = nzero

        mpi.mpi_barrier()
        
        


        # specific final conversions
        

          
          


    def write_particles(self, f):
        """
        specific format for particle file
        """
        # go to the end of the file
        if f is not None:
            f.seek(0, 2)
            

        name = "Unit_temp_in_cgs"
        if not hasattr(self, name):
            setattr(self, name, 1.0)

        name = "Unit_current_in_cgs"
        if not hasattr(self, name):
            setattr(self, name, 1.0)

        import h5py
        # not clean, but work around pNbody
        filename = self.p_name_global[0]
        # open file
        if mpi.mpi_NTask() > 1:
            from mpi4py import MPI
            h5f = h5py.File(filename, "w", driver="mpio", comm=MPI.COMM_WORLD)
        else:
            h5f = h5py.File(filename, "w")

        # add units to the usual gh5 struct
        if hasattr(self, "unitsparameters"):
            units = self.unitsparameters.get_dic()
            for key, i in list(units.items()):
                if not hasattr(self, key):
                    setattr(self, key, i)

        if hasattr(self,"UnitVelocity_in_cm_per_s") and hasattr(self,"UnitLength_in_cm"):
          self.Unit_time_in_cgs = self.UnitLength_in_cm / self.UnitVelocity_in_cm_per_s
        
 
          

        ############
        # HEADER
        ############
        self.message("Writing header...")

        list_header = self.get_list_header()
        trans = self.get_header_translation()
        # cheat a little bit in order to get the real number of particles in
        # this file
        trans["Header/NumPart_ThisFile"] = "npart_tot"
        
        for name in list_header:
            h5f.create_group(name)
        
                    
            
        for key in self.get_list_of_vars():
          
            if key in list(trans.values()):
                ind = list(trans.values()).index(key)
                name, hdf5 = list(trans.keys())[ind].split("/")
                value = getattr(self, key)
                
            
                if type(value) is not str:
                  value = np.array(value)
                else:
                  value = np.array(value,dtype="S")  
                  
                if value.shape == ():
                  value = np.array([value])
                  
                
                if not isinstance(value, dict):
                    if value is None:
                        h5f[name].attrs[hdf5] = "None"
                    else:
                        h5f[name].attrs[hdf5] = value

        ##############
        # PARTICULES
        ##############
        self.message("Writing particles...")

        for i in range(len(self.npart)):
            if self.massarr[i] != 0:
              self.warning("Massarr is not supported! Please specify the mass of all the particles!",verbose=2)

        ntab = self.get_array_translation()
        
                
        # get particles type present
        type_part = []
        for i in range(len(self.npart)):
            if self.npart[i] > 0:
                type_part.append(i)

        # write particles
        for i in type_part:
            if mpi.mpi_NTask() > 1:
                init, end = self.get_particles_limits_from_npart(i)                
            self.message("Writing particles (type %i)..." % i,verbose=2)
            group = "PartType%i" % i
            grp = h5f.create_group(group)
            nb_sel = self.select(i)                                   # this is really bad as we duplicate the model
            
            for key, j in list(ntab.items()):
                varname = j[0]
                var_type = j[1]
                
  
                if (var_type is True) or i in var_type:
                    if hasattr(nb_sel, varname):
                      
                        # get and transform type
                        tmp = getattr(nb_sel, varname)
                        if tmp is None:
                            continue
                        tmp = tmp.astype(j[2])
                        # create dataset
                        size = list(tmp.shape)
                        size[0] = self.npart_tot[i]
                        if mpi.mpi_NTask() > 1:
                            dset = grp.create_dataset(key, size, dtype=j[2])
                            dset[init:end] = tmp
                        else:
                            h5f[group][key] = tmp

        

        h5f.close()
        
        

        
