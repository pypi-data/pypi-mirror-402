#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      deprojsersic.py
#  brief:     Defines plummer profiles
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

"""
deprojected 3D sersic model

see : Lima Neto, Gerbal & Márquez 1999
see : Prugniel & Simien 1997
see : Vitral & Mamon 2020

taken from : https://gitlab.com/eduardo-vitral/vitral_mamon_2020a/

"""


import numpy as np
from scipy.special import gamma, gammainc, kv
import matplotlib.pyplot as plt
from math import log10, floor, ceil



coeff_nu = np.array([ 2.11650375e-08, -4.22902325e-06, -2.46359447e-05, -5.73388080e-05,
       -4.04289109e-04,  5.05909349e-03,  4.30984431e-02,  1.38104012e-01,
        7.60442690e-01,  1.16175463e+00, -1.20874761e+00,  2.92420877e-06,
        2.49602094e-05, -1.07424151e-05,  4.86719164e-04, -1.27213457e-02,
       -1.19985306e-01, -3.66974460e-01, -2.66376910e+00, -5.06511334e+00,
        2.77051991e+00, -4.30613198e-06,  1.80103630e-04,  4.63612108e-04,
        1.11207157e-02,  1.24754026e-01,  2.21903647e-01,  3.09335388e+00,
        7.97967553e+00, -1.17758636e+00, -9.50502108e-05, -5.90101923e-04,
       -1.61497015e-03, -5.38531024e-02,  1.92264891e-01, -7.07798110e-01,
       -5.05161807e+00, -8.64950082e-01,  9.61342895e-05, -3.26083391e-03,
       -2.89692502e-04, -2.79459955e-01, -1.31804255e+00,  3.11290486e-01,
       -2.45546680e-01,  1.38793611e-03,  7.56339933e-03,  8.32395220e-02,
        1.13389627e+00,  9.34938769e-01,  1.19073672e+00, -1.42758124e-03,
        2.44367598e-02, -2.70566861e-01, -2.29803584e-01, -4.04723030e-01,
       -1.37314044e-02, -6.92094357e-02, -5.43009351e-02, -1.25610803e-01,
        4.25126945e-02,  8.62326111e-03,  7.17533687e-02,  4.50685113e-03,
       -1.57309618e-03, -5.01681615e-03])

coeff_m =  np.array([ 6.22672056e-07, -1.30302402e-05,  3.24855852e-07, -3.03912093e-04,
       -2.77858700e-04,  6.19557246e-03,  2.72275234e-02,  1.81684559e-01,
        7.77611406e-01,  1.07956651e+00, -1.62156611e+00,  9.52335271e-06,
        2.20326253e-06,  2.99340196e-04,  3.00610892e-04, -1.65575262e-02,
       -7.55461055e-02, -5.20207978e-01, -2.70580878e+00, -5.05515391e+00,
        4.11456696e+00, -1.60773606e-05,  3.08572568e-04,  4.97043595e-05,
        1.95889557e-02,  7.73354141e-02,  4.22720220e-01,  3.22786371e+00,
        8.41337594e+00, -2.56514656e+00, -2.55672468e-04, -1.41080336e-04,
       -8.71968935e-03, -3.03997943e-02,  8.74574001e-02, -1.00125853e+00,
       -5.50752214e+00, -8.36703868e-01,  1.61954227e-04, -3.49367783e-03,
       -1.98904248e-03, -2.99960424e-01, -1.00655700e+00,  3.15734060e-02,
        6.34227640e-01,  2.85344033e-03,  4.46749767e-03,  1.27638954e-01,
        9.63766719e-01,  1.69969995e+00,  6.90422589e-01, -1.27379718e-03,
        2.01661088e-02, -2.32825707e-01, -7.48850015e-01, -4.24711772e-01,
       -1.98614440e-02, -5.73985763e-02,  6.11418584e-02, -2.78486233e-02,
        3.51746664e-02,  4.10668692e-02,  3.79442747e-02, -1.55676070e-02,
       -1.01410465e-04, -7.07564632e-04])



def RoundIt (Number) :
    """
    Rounds a number up to its three first significative numbers
    
    """
    if (Number == 0) :
        return 0
    else :
        Rounded = round(Number, -int(floor(log10(abs(Number))))+3)
        return Rounded


def Polynomial(x,n,params) :
    """
    Computes the polynomial P = SUM a_ij log^i(x) log^j(n), by using the 
    parameters provided in a shape such as saved by the code
    sersic_grid_num.py
    
    """
    P        = np.zeros(len(x)) 
    n_params = len(params)

    for i in range(0,len(x)) :    
      for k in range(1,n_params+1) :
          
          p     = ceil((-3 + np.sqrt(1 + 8*k))/2)
          x_exp = int(k - 1 - p*(p+1)/2)
          n_exp = int(1 - k + p*(p+3)/2)
          coeff = RoundIt(params[n_params - (k-1) -1])
          
          P[i] += coeff * \
                      (np.log10(n))**n_exp * \
                        (np.log10(x[i]))**x_exp
                        
    return P





def pPS(n) :
    """
    Formula from Prugniel & Simien 1997, (PS97)
    
    """
    p = 1 - 1.188/(2*n) + 0.22/(4*n**2)
    return p

def pLN(n) :
    """
    Formula from Lima Neto, Gerbal & Márquez 1999, (LGM99)
    
    """
    p = 1 - 0.6097/n + 0.05463/(n**2)
    return p

def b(n) :
    """
    Formula from Ciotti & Bertin 1999, (CB99)
    
    """
    b = 2*n - 1/3 + 4/(405*n) + 46/(25515*n**2) + 131/(1148175*n**3) - 2194697/(30690717750*n**4)
    return b




def DeprojectedSersicDensity(r,re,n,model):
  """
  r  : radius
  re : effective radius
  n  : sersic index
  """
  x = r/re
  
  if (model == 'LN') :
      p = pLN(n)
  if (model == 'PS') :
      p = pPS(n)
  try:
      p
  except NameError:
      print("You did not give a valid model")
      return  

  norm    = b(n)**(n*(3-p)) / (n * gamma(n*(3-p)))
  nu      = norm * np.exp(- b(n) * x**(1/n)) * x**(-p)  
  
  return nu
  
def DeprojectedSersicDensityVitral(r,re,n):
  """
  r  : radius
  re : effective radius
  n  : sersic index
  """
  x = r/re
  nu = DeprojectedSersicDensity(r,re,n,"LN") * 10**(Polynomial(x,n,coeff_nu))
  return nu  

def DeprojectedSersicCumulativeMassVitral(r,re,n):
  """
  r  : radius
  re : effective radius
  n  : sersic index
  """
  x = r/re
  mass = DeprojectedSersicCumulativeMass(r,re,n,"LN") * 10**(Polynomial(x,n,coeff_m))
  return mass  
    
  
  
def DeprojectedSersicCumulativeMass(r,re,n,model):
  """
  r  : radius
  re : effective radius  
  n  : sersic index
  
  model : LN or PS
          LN = Lima Neto, Gerbal & Márquez 1999
          PS = Prugniel & Simien 1997
  """
  x = r/re
  
  if (model == 'LN') :
      p = pLN(n)
  if (model == 'PS') :
      p = pPS(n)
  try:
      p
  except NameError:
      print("You did not give a valid model")
      return  
  
  M = gammainc(n*(3-p), b(n) * x**(1/n)) 
  
  return M


####################################
#
#    M A I N
#
####################################


def CumulativeMass(M, re, n, r, G=1.):
  """
  Deprojected Sersic cumulative mass
  """
  #M = DeprojectedSersicCumulativeMassVitral(r,re,n)
  Mr = M*DeprojectedSersicCumulativeMass(r,re,n,'LN')
  return Mr


def Density(M, re, n, r, G=1.):
  """
  Deprojected Sersic Density
  """
  # Rho = DeprojectedSersicDensityVitral(r,re,n)
  Rho = M*DeprojectedSersicDensity(r,re,n,'LN')
  return Rho
   




