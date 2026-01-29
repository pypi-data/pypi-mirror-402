#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      kernels.py
#  brief:     kernels definitions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

"""
kernel implementation
see : Dehnen & Aly 2012
"""


import numpy as np

# normalization constants

C_cub_spline_1D  = 8/3.
C_qua_spline_1D  = 5**5/768
C_qui_spline_1D  = 3**5/40

C_cub_spline_2D  = 80./(7*np.pi)
C_qua_spline_2D  = 3*5**6/(2398*np.pi)
C_qui_spline_2D  = 7*3**7/(478*np.pi)

C_cub_spline_3D  = 16/np.pi
C_qua_spline_3D  = 5**6/(512*np.pi)
C_qui_spline_3D  = 3**7/(40*np.pi)

# H/h ratio
# h is the smoothing scale
# H is the kernel-support radius

Hh_cub_spline_1D = 1.732051
Hh_qua_spline_1D = 1.936492
Hh_qui_spline_1D = 2.121321

Hh_cub_spline_2D = 1.778002
Hh_qua_spline_2D = 1.977173
Hh_qui_spline_2D = 2.158131

Hh_cub_spline_3D = 1.825742
Hh_qua_spline_3D = 2.018932
Hh_qui_spline_3D = 2.195775



def cub_spline(r):
  '''
  Cubic spline 
  not normalized
  '''
  
  w1 = (1-r)
  w1 = np.where(w1>0,w1,0)**3
  
  w2 = (0.5-r) 
  w2 = -4*np.where(w2>0,w2,0)**3 
  
  w = w1+w2

  return w
  

def qua_spline(r):
  '''
  Quartic spline
  not normalized 
  '''  
    
  w1 = (1-r)
  w1 = np.where(w1>0,w1,0)**4

  w2 = (3/5-r) 
  w2 = -5*np.where(w2>0,w2,0)**4  

  w3 = (1/5-r) 
  w3 = +10*np.where(w3>0,w3,0)**4  
  
  w = w1+w2+w3

  return w


def qui_spline(r):
  '''
  Quintic spline
  not normalized 
  '''  
    
  w1 = (1-r)
  w1 = np.where(w1>0,w1,0)**5

  w2 = (2/3-r) 
  w2 = -6*np.where(w2>0,w2,0)**5  

  w3 = (1/3-r) 
  w3 = +15*np.where(w3>0,w3,0)**5  
    
  w = w1+w2+w3

  return w



def Wcub_1D(r,h):
  """
  Normalized 1D cubic kernel 
  
  h : the smoothing scale (2 sigma)
  """
  h = h*Hh_cub_spline_1D  # h becomes now H, the kernel-support radius
  return   C_cub_spline_1D * cub_spline(r/h)/h
  
def Wqua_1D(r,h):
  """
  Normalized 1D quadratic kernel 
  
  h : the smoothing scale (2 sigma)
  """  
  h = h*Hh_qua_spline_1D  # h becomes now H, the kernel-support radius
  return   C_qua_spline_1D * qua_spline(r/h)/h  
  
def Wqui_1D(r,h):
  """
  Normalized 1D quintic kernel 
  
  h : the smoothing scale (2 sigma)
  """    
  h = h*Hh_qui_spline_1D  # h becomes now H, the kernel-support radius
  return   C_qui_spline_1D * qui_spline(r/h)/h  

def Wcub_2D(r,h):
  """
  Normalized 2D cubic kernel 
  
  h : the smoothing scale (2 sigma)
  """  
  h = h*Hh_cub_spline_2D  # h becomes now H, the kernel-support radius
  return   C_cub_spline_2D * cub_spline(r/h)/h**2
  
def Wqua_2D(r,h):
  """
  Normalized 2D quadratic kernel 
  
  h : the smoothing scale (2 sigma)
  """    
  h = h*Hh_qua_spline_2D  # h becomes now H, the kernel-support radius
  return   C_qua_spline_2D * qua_spline(r/h)/h**2  
  
def Wqui_2D(r,h):
  """
  Normalized 2D quintic kernel 
  
  h : the smoothing scale (2 sigma)
  """    
  h = h*Hh_qui_spline_2D  # h becomes now H, the kernel-support radius
  return   C_qui_spline_2D * qui_spline(r/h)/h**2    
  
def Wcub_3D(r,h):
  """
  Normalized 3D cubic kernel 
  
  h : the smoothing scale (2 sigma)
  """
  h = h*Hh_cub_spline_3D  # h becomes now H, the kernel-support radius  
  return   C_cub_spline_3D * cub_spline(r/h)/h**3
  
def Wqua_3D(r,h):
  """
  Normalized 3D quadratic kernel 
  
  h : the smoothing scale (2 sigma)
  """    
  h = h*Hh_qua_spline_3D  # h becomes now H, the kernel-support radius
  return   C_qua_spline_3D * qua_spline(r/h)/h**3  
  
def Wqui_3D(r,h):
  """
  Normalized 3D quintic kernel 
  
  h : the smoothing scale (2 sigma)
  """  
  h = h*Hh_qui_spline_3D  # h becomes now H, the kernel-support radius
  return   C_qui_spline_3D * qui_spline(r/h)/h**3   
  


######################################
# serial C versions
######################################

def Wcub_1Ds(r,h):
  '''
  Normalized 1D cubic kernel : serial version
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_cub_spline_1D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +  max(1-r,0)**3
  w = w -4*max(0.5-r,0)**3  
  
  w = w *C_cub_spline_1D/h
  
  return w


def Wqua_1Ds(r,h):
  '''
  Normalized 1D quadratic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qua_spline_1D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**4
  w = w -5 *max(3/5-r,0)**4  
  w = w +10*max(1/5-r,0)**4
  
  w = w *C_qua_spline_1D/h
  
  return w  

def Wqui_1Ds(r,h):
  '''
  Normalized 1D quintic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qui_spline_1D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**5
  w = w -6 *max(2/3-r,0)**5  
  w = w +15*max(1/3-r,0)**5
  
  w = w *C_qui_spline_1D/h
  
  return w    
  


def Wcub_2Ds(r,h):
  '''
  Normalized 2D cubic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_cub_spline_2D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +  max(1-r,0)**3
  w = w -4*max(0.5-r,0)**3  
  
  w = w *C_cub_spline_2D/(h*h)
  
  return w


def Wqua_2Ds(r,h):
  '''
  Normalized 2D quadratic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qua_spline_2D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**4
  w = w -5 *max(3/5-r,0)**4  
  w = w +10*max(1/5-r,0)**4
  
  w = w *C_qua_spline_2D/(h*h)
  
  return w  

def Wqui_2Ds(r,h):
  '''
  Normalized 2D quintic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qui_spline_2D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**5
  w = w -6 *max(2/3-r,0)**5  
  w = w +15*max(1/3-r,0)**5
  
  w = w *C_qui_spline_2D/(h*h)
  
  return w    


def Wcub_3Ds(r,h):
  '''
  Normalized 3D cubic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_cub_spline_3D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +  max(1-r,0)**3
  w = w -4*max(0.5-r,0)**3  
  
  w = w *C_cub_spline_3D/(h*h*h)
  
  return w


def Wqua_3Ds(r,h):
  '''
  Normalized 3D quadratic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qua_spline_3D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**4
  w = w -5 *max(3/5-r,0)**4  
  w = w +10*max(1/5-r,0)**4
  
  w = w *C_qua_spline_3D/(h*h*h)
  
  return w  

def Wqui_3Ds(r,h):
  '''
  Normalized 3D quintic kernel : serial version 
  
  h : the smoothing scale (2 sigma)
  '''
  
  # h becomes now H, the kernel-support radius
  h = h*Hh_qui_spline_3D  
  
  # scale the radius
  r = r/h
  
  # normalized kernel part
  
  w = 0
  w = w +   max(1-r,0)**5
  w = w -6 *max(2/3-r,0)**5  
  w = w +15*max(1/3-r,0)**5
  
  w = w *C_qui_spline_3D/(h*h*h)
  
  return w   
