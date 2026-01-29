#!/usr/bin/env python3

###########################################################################################
#  package:   pNbody
#  file:      libvazdekis.py
#  brief:     Vazdekis luminosities
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
###########################################################################################


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

    # now, read the file content
    lines = f.readlines()
    f.close()

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


BAND_DIC = {"U":18,"B":19,"V":20,"R":21,"I":22}

class VazdekisLuminosities(SSPLuminosities):
  
    
    def Read(self):
        """
        read file and create a data table
        """
        self.data = read_ascii(self.file, cchar='#', skipheader=True)

    def CreateMatrix(self):
        """
        from data extract
        metalicites (zs)
        ages (ages)
        and ML (vs)
        """
        zs = self.data[1, :]
        ages = self.data[2, :]
        mls = self.data[BAND_DIC[self.band], :]

        # create borders
        Zs = [-2.3152, -1.7129, -1.3146, -0.7052, -0.3960, 0.0000, 0.2223]
        Ages = np.compress(Zs[1] == zs, ages)

        MatLv = np.zeros((len(Zs), len(Ages)))

        for iZ, Z in enumerate(Zs):

            zs, ages, mls

            c = (zs == Z)

            age = np.compress(c, ages)
            ml = np.compress(c, mls)
            Lv = 1 / ml

            if len(age) < len(Ages):
                n = len(Ages) - len(age)
                age = np.concatenate((Ages[:n], age))
                Lv = np.concatenate((1e-10 * np.ones(n), Lv))

            MatLv[iZ, :] = Lv

        self.MatLv = MatLv
        self.Ages = Ages
        self.Zs = Zs
