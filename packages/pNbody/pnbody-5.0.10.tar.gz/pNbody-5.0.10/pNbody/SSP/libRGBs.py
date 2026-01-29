#!/usr/bin/env python3

###########################################################################################
#  package:   pNbody
#  file:      libRGBs.py
#  brief:     ???
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
###########################################################################################

import numpy as np
from pNbody import *

# Should be in its own class...
Kroupa_meanstar = 0.4820


def Kroupa_IMF(m):
        #Meanstar = 0.4820
    A = 0.10629
    if m <= 0.08:
        return(A * m**-0.3)
    elif m <= 0.5:
        return(A * m**-1.8)
    elif m <= 1:
        return(A * m**-2.7)
    else:
        return(A * m**-2.3)


def Kroupa_IMFint(m):
    A = 0.10629

    f = np.zeros(np.size(m))
    ind = np.where(m <= 0.08)
    f[ind] = A * m[ind]**0.7 / 0.7 - 0.01864976527083534

    ind = np.where((m > 0.08) * (m <= 0.5))
    f[ind] = -A * m[ind]**-.8 / .8 + 1.0021446918927897 + 0.0072656

    ind = np.where((m > 0.5) * (m <= 1))
    f[ind] = -A * m[ind]**-1.7 / 1.7 + 0.2031395463734218 + 0.778083245211

    ind = np.where(m > 1)
    f[ind] = -A * m[ind]**-1.3 / 1.3 + A * 1**-1.3 / 1.3 + 0.918699
    return(f)


class NRGB:

    def __init__(self, file):
        self.fileMS = file + 'MS.dat'
        self.fileRGB = file + 'rgb.dat'

        self.ReadMS()  # Read data file, create self.data
        self.ReadRGB()
        self.InterpolateMS()

        self.InterpolateTRGB()

    def ReadMS(self):
        pass

    def ReadRGB(self):
        pass

    def InterpolateMS(self):
        pass

    def InterpolateTRGB(self):
        pass

    Kroupa_meanstar = 0.4820

    def Kroupa_IMF(m):
        #Meanstar = 0.4820
        A = 0.10629
        if m <= 0.08:
            return(A * m**-0.3)
        elif m <= 0.5:
            return(A * m**-1.8)
        elif m <= 1:
            return(A * m**-2.7)
        else:
            return(A * m**-2.3)

    def Kroupa_IMFint(m):
        A = 0.10629

        f = np.zeros(np.size(m))
        f[np.where(m <= 0.08)] = A * m**0.7 / 0.7 - 0.01864976527083534
        f[np.where((m > 0.08) * (m <= 0.5))] = -A * \
            m**-.8 / .8 + 1.0021446918927897 + 0.0072656
        f[np.where((m > 0.5) * (m <= 1))] = -A * m**-1.7 / \
            1.7 + 0.2031395463734218 + 0.778083245211
        f[np.where(m > 1)] = -A * m**-1.3 / 1.3 + A * 1**-1.3 / 1.3 + 0.918699
        return(f)

    def RGBs(self, Zs, Ages):
        Frac = Kroupa_IMFint(self.InterpolateTRGB.ev(
            Zs, Ages)) - Kroupa_IMFint(self.InterpolateMS.ev(Zs, Ages))
        return(Frac / Kroupa_meanstar)
