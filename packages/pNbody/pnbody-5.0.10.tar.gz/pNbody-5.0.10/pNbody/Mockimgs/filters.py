###########################################################################################
#  package:   Mockimgs
#  file:      filters.py
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

from astropy import units as u
from astropy import constants as c
from scipy import integrate

from ..parameters import FILTERSDIR
from ..interpolator import SSPInterpolator
from ..iofunc import SSPGrid 
from .spectra import Spectra 

filters_dic = {}

# magnitude
filters_dic['GAEA_B']          = (os.path.join(FILTERSDIR,"ages_mag_B.dat"),  "GAEA")
filters_dic['GAEA_VIS']        = (os.path.join(FILTERSDIR,"ages_mag_VIS.dat"),"GAEA")
filters_dic['GAEA_Y']          = (os.path.join(FILTERSDIR,"ages_mag_Y.dat"),  "GAEA")
filters_dic['GAEA_J']          = (os.path.join(FILTERSDIR,"ages_mag_J.dat"),  "GAEA")

filters_dic['CMD_F475X']       = (os.path.join(FILTERSDIR,"HSTF475Xmag_CMD_1e6_patched.pkl"),   "CMD")
filters_dic['CMD_VIS']         = (os.path.join(FILTERSDIR,"EuclidVISmag_CMD_1e6_patched.pkl"),  "CMD")
filters_dic['CMD_VISb']        = (os.path.join(FILTERSDIR,"EuclidVISmag_CMD_1e6_b_patched.pkl"),"CMD")
filters_dic['CMD_Y']           = (os.path.join(FILTERSDIR,"EuclidYmag_CMD_1e6_patched.pkl"),    "CMD")
filters_dic['CMD_J']           = (os.path.join(FILTERSDIR,"EuclidJmag_CMD_1e6_patched.pkl"),    "CMD")

filters_dic['BastI_GAIA_G']    = (os.path.join(FILTERSDIR,"GAIA_G_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_GAIA_G_RP'] = (os.path.join(FILTERSDIR,"GAIA_G_RP_BastI_1e6.hdf5"), "hdf5")
filters_dic['BastI_GAIA_G_BP'] = (os.path.join(FILTERSDIR,"GAIA_G_BP_BastI_1e6.hdf5"), "hdf5")
filters_dic['BastI_SDSS_u']    = (os.path.join(FILTERSDIR,"SDSS_u_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_SDSS_g']    = (os.path.join(FILTERSDIR,"SDSS_g_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_SDSS_r']    = (os.path.join(FILTERSDIR,"SDSS_r_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_SDSS_i']    = (os.path.join(FILTERSDIR,"SDSS_i_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_SDSS_z']    = (os.path.join(FILTERSDIR,"SDSS_z_BastI_1e6.hdf5"),    "hdf5")
filters_dic['BastI_HST_F475X'] = (os.path.join(FILTERSDIR,"HST_F475X_BastI_1e6.hdf5"), "hdf5")
filters_dic['BastI_Euclid_VIS']= (os.path.join(FILTERSDIR,"Euclid_VIS_BastI_1e6.hdf5"),"hdf5")
filters_dic['BastI_Euclid_J']  = (os.path.join(FILTERSDIR,"Euclid_J_BastI_1e6.hdf5"),  "hdf5")
filters_dic['BastI_Euclid_Y']  = (os.path.join(FILTERSDIR,"Euclid_Y_BastI_1e6.hdf5"),  "hdf5")
filters_dic['BastI_Euclid_H']  = (os.path.join(FILTERSDIR,"Euclid_H_BastI_1e6.hdf5"),  "hdf5")
filters_dic['BastI_Jonhson_V']  = (os.path.join(FILTERSDIR,"Johnson_V_BastI_1e6.hdf5"),  "hdf5")


filters_dic['SB99_SDSS_u']    = (os.path.join(FILTERSDIR,"SB99_SDSSu.hdf5"),    "hdf5")
filters_dic['SB99_SDSS_g']    = (os.path.join(FILTERSDIR,"SB99_SDSSg.hdf5"),    "hdf5")
filters_dic['SB99_SDSS_r']    = (os.path.join(FILTERSDIR,"SB99_SDSSr.hdf5"),    "hdf5")
filters_dic['SB99_SDSS_i']    = (os.path.join(FILTERSDIR,"SB99_SDSSi.hdf5"),    "hdf5")
filters_dic['SB99_SDSS_z']    = (os.path.join(FILTERSDIR,"SB99_SDSSz.hdf5"),    "hdf5")

filters_dic['SB99_ARK_VIS1']    = (os.path.join(FILTERSDIR,"SB99_ARKVIS1.hdf5"),    "hdf5")
filters_dic['SB99_ARK_VIS2']    = (os.path.join(FILTERSDIR,"SB99_ARKVIS2.hdf5"),    "hdf5")
filters_dic['SB99_ARK_NIR1']    = (os.path.join(FILTERSDIR,"SB99_ARKNIR1.hdf5"),    "hdf5")
filters_dic['SB99_ARK_NIR2']    = (os.path.join(FILTERSDIR,"SB99_ARKNIR2.hdf5"),    "hdf5")

filters_dic['BPASS230_ARK_VIS1']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS1.hdf5"),    "hdf5")
filters_dic['BPASS230_ARK_VIS2']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS2.hdf5"),    "hdf5")
filters_dic['BPASS230_ARK_VIS1bc']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS1bc.hdf5"),    "hdf5")
filters_dic['BPASS230_ARK_VIS2bc']    = (os.path.join(FILTERSDIR,"BPASS230_ARKVIS2bc.hdf5"),    "hdf5")
filters_dic['BPASS230_ARK_NIR1']    = (os.path.join(FILTERSDIR,"BPASS230_ARKNIR1.hdf5"),    "hdf5")
filters_dic['BPASS230_ARK_NIR2']    = (os.path.join(FILTERSDIR,"BPASS230_ARKNIR2.hdf5"),    "hdf5")


filters_dic['BPASS221_SDSS_u']    = (os.path.join(FILTERSDIR,"BPASS221_SDSSu.hdf5"),    "hdf5")
filters_dic['BPASS221_SDSS_g']    = (os.path.join(FILTERSDIR,"BPASS221_SDSSg.hdf5"),    "hdf5")
filters_dic['BPASS221_SDSS_r']    = (os.path.join(FILTERSDIR,"BPASS221_SDSSr.hdf5"),    "hdf5")
filters_dic['BPASS221_SDSS_i']    = (os.path.join(FILTERSDIR,"BPASS221_SDSSi.hdf5"),    "hdf5")
filters_dic['BPASS221_SDSS_z']    = (os.path.join(FILTERSDIR,"BPASS221_SDSSz.hdf5"),    "hdf5")

filters_dic['BPASS230_SDSS_u']    = (os.path.join(FILTERSDIR,"BPASS230_SDSSu.hdf5"),    "hdf5")
filters_dic['BPASS230_SDSS_g']    = (os.path.join(FILTERSDIR,"BPASS230_SDSSg.hdf5"),    "hdf5")
filters_dic['BPASS230_SDSS_r']    = (os.path.join(FILTERSDIR,"BPASS230_SDSSr.hdf5"),    "hdf5")
filters_dic['BPASS230_SDSS_i']    = (os.path.join(FILTERSDIR,"BPASS230_SDSSi.hdf5"),    "hdf5")
filters_dic['BPASS230_SDSS_z']    = (os.path.join(FILTERSDIR,"BPASS230_SDSSz.hdf5"),    "hdf5")

filters_dic['BPASS230_Euclid_Y']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPY.hdf5"),    "hdf5")
filters_dic['BPASS230_Euclid_J']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPJ.hdf5"),    "hdf5")
filters_dic['BPASS230_Euclid_H']    = (os.path.join(FILTERSDIR,"BPASS230_EuclidNISPH.hdf5"),    "hdf5")
filters_dic['BPASS230_Euclid_VIS']  = (os.path.join(FILTERSDIR,"BPASS230_EuclidVIS.hdf5"),      "hdf5")

filters_dic['BPASS230_JKC_U']  = (os.path.join(FILTERSDIR,"BPASS230_JKC_U.hdf5"),      "hdf5")
filters_dic['BPASS230_JKC_V']  = (os.path.join(FILTERSDIR,"BPASS230_JKC_V.hdf5"),      "hdf5")



default = "BastI_SDSS_g"


def List():
  """
  return a list of current available filters
  """  
  for name in filters_dic.keys():
    print(name)
    
    
def list():
  """
  return a list of current available filters
  """
  for k in filters_dic.keys():
    print(k)
          

class FilterCl(Spectra):
  '''
  Define a filter class that describe a filter from its transmission curve.
  
  filters are characterised by their transmission curve given as a function
  of the wavelength (by default in angstrom)
  
  '''

  def __init__(self,filter_filename):
    
    self.filter_filename = filter_filename
    self.read()    
    self.init()
    

  def read(self):
    """
    Read the file that contains the filter information
    and return the filter transmission
    as a function of the wavelength in Angstrom
    """
    data = np.loadtxt(self.filter_filename)
    # wavelength in Agstrom
    self.wavelength = data[:,0]*u.angstrom
    self.data       = data[:,1]
  
  
  def init(self):
    """
    init a set of useful quantities defining the properties of the filter
    """
    
    l = self.wavelength.to(u.angstrom).value
    R = self.data
    
    # Lambda mean (0.4719 micrometer)
    I1 = integrate.simpson(l*R,l)
    I2 = integrate.simpson(R,l)
    self.wavelength_mean = (I1/I2 * u.angstrom).to(u.micrometer)
    #print("lambda_mean [micrometer]",lambda_mean)
    
    
    # Lambda pivot (0.4702 micrometer)
    I1 = integrate.simpson(l*R,l)
    I2 = integrate.simpson(R/l,l)
    self.wavelength_pivot = (np.sqrt(I1/I2) * u.angstrom).to(u.micrometer)
    #print("lambda_pivot [micrometer]",lambda_pivot)
    
    # Lambda n1 (0.4751 micrometer)
    I1 = integrate.simpson(R*l**2,l)
    I2 = integrate.simpson(R*l   ,l)
    self.wavelength_n1 = (I1/I2 * u.angstrom).to(u.micrometer)
    #print("lambda_n1 [micrometer]",lambda_n1)
    
    # Lambda n2 (0.4686 micrometer)
    I1 = integrate.simpson(R,   l)
    I2 = integrate.simpson(R/l, l)
    self.wavelength_n2 = (I1/I2 * u.angstrom).to(u.micrometer)
    #print("lambda_n2 [micrometer]",lambda_n2)  
    
    # delta Lambda
    I1 = integrate.simpson(R,   l)
    self.delta_wavelength = I1/np.max(R) * u.angstrom

    # lambda_min
    self.wavelength_min = (self.wavelength_pivot - self.delta_wavelength/2).to(u.angstrom)
    #self.wavelength_min = min(l) * u.angstrom
    
    # lambda_max
    self.wavelength_max = (self.wavelength_pivot + self.delta_wavelength/2).to(u.angstrom)
    #self.wavelength_max = max(l) * u.angstrom
    
    # response maxW
    self.response_max = np.max(R)
    
    # total response
    c = (l>=self.wavelength_min.value)*(l<=self.wavelength_max.value)
    lc = np.compress(c,l)
    Rc = np.compress(c,R)
    I1 = integrate.simpson(Rc,   lc)
    I2 = lc[-1] - lc[0]
    self.TotalResponse = I1/I2
    
  
  def SEDmultiply(self,SED,wavelength):
    """
    multipy a given SED with the current filter
    
    SED        : the SED in arbitrary units
    wavelength : wavelength in angstrom 
    """
    
  
  def get_wavelength(self,units=u.angstrom):
    """
    get the wavelength
    """
    return self.wavelength.to(units)
  
  def get_response(self):
    """
    get the filter response
    """
    return self.get_data(units=None)

  


  
    

def Filter(name,filter_type=None):
  """
  the filter class builder
  """
  
  if os.path.isfile(name):
    filename = name
    if filter_type is None:
      # try to find the filter type
      ext=os.path.splitext(name)[1]
      if   ext==".HDF5" or ext==".hdf5":
        filter_type="hdf5"
      elif ext==".PKL" or  ext==".pkl":
        filter_type="CMD"
      else:
        raise NameError("Unrecognized filter type %s"%name) 
  else:
    filename,filter_type = filters_dic[name]  
  
  if   filter_type == "GAEA":
    return FilterGAEA(filename,filter_name=name)
  
  elif filter_type == "CMD" or filter_type == "BastI" or filter_type == "PKL":
    return FilterPKL(filename,filter_name=name)

  elif filter_type == "hdf5":
    return FilterHDF5(filename,filter_name=name)
           
  raise NameError("Unknown filter %s"%name) 



class FilterClass():
  """
  the filter class
  """
  
  def __init__(self,filename,filter_name=None):
    """
    filtername : name of the filter, e.g. GAEA_B, GAEA_VIS, BastI_GAIA_G
    """
    
    self.file = filename
    self.name = filter_name
    
    # read the file containing the filter information
    Ages,Zs,Mat,MfinMini = self.Read()
    
    # make global
    self.Mat = Mat
    
    # create the interpolator
    self.interpolator = SSPInterpolator(Mat,Ages,Zs)
    
    # create the Mass ratio interpolator
    if MfinMini is not None:
      self.Mratio_interpolator = SSPInterpolator(MfinMini,Ages,Zs)
    


  def info(self):
    print("filter class          : %s"%self.__class__.__name__)
    print("filter name           : %s"%self.name)
    
  def get_parameters(self,fmt=None):
    """
    return a dictionary containing useful parameters    
    """
    params = {}
    if fmt=="fits":
      params["FILTER"]           = (self.name,"Filter name")
    else:  
      params["filter_name"]      = self.name
    
    return params

  def Read(self):
    """
    read the file and create a table
    """
    pass




class FilterGAEA(FilterClass):
  """
  the filter GAEA class
  """
  
  def Read(self):
    """
    special read for FilterGAEA
    """
    from astropy.io import ascii 
    data = ascii.read(self.file)

    # from data extract metalicites (zs) ages (ages) and ML (vs)
    key_zs = [22, 32, 42, 52, 62, 72] # see http://www.bruzual.org/bc03/doc/bc03.pdf
    zs = [-2.2490, -1.6464, -0.6392, -0.3300, 0.0932, 0.5595]
    ages  = []
    for i in range(0,220):
      ages.append(data[i][0])

    Mat = np.zeros((len(ages), len(zs)))

    for i in range(len(ages)):
      for j in range(len(zs)):
        Mat[i][j] = data[i][j+1]

    Mat = Mat.transpose() # transpose to agree with the convention in libvazdekis.py
    
    # here Mat contains magnitudes
    return ages, zs, Mat, None


  def Magnitudes(self,mass, age, Z):
    '''
    Ages are provided in Gyrs 
    Mass in Msol
    '''  
    # convert ages to yrs
    age = age*1e9
    
    # get magnitudes
    M = self.interpolator.Get(age,Z)
    # normalize (tables assume 1e11 Msol)
    F = 10**(-M*0.4)*mass/1e11
    # back to magnitudes
    Mag = -2.5*np.log10(F)
    return Mag



class FilterPKL(FilterClass):
  """
  the Filter PKL class
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
    f.close()

    Mat = np.transpose(data)    
    Ages = binsAge
    Zs   = binsFe   
    
    return Ages,Zs, Mat, None


  def Magnitudes(self,mass, age, Z):
    '''
    Ages are provided in Gyrs 
    '''  
    # convert ages to Myrs
    age = age*1e3
        
    # get magnitudes
    M = self.interpolator.Get(age,Z)
    # transform to a flux
    F  = 10**(-M/2.5)
    F = F*mass
    # back to magnitudes
    Mag = -2.5*np.log10(F)
    
    return Mag



class FilterHDF5(FilterClass):
  """
  the Filter HDF5 class
  """
  
  def Read(self):
    """
    special read for FilterPKL
    """
    SSP = SSPGrid(self.file)
    data = SSP.read()

    Mat       = np.transpose(data["Data"]["Magnitudes"])
    MfinMini  = np.transpose(data["Data"]["MiniMfin"])    
    Ages      = np.transpose(data["Data"]["Ages"])
    Zs        = np.transpose(data["Data"]["MH"])   
    
    return Ages,Zs,Mat,MfinMini


  def Magnitudes(self,mass, age, MH, current_mass=False):
    '''
    mass       : initial SSP mass in Msol
    age        : SSP age in Gyr
    MH         : SSP metallicity in log10(M/M0)

    current_mass : if True, assume the mass to be the final SSP mass
                   and convert it to the initial SSP mass
                   default=False
                 : if False, assume the mass is the initial SSP mass
                 
    '''  
    # convert ages to Myrs
    age = age*1e3
    
    # convert final mass to initial IMF mass
    if current_mass is True:
      mass = mass *self.Mratio_interpolator.Get(age,MH)  
        
    # get magnitudes
    M = self.interpolator.Get(age,MH)
    # transform to a flux
    F  = 10**(-M/2.5)
    F = F*mass
    # back to magnitudes
    Mag = -2.5*np.log10(F)
        
    return Mag


  def SSPMassRatio(self, age, MH):
    """
    Return the ratio of the initial SSP to the final SSP mass
    """
    # convert ages to Myrs
    age = age*1e3
    return self.Mratio_interpolator.Get(age,MH)


