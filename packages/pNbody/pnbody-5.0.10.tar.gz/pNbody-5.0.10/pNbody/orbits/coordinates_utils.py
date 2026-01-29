#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:     integration_utils.py
#  brief:     Contains utilities fo coordinates system manipulation
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import units as u
import astropy.coordinates as coord

coord.galactocentric_frame_defaults.set("v4.0")


#Data coming from Battaglia 2023 (http://arxiv.org/abs/2106.08819)
r_sun = 8.129*u.kpc
v_sun = np.array((11.1, 241.24, 7.25))*u.km/u.s


def compute_distance(distance_modulus):
    """Comute the distance with the distance modulus of an object."""
    return 10**(distance_modulus/5.0 + 1)


def convert_ICRS2carth(distance_modulus, right_ascension, declination,
                               pm_RA, pm_DEC, v_radial, unit_length,
                               unit_velocity):
    """Convert ICRS coordinates to galactocentric carthesian coordinates."""
    dist_particles = compute_distance(distance_modulus)*u.pc
    dist_particles = dist_particles.to(u.kpc).value

    # convert the proper motion in right ascension on the sky (\mu_{\alpha,\star})
    # into the proper motion \mu_{\alpha}
    pm_RA = pm_RA/np.cos(declination*np.pi/180) 
    
    ics = coord.SkyCoord(frame='icrs', ra=right_ascension*u.degree, dec=declination*u.degree,
                         distance=dist_particles*u.kpc,
                         pm_ra=pm_RA*u.mas/u.yr,
                         pm_dec=pm_DEC*u.mas/u.yr,
                         radial_velocity=v_radial*u.km/u.s,
                         differential_type=coord.SphericalDifferential)
    ics = ics.transform_to(coord.Galactocentric(galcen_distance=r_sun,
                                                galcen_v_sun=v_sun))
    # Using the parameters given in sec7, p. 13 from Battaglia et al.
    position = ics.data.get_xyz().to(unit_length)
    velocity = ics.velocity.get_d_xyz().to(unit_velocity)
    return position, velocity

def convert_sph2carth(r, phi, theta):
    """Converts spherical coordinates to carthesian coordinates."""
    x = r*np.cos(phi)*np.sin(theta)
    y = r*np.sin(phi)*np.sin(theta)
    z = r*np.cos(theta)
    return x, y, z


def convert_cyl2carth(R, phi, z):
    """Converts cylindrical coordinates to carthesian coordinates."""
    x = R*np.cos(phi)
    y = R*np.sin(phi)
    return x, y, z


def convert_cart2cyl(x, y, z):
    """Converts carthesian coordinates to cylindrical coordinates."""
    R = np.sqrt(x*x + y*y)
    # Determines phi
    if (x == 0) and (y == 0):
        phi = 0
    elif (x == 0) and (y != 0):
        phi = np.pi/2*y/np.abs(y)
    elif (x > 0):
        phi = np.arctan(y/x)
    elif (x < 0) and (y >= 0):
        phi = np.arctan(y/x)+np.pi
    elif (x < 0) and (y < 0):
        phi = np.arctan(y/x)-np.pi

    return R, phi, z
