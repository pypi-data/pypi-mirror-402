#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      parameters.py
#  brief:     Deal with environment variables
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import os
import sys
import string

################################
# installation path
################################
PNBODYPATH = os.path.dirname(__file__)
#PNBODYPATH = PNBODYPATH.split("/")[:-1]
#PNBODYPATH = '/'.join(PNBODYPATH)

################################
# home directory
################################
HOME = os.environ['HOME']

################################
# default config directory
################################
CONFIGDIR = os.path.join(PNBODYPATH, 'config')

# parameter file
PARAMETERFILE = os.path.join(CONFIGDIR, 'defaultparameters')
if os.path.isfile(os.path.join(HOME, '.pNbody', 'defaultparameters')):
    PARAMETERFILE = os.path.join(HOME, '.pNbody', 'defaultparameters')

# parameter file
UNITSPARAMETERFILE = os.path.join(CONFIGDIR, 'unitsparameters')
if os.path.isfile(os.path.join(HOME, '.pNbody', 'unitsparameters')):
    UNITSPARAMETERFILE = os.path.join(HOME, '.pNbody', 'unitsparameters')

# default palette dir
PALETTEDIR = os.path.join(CONFIGDIR, 'rgb_tables')
if os.path.isdir(os.path.join(HOME, '.pNbody', 'rgb_tables')):
    PALETTEDIR = os.path.join(os.path.join(HOME, '.pNbody', 'rgb_tables'))
# default plugins dir
PLUGINSDIR = os.path.join(CONFIGDIR, 'plugins')
if os.path.isdir(os.path.join(HOME, '.pNbody', 'plugins')):
    PLUGINSDIR = os.path.join(os.path.join(HOME, '.pNbody', 'plugins'))
# default opt dir
OPTDIR = os.path.join(CONFIGDIR, 'opt')
if os.path.isdir(os.path.join(HOME, '.pNbody', 'opt')):
    OPTDIR = os.path.join(os.path.join(HOME, '.pNbody', 'opt'))

# user format dir
if os.path.isdir(os.path.join(HOME, '.pNbody', 'formats')):
    FORMATSDIR = os.path.join(HOME, '.pNbody', 'formats')
else:
    FORMATSDIR = os.path.join(CONFIGDIR, 'formats')


EXTENSIONS = "extensions"
EXTENSIONSDIRS = [os.path.join(CONFIGDIR, EXTENSIONS)]
if os.path.isdir(os.path.join(HOME, '.pNbody', EXTENSIONS)):
    EXTENSIONSDIRS.append(os.path.join(HOME, '.pNbody', EXTENSIONS))

# if os.path.isdir(os.path.join(HOME,'.pNbody', 'extensions')):
#  EXTENSIONSDIR = os.path.join(HOME,'.pNbody', 'extensions')
# else:
#  EXTENSIONSDIR = os.path.join(CONFIGDIR,'extensions')


PREFERRED_FORMATFILE = "preferred_format"
DEFAULT_EXTENSION = "default_extension"

# default format file
# if os.path.isfile(os.path.join(PNBODYPATH,'formats.py')):
#  FORMATSFILE = os.path.join(PNBODYPATH,'formats.py')
# else:
#  FORMATSFILE = None


# user format file
# if os.path.isfile(os.path.join(HOME,'.pNbody','formats.py')):
#  USERFORMATSFILE = os.path.join(HOME,'.pNbody','formats.py')
# else:
#  USERFORMATSFILE = os.path.join(HOME,'CONFIGDIR','formats.py')


# other parameters
DEFAULTPALETTE = 'light'


# filter dir
if os.path.isdir(os.path.join(HOME, '.pNbody', 'opt', 'filters')):
    FILTERSDIR = os.path.join(HOME, '.pNbody', 'opt', 'filters')
else:
    FILTERSDIR = os.path.join(CONFIGDIR, 'opt', 'filters')
    


def print_path():

    print()
    print(("HOME               : %s" % HOME))
    print(("PNBODYPATH         : %s" % PNBODYPATH))
    print(("CONFIGDIR          : %s" % CONFIGDIR))
    print()
    print(("PARAMETERFILE      : %s" % PARAMETERFILE))
    print(("UNITSPARAMETERFILE : %s" % UNITSPARAMETERFILE))
    print(("PALETTEDIR         : %s" % PALETTEDIR))
    print(("PLUGINSDIR         : %s" % PLUGINSDIR))
    print(("OPTDIR             : %s" % OPTDIR))
    print(("FILTERSDIR         : %s" % FILTERSDIR))
    print(("FORMATSDIR         : %s" % FORMATSDIR))
    print(("EXTENSIONSDIR      : %s" % EXTENSIONSDIRS[0]))
    for EXTENSIONSDIR in EXTENSIONSDIRS[1:]:
        print(("                   : %s" % EXTENSIONSDIR))
    print()
