###########################################################################################
#  package:   pNbody
#  file:      dd.py
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

self.X = self.X.subdis(mode='dd')
self.display()
self.display_info(self.X)
