###########################################################################################
#  package:   pNbody
#  file:      gh5.py
#  brief:     gh5 format (Gear in HDF5)
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>, Loic Hausammann <loic_hausammann@hotmail.com>
#
# This file is part of pNbody.
###########################################################################################

# 
#
#



##########################################################################
#
# GEAR HDF5 CLASS
#
##########################################################################

import sys
import numpy as np

import pNbody
from pNbody import mpi, error, units
import h5py


class Nbody_arepo:

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
            'stars':  4,
            'bndry': 2}
        
        return index         

    def check_spec_ftype(self):
        try:
            if mpi.NTask > 1:
                fd = h5py.File(self.p_name_global[0],'r',driver="mpio",comm=MPI.COMM_WORLD)
            else:
                fd = h5py.File(self.p_name_global[0])

            test = "ExpansionFactor" not in fd["Header"].attrs

            fd.close()
            
            if test:
                raise error.FormatError("arepo")

        except IOError as e:
            if self.verbose > 1:
                print("arepo not recognized: %s" % e)
            raise error.FormatError("arepo")
            
            

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
        #header_var["Header/Code"] = "Gear"
        
        # Size variables
        header_var["Header/NumPart_ThisFile"] = "npart"
        header_var["Header/NumPart_Total"] = "nall"
        header_var["Header/NumPart_Total_HighWord"] = "nallhw"
        
        header_var["Header/MassTable"] = "massarr"
        header_var["Header/NumFilesPerSnapshot"] = "num_files"
        header_var["Header/BoxSize"] = "boxsize"
        
        header_var["Header/Git_commit"] = "git_commit"
        header_var["Header/Git_date"]   = "git_date"


        # Physics
        header_var["Header/ExpansionFactor"] = "atime"
        header_var["Header/Redshift"] = "redshift"
        header_var["Header/OmegaBaryon"] = "omegabaryon"
        header_var["Header/Omega0"] = "omega0"
        header_var["Header/OmegaLambda"] = "omegalambda"
        header_var["Header/HubbleParam"] = "hubbleparam"
        header_var["Header/Cosmorun"] = "cosmorun"




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
        # common data
        ntab["Coordinates"]   = ["pos", True, np.float32]
        ntab["Velocities"]    = ["vel", True, np.float32]
        ntab["ParticleIDs"]   = ["num", True, np.uint32]
        ntab["Masses"]        = ["mass", True, np.float32]

        # stars data        
        ntab["StellarHsml"]           = ["rsp", [4], np.float32]
        ntab["LookbackFormed"]        = ["age", [4], np.float32]
        ntab["Mmetal"]                = ["metallicity",  [4], np.float32]
        ntab["mh"]                    = ["mh",  [4], np.float32]

        
        return ntab


    def get_array_default_value(self):
        """
        Gives a dictionary of default value for pNbody's arrays
        """
        # default value
        dval = {}
        dval["pos"] = 0.0
        dval["vel"] = 0.0
        dval["num"] = 0.0
        dval["mass"] = 0.0
        dval["u"] = 0.0
        dval["rho"] = 0.0
        dval["metals"] = 0.0
        dval["mh"] = 0.0
        dval["opt1"] = 0.0
        dval["opt2"] = 0.0
        dval["rsp"] = 0.0
        dval["minit"] = 0.0
        dval["tstar"] = 0.0
        dval["idp"] = 0.0
        dval["rsp_stars"] = 0.0
        dval["metals_stars"] = 0.0
        dval["metallicity_stars"] = 0.0
        dval["rho_stars"] = 0.0
        dval["snii_thermal_time"] = 0.0
        dval["snia_thermal_time"] = 0.0
        dval["xdi"] = 0.
        dval["xdii"] = 0.
        dval["xe"] = 0.
        dval["xh2i"] = 0.
        dval["xh2ii"] = 0.
        dval["xhdi"] = 0.
        dval["xhi"] = 0.
        dval["xhii"] = 0.
        dval["xhm"] = 0.
        dval["xhei"] = 0.
        dval["xheii"] = 0.
        dval["xheiii"] = 0.
        dval["Lr"] = 0.0
        dval["Lv"] = 0.0
        dval["Lb"] = 0.0
        return dval

    def get_array_dimension(self):
        """
        Gives a dictionary of dimension for pNbody's arrays
        """
        # dimension
        vdim = {}
        vdim["pos"] = 3
        vdim["vel"] = 3

        vdim["num"] = 1
        vdim["mass"] = 1
        vdim["u"] = 1
        vdim["rho"] = 1
        vdim["opt1"] = 1
        vdim["opt2"] = 1
        vdim["rsp"] = 1
        vdim["minit"] = 1
        vdim["tstar"] = 1
        vdim["idp"] = 1
        vdim["rsp_stars"] = 1
        vdim["rho_stars"] = 1
        vdim["snii_thermal_time"] = 1
        vdim["snia_thermal_time"] = 1
        vdim["xdi"] = 1
        vdim["xdii"] = 1
        vdim["xe"] = 1
        vdim["xh2i"] = 1
        vdim["xh2ii"] = 1
        vdim["xhdi"] = 1
        vdim["xhi"] = 1
        vdim["xhii"] = 1
        vdim["xhm"] = 1
        vdim["xhei"] = 1
        vdim["xheii"] = 1
        vdim["xheiii"] = 1

        vdim["metals"] = self.ChimieNelements
        vdim["metals_stars"] = self.ChimieNelements
        vdim["mh"] = 1
        vdim["Lr"] = 1
        vdim["Lv"] = 1
        vdim["Lb"] = 1        
        return vdim

    def get_default_spec_vars(self):
        '''
        return specific variables default values for the class
        '''

        return {'massarr': np.array([0, 0, self.nbody, 0, 0, 0]),
                'atime': 0.,
                'redshift': 0.,
                'flag_sfr': 0,
                'flag_feedback': 0,
                'nall': np.array([0, 0, self.nbody, 0, 0, 0]),
                'npart': np.array([0, 0, self.nbody, 0, 0, 0]),
                'flag_cooling': 0,
                'num_files': 1,
                'boxsize': 0.,
                'omega0': 0.,
                'omegalambda': 0.,
                'hubbleparam': 0.,
                'flag_age': 0.,
                'hubbleparam': 0.,
                'flag_metals': 0.,
                'nallhw': np.array([0, 0, 0, 0, 0, 0]),
                'flag_entr_ic': 0,
                'flag_chimie_extraheader': 0,
                'critical_energy_spec': 0.,
                'flag_thermaltime': 0,
                'empty': '',
                'comovingintegration': True,
                'hubblefactorcorrection': True,
                'comovingtoproperconversion': True,
                'ChimieNelements': 0,
                'cosmorun': 1,
                'utype':"gear",
                }

    def get_particles_limits(self, i):
        """ Gives the limits for a thread.
        In order to get the particles, slice them like this pos[start:end].
        :param int i: Particle type
        :returns: (start, end)
        """
        nber = float(self.nall[i]) / mpi.mpi_NTask()
        start = int(mpi.mpi_ThisTask() * nber)
        end = int((mpi.mpi_ThisTask() + 1) * nber)
        return start, end

    def set_local_value(self):
        N = mpi.mpi_NTask()
        if N == 1:
            return
        part = len(self.nall)
        for i in range(part):
            s, e = self.get_particles_limits(i)
            self.npart[i] = e - s

    def get_massarr_and_nzero(self):
        """
        return massarr and nzero

        !!! when used in //, if only a proc has a star particle,
        !!! nzero is set to 1 for all cpu, while massarr has a length of zero !!!
        """

        if self.has_var('massarr') and self.has_var('nzero'):
            if self.massarr is not None and self.nzero is not None:
                if mpi.mpi_IsMaster():
                    print((
                        "warning : get_massarr_and_nzero : here we use massarr and nzero",
                        self.massarr,
                        self.nzero))
                return self.massarr, self.nzero

        massarr = zeros(len(self.npart), float)
        nzero = 0

        # for each particle type, see if masses are equal
        for i in range(len(self.npart)):
            first_elt = sum((arange(len(self.npart)) < i) * self.npart)
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
        '''
        read gadget file
        '''
        from copy import deepcopy

        # go to the end of the file
        if f is not None:
            f.seek(0, 2)

        import h5py
        if mpi.mpi_NTask() > 1:
            fd = h5py.File(
                self.p_name_global[0],
                'r',
                driver="mpio",
                comm=mpi.comm)
        else:
            fd = h5py.File(self.p_name_global[0], 'r')

        ################
        # read header
        ################
        if self.verbose > 0 and mpi.mpi_IsMaster():
            print("reading header...")

        # set default values
        default = self.get_default_spec_vars()
        for key, i in list(default.items()):
            setattr(self, key, i)

        # get values from snapshot
        trans = self.get_header_translation()

        list_header = self.get_list_header()

        for name in list_header:
            # e.g. create self.npart with the value
            # fd["Header"].attrs["NumPart_ThisFile"]
            for key in fd[name].attrs:
                full_name = name + "/" + key
                if full_name not in list(trans.keys()):
                    print((
                        "'%s' key not recognized, please add it to config/format/gh5.py file in get_header_translation" %
                        full_name))
                    trans[full_name] = key
                tmp = fd[name].attrs[key]
                if isinstance(tmp, bytes) and tmp == "None":
                    tmp = None
                if isinstance(tmp, bytes):
                    tmp = tmp.decode('utf-8', "ignore")
                setattr(self, trans[full_name], tmp)




        # get local value from global ones
        self.set_local_value()

        ###############
        # read units
        ###############
        if self.verbose > 0 and mpi.mpi_IsMaster():
            print("reading units...")


        # define system of units
        # ignore units
        #params = {}
        #params['UnitLength_in_cm']         = 3.085678e21 * 1000
        #params['UnitVelocity_in_cm_per_s'] = 1.0e5
        #params['UnitMass_in_g']            = 1.989e43
        #self.localsystem_of_units = units.Set_SystemUnits_From_Params(params)
 

        ################
        # read particles
        ################

        if self.verbose > 0 and mpi.mpi_IsMaster():
            print("reading particles...")

        def getsize(n, dim):
            if dim == 1:
                return (n,)
            if dim > 1:
                return (n, dim)

        list_of_vectors = []

        # check what vector we needs to be created

        ntab = self.get_array_translation()
        vdim = self.get_array_dimension()
        dval = self.get_array_default_value()

        for i, n in enumerate(self.npart):

            if n == 0:
                continue

            if list(fd.keys()).count("PartType%d" % i) == 0:
                raise IOError("type=%d n=%d but group %s is not found !" %
                              (i, n, "PartType%d" % i))

            # loop over dataset
            block = fd["PartType%d" % i]
            for key in list(block.keys()):
                if key not in ntab:
                    print("get a dataset with name %s but no such key in ntab" %key)
                    
                    continue

                varname = ntab[key][0]

                if self.has_var(varname):
                    pass  # do nothing
                else:
                    setattr(self, varname, None)

                # record the variable in a list
                if list_of_vectors.count(varname) == 0:
                    list_of_vectors.append(varname)

        # read the tables
        for i, n in enumerate(self.npart):

            if n == 0:
                continue

            if self.verbose > 1 and mpi.mpi_IsMaster():
                print(("Reading particles (type %i)..." % i))

            remaining_vectors = deepcopy(list_of_vectors)

            # loop over dataset
            block = fd["PartType%d" % i]
            if mpi.mpi_NTask() > 1:
                init, end = self.get_particles_limits(i)

            for key in list(block.keys()):
                if key not in ntab:
                    continue
                varname = ntab[key][0]
                if self.skip_io_block(varname):
                    if self.verbose > 1:
                        print(("Skipping %s block" % varname))
                    continue
                else:
                    if self.verbose > 1:
                        print("Reading %s block" % varname)
                var = getattr(self, varname)

                if mpi.mpi_NTask() > 1:
                    data = block[key][init:end]
                else:
                    data = block[key][()]
                if var is not None:
                    setattr(self, varname, np.concatenate(
                        (getattr(self, varname), data)))
                else:
                    setattr(self, varname, data)
                
                
                
                remaining_vectors.remove(varname)

            # loop over vectors absent from the block
            for varname in remaining_vectors:
                var = getattr(self, varname)
                data = (
                    np.ones(getsize(n, vdim[varname])) *
                    dval[varname]).astype(np.float32)
                if var is not None:
                    setattr(self, varname, np.concatenate(
                        (getattr(self, varname), data)))
                else:
                    setattr(self, varname, data)

        # set tpe
        self.tpe = np.array([], np.int32)
        for i in range(len(self.npart)):
            self.tpe = np.concatenate((self.tpe, np.ones(self.npart[i]) * i))

        # compute nzero
        nzero = 0
        mass = np.array([])

        for i in range(len(self.npart)):
            if self.massarr is None or self.massarr[i] == 0:
                nzero = nzero + self.npart[i]
            else:
              if self.verbose > 0 and mpi.mpi_IsMaster():
                print(
                    "Massarr is not supported! Please specify the mass of all the particles!")

        self.nzero = nzero

        mpi.mpi_barrier()
        fd.close()
        
        
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
        
        
        

    def write_particles(self, f):
        '''
        specific format for particle file
        '''
        # go to the end of the file
        if f is not None:
            f.close()

        # not clean, but work around pNbody
        filename = self.p_name_global[0]
        # open file
        if mpi.mpi_NTask() > 1:
            h5f = h5py.File(filename, "w", driver="mpio", comm=mpi.comm)
        else:
            h5f = h5py.File(filename, "w")

        # add units to the usual gh5 struct
        if hasattr(self, "unitsparameters"):
            units = self.unitsparameters.get_dic()
            for key, i in list(units.items()):
                if not hasattr(self, key):
                    setattr(self, key, i)

        if hasattr(self, "UnitVelocity_in_cm_per_s") and hasattr(
                self, "UnitLength_in_cm"):
            self.Unit_time_in_cgs = self.UnitLength_in_cm / self.UnitVelocity_in_cm_per_s

        ############
        # HEADER
        ############
        if self.verbose > 0 and mpi.mpi_IsMaster():
            print("Writing header...")

        if self.massarr is None:
            self.massarr = np.zeros(len(self.npart))

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
                if not isinstance(value, dict):
                    if value is None:
                        h5f[name].attrs[hdf5] = "None"
                    else:
                        print(name, hdf5, value)
                        if hdf5 == "ChimieLabels":
                            value = ','.join(value)
                        h5f[name].attrs[hdf5] = value


        ##############
        # PARTICULES
        ##############
        if self.verbose > 0 and mpi.mpi_IsMaster():
            print("Writing particles...")

        for i in range(len(self.npart)):
            if self.massarr is not None and self.massarr[i] != 0:
              if self.verbose > 0 and mpi.mpi_IsMaster():
                print(
                    "Massarr is not supported! Please specify the mass of all the particles!")

        ntab = self.get_array_translation()
        # get particles type present
        type_part = []
        for i in range(len(self.npart)):
            if self.npart[i] > 0:
                type_part.append(i)

        # write particles
        for i in type_part:
            if mpi.mpi_NTask() > 1:
                init, end = self.get_particles_limits(i)
            if self.verbose > 1 and mpi.mpi_IsMaster():
                print("Writing particles (type %i)..." % i)
            group = "PartType%i" % i
            grp = h5f.create_group(group)
            nb_sel = self.select(i)
            for key, j in list(ntab.items()):
                            
                varname = j[0]
                var_type = j[1]
                
                if (var_type is True) or i in var_type:
                    if hasattr(nb_sel, varname) and getattr(nb_sel, varname) is not None:
                        # get and transform type
                        tmp = getattr(nb_sel, varname)
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
