###########################################################################################
#  package:   pNbody
#  file:      default_extension.py
#  brief:     Default Nbody class extension
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import types
import os
import numpy as np

from copy import copy, deepcopy

import pNbody
from pNbody import thermodyn, mapping, myNumeric
from pNbody import ctes, libutil, FLOAT, nbodymodule
from pNbody import coolinglib, geometry, treelib, libgrid, libdisk
from pNbody import fourier
import pNbody.iofunc as pnio
import pNbody.mpiwrapper as mpi

from scipy.interpolate import interp1d

class _NbodyDefault:



    #################################
    #
    # Thermodynamic functions
    #
    #################################

    def U(self):
        """
        Return the gas specific energy of the model.
        The output is an nx1 float array.
        """
        return self.u

    def MeanWeight(self):
        """
        Return the mean weight of a model, taking into account
        heating by UV source.
        The output is an nx1 float array.
        """

        xi = self.unitsparameters.get('xi')
        Redshift = 1. / self.atime - 1.

        UnitDensity_in_cgs = self.localsystem_of_units.get_UnitDensity_in_cgs()
        UnitEnergy_in_cgs = self.localsystem_of_units.get_UnitEnergy_in_cgs()
        UnitMass_in_g = self.localsystem_of_units.get_UnitMass_in_g()
        HubbleParam = self.hubbleparam

        # 0) convert into cgs
        Density = self.rho.astype(
            float) * UnitDensity_in_cgs * (HubbleParam * HubbleParam) / self.atime**3
        Egyspec = self.u.astype(float) * UnitEnergy_in_cgs / UnitMass_in_g

        # 1) compute mu
        MeanWeight, Lambda = coolinglib.cooling(Egyspec, Density, xi, Redshift)

        return MeanWeight.astype(np.float32)

    def A(self):
        """
        Return the gas entropy of the model.
        The output is an nx1 float array.
        """
        gamma = self.unitsparameters.get('gamma')
        xi = self.unitsparameters.get('xi')
        ionisation = self.unitsparameters.get('ionisation')
        mu = thermodyn.MeanWeight(xi, ionisation)
        mh = ctes.PROTONMASS.into(self.localsystem_of_units)
        k = ctes.BOLTZMANN.into(self.localsystem_of_units)
        thermopars = {"k": k, "mh": mh, "mu": mu, "gamma": gamma}

        A = np.where(
            (self.u > 0),
            thermodyn.Aru(
                self.Rho(),
                self.u,
                thermopars),
            0)
        return A

    def P(self):
        """
        Return the gas pressure of the model.
        The output is an nx1 float array.
        """
        gamma = self.unitsparameters.get('gamma')
        xi = self.unitsparameters.get('xi')
        ionisation = self.unitsparameters.get('ionisation')
        mu = thermodyn.MeanWeight(xi, ionisation)
        mh = ctes.PROTONMASS.into(self.localsystem_of_units)
        k = ctes.BOLTZMANN.into(self.localsystem_of_units)
        thermopars = {"k": k, "mh": mh, "mu": mu, "gamma": gamma}

        P = np.where(
            (self.u > 0),
            thermodyn.Pru(
                self.Rho(),
                self.u,
                thermopars),
            0)
        return P

    def Ne(self):
        """
        Return the electron density of the model.
        The output is an nx1 float array.
        """

        xi = self.unitsparameters.get('xi')
        ionisation = self.unitsparameters.get('ionisation')
        mh = ctes.PROTONMASS.into(self.localsystem_of_units)

        thermopars = {"mh": mh, "Xi": xi, "ionisation": ionisation}
        ne = thermodyn.ElectronDensity(self.Rho(), thermopars)

        return ne

    def S(self):
        """
        Return the `entropy` of the model, defined as
        S = T * Ne^(1-gamma)
        The output is an nx1 float array.
        """

        gamma = self.unitsparameters.get('gamma')

        s = self.T() * self.Ne()**(1. - gamma)

        return s

    def Lum(self):
        """
        Return the luminosty of the model, defined as
        Lum = m*u/Tcool = m*Lambda/rho

        The output is an nx1 float array.
        """

        Lum = self.mass * self.u / self.Tcool()

        return Lum
