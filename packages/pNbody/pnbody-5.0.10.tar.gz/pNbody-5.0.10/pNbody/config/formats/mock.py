###########################################################################################
#  package:   pNbody
#  file:      mock.py
#  brief:     MOCK file format
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
from pNbody import h5utils
from pNbody import mpi, error, units, h5utils

try:				# all this is useful to read files
    from mpi4py import MPI
except BaseException:
    MPI = None



class Nbody_mock:
  
  
    def get_default_arrays_props(self):
      '''
      get the default properties of arrays considered
      This function is basically used to initialize self.arrays_props
      
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
                          

      aprops["rsp"] =  {
                        "h5name"  :     "SmoothingLengths", 
                        "dtype"   :     np.float32,                        
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
                      
      aprops["mh"] =  {
                        "h5name"  :     "StellarMetallicity", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }

                                            
      aprops["MagG"] =  {
                        "h5name"  :     "MagG", 
                        "dtype"   :     np.float32,                        
                        "dim"     :     1,
                        "ptypes"  :     [4], 
                        "read"    :     True,
                        "write"   :     True, 
                        "default" :     0,
                        "loaded"  :     False
                      }


      return aprops  
    

    def get_default_spec_vars(self):
        """
        return specific variables default values for the class
        """
        

        return {'massarr': np.array([0, 0, 0, 0, 0, 0]),
                'atime': 1.,
                'redshift': 0.,
                'npart_tot': np.array([0, 0, self.nbody, 0, 0, 0]),
                'npart': np.array([0, 0, self.nbody, 0, 0, 0]),
                'num_files': 1,
                'nallhw': np.array([0, 0, 0, 0, 0, 0]),
                'command_line':"none",
                'gittag':"none",
                'date':"none",
                'username':"username",
                'ftype':"mock",
                }    
                

    def load(self,name=None,ptypes=None,force=False):
      '''
      The function in charge of loading arrays on demand.
      Here we use the generic hdf5 one.
      '''
      self.loadFromHDF5(name=name,ptypes=ptypes,force=force)

    
    def dump(self,aname=None):
      '''
      The function in charge of duming the array aname 
      to a file on demand.
      '''
      self.dumpToHDF5(aname=aname)
      
 

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
        
        index = {'stars': 4}
        
        return index 

    def check_spec_ftype(self):
        self.message("checking mock format...")

        try:

            fd = h5utils.openFile(self.p_name_global[0])                

            if "Header" not in fd:
              raise error.FormatError("mock")
            
            if "Format" not in fd["Header"].attrs:
              raise error.FormatError("mock")
            
            if fd["Header"].attrs["Format"] != "mock":
              raise error.FormatError("mock")


        except IOError as e:
            self.message("mock not recognized: %s" % e)
            raise error.FormatError("mock")

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

        # File type 
        header_var["Header/Format"] = "ftype"

        # Size variables
        header_var["Header/NumPart_ThisFile"] = "npart"
        header_var["Header/NumPart_Total"] =  "npart_tot"
        header_var["Header/NumPart_Total_HighWord"] = "nallhw"
        header_var["Header/MassTable"] = "massarr"
        header_var["Header/NumFilesPerSnapshot"] = "num_files"

        # Physics
        header_var["Header/Time"] = "time"
        
        # General Info
        header_var["Header/Command_line"] = "command_line"
        header_var["Header/GitTag"]   = "gittag"
        header_var["Header/UserName"] = "username"
        header_var["Header/Date"]     = "date"
        

        # Units
        header_var["Units/Unit length in cgs (U_L)"] = "UnitLength_in_cm"
        header_var["Units/Unit mass in cgs (U_M)"] = "UnitMass_in_g"
        header_var["Units/Unit time in cgs (U_t)"] = "Unit_time_in_cgs"
        header_var["Units/Unit temperature in cgs (U_T)"] = "Unit_temp_in_cgs"
        header_var["Units/Unit current in cgs (U_I)"] = "Unit_current_in_cgs"

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


                  

    def get_massarr_and_nzero(self):
        """
        return massarr and nzero

        !!! when used in //, if only a proc has a star particle,
        !!! nzero is set to 1 for all cpu, while massarr has a length of zero !!!
        """

        if self.has_var('massarr') and self.has_var('nzero'):
          if self.massarr is not None and self.nzero is not None:
            self.message("warning : get_massarr_and_nzero : here we use massarr and nzero",self.massarr,self.nzero,verbosity=2)
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


        fd = h5utils.openFile(self.p_name_global[0],'r')    
            

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
        

        ##################################################
        # read cosmorun and set specific units corrections
        ##################################################
        
        # mock does not consider the Hubble parameter in its units
        self.setComovingIntegrationOff()  # obsolete
        self.HubbleFactorCorrectionOff()
        self.ComovingToProperConversionOff()
 

        
        ###############
        # read units
        ###############
        self.message("reading units...")

        # define system of units
        params = {}

        # consider that if we have length unit, we should have them all
        if hasattr(self, "UnitLength_in_cm"):
            params['UnitLength_in_cm'] = float(self.UnitLength_in_cm)
            if hasattr(self, "UnitVelocity_in_cm_per_s"):
                params['UnitVelocity_in_cm_per_s'] = float(
                    self.UnitVelocity_in_cm_per_s)
            else:
                self.UnitVelocity_in_cm_per_s = float(
                    self.UnitLength_in_cm) / float(self.Unit_time_in_cgs)
                params['UnitVelocity_in_cm_per_s'] = self.UnitVelocity_in_cm_per_s
            params['UnitMass_in_g'] = float(self.UnitMass_in_g)
            self.localsystem_of_units = units.Set_SystemUnits_From_Params(
                params)
        else:
            self.message("WARNING: snapshot seems broken! There is no units!")
        
        
        # close the file
        h5utils.closeFile(fd)
        
        
        ################
        # read particles
        ################
        
        self.message("reading particles...")
                
        # get npart from the blocks
        self.npart = h5utils.get_npart_from_dataset(self.p_name_global[0],self._AM.array_h5_key('pos'),self.get_mxntpe(),ptypes=self.ptypes)
        
        # check that arrays are present
        self._AM.setReadableArraysFromHDFH5File(self.p_name_global[0],arrays=self.arrays,ptypes=self.ptypes)
        
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


        #############################
        # specific final conversions
        #############################        
        
        
        if hasattr(self, 'idp'):
          self.idp = self.idp.astype(int) 
        
        if type(self.atime) == np.ndarray:
          self.atime = self.atime[0]
          
        if type(self.redshift) == np.ndarray:
          self.redshift = self.redshift[0]
        

          
          
          
                    

    def write_particles(self, f):
        """
        specific format for particle file
        """
        
        self.update_creation_info()
        
        
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
        h5f = h5utils.openFile(filename,'w')    

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
        
        for name in list_header:
            h5f.create_group(name)
                    
            
        for key in self.get_list_of_vars():
          
          
            if key in list(trans.values()):
                ind = list(trans.values()).index(key)
                name, hdf5 = list(trans.keys())[ind].split("/")
                value = getattr(self, key)
                                
                # !!! force value of npart to be npart_tot (to be improved)
                if mpi.mpi_NTask() > 1: 
                  if key=="npart":
                    value = self.npart_tot
                
                
                if type(value) is str:
                  pass
                elif type(value) is list:
                  value = np.array(value)  
                
                # if the value is different than the dict class
                if not isinstance(value, dict):
                    if value is None:
                        h5f[name].attrs[hdf5] = "None"
                    else:
                        h5f[name].attrs[hdf5] = value



        h5utils.closeFile(h5f)
        
        ##############
        # PARTICULES
        ##############
        self.message("Writing particles...")
            
            
        # loop over all arrays
        for aname in self.get_list_of_arrays():
          if aname in self._AM.arrays():
          
            if self._AM.array_write(aname):
              # dump the array
              self.dump(aname)
            else:
              self.warning("array %s is not set as to be written."%aname,verbosity=2)
          
          else:
            self.warning("array %s is not stored in the array manager."%aname,verbosity=2)    
              
