#!/usr/bin/env python3
###########################################################################################
#  package:   RT
#  file:      __init__.py
#  brief:     init file
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#             Mladen Ivkovic 
#
# This file is part of pNbody.
###########################################################################################

from astropy import units as u
from astropy import constants as cte

from ..rtlib import * 

# some constants
kB = getkB()              # 1.3806488e-16  # erg/K
h_planck = geth_planck()  # 6.62606957e-27  # cm**2*g/s
c = getc()                # 29979245800.0  # cm/s
L_Sol = getL_Sol()        #3.827e33  # erg/s


# ionization levels
NuiHI   = getNuiHI()   #  3.288e15 Hz 
NuiHeI  = getNuiHeI()  #  5.945e15 Hz
NuiHeII = getNuiHeII() # 13.157e15 Hz
frequency_bins = [NuiHI,NuiHeI,NuiHeII] 


# ionization energies in eV
EiHI   = getEiHI()  *u.eV  #13.59807*u.eV
EiHeI  = getEiHeI() *u.eV  #24.58654*u.eV
EiHeII = getEiHeII()*u.eV  #54.41298*u.eV

# ionization frequencies in Hz
nuiHI  = (EiHI/cte.h).to(u.Hz)
nuiHeI = (EiHeI/cte.h).to(u.Hz)
nuiHeII= (EiHeII/cte.h).to(u.Hz)


def convert_photon_number_rate_to_luminosity_with_frequency_bins(T=1e5,Ndot=1e12,frequency_bins=frequency_bins):
  """
   -----------------------------------------------------------------------------
   Given a photon number and a minimal frequency, compute the corresponding
   luminosity in units of stellar luminosities assuming a blackbody spectrum
   for given frequency bins.
  
   Given the spectrum, we first compute the average ionizing photon energy for
   each frequency bin `i` by integrating the energy density and the number
   density from the lowest ionizing frequency to infinity (or rather until a
   very high maximal value):
  
     <E_photon>_i = [ \int_\nu J(\nu) d\nu ] / [ \int_\nu J(\nu) / (h \nu) d\nu ]
  
   with the integration boundaries [\nu_{i, min}, \nu_{i, max}] which are
   provided by the user.
  
   Then we need to compute the fraction `f` of ionizing photons in each bin:
  
    let  nl = \nu_{i,min},
         nu = \nu_{i,max}
  
     f_i = [ \int_{nl}^{nu}   J(\nu) / (h \nu) d\nu ] /
           [ \int_{nl}^\infty J(\nu) / (h \nu) d\nu ]
  
   Note that we start both integrations with `nl` because we assume that
   we need to distribute a certain amount of *ionizing* photons, not
   total photons following the given spectrum.
   We finally get the luminosity L from the photon number rate Ndot as
  
     L_i = <E_photon>_i * f_i * Ndot
  
   The final computation then simplifies to
  
     L_i = [ \int_{nl}^{nu}   J(\nu)           d\nu ] /
           [ \int_{nl}^\infty J(\nu) / (h \nu) d\nu ] * Ndot
           
   
   # temperature for blackbody spectrum
   T = 1e5  # K
   
   # ionizing photon number emission rate you want
   Ndot = 1e12  # s^-1 # for many Iliev tests

   # define upper limits for frequency bins. We assume that
   # the lowest bin is the first ionizing frequency.
   frequency_bins = [3.288e15, 5.945e15, 13.157e15]  # Hz
   
   # return
   luminosities in erg/s for each photon group
           
   -----------------------------------------------------------------------------
  """

  import scipy.integrate as integrate
  from .blackbody import B_nu, B_nu_over_h_nu, nu_peak


  peak_frequency = nu_peak(T, kB, h_planck)
  integration_limit = 100 * peak_frequency
  print("peak of the blackbody spectrum: {0:10.3e} [Hz]".format(peak_frequency))
  
  # Get the full integral over the photon number density
  number_density_integral_tot, nerr = integrate.quad(
      B_nu_over_h_nu, frequency_bins[0], integration_limit, args=(T, kB, h_planck, c)
  )
  
  Lsum = 0
  
  Luminosities_erg_per_s = []

  for f in range(len(frequency_bins)):
    # Set integration ranges.
    nu_min = frequency_bins[f]
    if f < len(frequency_bins) - 1:
        nu_max = frequency_bins[f + 1]
    else:
        # A potential problem is that the integral is non-convergent
        # for the methods used. So instead of integrating to infinity,
        # peak an upper limit in units of the peak frequency.
        nu_max = integration_limit

    print("Bin {0:3d}: {1:10.3e} - {2:10.3e} [Hz] ".format(f, nu_min, nu_max), end=" ")

    energy_density_integral, eerr = integrate.quad(
        B_nu, nu_min, nu_max, args=(T, kB, h_planck, c)
    )
    L = energy_density_integral / number_density_integral_tot * Ndot
    
    Luminosities_erg_per_s_cm2.append(L)

    print("Luminosity = {0:12.3e} [erg/s] {1:12.3e} [L_Sol]".format(L, L / L_Sol))

    Lsum += L

  # Sanity check: Sum of individual luminosities must correspond to luminosity
  # of a single frequency bin
  
  #  energy_density_integral, eerr = integrate.quad(
  #      B_nu, frequency_bins[0], integration_limit, args=(T, kB, h_planck, c)
  #  )
  #  number_density_integral, nerr = integrate.quad(
  #      B_nu_over_h_nu, frequency_bins[0], integration_limit, args=(T, kB, h_planck, c)
  #  )
  #
  #  L_single = energy_density_integral / number_density_integral * Ndot
  #
  #  print("Sanity check: sum over all bins / total luminosity integral = {0:12.3e}".format(Lsum / L_single))

  return Luminosities_erg_per_s_cm2









