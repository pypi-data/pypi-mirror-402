#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      errorfuncs.py
#  brief:     Defines a few error classes
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################



class FormatError(Exception):
    """
    format error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

