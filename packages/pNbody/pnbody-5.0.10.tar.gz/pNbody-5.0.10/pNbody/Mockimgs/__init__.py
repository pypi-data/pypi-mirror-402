#!/usr/bin/env python3
###########################################################################################
#  package:   Mockimgs
#  file:      __init__.py
#  brief:     init file
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from astropy import units as u

from . import instrument
from . import telescope
from . import filters
from . import ccd
from . import ifu
from . import mos
from . import obs_object



# list of telescopes      
telescopes = {}
telescopes["arrakihs"] = telescope.Telescope(name="iSIM-170",focal=1500*u.mm)
telescopes["euclid"]   = telescope.Telescope(name="Euclid"  ,focal=24.5*u.m)
telescopes["CTIO4.0m"]   = telescope.Telescope(name="CTIO4.0m"  ,focal=11.81*u.m)

# list of ccds
ccds = {}
ccds["arrakihs_vis"]   = ccd.CCD(name="arrakihs_vis",shape=[4096,4096],size=[41*u.mm,41*u.mm])
ccds["arrakihs_nir"]   = ccd.CCD(name="arrakihs_nir",shape=[2048,2048],size=[36.9*u.mm,36.9*u.mm])
ccds["CCD273-84"]      = ccd.CCD(name="CCD273-84"   ,shape=[4096,4096],pixel_size=[12*u.micron,12*u.micron])
ccds["CIS-300"]        = ccd.CCD(name="CIS-300"     ,shape=[4096,4096],pixel_size=[10*u.micron,10*u.micron])
ccds["Hawaii-2RG"]     = ccd.CCD(name="Hawaii-2RG"  ,shape=[2048,2048],pixel_size=[18*u.micron,18*u.micron])
ccds["DECam"]          = ccd.CCD(name="DECam"       ,shape=[2290,2290],pixel_size=[15*u.micron,15*u.micron])

#ccds["euclid_vis"]     = ccd.CCD(name="euclid_vis"  ,shape=[24576,24576])






# list of instruments
instruments = {}

#########################
# ARRAKIHS
#########################

###########
# Visible

# GAEA

instruments["arrakihs_vis_GAIA_VIS"] = instrument.Instrument(
  name        = "arrakihs_vis_GAIA_VIS",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("GAEA_VIS"),
  )

# BastI

instruments["arrakihs_vis_G"] = instrument.Instrument(
  name        = "arrakihs_vis_G",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_GAIA_G"),
  )

instruments["arrakihs_vis_G_RP"] = instrument.Instrument(
  name        = "arrakihs_vis_G_RP",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_GAIA_G_RP"),
  )
  
instruments["arrakihs_vis_G_BP"] = instrument.Instrument(
  name        = "arrakihs_vis_G_BP",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_GAIA_G_BP"),
  )  

instruments["arrakihs_vis_SDSSu"] = instrument.Instrument(
  name        = "arrakihs_vis_SDSSu",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_SDSS_u"),
  )
  
instruments["arrakihs_vis_SDSSg"] = instrument.Instrument(
  name        = "arrakihs_vis_SDSSg",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_SDSS_g"),
  )
  
instruments["arrakihs_vis_SDSSr"] = instrument.Instrument(
  name        = "arrakihs_vis_SDSSr",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_SDSS_r"),
  )

instruments["arrakihs_vis_SDSSi"] = instrument.Instrument(
  name        = "arrakihs_vis_SDSSi",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_SDSS_i"),
  )

instruments["arrakihs_vis_SDSSz"] = instrument.Instrument(
  name        = "arrakihs_vis_SDSSz",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_SDSS_z"),
  )
  
instruments["arrakihs_vis_F475X"] = instrument.Instrument(
  name        = "arrakihs_vis_F475X",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_HST_F475X"),
  )  
    
instruments["arrakihs_vis_VIS"] = instrument.Instrument(
  name        = "arrakihs_vis_VIS",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BastI_Euclid_VIS"),
  )    

# SB99
#instruments["arrakihs_vis_VIS1"] = instrument.Instrument(
#  name        = "arrakihs_vis_VIS1",
#  telescope   = telescopes["arrakihs"],
#  ccd         = ccds["CIS-300"],
#  filter_type = filters.Filter("SB99_ARK_VIS1"),
#  )

#instruments["arrakihs_vis_VIS2"] = instrument.Instrument(
#  name        = "arrakihs_vis_VIS2",
#  telescope   = telescopes["arrakihs"],
#  ccd         = ccds["CIS-300"],
#  filter_type = filters.Filter("SB99_ARK_VIS2"),
#  )

# BPASS
instruments["arrakihs_vis_VIS1"] = instrument.Instrument(
  name        = "arrakihs_vis_VIS1",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BPASS230_ARK_VIS1"),
  )

instruments["arrakihs_vis_VIS2"] = instrument.Instrument(
  name        = "arrakihs_vis_VIS2",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["CIS-300"],
  filter_type = filters.Filter("BPASS230_ARK_VIS2"),
  )






##################
# Near Infrared

# GAEA

instruments["arrakihs_nir_GAIA_Y"] = instrument.Instrument(
  name        = "arrakihs_nir_GAIA_Y",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("GAEA_Y"),
  )

instruments["arrakihs_nir_GAIA_J"] = instrument.Instrument(
  name        = "arrakihs_nir_GAIA_J",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("GAEA_J"),
  )

# BastI

instruments["arrakihs_nir_J"] = instrument.Instrument(
  name        = "arrakihs_nir_J",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("BastI_Euclid_J"),
  )      

instruments["arrakihs_nir_Y"] = instrument.Instrument(
  name        = "arrakihs_nir_Y",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("BastI_Euclid_Y"),
  )      

instruments["arrakihs_nir_H"] = instrument.Instrument(
  name        = "arrakihs_nir_H",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("BastI_Euclid_H"),
  )   

# SB99

#instruments["arrakihs_nir_NIR1"] = instrument.Instrument(
#  name        = "arrakihs_nir_NIR1",
#  telescope   = telescopes["arrakihs"],
#  ccd         = ccds["Hawaii-2RG"],
#  filter_type = filters.Filter("SB99_ARK_NIR1"),
#  )   

#instruments["arrakihs_nir_NIR2"] = instrument.Instrument(
#  name        = "arrakihs_nir_NIR2",
#  telescope   = telescopes["arrakihs"],
#  ccd         = ccds["Hawaii-2RG"],
#  filter_type = filters.Filter("SB99_ARK_NIR2"),
#  )   
  
# BPASS (now default)

instruments["arrakihs_nir_NIR1"] = instrument.Instrument(
  name        = "arrakihs_nir_NIR1",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("BPASS230_ARK_NIR1"),
  )   

instruments["arrakihs_nir_NIR2"] = instrument.Instrument(
  name        = "arrakihs_nir_NIR2",
  telescope   = telescopes["arrakihs"],
  ccd         = ccds["Hawaii-2RG"],
  filter_type = filters.Filter("BPASS230_ARK_NIR2"),
  )     
  
  
  

#########################
# DES DECam (SDSS filters)
#########################

instruments["DES_DECam_SDSSg"] = instrument.Instrument(
  name        = "DES_DECam_SDSSg",
  telescope   = telescopes["CTIO4.0m"],
  ccd         = ccds["DECam"],
  filter_type = filters.Filter("BastI_SDSS_g"),
  )

instruments["DES_DECam_SDSSr"] = instrument.Instrument(
  name        = "DES_DECam_SDSSr",
  telescope   = telescopes["CTIO4.0m"],
  ccd         = ccds["DECam"],
  filter_type = filters.Filter("BastI_SDSS_r"),
  )

instruments["DES_DECam_SDSSz"] = instrument.Instrument(
  name        = "DES_DECam_SDSSz",
  telescope   = telescopes["CTIO4.0m"],
  ccd         = ccds["DECam"],
  filter_type = filters.Filter("BastI_SDSS_z"),
  )

instruments["DES_DECam_SDSSi"] = instrument.Instrument(
  name        = "DES_DECam_SDSSi",
  telescope   = telescopes["CTIO4.0m"],
  ccd         = ccds["DECam"],
  filter_type = filters.Filter("BastI_SDSS_i"),
  )




def InstrumentsList():
  
  for name in instruments.keys():
    print(60*"#")
    print(name)
    print(60*"#")
    instruments[name].info()
    print()
    print()
  
  
