#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      fourier.py
#  brief:     Fourier Transform
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import numpy as np
from numpy import fft


####################################
def tofrec(fmin, fmax, n, i):
    ####################################
    nn = float(n)
    if i <= n // 2 + 1:
        return (i / nn + 0.5) * (fmax - fmin) + fmin
    else:
        return (i / nn - 0.5) * (fmax - fmin) + fmin


####################################
def fourier(x, y):
    ####################################
    """

    Fct = Sum_(m=1,n) amp_m cos( 2.pi f_m phi + phi_m )
        = Sum_(m=1,n) amp_m cos(        m phi + phi_m )

    m = 2.pi f_m

    """

    dx = (x.max() - x.min()) / (len(x) - 1)
    fmin = -1. / (2. * dx)
    fmax = -fmin

    # f = fromfunction(lambda ii:tofrec(fmin,fmax,len(x),ii) ,(len(x),))
    f = np.array([], float)
    for i in range(len(x)):
        f = np.concatenate((f, np.array([tofrec(fmin, fmax, len(x), i)])))

    ## FFT ##
    ffft = fft.fft(y)

    amp = np.sqrt(ffft.real**2 + ffft.imag**2)  # amplitude du signal d'entree
    phi = np.arctan2(ffft.imag, ffft.real)		# phase a p/2 pres
    phi = np.fmod(phi + 2 * np.pi, 2. * np.pi)  # de 0 a 2*pi (ok avec phase positive)

    amp = 2. * amp / len(x)			            # doubler ok, /len(x) ???

    f = f[0:len(x) // 2]				        # on sort que les frequences positives
    amp = amp[0:len(x) // 2]
    phi = phi[0:len(x) // 2]

    amp[0] = amp[0] / 2.

    return f, amp, phi
