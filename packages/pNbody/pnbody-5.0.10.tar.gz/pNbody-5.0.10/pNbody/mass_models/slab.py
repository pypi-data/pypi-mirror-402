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




def SurfaceDensity(Sigma0,x,y,z,G=1.):
    """
    Slab with a constant density
    """

    return  Sigma



def Potential(Sigma0,x,y,z,G=1.):
    """
    Slab
    """
    return  2*np.pi*G*Sigma0*np.fabs(z)
    
    
    
    
    
    

