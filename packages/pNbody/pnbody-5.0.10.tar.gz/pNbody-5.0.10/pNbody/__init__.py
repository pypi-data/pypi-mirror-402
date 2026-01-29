#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      __init__.py
#  brief:     init file
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################



"""
This python module is useful to manipulate N-body data.
It allows to compute simple physical values like energy,
kinetic momentum, inertial momentum, centre of mass etc.
It also allows to modify the data with rotation, translations,
select some particles, add particles etc.
Associated scripts like "gdisp", "mkmovie" or "movie" allow
to visualise the N-body data in different ways : surface density,
velocity map, velocity dispersion map, etc.

Yves Revaz 14.05.05
"""

# nbody classes
from .main import *

from ._version import get_versions
__version__ = get_versions()['full-revisionid']
