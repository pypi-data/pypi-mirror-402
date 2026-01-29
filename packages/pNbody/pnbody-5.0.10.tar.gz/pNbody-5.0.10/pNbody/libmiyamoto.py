#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libmiyamoto.py
#  brief:     Defines Miyamoto profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np


# miyam.f
# 
#       DO 60 I = 1, NTOT
#         R2 = X(I)**2 + Y(I)**2 + EPS
#         R = SQRT(R2)
#         C2 = Z(I)**2 + B12
#         C  = SQRT(C2)
#         D1 = A1 + C
#         D12 = D1*D1
#         D2 = A2 + C
#         D22 = D2*D2
# C
#         S12 = R2 + D12
#         S1 = SQRT(S12)
#         S22 = R2 + D22
#         S2 = SQRT(S22)
# C
#         T11 = GM1/S1
#         T13 = T11/S12
#         TD13 = T13*D1
#         TD15 = TD13/S12
#         T21 = GM2/S2
#         T23 = T21/S22
#         TD23 = T23*D2
#         TD25 = TD23/S22
# C P4RC2B2 : 4*Pi*Rho*C2/B2
#         P4RC2B2 = ( GM1*(A1*R2+(D1+C+C)*D12)/(S12*S12*S1) +
#      &              GM2*(A2*R2+(D2+C+C)*D22)/(S22*S22*S2) ) / C
#         SV = SQRT( .5/P4RC2B2 ) * (TD13 + TD23)
#         VT12 = R2*(T13+T23 - 3./P4RC2B2*(TD13+TD23)*(TD15+TD25) )
#         IF (VT12 .LT. 0.) THEN
#           NOUT = NOUT + 1
#           VV2 = 3.*SV*SV + VT12
#           VT1 = 0.
#           SV = SQRT(VV2/3.)
#         ELSE
#           VT1 = SQRT(VT12)
#         ENDIF
# C
# 	VT = SV*GASDEV() + VT1
#         VR = SV*GASDEV()
# C
#         PX(I) = (VR*X(I) - VT*Y(I))/R
#         PY(I) = (VR*Y(I) + VT*X(I))/R
#         PZ(I) = SV*GASDEV()
# C
#    60 CONTINUE



def Potential(G, M, a, b, R, z):
    """
    Miyamoto-Nagai Potential
    """
    return -G * M / np.sqrt(R**2 + (a + np.sqrt(z**2 + b**2))**2)


def Vcirc(G, M, a, b, R):
    """
    Miyamoto-Nagai Circular velocity
    """
    return np.sqrt(G * M / (R**2 + (a + b)**2)**1.5 * R**2)


def Omega(G, M, a, b, R):
    """
    Miyamoto-Nagai Omega
    """
    return np.sqrt(G * M / (R**2 + (a + b)**2)**1.5)


def Kappa(G, M, a, b, R):
    """
    Miyamoto-Nagai Kappa
    """

    r2 = R * R
    x = np.sqrt(r2 + (a + b)**2)
    return np.sqrt(G * M * (-3. * r2 / x**5 + 4. / x**3))


def Density(G, M, a, b, R, z):
    """
    Miyamoto-Nagai Density
    """

    zb = np.sqrt(z**2 + b**2)
    azb2 = (a + zb)**2
    R2 = R * R

    cte = (b * b * M) / (4 * np.pi)
    return cte * (a * R2 + (a + 3 * zb) * azb2) / ((R2 + azb2)**2.5 * zb**3)


def dR_Potential(G, M, a, b, R, z):
    """
    first derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2 + b**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return G * M * R / R2azb2**(3.0 / 2.0)


def d2R_Potential(G, M, a, b, R, z):
    """
    second derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2 + b**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return -3 * G * M * R2 * \
        R2azb2**(-5.0 / 2.0) + G * M * R2azb2**(-3.0 / 2.0)


def dz_Potential(G, M, a, b, R, z):
    """
    first derivative in R
    """

    R2 = R * R
    zb = np.sqrt(z**2 + b**2)
    azb2 = (a + zb)**2

    R2azb2 = R2 + azb2

    return G * M * z * (a + zb) / (R2azb2**(3.0 / 2.0) * zb)


def d2z_Potential(G, M, a, b, R, z):
    """
    second derivative in R
    """

    R2 = R * R
    z2 = z * z
    zb2 = z**2 + b**2
    zb = np.sqrt(zb2)
    azb = a + zb
    azb2 = azb**2

    R2azb2 = R2 + azb2

    c1 = -3 * z2 * azb2 / (R2azb2**(5.0 / 2.0) * zb2)
    c2 = z2 / (R2azb2**(3.0 / 2.0) * zb2)
    c3 = -  z2 * azb / (R2azb2**(3.0 / 2.0) * zb**3.0)
    c4 = azb / (R2azb2**(3.0 / 2.0) * zb)

    return G * M * (c1 + c2 + c3 + c4)


def Sigma_z(G, M, a, b, R, z):
    """
    Return sigma_z from Jeans equation : 1/rho Int( rho * dzPhi * dz )
    """

    R2 = R * R
    b2 = b * b
    z2 = z * z
    c2 = z2 + b2
    c = np.sqrt(c2)

    zb2 = z**2 + b**2
    zb = np.sqrt(zb2)
    azb = a + zb
    azb2 = azb**2
    R2azb2 = R2 + azb2

    TD = G * M * (a + c) / R2azb2**(3.0 / 2.0)

    return np.sqrt(b2 / (8 * np.pi * c2) * TD**2 / Density(G, M, a, b, R, z))


def Sigma_zbis(G, M, a, b, R, z):
    """
    Same than Sigma_z, but optimized
    """

    GM1 = G * M
    A1 = a
    B1 = b

    B12 = B1 * B1
    R2 = R * R
    C2 = z**2 + B12
    C = np.sqrt(C2)
    D1 = A1 + C
    D12 = D1 * D1

    S12 = R2 + D12
    S1 = np.sqrt(S12)

    T11 = GM1 / S1
    T13 = T11 / S12
    TD13 = T13 * D1
    TD15 = TD13 / S12

    P4RC2B2 = (GM1 * (A1 * R2 + (D1 + C + C) * D12) / (S12 * S12 * S1)) / C

    SV = np.sqrt(0.5 / P4RC2B2) * TD13

    return SV


def Sigma_t(G, M, a, b, R, z):
    """
    Return sigma_z from Jeans equation : 1/rho Int( rho * dzPhi * dz )

    sigma_t^2 =   R*d/dr(Phi) + R/rho*d/dr(rho*sigma_z^2)

    """

    GM1 = G * M
    A1 = a
    B1 = b
    B12 = b * b

    R2 = R * R
    C2 = z**2 + B12
    C = np.sqrt(C2)
    D1 = A1 + C
    D12 = D1 * D1

    S12 = R2 + D12
    S1 = np.sqrt(S12)

    T11 = GM1 / S1
    T13 = T11 / S12
    TD13 = T13 * D1
    TD15 = TD13 / S12

    P4RC2B2 = (GM1 * (A1 * R2 + (D1 + C + C) * D12) / (S12 * S12 * S1)) / C

    SV = np.sqrt(.5 / P4RC2B2) * TD13
    VT12 = R2 * (T13 - 3. / P4RC2B2 * TD13 * TD15)

    if (VT12 >= 0.):
        VT1 = np.sqrt(VT12)
    else:
        VT1 = 0.

    return VT1


def SurfaceDensity(G, M, a, b, R):
    """
    Miyamoto-Nagai Surface density
    """

    z = 0
    dz = b / 100.
    integral = 0.0
    err = 1.
    i = 0

    while (i < 300):
        integral = integral + Density(G, M, a, b, R, z)
        z = z + dz

        #err = abs(old_integral-integral)/integral

        i = i + 1

    return integral * 2. * dz
