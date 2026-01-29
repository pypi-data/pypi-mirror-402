#!/usr/bin/env python3

###########################################################################################
#  package:   pNbody
#  file:      libSSPluminosity.py
#  brief:     SSP luminosities
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
###########################################################################################

import scipy
import scipy.interpolate
import numpy as np

from pNbody import *


class SSPLuminosities:

    def __init__(self, file,band,luminosity=False):

        self.file = file
        self.band = band
        self.luminosity = luminosity

        # read file and crate self.data
        self.Read()

        # create the matrix
        self.CreateMatrix()

    def Read(self):
        """
        read file and create a data table
        """
        pass

    def CreateMatrix(self):
        """
        from data extract
        metalicites (zs)
        ages (ages)
        and ML (vs)
        """

        pass

    def CreateInterpolator(self):
        """
        from the matrix self.MatLv, create a spline interpolator
        """
        self.spl = scipy.interpolate.RectBivariateSpline(
            self.Zs, self.Ages, self.MatLv)

    def ExtrapolateMatrix(self, order=1, zmin=-5, zmax=2, nz=50, s=0, extrapolate=True):
        """
        extrapolate the matrix self.MatLv in 1d (using spline), along the Z axis
        The function create a new self.MatLv and self.Zs
        """

        # if extrapolated is true, we extrapolate values further out
        # elsewhere we use the neareast value (keep the value constant)
        if extrapolate:
          ext=0 
        else:
          ext=3   

        xx = np.linspace(zmin, zmax, nz)

        newMatLv = np.zeros((len(xx), len(self.Ages)))

        for i in np.arange(len(self.Ages)):

            Ls = self.MatLv[:, i]

            # 1d spline interpolation
            x = self.Zs
            y = Ls

            tck = scipy.interpolate.splrep(x, y, k=order, s=s)
            yy = scipy.interpolate.splev(xx, tck, ext=ext)

            newMatLv[:, i] = yy

        self.Zs = xx
        self.MatLv = newMatLv

    def Extrapolate2DMatrix(
            self,
            zmin=-10,
            zmax=2,
            nz=256,
            agemin=None,
            agemax=None,
            nage=256):
        if agemin is None:
            agemin = min(self.Ages)
        if agemax is None:
            agemax = max(self.Ages)

        self.Zs = np.linspace(zmin, zmax, nz)
        self.Ages = 10**np.linspace(np.log10(agemin), np.log10(agemax), nage)
        #self.Ages  = np.linspace((agemin),(agemax),nage)

        self.MatLv = self.Luminosity(self.Zs, self.Ages)

    def GetAgeIndexes(self, Ages):
        """
        Get the indexes of the nearest values of self.Ages from Ages
        """
        return self.Ages.searchsorted(Ages)

    def GetZIndexes(self, Zs):
        """
        Get the indexes of the nearest values of self.Zs from Zs
        """
        return self.Zs.searchsorted(Zs)

    def Luminosity(self, Zs, Ages):
        """
        return an interpolated value of Luminosity using self.slp
        from a given Zs and Ages
        """

        MatLvi = self.spl(Zs, Ages)
        return MatLvi

    def Luminosities(self, Zs, Ages):
        """
        return an interpolated value of Luminosity using self.slp
        from a given Zs and Ages
        """

        i = self.Zs.searchsorted(Zs)
        j = self.Ages.searchsorted(Ages)
        i = i.clip(0, len(self.Zs) - 1)
        j = j.clip(0, len(self.Ages) - 1)

        return self.MatLv[i, j]
