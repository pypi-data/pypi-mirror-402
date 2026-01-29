#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      observations.py
#  brief:     observations.py
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from pickle import load
from h5py import File, special_dtype
from os import path

# Transformation between pickle host name to HDF5
pickle_to_hdf5 = {
    "MW": "MilkyWay Dwarfs",
    "M31": "Andromeda Dwarfs"
}

# All the required pickle fields
pickle_fields = [
    'eFeHp', 'eVmagp', 'eVmagm', 'Rh', 'eFeHm', 'Vmag',
    'D_max', 'MHI', 'FeH', 'ra', 'eMvp', 'D', 'eLm', 'L',
    'Mv', 'D_min', 'eMvm', 'eLp', 'Sigma',
    'eSigmam', 'eRhp', 'mM0', 'FeH_Tech', 'eRhm', 'eSigmap',
    'dec'
]

# List of fields containing strings
pickle_string_fields = [
    "FeH_Tech",
    "host"
]

# Transformation between pickle fields and HDF5 fields
pickle_fields_to_hdf5 = {
    'Rh': "HalfLightRadius",
    'MHI': "MassHI",
    'FeH': "FeH",
    'ra': "RightAscension",
    'D': "Distance",
    'L': "Luminosity",
    'FeH_Tech': "FeHTechnique",
    'dec': "Declination",
    'Sigma': "VelocityDispersion",
    'host': "Host"
}

# Error fields corresponding to a pickle field
pickle_error_fields = {
    "Rh": ("rel", ["eRhm", "eRhp"]),
    "MHI": None,
    "FeH": ("rel", ["eFeHm", "eFeHp"]),
    "D": ("abs", ["D_min", "D_max"]),
    "L": ("rel", ["eLm", "eLp"]),
    "FeH_Tech": None,
    "dec": None,
    "ra": None,
    "Sigma": ("rel", ["eSigmam", "eSigmap"]),
    "host": None,
}

# Description of each pickle field
pickle_fields_description = {
    "Rh": "Half Light Radius",
    "MHI": "Total mass of HI",
    "FeH": "[Fe/H]",
    "D": "Distance from the Sun",
    "L": "Luminosity",
    "FeH_Tech": "Technique used to measure [Fe/H]",
    "dec": "Declination",
    "ra": "Right Ascension",
    "Sigma": "Stellar velocity dispersion",
    "host": "Host of the satellite [see /Hosts for details]",
}

# Units of each field (in astropy convention)
pickle_fields_units = {
    "FeH": "",
    "D": "kpc",
    "Rh": "kpc",
    "MHI": "solMass",
    "L": "solLum",
    "FeH_Tech": None,
    "dec": "deg",
    "ra": "deg",
    "Sigma": "km/s",
    "host": None,
}

# ASCII format
ascii_data_type = [
    ("name", "S20"),
    ("ra", "f8"),
    ("dec", "f8"),
    ("D", "f8"),
    ("Mass", "f8"),
    ("Radius", "f8"),
    ("source", "S200")
]


class Observations():
    def __init__(self, filename, dataset=None):
        # init fields
        self.filename = filename
        self.data = None
        self.dataset = dataset

        # read data
        self.readHDF5File(filename)

    def readHDF5File(self, filename):
        return

    def useDataset(self, dataset):
        if (self.dataset is None or
                dataset in self.dataset):
            return True

        return False

    def getPosition(self):
        f = File(self.filename)
        x = []
        y = []
        z = []

        for name in f:
            if not self.useDataset(name):
                continue
            # get values
            ra = f[name + "/RightAscension"]
            dec = f[name + "/Declination"]
            # discard errors
            D = f[name + "/Distance"][:, 0]

            # compute position
            x_tmp = D * np.cos(dec) * np.cos(ra)
            y_tmp = D * np.cos(dec) * np.sin(ra)
            z_tmp = D * np.sin(ra)

            x.extend(x_tmp)
            y.extend(y_tmp)
            z.extend(z_tmp)

        pos = np.array([x, y, z]).transpose()
        return pos

    @staticmethod
    def _generateArraysFromPickle(p_data, host):
        """
        Pick all the arrays for a host from the pickle data

        Parameters
        ----------

        p_data: dict
            The whole pickle file data

        host: str
            Name of the host (in HDF5)
        """
        ret = {}

        # initialize data
        for f in pickle_fields:
            ret[f] = []
        ret["name"] = []

        # set data
        for gal_name in p_data:
            gal = p_data[gal_name]
            gal_host = pickle_to_hdf5[gal["host"]]
            if gal_host != host:
                continue

            for f in pickle_fields:
                tmp = gal[f]
                if tmp is None:
                    tmp = np.nan
                ret[f].append(tmp)
            ret["name"].append(gal_name)

        return ret

    @staticmethod
    def _writeArrays(grp, data):
        """
        Write all the arrays to an HDF5 group.

        Parameters
        ----------

        grp: HDF5 group
            The HDF5 group to write

        data: dict
            All the arrays to write
        """
        string_dtype = special_dtype(vlen=str)
        for i in data:
            if i not in list(pickle_fields_to_hdf5.keys()):
                continue

            arr = np.array(data[i])

            err_fields = pickle_error_fields[i]
            if err_fields is not None:
                tpe = err_fields[0]
                fields = err_fields[1]

                arr = arr[:, np.newaxis]
                ret_arr = arr
                # add errors
                for j in fields:
                    tmp = np.array(data[j])[:, np.newaxis]
                    if tpe == "abs":
                        tmp = np.abs(tmp - ret_arr)
                    arr = np.append(arr, tmp, axis=1)

            # write dataset
            name = pickle_fields_to_hdf5[i]
            if i in pickle_string_fields:
                ds = grp.create_dataset(name, data=arr, dtype=string_dtype)
            else:
                ds = grp.create_dataset(name, data=arr)

            # write attributes
            ds.attrs["Description"] = pickle_fields_description[i]
            units = pickle_fields_units[i]
            if units is not None:
                ds.attrs["Units"] = units

        names = np.array(data["name"])
        grp.create_dataset("Name", data=names, dtype=string_dtype)

    @staticmethod
    def transformPickleFile(f_read, f_write, source=None):
        """
        Transform a pickle file containing observations to an HDF5 file.

        You can decide which fields are written and with the arrays at
        the beginning of this document.

        Parameters
        ----------

        f_read: str
            Pickle filename to read

        f_write: str
            HDF5 filename to write
        """

        # open files
        with open(f_read, "rb") as f:
            p_data = load(f)

        f = File(f_write, "a")

        # get list of all hosts
        hosts = []
        for gal in p_data:
            host = p_data[gal]["host"]
            if host not in hosts:
                hosts.append(host)

        # Transform hosts to HDF5 format
        for i, h in enumerate(hosts):
            hosts[i] = pickle_to_hdf5[h]

        # check if only new database
        for h in hosts:
            if h in f:
                raise IOError(
                    "Cannot overwrite an existing group (%s)" % h)

        # create data base
        for h in hosts:
            grp = f.create_group(h)

            # Generate host data
            data = Observations._generateArraysFromPickle(p_data, h)

            # Write the data to HDF5
            Observations._writeArrays(grp, data)

            # Write source
            if source is None:
                source = "Unknown"
            grp.attrs["Source"] = source
            grp.attrs["From file"] = f_read

        # Close file
        f.close()

    @staticmethod
    def transformASCIIFile(f_read, f_write, source=None, group_name=None):
        # read data
        data = np.genfromtxt(f_read, dtype=ascii_data_type, delimiter=",")

        # Open output
        f = File(f_write, "a")

        # create data base
        if group_name is None:
            group_name = path.splitext(f_read)[0]

        grp = f.create_group(group_name)

        # Write data to HDF5
