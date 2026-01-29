#!/usr/bin/env python3

###########################################################################################
#  package:   pNbody
#  file:      libbruzual.py
#  brief:     bruzual luminosities
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
###########################################################################################

import os
import numpy as np

from .libSSPluminosity import SSPLuminosities


#####################################################
def read_ascii(
        file,
        columns=None,
        lines=None,
        dtype=float,
        skipheader=False,
        cchar='#'):
    #####################################################
    """[X,Y,Z] = READ('FILE',[1,4,13],lines=[10,1000])
    Read columns 1,4 and 13 from 'FILE'  from line 10 to 1000
    into array X,Y and Z

    file is either fd or name file

    """

    def RemoveComments(l):
        if l[0] == cchar:
            return None
        else:
            return l

    def toNumList(l):
        return list(map(dtype, l))

    if isinstance(file, str):
        f = open(file, 'r')
    else:
        f = file

    # read header while there is one
    while True:
        fpos = f.tell()
        header = f.readline()
        if header[0] != cchar:
            f.seek(fpos)
            header = None
            break
        else:
            if skipheader:
                header = None
            else:
                # create dict from header
                header = str.strip(header[2:])
                elts = str.split(header)
                break

    """
  # read header if there is one
  header = f.readline()
  if header[0] != cchar:
    f.seek(0)
    header = None
  else:
    if skipheader:
      header = None
    else:
      # create dict from header
      header = string.strip(header[2:])
      elts = string.split(header)
  """

    # now, read the file content
    lines = f.readlines()

    # remove trailing
    lines = list(map(str.strip, lines))

    # remove comments
    #lines = map(RemoveComments, lines)

    # split
    lines = list(map(str.split, lines))

    # convert into float
    lines = list(map(toNumList, lines))

    # convert into array
    lines = np.array(list(map(np.array, lines)))

    # np.transpose
    lines = np.transpose(lines)

    if header is not None:
        iobs = {}
        i = 0
        for elt in elts:
            iobs[elt] = i
            i = i + 1

        vals = {}
        for key in list(iobs.keys()):
            vals[key] = lines[iobs[key]]

        return vals

    # return
    if columns is None:
        return lines
    else:
        return lines.take(axis=0, indices=columns)


class BruzualLuminosities(SSPLuminosities):

    def __init__(self, directory):

        Z0 = 0.02

        self.Ids = [22, 32, 42, 52, 62, 72]
        self.Zs = np.array([0.0001, 0.0004, 0.004, 0.008, 0.02, 0.05])
        self.Zs = np.log10(self.Zs / Z0)

        self.directory = directory

        # read files and crate self.data
        self.Read()

        # create the matrix
        self.CreateMatrix()

    def Read(self):
        """
        read files and create a data table
        """

        self.data = {}

        for Id, Z in zip(self.Ids, self.Zs):
            name = os.path.join(
                self.directory,
                "bc2003_hr_m%d_salp_ssp.1color" %
                (Id))
            data = read_ascii(name, skipheader=True, cchar='#')
            self.data[Z] = data

    def CreateMatrix(self):
        """
        from data extract
        metalicites (zs)
        ages (ages)
        and ML (vs)
        """

        # create borders
        Zs = self.Zs
        Ages = (10**self.data[Zs[0]][0]) / 1e9

        MatLv = np.zeros((len(Zs), len(Ages)))

        for iZ, z in enumerate(Zs):
            mv = self.data[z][4]
            mv0 = 4.83  # ok
            Lv = 10**(-(mv - mv0) / 2.5)
            MatLv[iZ, :] = Lv

        self.MatLv = MatLv
        self.Ages = Ages
        self.Zs = Zs
