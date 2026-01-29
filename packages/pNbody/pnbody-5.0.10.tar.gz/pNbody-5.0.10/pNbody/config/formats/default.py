###########################################################################################
#  package:   pNbody
#  file:      bnbf.py
#  brief:
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

##########################################################################
#
# DEFAULT CLASS
#
##########################################################################

from pNbody import error


class Nbody_default:
    """
    This class is usefull to create an empty Nbody object
    """

    def _init_spec(self):
        """
        Initialize specific variable for this format
        """
        pass

    def get_excluded_extension(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        return "all"

    def check_spec_ftype(self):
        """
        Check the format type.
        As this format is only virtual, allways return an error.
        """
        raise error.FormatError("default")

    def get_read_fcts(self):
        """
        returns the functions needed to read a file.
        """
        return [self.read_particles]

    def get_write_fcts(self):
        """
        returns the functions needed to write a file.
        """
        return [self.write_particles]

    def get_default_spec_vars(self):
        """
        Specific variables to this format
        """
        return {}

    def get_default_spec_array(self):
        """
        return specific array default values for the class
        """
        return {}

    def read_particles(self, f):
        """
        Function that read particles.
        """
        pass

    def write_particles(self, f):
        """
        Function that write particles.
        """
        pass
