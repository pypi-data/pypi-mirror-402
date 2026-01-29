 #!/usr/bin/env python3
 ###########################################################################################
 #  package:   pNbody
 #  file:      powerSphericalCutoff.py
 #  brief:     Defines power spherical cut-off profiles
 #  copyright: GPLv3
 #             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
 #             LASTRO - Laboratory of Astrophysics of EPFL
 #  author:    Darwin Roduit <darwin.roduit@epfl.ch>
 #
 # This file is part of pNbody. 
 ###########################################################################################


"""
    Power spherical cut-off model based on the following density:
        \rho(r) = A (\frac{r_1}{r})^\alpha \exp(- \frac{r^2}{r_c^2})
    with A, r_1, \alpha and r_c the parameters of the model.
"""

import numpy as np
from scipy.special import gamma, gammaincc, gammainc

def Potential(alpha, r_c, amplitude, r_1, r, G=1.):
    """
    Potential
    """
    part_1 = - G*CumulativeMass(alpha, r_c, amplitude, r_1, r, G)/r 
    part_2 = - 2*np.pi*G*amplitude *r_1**alpha * r_c**(2-alpha) * gammaincc(1.0-alpha/2, r**2 / r_c**2)*gamma(1.0-alpha/2)
    return part_1+part_2

def CumulativeMass(alpha, r_c, amplitude, r_1, r, G=1.):
    """
    Cumulative mass
    """     
    return 2*np.pi*amplitude*r_1**alpha * r_c**(3.0-alpha) * gammainc(1.5-alpha/2, r**2/r_c**2)*gamma(1.5-alpha/2)    

def Density(alpha, r_c, amplitude, r_1, r, G=1.):
    """
    Density
    """
    return amplitude*(r_1/r)**alpha*np.exp(-(r/r_c)**2)
    

def Vcirc(alpha, r_c, amplitude, r_1, r, G=1.):
    """
    Circular velocity
    """
    M = CumulativeMass(alpha, r_c, amplitude, r_1, r, G=1.)
    return np.sqrt(G*M/r)
     