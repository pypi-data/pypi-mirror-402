#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:     integration_utils.py
#  brief:     Contains utilities the orbit_integration scripts
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################
from pNbody.mass_models import MWPotential2014 as MW



def MW_time_evolution_factor(time, slope=0.09):
    """Time dependent multiplicative factor to change the mass off the
    MWPotential as time evolves. We assume a linear growth in time. This is
    roughly valid during the last 10 Gyr. """
    return slope*time + 1


def GradPot_time_evolved(rho_0, r_s, M_disk, a, b, alpha,
                             r_c, amplitude, r_1, f_1, f_2, f_3, position, time, G=1):
    """Gradient of MW potential (time evolving) in time in carthesian
    coordinates. For orbit integratrion."""

    # We add a time evolved component
    factor = MW_time_evolution_factor(time)

    # Total gradient
    grad_Phi = factor*MW.GradPot(rho_0, r_s, M_disk, a, b, alpha, r_c,
                                  amplitude, r_1, f_1, f_2, f_3, position, time, G)

    return grad_Phi
