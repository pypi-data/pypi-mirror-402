#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libmiyamoto.py
#  brief:     Defines Miyamoto profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np




def Vcirc(V, R, G=1.):
    """
    Mestel Circular velocity
    """
    return V




def SurfaceDensity(V, R, G=1.):
    """
    Mestel Density
    """

    return   V**2/(2*np.pi*G) /R





