#!/usr/bin/env python3

###########################################################################################
#  package:   pNbody
#  file:      libbastitime.py
#  brief:     Basti RGB
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
###########################################################################################

import numpy as np
import scipy
import scipy.interpolate
from .libRGBs import NRGB


def readfile(file):
    return(np.genfromtxt(file))


ages = np.linspace(0.3, 17, 50)
zs = [-3.62, -2.62, -2.14, -1.84, -1.62, -1.31, -
      1.01, -0.70, -0.60, -0.29, -0.09, 0.05, 0.16]


class BastiRGB(NRGB):

    def ReadMS(self):
        self.dataMS = readfile(self.fileMS)

    def ReadRGB(self):
        self.dataRGB = readfile(self.fileRGB)

    def InterpolateMS(self):
        # Interpolate so you get the mass given the values
        self.InterpolateMS = scipy.interpolate.RectBivariateSpline(
            ages, zs, self.dataMS, kx=1, ky=1)

    def InterpolateTRGB(self):

        self.InterpolateTRGB = scipy.interpolate.RectBivariateSpline(
            ages, zs, self.dataRGB, kx=1, ky=1)
