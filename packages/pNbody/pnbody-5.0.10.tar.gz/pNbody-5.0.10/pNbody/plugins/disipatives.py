###########################################################################################
#  package:   pNbody
#  file:      dissipatives.py
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

        Label(
            box,
            text='dissipative period %5d' %
            (self.master.X.pdis)).grid(
            columnspan=2,
            column=0,
            row=0,
            sticky=E +
            N +
            S +
            W)
        Label(
            box,
            text='dissipative time   %5d' %
            (self.master.X.tdis)).grid(
            columnspan=2,
            column=0,
            row=1,
            sticky=E +
            N +
            S +
            W)
        Label(
            box,
            text='select particules with').grid(
            columnspan=2,
            column=0,
            row=2,
            sticky=E +
            N +
            S +
            W)

        Label(box, text='tdis < ').grid(column=0, row=3, sticky=E + N + S + W)
        Label(box, text='tdis > ').grid(column=0, row=5, sticky=E + N + S + W)

        self.andRad = Radiobutton(
            box,
            text="and",
            command=self.cmdRad,
            var=self.varRad,
            value="and")
        self.andRad.grid(column=0, row=4)
        self.orRad = Radiobutton(
            box,
            text="or",
            command=self.cmdRad,
            var=self.varRad,
            value="or")
        self.orRad.grid(column=1, row=4)

        self.t1Ent = Entry(box)
        self.t1Ent.grid(column=1, row=3, sticky=E + N + S + W)
        self.t2Ent = Entry(box)
        self.t2Ent.grid(column=1, row=5, sticky=E + N + S + W)

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
        t2 = float(self.t2Ent.get())

        # selection

        c1 = less(self.master.X.dis, t1)
        c2 = greater(self.master.X.dis, t2)

        if self.selectmode == 'and':
            c = c1 * c2
        elif self.selectmode == 'or':
            c = 1 - ((1 - c1) * (1 - c2))

        self.master.X = self.master.X.selectc(c)

        self.master.display()
        self.master.display_info(self.master.X)

        self.root.destroy()


Dissip(self)
