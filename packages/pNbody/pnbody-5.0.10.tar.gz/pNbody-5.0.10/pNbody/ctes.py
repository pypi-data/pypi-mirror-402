#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      ctes.py
#  brief:     Physics Constants
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


from . import units as u


GRAVITY = u.PhysCte(6.6732e-11, u.Unit_G)
SOLAR_MASS = u.PhysCte(1.989e33, u.Unit_g)
SOLAR_LUM = u.PhysCte(3.826e33, u.Unit_erg / u.Unit_s)
AVOGADRO = u.PhysCte(6.0220e+23, u.Unit_mol)
BOLTZMANN = u.PhysCte(1.3807e-23, u.Unit_J / u.Unit_K)
GAS_CONST = u.PhysCte(8.3144e+00, u.Unit_J / u.Unit_mol)
C = u.PhysCte(2.99792458e8, u.Unit_m / u.Unit_s)
PLANCK = u.PhysCte(6.6262e-34, u.Unit_J * u.Unit_s)
PROTONMASS = u.PhysCte(1.6726e-27, u.Unit_kg)
ELECTRONMASS = u.PhysCte(9.1095e-31, u.Unit_kg)
ELECTRONCHARGE = u.PhysCte(4.8032e-10, u.Unit_C)
AV = u.PhysCte(6.828e-50, u.Unit_Pa * u.Unit_m**6)
BV = u.PhysCte(4.419e-29, u.Unit_m**3)
HUBBLE = u.PhysCte(3.2407789e-18, 1 / u.Unit_s)  # in h/s



def convert_ctes(units):
    """
    convert a constant into a given unit system.
    """
    global BOLTZMANN, PROTONMASS

    # UnitLength_in_cm = units[0]
    UnitMass_in_g = units[1]
    UnitVelocity_in_cm_per_s = units[2]
    # UnitTime_in_s = UnitLength_in_cm / UnitVelocity_in_cm_per_s
    UnitEnergy_in_cgs = UnitMass_in_g * UnitVelocity_in_cm_per_s**2

    BOLTZMANN = BOLTZMANN / UnitEnergy_in_cgs
    PROTONMASS = PROTONMASS / UnitMass_in_g