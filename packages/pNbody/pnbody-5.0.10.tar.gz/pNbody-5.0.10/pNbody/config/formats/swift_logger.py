###########################################################################################
#  package:   pNbody
#  file:      swift_logger.py
#  brief:
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>, Loic Hausammann <loic_hausammann@hotmail.com>
#
# This file is part of pNbody.
###########################################################################################


##########################################################################
#
# SWIFT LOGGER CLASS
#
##########################################################################

import sys
import types
import string
import numpy as np
import h5py
from copy import deepcopy

import pNbody
from pNbody import mpi, error, units, thermodyn
from astropy import units
try:				# all this is useful to read files
    from mpi4py import MPI
except BaseException:
    MPI = None

class Nbody_logger:

    def _init_spec(self):
        return

    def get_excluded_extension(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        return []

    def check_spec_ftype(self):
        try:
            import h5py
            if mpi.NTask > 1:
                fd = h5py.File(
                    self.p_name_global[0],
                    'r',
                    driver="mpio",
                    comm=MPI.COMM_WORLD)
            else:
                fd = h5py.File(self.p_name_global[0],'r')
            test = "PartType0/Offset" not in fd
            fd.close()
            if test:
                raise error.FormatError("logger")
        except IOError as e:
            self.warning("logger not recognized: %s" % e)
            raise error.FormatError("logger")

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

    def get_default_spec_vars(self):
        """
        return specific variables default values for the class
        """

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
                'empty': 48 * '',
                'comovingintegration': None,
                'ChimieNelements': 0,
                }

    def get_massarr_and_nzero(self):
        """
        return massarr and nzero

        !!! when used in //, if only a proc has a star particle,
        !!! nzero is set to 1 for all cpu, while massarr has a length of zero !!!
        """

    def getHeaderTranslation(self):
        header_var = {}

        # Size variables
        header_var["Header/NumPart_ThisFile"] = "npart"
        header_var["Header/NumPart_Total"] = "nall"
        header_var["Header/NumPart_Total_HighWord"] = "nallhw"
        header_var["Header/MassTable"] = "massarr"
        header_var["Header/NumFilesPerSnapshot"] = "num_files"
        header_var["Header/BoxSize"] = "boxsize"
        header_var["Header/Time Offset"] = "time_offset"

        # Physics
        header_var["Header/Time"] = "atime"

        # Units
        header_var["Units/Unit length in cgs (U_L)"] = "UnitLength_in_cm"
        header_var["Units/Unit mass in cgs (U_M)"] = "UnitMass_in_g"
        header_var["Units/Unit time in cgs (U_t)"] = "Unit_time_in_cgs"
        header_var["Units/Unit temperature in cgs (U_T)"] = "Unit_temp_in_cgs"
        header_var["Units/Unit current in cgs (U_I)"] = "Unit_current_in_cgs"

        # Code
        header_var["Code/Code"] = "Unit_current_in_cgs"
        header_var["Code/CFLAGS"] = "cflags"
        header_var["Code/Code Version"] = "code_version"
        header_var["Code/Compiler Name"] = "compiler_name"
        header_var["Code/Compiler Version"] = "compiler_version"
        header_var["Code/Configuration options"] = "config_options"
        header_var["Code/FFTW library version"] = "fftw_lib_version"
        header_var["Code/Git Branch"] = "git_branch"
        header_var["Code/Git Date"] = "git_date"
        header_var["Code/Git Revision"] = "git_revision"
        header_var["Code/HDF5 library version"] = "hdf5_lib_version"
        header_var["Code/MPI library"] = "mpi_lib"

        # HydroScheme
        header_var["HydroScheme/Adiabatic index"] = "adiabatic_index"
        header_var["HydroScheme/CFL parameter"] = "cfl_parameter"
        header_var["HydroScheme/Dimension"] = "dimension"
        header_var["HydroScheme/Kernel delta N_ngb"] = "kernel_delta_n_ngb"
        header_var["HydroScheme/Kernel eta"] = "kernel_eta"
        header_var["HydroScheme/Kernel function"] = "kernel_function"
        header_var["HydroScheme/Kernel target N_ngb"] = "kernel_target_n_ngb"
        header_var["HydroScheme/Max ghost iterations"] = "max_ghost_iterations"
        header_var["HydroScheme/Maximal smoothing length"] = "maximal_smoothing_length"
        header_var["HydroScheme/Scheme"] = "scheme"
        header_var["HydroScheme/Smoothing length tolerance"] = "smoothing_length_tolerance"
        header_var["HydroScheme/Thermal Conductivity Model"] = "thermal_conductivity_model"
        header_var["HydroScheme/Viscosity Model"] = "viscosity_model"
        header_var["HydroScheme/Viscosity alpha"] = "viscosity_alpha"
        header_var["HydroScheme/Viscosity beta"] = "viscosity_beta"
        header_var["HydroScheme/Volume log(max(delta h))"] = "volume_log"
        header_var["HydroScheme/Volume max change time-step"] = "volume_max_change"

        # Swift directory
        header_var["RuntimePars/PeriodicBoundariesOn"] = "periodic"

        return header_var

    def getArrayTranslation(self):
        array_var = {}

        array_var["ParticleIDs"] = "num"
        array_var["Offset"] = "offset"

        return array_var

    def getArrayDefaultValue(self):
        """
        Gives a dictionary of default value for pNbody's arrays
        """
        # default value
        dval = {}
        dval["ParticleIDs"] = -1
        dval["Offset"] = -1
        return dval

    def getArrayDimension(self):
        """
        Gives a dictionary of dimension for pNbody's arrays
        """
        # dimension
        vdim = {}
        vdim["ParticleIDs"] = 1
        vdim["Offset"] = 1
        return vdim

    def get_list_header(self):
        """
        Gives a list of header directory from self.get_header_translation
        """
        list_header = []
        trans = self.getHeaderTranslation()
        for key, tmp in list(trans.items()):
            directory = key.split("/")[0]
            if directory not in list_header:
                list_header.append(directory)
        return list_header

    def read_particles(self, f):
        """
        read logger file
        """
        import libswiftlogger as logger

        if f is not None:
            f.seek(0, 2)

        fd = h5py.File(self.p_name_global[0], 'r')

        trans = self.getHeaderTranslation()
        list_header = self.get_list_header()

        for name in list_header:
            # e.g. create self.npart with the value
            # fd["Header"].attrs["NumPart_ThisFile"]
            for key in fd[name].attrs:
                full_name = name + "/" + key
                if full_name not in list(trans.keys()):
                    self.warning(
                        "'%s' key not recognized, please add it to config/format/swift_logger.py file in get_header_translation" %
                        full_name)
                else:
                    setattr(self, trans[full_name], fd[name].attrs[key])

        n = np.sum(self.npart)

        list_of_vectors = []

        ntab = self.getArrayTranslation()
        vdim = self.getArrayDimension()
        dval = self.getArrayDefaultValue()

        for i, n in enumerate(self.npart):

            if n == 0:
                continue

            if list(fd.keys()).count("PartType%d" % i) == 0:
                self.warning(
                    "type=%d n=%d but group %s is not found !" %
                    (i, n, "PartType%d" %
                     i))
                sys.exit()

            # loop over dataset
            block = fd["PartType%d" % i]
            for key in list(block.keys()):
                if key not in ntab:
                    self.warning(
                        "get a dataset with name %s but no such key in ntab" %
                        key)
                    continue

                varname = ntab[key]

                if not self.has_var(varname):
                    setattr(self, varname, None)

                # record the variable in a list
                if list_of_vectors.count(varname) == 0:
                    list_of_vectors.append(varname)

        # read the tables
        for i, n in enumerate(self.npart):

            if n != 0:
                if self.verbose and mpi.mpi_IsMaster():
                    self.message("Reading particles (type %i)..." % i)

                remaining_vectors = deepcopy(list_of_vectors)

                # loop over dataset
                block = fd["PartType%d" % i]
                if mpi.mpi_NTask() > 1:
                    init, end = self.get_particles_limits(i)

                for key in list(block.keys()):
                    varname = ntab[key]
                    if self.skip_io_block(varname):
                        self.message("Skipping %s block" % varname)
                        continue

                    if mpi.mpi_NTask() > 1:
                        data = block[key][init:end]
                    else:
                        data = block[key].value
                    if getattr(self, varname) is None:
                        setattr(self, varname, data)
                    else:
                        setattr(self, varname, np.concatenate(
                            (getattr(self, varname), data)))

                    remaining_vectors.remove(varname)

                # loop over vectors absent from the block
                for varname in remaining_vectors:
                    var = getattr(self, varname)
                    data = (
                        np.ones(
                            np.getsize(
                                n,
                                vdim[varname])) *
                        dval[varname]).astype(
                        np.float32)
                    if var is not None:
                        setattr(self, varname, np.concatenate(
                            (getattr(self, varname), data)))
                    else:
                        setattr(self, varname, data)

        dump_file = self.p_name_global[0].split("_")[:-1]
        dump_file = "".join(dump_file) + ".dump"
        data = logger.loadFromIndex(
            self.offset, dump_file, self.time_offset)

        self.pos = data["position"]
        self.vel = data["velocity"]
        self.acc = data["acceleration"]
        self.rho = data["rho"]
        self.message("Manually setting values")
        params = {
            'mh': 1.6726e-24,
            'k': None,  # useless
            'mu': 2,
            "gamma": 5. / 3.
        }
        tmp = data["entropy"]
        self.u = thermodyn.Ura(self.rho, tmp, params)
        self.num = data["id"]
        self.rsp = data["h_sph"]
        self.mass = data["mass"]

        # set tpe
        self.tpe = np.array([], np.int32)
        for i in range(len(self.npart)):
            self.tpe = np.concatenate((self.tpe, np.ones(self.npart[i]) * i))

        self.massarr = [0.] * 6
