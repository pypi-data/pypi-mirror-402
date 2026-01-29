###########################################################################################
#  package:   pNbody
#  file:      cut.py
#  brief:
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from Nbody import *
from Numeric import *

xm = self.params.get('size')[0]
zm = self.params.get('size')[1]
xmin = - xm
xmax = + xm
zmin = - zm
zmax = + zm

# expose the model
self.nbodyviewer.pose()

# keep only particules that are in the window
self.X = self.X.selectp(self.nbodyviewer.X.num)


x = self.nbodyviewer.X.pos[:, 0]
z = self.nbodyviewer.X.pos[:, 2]

cx1 = greater(x, xmin)
cx2 = less(x, xmax)

cz1 = greater(z, zmin)
cz2 = less(z, zmax)

self.X = self.X.selectc(cx1 * cx2 * cz1 * cz2)

# redisplay
self.display()
self.display_info(self.X)
