###########################################################################################
#  package:   pNbody
#  file:      thermodyn.py
#  brief:     thermodynamics functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np
from astropy import constants as c
from astropy import units as u
#from pNbody.units import unitSystem
from pNbody import thermodynlib


# default adiabatic index
gamma = 5/3.


'''
lu = unitSystem()

def ToEnergySpec(x):
  if type(x) is not u.quantity.Quantity:
    x = x*lu.UnitEnergySpec
  return x

def ToDensity(x):
  if type(x) is not u.quantity.Quantity:
    x = x*lu.UnitDensity
  return x

def ToTemperature(x):
  if type(x) is not u.quantity.Quantity:
    x = x*lu.UnitTemperature
  return x  
'''

def checkQuantity(x):
  if type(x) is not u.quantity.Quantity:
    raise("must be an astropy Quantity")



# tabulation of the mean weight (from Grackle)
nt = 10
tt = np.array([1.0e+01, 1.0e+02, 1.0e+03, 1.0e+04, 1.3e+04,2.1e+04, 3.4e+04, 6.3e+04, 1.0e+05, 1.0e+09])
mt = np.array([1.18701555,1.15484424,1.09603514,0.9981496,0.96346395,0.65175895,0.6142901,0.6056833,0.5897776,0.58822635])



def MeanMolecularWeight(T):
  """
  mean molecular weight as a function of the Temperature
  T: temperature
  """
  return thermodynlib.MeanWeightT(T)


def UN_T(T):
  """
  UN_T(T) = energy normalized as a function of the Temperature
        = T/mu(T)
  T: temperature
  """
  return T / MeanMolecularWeight(T)


# tabulation of the normalized energy vs T
unr = UN_T(tt)


def T_UN(UN):
  """
  T_UN(UN) = temperature vs energy normalized
  
  inverse of UN_T(U)
  
  """
  
  if isinstance(UN, np.ndarray):

      T = np.zeros(len(UN))
      for i in range(len(UN)):
          T[i] = Tun(UN[i])

  else:

      logu = np.log(UN)
      uuu = np.exp(logu)

      if uuu < unr[0]:
          j = 1
      else:
          for j in range(1, nt):
              if (uuu > unr[j - 1]) and (uuu <= unr[j]):
                  break

      slope = np.log(tt[j] / tt[j - 1]) / np.log(unr[j] / unr[j - 1])
      T = np.exp(slope * (logu - np.log(unr[j])) + np.log(tt[j]))

  return T
  


def Temperature_fromEnergySpec(energy):
  """
  temperature from energy
  energy  : specific energy
  """
  # add units if needed
  #energy = ToEnergySpec(energy)
  checkQuantity(energy)

  # normalized energy : UN is in K
  UN = (gamma - 1) * c.m_p/c.k_B * energy 
    
  # compute temperature from normalized energy
  T = thermodynlib.Tun(UN.to(u.K).value)*u.K
  
  return T


def Temperature_fromSoundSpeed(density, sound_speed):
  """
  Temperature from Sound Speed
  density : density
  sound_speed  : sound speed  
  """
  energy = EnergySpec_fromSoundSpeed(density, sound_speed)
  return Temperature_fromEnergySpec(energy)


def Temperature_fromJeansMass(density, jeans_mass):
  """
  Temperature from Jeans Mass
  density : density
  jeans_mass  : jeans mass
  """
  energy = EnergySpec_fromJeansMass(density,jeans_mass)
  return Temperature_fromEnergySpec(energy)  







def Energy_fromTemperature(temperature):
  """
  temperature from energy
  energy  : specific energy
  """
  # add units if needed
  #temperature = ToTemperature(temperature)
  checkQuantity(temperature)
  
  U = 1/(gamma - 1.) * (c.k_B/c.m_p) * UN_T(temperature.to(u.K).value)*u.K

  #return ToEnergySpec(U)
  return U


def EnergySpec_fromSoundSpeed(density, sound_speed):
  """
  Energy Spec from Sound Speed
  density : density
  sound_speed  : sound speed  
  """
  checkQuantity(density)
  checkQuantity(sound_speed)  

  return sound_speed**2/((gamma - 1.) * gamma)


def EnergySpec_fromJeansMass(density, jeans_mass):
  """
  Energy Spec from Jeans Mass
  density : density
  jeans_mass  : jeans mass
  """
  Cs = SoundSpeed_fromJeansMass(density,jeans_mass)
  return EnergySpec_fromSoundSpeed(density,Cs)
  
  
  




def Pressure_fromEnergySpec(density, energy):
  """
  pressure from density and energy
  density : density
  energy  : specific energy
  """
  # add units if needed
  #density = ToDensity(density)
  #energy  = ToEnergySpec(energy)
  checkQuantity(density)
  checkQuantity(energy)

  return (gamma-1) * energy * density
    
    
def Pressure_fromTemperature(density, temperature):
  """
  pressure from density and temperature
  density : density
  temperature  : temperature
  """
  # add units if needed
  #density = ToDensity(density)
  #temperature  = ToTemperature(temperature)
  checkQuantity(density)
  checkQuantity(temperature)
    
  energy = Energy_fromTemperature(temperature)

  return Pressure_fromEnergySpec(density, energy)






def SoundSpeed_fromEnergySpec(density, energy):
  """
  Sound Speed
  density : density
  energy  : specific energy  
  """
  # add units if needed
  #density = ToDensity(density)
  #energy  = ToEnergySpec(energy)
  checkQuantity(density)
  checkQuantity(energy)  
  
  return np.sqrt((gamma - 1.) * gamma * energy)


def SoundSpeed_fromTemperature(density, temperature):
  """
  Sound Speed
  density : density
  energy  : specific energy  
  """
  energy = Energy_fromTemperature(temperature)  
  return SoundSpeed_fromEnergySpec(density, energy)
  

def SoundSpeed_fromJeansMass(density, jeans_mass):
  """
  Sound Speed
  density : density
  jeans_mass  : jeans mass 
  """
  # add units if needed
  #density = ToDensity(density)
  #energy  = ToEnergySpec(energy)
  checkQuantity(density)
  checkQuantity(jeans_mass)
  
  return (jeans_mass * (6 * c.G**(3 / 2.) * np.sqrt(density)) / np.pi**(5 / 2.))**(1/3.)






     
def JeansLength_fromEnergySpec(density, energy):
  """
  Jeans Length
  density : density
  energy  : specific energy  
  """  
  Cs = SoundSpeed_fromEnergySpec(density,energy)
  return Cs * np.sqrt(np.pi / (c.G * density))  


def JeansLength_fromTemperature(density, temperature):
  """
  Jeans Length
  density : density
  temperature  : temperature 
  """
  energy = Energy_fromTemperature(temperature)  
  return JeansLength_fromEnergySpec(density, energy)





def JeansMass_fromEnergySpec(density, energy):
  """
  Jeans Mass
  density : density
  energy  : specific energy  
  """
  Cs = SoundSpeed_fromEnergySpec(density,energy)
  return (np.pi**(5 / 2.) * Cs**3) / (6 * c.G**(3 / 2.) * np.sqrt(density))


def JeansMass_fromTemperature(density, temperature):
  """
  Jeans Mass
  density : density
  temperature  : temperature 
  """
  energy = Energy_fromTemperature(temperature)  
  return JeansMass_fromEnergySpec(density, energy)














