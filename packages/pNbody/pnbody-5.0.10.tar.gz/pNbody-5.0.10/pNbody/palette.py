#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      palette.py
#  brief:     Color palette for plots
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


"""
this module is used to deal with color palettes.
"""

try:
    import tkinter as tk
    from PIL import ImageTk
    is_tk = True
except ImportError:
    is_tk = False

import numpy as np
import os
import string
import glob


# import parameters
from .parameters import *

from PIL import Image
from scipy.interpolate import splrep, splev

##########################################################################
# read lut (palette)
##########################################################################


def readlut(filename=os.path.join(PALETTEDIR, DEFAULTPALETTE)):
    """
    Read a lut file.
    """

    numByte = 256

    file = open(filename, "r")

    data = file.read(numByte)
    data = file.read(numByte)

    # read red
    data = file.read(numByte)
    red = np.fromstring(data, 'b')

    # read green
    data = file.read(numByte)
    green = np.fromstring(data, 'b')

    # read blue
    data = file.read(numByte)
    blue = np.fromstring(data, 'b')

    file.close()

    # combine the colors

    pal = chr(red[0]) + chr(green[0]) + chr(blue[0])

    for i in range(1, 256):
        pal = pal + chr(red[i]) + chr(green[i]) + chr(blue[i])

    return pal


def read_gimp_palette(name):

    f = open(name)
    f.readline()
    pal = ''
    for i in range(255):
        line = f.readline()
        line = str.split(line)
        r = int(line[0])
        g = int(line[1])
        b = int(line[2])

        pal = pal + chr(r) + chr(g) + chr(b)

    return pal

##########################################################################
# Create a palette
##########################################################################


def getpalette(palettename):

    try:
        pal = read_gimp_palette(palettename)
    except BaseException:
        try:
            pal = readlut(palettename)
        except BaseException:
            pal = readlut()

    return(pal)


##########################
class EditParams:
    ##########################

    def __init__(self, master, c, w, d, r):

        self.master = master

        self.root = Toplevel()

        self.frame = Frame(self.root)
        self.frame.grid(column=0, row=0)

        # lablel c
        self.labelc = Label(self.frame, text='valeur c = ')
        self.labelc.grid(column=0, row=0)

        # entry c
        self.entryc = Entry(self.frame)
        self.entryc.grid(column=1, row=0)
        self.entryc.insert(INSERT, "%s" % c)

        # lablel w
        self.labelw = Label(self.frame, text='valeur w = ')
        self.labelw.grid(column=0, row=1)

        # entry w
        self.entryw = Entry(self.frame)
        self.entryw.grid(column=1, row=1)
        self.entryw.insert(INSERT, "%s" % w)

        # lablel d
        self.labeld = Label(self.frame, text='valeur d = ')
        self.labeld.grid(column=0, row=2)

        # entry d
        self.entryd = Entry(self.frame)
        self.entryd.grid(column=1, row=2)
        self.entryd.insert(INSERT, "%s" % d)

        # lablel r
        self.labelr = Label(self.frame, text='valeur r = ')
        self.labelr.grid(column=0, row=3)

        # entry r
        self.entryr = Entry(self.frame)
        self.entryr.grid(column=1, row=3)
        self.entryr.insert(INSERT, "%s" % r)

        # buttons
        self.sendbutton = Button(self.frame, text='send', command=self.send)
        self.sendbutton.grid(column=0, row=4)

        self.okbutton = Button(self.frame, text='ok', command=self.ok)
        self.okbutton.grid(column=1, row=4)

        self.cancelbutton = Button(
            self.frame, text='cancel', command=self.cancel)
        self.cancelbutton.grid(column=2, row=4)

    def ok(self):

        try:
            c = int(self.entryc.get())
        except BaseException:
            print("invalid value for c")

        try:
            w = int(self.entryw.get())
        except BaseException:
            print("invalid value for w")

        try:
            d = float(self.entryd.get())
        except BaseException:
            print("invalid value for d")

        try:
            r = int(self.entryr.get())
        except BaseException:
            print("invalid value for r")

        # send values to main
        self.master.c = c
        self.master.w = w
        self.master.d = d
        self.master.invert = r
        self.master.get(c=c, w=w, d=d, invert=r)
        self.master.draw()

        self.root.destroy()

    def send(self):

        try:
            c = int(self.entryc.get())
        except BaseException:
            print("invalid value for c")

        try:
            w = int(self.entryw.get())
        except BaseException:
            print("invalid value for w")

        try:
            d = float(self.entryd.get())
        except BaseException:
            print("invalid value for d")

        try:
            r = int(self.entryr.get())
        except BaseException:
            print("invalid value for r")

        # send values to main
        self.master.c = c
        self.master.w = w
        self.master.d = d
        self.master.invert = r
        self.master.get(c=c, w=w, d=d, invert=r)
        self.master.draw()

    def cancel(self):
        self.root.destroy()


##########################################################################
# Class Palette
##########################################################################

class Palette:

    def __init__(self, name='light'):

        self.name = self.check_palette_name(name)

        self.Canvas = None

        self.tables = glob.glob(os.path.join(PALETTEDIR, '*'))

        self.c = 128
        self.w = 256
        self.d = 256.
        self.invert = 0

        self.read(self.name)

    ###########################
    def check_palette_name(self, name):
        ###########################

        if os.path.isfile(name):
            pass
        else:
            name = os.path.join(PALETTEDIR, name)

        if not os.path.exists(name):
            print((name, "do not exists, using %s instead" % (DEFAULTPALETTE)))
            name = os.path.join(PALETTEDIR, DEFAULTPALETTE)

        return name

    ################################

    def read(self, name):
        ################################

        t = []
        r = []
        g = []
        b = []

        f = open(name)
        f.readline()
        pal = ''
        for i in range(256):
            line = f.readline()
            line = str.split(line)
            t.append(float(i))
            r.append(float(line[0]))
            g.append(float(line[1]))
            b.append(float(line[2]))

        self.t = np.array(t, float)
        self.r = np.array(r, float)
        self.g = np.array(g, float)
        self.b = np.array(b, float)

        # store initial values
        self.t0 = self.t
        self.r0 = self.r
        self.g0 = self.g
        self.b0 = self.b

        self.mkspline()
        # spline should not be done here
        self.get(c=self.c, w=self.w, d=self.d)

    ################################
    def write(self, name):
        ################################

        f = open(name, 'w')
        f.write("# table rgb (%s)\n" % name)

        for i in range(256):
            f.write("%3d %3d %3d\n" % (self.r[i], self.g[i], self.b[i]))

        f.close()

    ################################
    def mkspline(self):
        ################################

        # splines
        self.ar = splrep(self.t, self.r, s=0)
        self.ag = splrep(self.t, self.g, s=0)
        self.ab = splrep(self.t, self.b, s=0)

    ################################

    def append(self, p):
        ################################
        """
        add a new palette
        """

        c = self.r + self.g + self.b

        self.r = np.where(c == 0, p.r, self.r)
        self.g = np.where(c == 0, p.g, self.g)
        self.b = np.where(c == 0, p.b, self.b)

    ################################
    def getr(self, vals):
        ################################
        """
        return r value
        """
        vals = np.clip(vals, 0, 255)
        return self.r[vals]

    ################################
    def getg(self, vals):
        ################################
        """
        return g value
        """
        vals = np.clip(vals, 0, 255)
        return self.g[vals]

    ################################
    def getb(self, vals):
        ################################
        """
        return b value
        """
        vals = np.clip(vals, 0, 255)
        return self.b[vals]

    ################################
    def get(self, c=0, w=0, d=256., invert=0):
        ################################
        """
        return the palette

        w : width of the interval [0,255]
        c : center of the interval [0,255]

        """

        if w == 0 or c == 0:
            xmin = 0
            xmax = 256
        else:
            xmin = c - w / 2
            xmax = c + w / 2

        self.t = np.arange(xmin, xmax, (xmax - xmin) / 256.)

        # fonction logarithmique pour exemple
        if d < 256.:
            self.t = (np.log((self.t - xmin) / d + 1) /
                      np.log((xmax - xmin) / d + 1)) * (xmax - xmin) + xmin

        self.r = splev(self.t, self.ar)
        self.g = splev(self.t, self.ag)
        self.b = splev(self.t, self.ab)

        self.r = np.clip(self.r, 0., 255.)
        self.g = np.clip(self.g, 0., 255.)
        self.b = np.clip(self.b, 0., 255.)

        # inversion
        if invert:
            self.r = 255. - self.r
            self.g = 255. - self.g
            self.b = 255. - self.b

        self.palette = b''

        for i in range(256):

            r = int(self.r[i])
            g = int(self.g[i])
            b = int(self.b[i])

            self.palette = self.palette + \
                bytearray((r,)) + bytearray((g,)) + bytearray((b,))

    ################################
    def setrange(self, mn, mx):
        ################################
        """
        clip the palette between mn and mx

        NB: this function should be added to get

        mn = minimum
        mx = maximum

        """

        self.t = np.arange(0, 255, 255. / (mx - mn))

        self.r = splev(self.t, self.ar)
        self.g = splev(self.t, self.ag)
        self.b = splev(self.t, self.ab)

        self.r = np.clip(self.r, 0., 255.)
        self.g = np.clip(self.g, 0., 255.)
        self.b = np.clip(self.b, 0., 255.)

        # reconstuct the palette
        z = np.zeros(256, float)
        z[mn:mn + len(self.r)] = self.r
        self.r = z

        z = np.zeros(256, float)
        z[mn:mn + len(self.g)] = self.g
        self.g = z

        z = np.zeros(256, float)
        z[mn:mn + len(self.b)] = self.b
        self.b = z

        self.palette = b''

        for i in range(256):

            r = int(self.r[i])
            g = int(self.g[i])
            b = int(self.b[i])

            self.palette = self.palette + \
                bytearray((r,)) + bytearray((g,)) + bytearray((b,))

    ###########################

    def addFrame(self, frame):
        ###########################

        if is_tk:

            ###########################
            # frame
            ###########################

            self.Frame = frame
            self.Frame.bind('<Return>', self.revert)		  # marche pas...
            self.Frame.bind('<KeyPress-e>', self.edit) 	  # marche pas...

            ###########################
            # canvas
            ###########################

            self.Canvas = tk.Canvas(frame, height=48, width=512)
            self.Canvas.grid(column=0, row=0)
            self.Canvas.bind('<Motion>', self.motion)
            self.Canvas.bind('<B1-Motion>', self.move1)
            self.Canvas.bind('<B2-Motion>', self.move2)
            self.Canvas.bind('<B3-Motion>', self.move3)
            self.Canvas.bind('<Double-1>', self.mouse1)
            self.Canvas.bind('<Double-2>', self.edit)
            self.Canvas.bind('<Double-3>', self.mouse3)

            self.draw()

        else:
            print("addFrame : tk is not present")

    ###########################

    def change(self, name):
        ###########################

        self.name = self.check_palette_name(name)
        self.read(self.name)
        self.draw()

    ###########################
    def draw(self):
        ###########################

        if is_tk:

            palette_shape = (512, 48)

            data = chr(0)

            for i in range(0, 48):
                for j in range(0, 256):

                    data = data + chr(j)
                    data = data + chr(j)

            data = data[1:]

            # converting data
            image = Image.frombytes("P", palette_shape, data)

            # include the palette
            image.putpalette(self.palette)

            # create a Tk photo
            self.palette_pic = ImageTk.PhotoImage(image)

            # insert photo in the pannel
            if self.Canvas is not None:
                self.Canvas.create_image(
                    0., 0., anchor=tk.NW, image=self.palette_pic)

        else:

            print("draw : tk is not present")

    ###########################

    def edit(self, event):
        ###########################

        EditParams(self, self.c, self.w, self.d, self.invert)

    ###########################

    def mouse1(self, event):
        ###########################

        # find index in tables

        i = self.tables.index(self.name) + 1
        if i < len(self.tables):
            self.change(self.tables[i])

    ###########################
    def mouse2(self, event):
        ###########################

        # find index in tables

        i = self.tables.index(self.name) - 1
        if i >= 0:
            self.change(self.tables[i])

    ###########################
    def move1(self, event):
        ###########################

        self.c = self.c - (event.x - self.oevent.x)

        self.get(c=self.c, w=self.w, d=self.d)
        self.draw()

        self.oevent = event

    ###########################
    def move2(self, event):
        ###########################

        self.w = self.w + (event.x - self.oevent.x)

        self.get(c=self.c, w=self.w, d=self.d)
        self.draw()

        self.oevent = event

    ###########################
    def move3(self, event):
        ###########################

        self.d = self.d + (event.x - self.oevent.x) * (0.01 * self.d)

        if self.d < 0.:
            self.d = 1e-3
        if self.d > 256.:
            self.d = 256.

        self.get(c=self.c, w=self.w, d=self.d)
        self.draw()

        self.oevent = event

    ###########################
    def mouse3(self, event):
        ###########################

        self.c = 128
        self.w = 256
        self.d = 256.
        self.invert = 0
        self.get(c=self.c, w=self.w, d=self.d)
        self.draw()

        self.oevent = event

    ###########################
    def motion(self, event):
        ###########################

        self.oevent = event

    ###########################
    def revert(self, event):
        ###########################

        print("revert")
