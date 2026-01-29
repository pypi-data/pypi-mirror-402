###########################################################################################
#  package:   pNbody
#  file:      newstar.py
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

from tkinter import *


class Dissip:

    def __init__(self, master):

        self.master = master

        self.varRad = StringVar()

        self.root = Toplevel()
        box = Frame(self.root)
        box.grid(column=0, row=0, sticky=E + N + S + W)

        Label(box, text='tstar < ').grid(column=0, row=3, sticky=E + N + S + W)

        self.t1Ent = Entry(box)
        self.t1Ent.grid(column=1, row=3, sticky=E + N + S + W)

        but = Frame(self.root)
        but.grid(column=0, row=1, sticky=E + N + S + W)
        Button(but, text='Cancel', command=self.onCancel).pack(side=RIGHT)
        Button(but, text='Ok', command=self.onSubmit).pack(side=RIGHT)

    def cmdRad(self):
        self.selectmode = self.varRad.get()

    def onCancel(self):
        self.root.destroy()

    def onSubmit(self):

        t1 = float(self.t1Ent.get())

        # selection

        c1 = less(self.master.X.dis, 1024. + t1)
        c2 = greater_equal(self.master.X.dis, 1024.)

        c = c1 * c2

        self.master.X = self.master.X.selectc(c)

        self.master.display()
        self.master.display_info(self.master.X)

        self.root.destroy()


Dissip(self)
