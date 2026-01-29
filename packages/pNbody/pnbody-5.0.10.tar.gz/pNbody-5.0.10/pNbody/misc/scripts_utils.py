#!/usr/bin/python
###########################################################################################
#  package:   pNbody
#  file:      script_utils.py
#  brief:     Contains utilities classes and functions for scripts in the
#             scripts folder
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import argparse
import numpy as np


class ExplicitDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Prints the default arguments when they are provided."""

    def _get_help_string(self, action):
        if action.default in (None, False):
            return action.help
        return super()._get_help_string(action)


class RawTextArgumentDefaultsHelpFormatter(ExplicitDefaultsHelpFormatter,
                                           argparse.RawTextHelpFormatter):
    """Provides the defaults values and allows to format the text help."""
    pass


class store_as_array(argparse._StoreAction):
    """Provides numpy array as argparse arguments."""

    def __call__(self, parser, namespace, values, option_string=None):
        values = np.array(values)
        return super().__call__(parser, namespace, values, option_string)
