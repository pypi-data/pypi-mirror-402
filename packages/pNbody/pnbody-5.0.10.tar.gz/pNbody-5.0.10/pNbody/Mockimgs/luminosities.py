###########################################################################################
#  package:   Mockimgs
#  file:      luminosities.py
#  brief:     filter class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import sys
import os
import numpy as np

from ..parameters import FILTERSDIR
from ..interpolator import SSPInterpolator
from ..iofunc import SSPGrid 

luminosity_dic = {}

# luminosity
luminosity_dic['BastI_L'] = (os.path.join(FILTERSDIR,"BolLum_BastI_1e6.hdf5"), "hdf5")
luminosity_dic['CMD_L']   = (os.path.join(FILTERSDIR,"Euclid_logL_CMD_1e6.pkl"), "PKL_LUM")


luminosity_dic['BPASS230_ARK_VIS1']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS1.hdf5"),    "hdf5")
luminosity_dic['BPASS230_ARK_VIS2']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS2.hdf5"),    "hdf5")
luminosity_dic['BPASS230_ARK_NIR1']    = (os.path.join(FILTERSDIR,"BPASS230_ARKNIR1.hdf5"),    "hdf5")
luminosity_dic['BPASS230_ARK_NIR2']    = (os.path.join(FILTERSDIR,"BPASS230_ARKNIR2.hdf5"),    "hdf5")

luminosity_dic['BPASS230_SDSS_u']      = (os.path.join(FILTERSDIR,"BPASS230_SDSSu.hdf5"),    "hdf5")
luminosity_dic['BPASS230_SDSS_g']      = (os.path.join(FILTERSDIR,"BPASS230_SDSSg.hdf5"),    "hdf5")
luminosity_dic['BPASS230_SDSS_r']      = (os.path.join(FILTERSDIR,"BPASS230_SDSSr.hdf5"),    "hdf5")
luminosity_dic['BPASS230_SDSS_i']      = (os.path.join(FILTERSDIR,"BPASS230_SDSSi.hdf5"),    "hdf5")
luminosity_dic['BPASS230_SDSS_z']      = (os.path.join(FILTERSDIR,"BPASS230_SDSSz.hdf5"),    "hdf5")

luminosity_dic['BPASS230_Euclid_Y']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPY.hdf5"),    "hdf5")
luminosity_dic['BPASS230_Euclid_J']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPJ.hdf5"),    "hdf5")
luminosity_dic['BPASS230_Euclid_H']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPH.hdf5"),    "hdf5")
luminosity_dic['BPASS230_Euclid_VIS']  = (os.path.join(FILTERSDIR,"BPASS230_EuclidVIS.hdf5"),      "hdf5")

luminosity_dic['BPASS230_JKC_U']  = (os.path.join(FILTERSDIR,"BPASS230_JKC_U.hdf5"),      "hdf5")
luminosity_dic['BPASS230_JKC_V']  = (os.path.join(FILTERSDIR,"BPASS230_JKC_V.hdf5"),      "hdf5")

default = "BastI_L"

def getList():
  """
  return a list of current available luminosity models
  """
  for k in luminosity_dic.keys():
    print(k)
    
    
    
def LuminosityModel(name,luminosity_type=None):
  """
  the luminosity class builder
  """
  
  if os.path.isfile(name):
    filename = name
    if luminosity_type is None:
      # try to find the filter type
      ext=os.path.splitext(name)[1]
            
      if   ext==".HDF5" or ext==".hdf5":
        luminosity_type="hdf5"
      elif ext==".PKL" or  ext==".pkl":
        luminosity_type="PKL"
      else:
        raise NameError("Unrecognized luminosity model type %s"%name) 
  else:
    filename,luminosity_type = luminosity_dic[name]    
  

  if luminosity_type == "PKL_LUM":
    return LuminosityPKL(filename)    

  elif luminosity_type == "hdf5":
    return LuminosityHDF5(filename) 

        
  raise NameError("Unknown filter %s"%name) 
  
  


class LuminosityClass():
  """
  the luminosity class
  """
  
  def __init__(self,filename):
    """
    filename : file name
    """
    
    self.file = filename
    
    # read the file containing the filter information
    Ages,Zs,Lf,Lb,MfinMini = self.Read()
    
    # create the interpolator (bolometric)
    if Lb is not None:
      self.Lb_interpolator = SSPInterpolator(Lb,Ages,Zs)

    # create the interpolator (in the filter)
    if Lf is not None:    
      self.Lf_interpolator = SSPInterpolator(Lf,Ages,Zs)

    # create the Mass ratio interpolator
    if MfinMini is not None:
      self.Mratio_interpolator = SSPInterpolator(MfinMini,Ages,Zs)
      

  def info(self):
    print("class : %s"%self.__class__.__name__)
    
  def get_parameters(self,fmt=None):
    """
    return a dictionary containing useful parameters    
    """
    params = {}    
    return params

  def Read(self):
    """
    read the file and create a table
    """
    pass





class LuminosityPKL(LuminosityClass):
  """
  the Luminosity PKL class
  """
  
  def Read(self):
    """
    special read for FilterPKL
    """
    import pickle
  
    # read the pickle file  
    f = open(self.file,"rb")
    data = pickle.load(f)
    binsAge = pickle.load(f)
    binsFe  = pickle.load(f)
    #MiMf = pickle.load(f)
    f.close()

    Lb = np.transpose(data)    
    Ages = binsAge
    Zs   = binsFe   
    
    # as provided in log
    Lb = 10**(Lb)
    
    Lf = None
    
    return Ages,Zs,Lf,Lb,None


  def Luminosities(self,mass, age, Z, current_mass=False):
    '''
    Ages are provided in Gyrs 
    '''  
    # convert ages to Myrs
    age = age*1e3
        
    # get magnitudes
    L = self.Lb_interpolator.Get(age,Z)
    # apply scaling
    L = L*mass
    
    return L



class LuminosityHDF5(LuminosityClass):
  """
  the Luminosity HDF5 class
  """
  
  def Read(self):
    """
    special read for FilterPKL
    """
    SSP = SSPGrid(self.file)
    data = SSP.read()
    
    
    if "Bolometric Luminosities" in data["Data"]:
      Lb = 10**np.transpose(data["Data"]["Bolometric Luminosities"])
      Lf = 10**np.transpose(data["Data"]["Luminosities"])
    else:
      Lb = 10**np.transpose(data["Data"]["Luminosities"])
      Lf = None
        
    MfinMini  = np.transpose(data["Data"]["MiniMfin"])    
    Ages = np.transpose(data["Data"]["Ages"])
    Zs   = np.transpose(data["Data"]["MH"])   
        
    # store the Sun Absolute Magnitude in this filter    
    self.SunAbsMag = data["Header"]["SunAbsMag"]
    
    
    return Ages,Zs,Lf,Lb,MfinMini

    
  def Luminosities(self,mass, age, MH, current_mass=False,bolometric=False):
    '''
    Return the corresponding bolometric luminosities
    
    mass       : initial SSP mass in Msol
    age        : SSP age in Gyr
    MH         : SSP metallicity in log10(M/M0)

    current_mass : if True, assume the mass to be the final SSP mass
                 and convert it to the initial SSP mass
                 default=False
    
    bolometric   : if False, return the luminosity in the filter   
                   if True, return the bolometric luminosity
                             
    
    '''  
    # convert ages to Myrs
    age = age*1e3
        
    # convert final mass to initial IMF mass
    if current_mass is True:
      mass = mass *self.Mratio_interpolator.Get(age,MH)
    
    # get magnitudes
    if bolometric is True:
      L = self.Lb_interpolator.Get(age,MH)
    else:
      L = self.Lf_interpolator.Get(age,MH)
    
    # apply scaling
    L = L*mass
        
    return L



  def SSPMassRatio(self, age, MH):
    """
    Return the ratio of the current SSP mass to the initial SSP mass
    """
    # convert ages to Myrs
    age = age*1e3
    return self.Mratio_interpolator.Get(age,MH)


  def MassToLightRatio(self, age, MH,bolometric=False):
    """
    Return the mass to light ratio of a stellar population of a given age and metallicity
    age        : SSP age in Gyr
    MH         : SSP metallicity in log10(M/M0)
    
    bolometric : if true,  the bolometric luminosity is used
                 if false, the luminosity is computed from the photons that passes through the filter.
    
    """
    
    Mass = 1e6 # set the initial SSP mass to 1e6 Msol (arbitrary)
    
    # mass of the current stellar population (in Msol)
    M = Mass * self.SSPMassRatio(age,MH)
    
    # luminosity of the current stellar population (in Lsol)
    L = self.Luminosities(Mass,age,MH,bolometric=bolometric)

    return M/L
    
    
  def Magnitudes2Luminosities(self,M):
    """
    For a given magnitude, return the corresponding Luminosity (in the same filter).
    """   
    return pow(10, (self.SunAbsMag - M) / 2.5)

  
  def Luminosities2Masses(self,Lx,age,MH,initial_mass_flag=False):
    """
    Transform a luminosity or a set of luminosities (in solar luminosity) in the current filter 
    into a stellar mass or stellar masses (in solar mass)
    
    Lx  : luminosity in the current filter in solar luminosity
    age : age in Gyr
    MH  : metallicity in log10(M/M0)    

    initial_mass_flag : if true, return the initial SSP mass
    
    """        
    ML = self.MassToLightRatio(age, MH)
    Mass = ML*Lx
    
    if initial_mass_flag:
      # convert to initial mass
      Mass = Mass/self.SSPMassRatio(age,MH)
    
    return Mass  
 
  
  def Magnitudes2Masses(self,M,age,MH,initial_mass_flag=False):
    """
    Transform a magnitude or a set of magnitudes in the current filter 
    into a stellar mass or stellar masses (in solar mass)
    
    Lx  : luminosity in the current filter in solar luminosity
    age : age in Gyr
    MH  : metallicity in log10(M/M0)    

    initial_mass : if true, return the initial SSP mass
    
    """           
    Lx = self.Magnitudes2Luminosities(M)
    return self.Luminosities2Masses(Lx,age,MH,initial_mass_flag=initial_mass_flag)


  def InitialMasses2EvolvedMasses(self,Mass,age,MH):
    """
    Transform an initial SSP mass or a set of masses 
    into an evolved mass or masses (after mass loss) correspondig to the given age.
    
    Mass: SSP mass (arbitrary units)
    age : SSP age in Gyr
    MH  : SSP metallicity in log10(M/M0)    
    
    """           
    return Mass * self.SSPMassRatio(age,MH)



