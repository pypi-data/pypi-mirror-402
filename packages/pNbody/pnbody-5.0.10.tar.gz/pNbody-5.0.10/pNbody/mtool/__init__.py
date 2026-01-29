#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      __init__.py
#  brief:     mtools functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################



is_ptools = False


import os
import glob

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import types

from numpy import *

import sys

from pNbody.palette import Palette
from astropy.io import fits as pyfits


def img_open(img, mode="RGB"):

    img = Image.open(img)
    if mode is not None:
        img = img.convert(mode)

    return img


def img_add_text(
        img,
        text=None,
        color=(
            0,
            0,
            0),
    pos=(
            0,
            0),
        size=32,
        font=None,
        center=None,
        cbox=None):
    '''
    text  : text
    color : color of the border
    pos   : text position
    size  : text size
    font  : text font
    center : horizontal,vertical
    cbox  : centering box
    '''

    if text is None:
        return img

    if font is None:
        raise Exception("you must specify a font name")

    font = ImageFont.truetype(font, size)

    if cbox is not None:
        size = (cbox[2], cbox[3])
    else:
        size = img.size

    if center == 'horizontal':
        pos = (size[0] / 2 - font.getsize(text)[0] / 2, pos[1])

    elif center == 'vertical':
        pos = (pos[0], size[1] / 2 - font.getsize(text)[1] / 2)

    elif center == "both":
        pos = (size[0] / 2 - font.getsize(text)[0] / 2, pos[1])
        pos = (pos[0], size[1] / 2 - font.getsize(text)[1] / 2)

    if cbox is not None:
        pos = (pos[0] + cbox[0], pos[1] + cbox[1])

    draw = ImageDraw.Draw(img)
    draw.text(pos, text, fill=color, font=font)

    return img


def img_add_borders(
        img,
        color=(
            0,
            0,
            0),
    size=None,
    location=None,
    width=0,
        height=0):
    '''
    color : color of the border
    size : final size of the image
            in this case, the border is computed automatically and the image centred
    locate : location of the border : top,bottom,left,right
    width  : width of the border
    '''

    h, w = img.size

    # set size of the new image
    if size is not None:

        # compute position
        x = (size[0] - img.size[0]) / 2
        y = (size[1] - img.size[1]) / 2

    elif location == 'top':
        size = (img.size[0], img.size[1] + height)
        x = 0
        y = height

    elif location == 'bottom':
        size = (img.size[0], img.size[1] + height)
        x = 0
        y = 0

    elif location == 'left':
        size = (img.size[0] + width, img.size[1])
        x = width
        y = 0

    elif location == 'right':
        size = (img.size[0] + width, img.size[1])
        x = 0
        y = 0

    elif location == 'top_bottom':
        size = (img.size[0], height)
        x = 0
        y = (height - img.size[1]) / 2

    else:
        raise Exception("add_borders : argument must be either size (tuple) or location (top,bottom,left,right)")

    dx = img.size[0]
    dy = img.size[1]
    box = (int(x), int(y), int(x + dx), int(y + dy))
    imgb = Image.new(img.mode, size, color)

    # paste image
    imgb.paste(img, box)
    img = imgb

    return img


def img_add_thumbnail(
        img,
        thumbnail,
        pos=(
            0,
            0),
    size=None,
    rotate=None,
        mask=0):
    '''
    thumbnail : name of the thumbnail
    pos  : position of the thumbnail
    size : final size of the thumbnail
    '''

    if isinstance(thumbnail, str):
        imga = Image.open(thumbnail)
    else:
        imga = thumbnail

    if rotate is not None:
        imga = imga.rotate(rotate)

    if size is None:
        size = imga.size

    # resize imga if needed
    if (imga.size[0] != size[0]) or (imga.size[1] != size[0]):
        imga = imga.resize(size)

    x = pos[0]
    y = pos[1]
    box = (x, y, x + size[0], y + size[1])

    # if you need a mask
    #r,g,b = imga.split()
    #mask = r

    if mask == 'use_thumbnail':
        mask = imga

    img.paste(imga, box, mask=mask)

    return img


def img_add_axes(img, thumbnail, pos=(0, 0), size=None, rotate=None):
    '''
    thumbnail : name of the thumbnail
    pos  : position of the thumbnail
    size : final size of the thumbnail
    '''

    if isinstance(thumbnail, str):
        imga = Image.open(thumbnail)
    else:
        imga = thumbnail

    if rotate is not None:
        imga = imga.rotate(rotate)

    if size is None:
        size = imga.size

    # resize imga if needed
    if (imga.size[0] != size[0]) or (imga.size[1] != size[0]):
        imga = imga.resize(size)

    x = pos[0]
    y = pos[1]
    box = (x, y, x + size[0], y + size[1])

    # get 1
    img = img.convert('RGB')
    r, g, b = img.split()
    r1 = array(r.getdata())
    g1 = array(g.getdata())
    b1 = array(b.getdata())

    # get 2
    imga = imga.convert('RGB')
    r, g, b = imga.split()
    r2 = array(r.getdata())
    g2 = array(g.getdata())
    b2 = array(b.getdata())

    # transform in grey (where diff. from white)
    c = ((r2 < 255) * (g2 < 255) * (b2 < 255))
    # new color
    r2 = where(r1 > 128, r2, 255 - r2)
    g2 = where(g1 > 128, g2, 255 - g2)
    b2 = where(b1 > 128, b2, 255 - b2)

    ra = where(c, r2, r1)
    ga = where(c, g2, g1)
    ba = where(c, b2, b1)

    # put
    r.putdata(ra.tolist())
    g.putdata(ga.tolist())
    b.putdata(ba.tolist())

    img = Image.merge("RGB", (r, g, b))

    return img


def img_crop(img, pos=(0, 0), size=None):
    '''
    pos  : position
    size : size
    '''

    if size is None:
        size = imga.size

    img = img.crop((pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]))

    return img


def img_resize(img, size=None):
    '''
    size : size
    '''

    if size is not None:
        img = img.resize(size)

    return img


def img_append(imgs, location='horizontal'):
    '''
    size : size
    '''

    size = None

    if location == 'horizontal':
        for j, img in enumerate(imgs):
            if size is None:
                size = (imgs[j].size[0], imgs[j].size[1])
            else:
                size = (size[0] + imgs[j].size[0], size[1])

        # create an empty image
        imgf = Image.new('RGB', (size[0], size[1]), (0, 0, 0))
        
        sizex = 0

        for j, img in enumerate(imgs):

            # paste vignette
            x = sizex
            y = 0

            dx = img.size[0]
            dy = img.size[1]

            sizex = sizex + dx

            box = (x, y, x + dx, y + dy)
            imgf.paste(img, box)

        return imgf

    if location == 'vertical':
        for j, img in enumerate(imgs):
            if size is None:
                size = (imgs[j].size[0], imgs[j].size[1])
            else:
                size = (size[0], size[1] + imgs[j].size[1])

        # create an empty image
        imgf = Image.new('RGB', (size[0], size[1]), (0, 0, 0))

        sizey = 0

        for j, img in enumerate(imgs):

            # paste vignette
            x = 0
            y = sizey

            dx = img.size[0]
            dy = img.size[1]

            sizey = sizey + dy

            box = (x, y, x + dx, y + dy)
            imgf.paste(img, box)

        return imgf

    raise Exception("unknown location")
    return None


def img_togrey(img, greyscale=1.):
    '''
    greyscale
    '''

    f = greyscale

    if isinstance(img, str):
        img = Image.open(img)

    img = img.convert("RGB")

    r, g, b = img.split()

    # get
    ra = array(r.getdata())
    ga = array(g.getdata())
    ba = array(b.getdata())

    # transform in grey
    c = sqrt((ra**2 + ga**2 + ba**2) / 3)
    ra = f * c + (1. - f) * ra
    ga = f * c + (1. - f) * ga
    ba = f * c + (1. - f) * ba

    # put
    r.putdata(ra.tolist())
    g.putdata(ga.tolist())
    b.putdata(ba.tolist())

    img = Image.merge("RGB", (r, g, b))

    return img


def img_merge(img1, img2, f=0):
    '''
    merge two images
    '''

    if isinstance(img1, str):
        img1 = Image.open(img1)

    if isinstance(img2, str):
        img2 = Image.open(img2)

    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB")

    # img1
    r1, g1, b1 = img1.split()
    r1a = array(r1.getdata())
    g1a = array(g1.getdata())
    b1a = array(b1.getdata())

    # img2
    r2, g2, b2 = img2.split()
    r2a = array(r2.getdata())
    g2a = array(g2.getdata())
    b2a = array(b2.getdata())

    r = r1
    g = g1
    b = b1

    ra = r2a * f + r1a * (1 - f)
    ga = g2a * f + g1a * (1 - f)
    ba = b2a * f + b1a * (1 - f)

    # put
    r.putdata(ra.tolist())
    g.putdata(ga.tolist())
    b.putdata(ba.tolist())

    img = Image.merge("RGB", (r, g, b))

    return img


def img_add_background(img1, img2):
    '''
    add a background image
    '''

    if isinstance(img1, str):
        img1 = Image.open(img1)

    if isinstance(img2, str):
        img2 = Image.open(img2)

    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB")

    # img1
    r1, g1, b1 = img1.split()
    r1a = array(r1.getdata())
    g1a = array(g1.getdata())
    b1a = array(b1.getdata())

    # img2
    r2, g2, b2 = img2.split()
    r2a = array(r2.getdata())
    g2a = array(g2.getdata())
    b2a = array(b2.getdata())

    r = r1
    g = g1
    b = b1

    c = (r1a == 0) + (g1a == 0) + (b1a == 0)
    ra = where(c, r2a, r1a)
    ga = where(c, g2a, g1a)
    ba = where(c, b2a, b1a)

    # put
    r.putdata(ra.tolist())
    g.putdata(ga.tolist())
    b.putdata(ba.tolist())

    img = Image.merge("RGB", (r, g, b))

    return img


def img_toanaglyph(img1, img2, greyscale=1.):
    '''
    size : size
    '''

    f = greyscale

    if isinstance(img1, str):
        img1 = Image.open(img1)

    if isinstance(img2, str):
        img2 = Image.open(img2)

    # extract first image
    r1, g1, b1 = img1.split()

    # get
    ra1 = array(r1.getdata())
    ga1 = array(g1.getdata())
    ba1 = array(b1.getdata())

    # transform in grey
    c = sqrt((ra1**2 + ga1**2 + ba1**2) / 3)
    ra1 = f * c + (1. - f) * ra1
    ga1 = f * c + (1. - f) * ga1
    ba1 = f * c + (1. - f) * ba1

    # extract second image
    r2, g2, b2 = img2.split()

    # get
    ra2 = array(r2.getdata())
    ga2 = array(g2.getdata())
    ba2 = array(b2.getdata())

    # transform in grey
    c = sqrt((ra2**2 + ga2**2 + ba2**2) / 3)
    ra2 = f * c + (1. - f) * ra2
    ga2 = f * c + (1. - f) * ga2
    ba2 = f * c + (1. - f) * ba2

    # compute anaglyph
    ra = ra1
    ga = ga2
    ba = ba2

    # put
    r1.putdata(ra.tolist())
    g1.putdata(ga.tolist())
    b1.putdata(ba.tolist())

    img = Image.merge("RGB", (r1, g1, b1))

    return img


def img_shade(img, level=1):
    '''
    shade an image
    '''

    if isinstance(img, str):
        img = Image.open(img)

    img = img.convert("RGB")

    r, g, b = img.split()

    # get
    ra = array(r.getdata())
    ga = array(g.getdata())
    ba = array(b.getdata())

    # apply the shading
    ra = level * ra
    ga = level * ga
    ba = level * ba

    # put
    r.putdata(ra.tolist())
    g.putdata(ga.tolist())
    b.putdata(ba.tolist())

    img = Image.merge("RGB", (r, g, b))

    return img


def img_flip_right_left(img):
    '''
    flip half of the right image to the left
    '''

    if isinstance(img, str):
        img = Image.open(img)

    size = img.size

    hw = size[0] / 2

    pos = (0, 0)
    img_left = img.crop((pos[0], pos[1], pos[0] + hw, pos[1] + size[1]))

    pos = (hw, 0)
    img_right = img.crop((pos[0], pos[1], pos[0] + hw, pos[1] + size[1]))

    return img_append([img_right, img_left])


##################################################################
# functions that needs Mtools
##################################################################


def img_add_mplaxes(
        img,
        xmin=0,
        xmax=1,
        ymin=0,
        ymax=1,
        xlabel=None,
        ylabel=None,
        log=None,
        figopts=None,
        text=None,
        invertcolor=False):

    if not is_ptools:
        raise Error(000, 'module ptools needed for function img_add_mplaxes !')

    import matplotlib.image as mpimg

    levelmin = 0.
    levelmax = 1.

    # options
    if figopts is None:
        figopts = {}
        figopts['size'] = (512, 512)

    figsize = figopts['size']

    if 'left' in figopts:
        left = figopts['left']
    else:
        left = 0.0

    if 'right' in figopts:
        right = figopts['right']
    else:
        right = 1.0

    if 'bottom' in figopts:
        bottom = figopts['bottom']
    else:
        bottom = 0.0

    if 'top' in figopts:
        top = figopts['top']
    else:
        top = 1.0

    if 'wspace' in figopts:
        wspace = figopts['wspace']
    else:
        wspace = 0.0

    if 'hspace' in figopts:
        hspace = figopts['hspace']
    else:
        hspace = 0.0

    name = "/tmp/%015d.png" % (int(random.random() * 1e17))
    img.save(name)
    img = mpimg.imread(name)
    os.remove(name)

    ################################################
    # matplotlib part

    # init Ptool
    pt.InitPlot(files=[''], opt=None)

    if invertcolor:
        pt.rc("axes", edgecolor='w')
        pt.rc("axes", facecolor='w')
        pt.rc("axes", labelcolor='w')
        pt.rc("xtick", color='w')
        pt.rc("ytick", color='w')
        pt.rc("figure", facecolor='k')

    # set size
    pt.figure(figsize=(figsize[0] / 100., figsize[1] / 100.))

    fig = pt.gcf()
    fig.subplots_adjust(left=left)
    fig.subplots_adjust(right=right)
    fig.subplots_adjust(bottom=bottom)
    fig.subplots_adjust(top=top)

    fig.subplots_adjust(wspace=wspace)
    fig.subplots_adjust(hspace=hspace)

    # add axes
    pt.imshow(img, extent=(xmin, xmax, ymin, ymax), aspect='auto')

    # add labels
    pt.SetAxis(xmin, xmax, ymin, ymax, log=log)

    # add text
    if text is not None:

        if not isinstance(text, list):
            text = [text]

        texts = text

        for text in texts:
            if 'verticalalignment' not in text:
                text['verticalalignment'] = 'center'
            if 'horizontalalignment' not in text:
                text['horizontalalignment'] = 'center'
            if 'backgroundcolor' not in text:
                text['backgroundcolor'] = (255, 255, 255)
            if 'color' not in text:
                text['color'] = (0, 0, 0)

            pt.text(
                text['x'],
                text['y'],
                text['text'],
                fontdict=None,
                withdash=False,
                fontsize=18,
                verticalalignment=text['verticalalignment'],
                horizontalalignment=text['horizontalalignment'],
                color=text['color'])

    if xlabel is not None:
        pt.xlabel(xlabel, fontsize=pt.labelfont)
    if ylabel is not None:
        pt.ylabel(ylabel, fontsize=pt.labelfont)

    # end of matplotlib part
    ################################################

    # now, create a PIL image
    import io
    ram = io.StringIO()
    if invertcolor:
        pt.savefig(ram, format='png', facecolor='k')
    else:
        pt.savefig(ram, format='png')
    ram.seek(0)

    img = Image.open(ram)

    # close the matplotlib plot
    pt.clf()
    pt.close('all')

    return img


def old_img_add_mplaxes(
        img,
        mn=0,
        mx=0,
        cd=0,
        scale='lin',
        xmin=0,
        xmax=1,
        ymin=0,
        ymax=1,
        palette='rainbow4',
        reversed=True,
        log=None,
        xlabel=None,
        ylabel=None,
        figopts=None,
        text=None):

    if not is_ptools:
        raise Error(000, 'module ptools needed for function img_add_mplaxes !')

    import matplotlib.image as mpimg

    levelmin = 0.
    levelmax = 1.

    # options
    if figopts is None:
        figopts = {}
        figopts['size'] = (512, 512)

    figsize = figopts['size']

    if 'left' in figopts:
        left = figopts['left']
    else:
        left = 0.0

    if 'right' in figopts:
        right = figopts['right']
    else:
        right = 1.0

    if 'bottom' in figopts:
        bottom = figopts['bottom']
    else:
        bottom = 0.0

    if 'top' in figopts:
        top = figopts['top']
    else:
        top = 1.0

    if 'wspace' in figopts:
        wspace = figopts['wspace']
    else:
        wspace = 0.0

    if 'hspace' in figopts:
        hspace = figopts['hspace']
    else:
        hspace = 0.0

    if isinstance(img, ndarray):
        data, mnopt, mxopt, cdopt = normalize(img, scale, mn, mx, cd)

    else:

        '''
        # open image
        img = img.convert('RGB')
        r,g,b = img.split()

        r = array(r.getdata())
        r.shape = (img.size[1],img.size[0])
        mat  = flipud(r.astype(float))


        # normalize between 0-1
        data,mnopt,mxopt,cdopt = normalize(mat,scale,mn,mx,cd)
        '''

        name = "/tmp/%015d.png" % (int(random.random() * 1e17))
        img.save(name)
        img = mpimg.imread(name)
        os.remove(name)

    ################################################
    # matplotlib part

    # init Ptool
    pt.InitPlot(files=[''], opt=None)

    # set size
    pt.figure(figsize=(figsize[0] / 100., figsize[1] / 100.))

    fig = pt.gcf()
    fig.subplots_adjust(left=left)
    fig.subplots_adjust(right=right)
    fig.subplots_adjust(bottom=bottom)
    fig.subplots_adjust(top=top)

    fig.subplots_adjust(wspace=wspace)
    fig.subplots_adjust(hspace=hspace)

    # set the palette
    cmap = pt.GetColormap(palette, revesed=reversed)

    # add axes
    #pt.imshow(data, interpolation='bilinear', origin='lower',cmap=cmap, extent=(xmin,xmax,ymin,ymax),aspect='auto',vmin=levelmin,vmax=levelmax)
    pt.imshow(img, extent=(xmin, xmax, ymin, ymax), aspect='auto')

    # add labels
    pt.SetAxis(xmin, xmax, ymin, ymax, log=log)

    # add text
    if text is not None:

        if not isinstance(text, list):
            text = [text]

        texts = text

        for text in texts:
            if 'verticalalignment' not in text:
                text['verticalalignment'] = 'center'
            if 'horizontalalignment' not in text:
                text['horizontalalignment'] = 'center'
            if 'backgroundcolor' not in text:
                text['backgroundcolor'] = (255, 255, 255)
            if 'color' not in text:
                text['color'] = (0, 0, 0)

            pt.text(
                text['x'],
                text['y'],
                text['text'],
                fontdict=None,
                withdash=False,
                fontsize=18,
                verticalalignment=text['verticalalignment'],
                horizontalalignment=text['horizontalalignment'],
                color=text['color'])

    if xlabel is not None:
        pt.xlabel(xlabel, fontsize=pt.labelfont)
    if ylabel is not None:
        pt.ylabel(ylabel, fontsize=pt.labelfont)

    # end of matplotlib part
    ################################################

    # now, create a PIL image
    import io
    ram = io.StringIO()
    pt.savefig(ram, format='png')
    ram.seek(0)

    img = Image.open(ram)

    # close the matplotlib plot
    pt.clf()
    pt.close('all')

    return img


def img_mplmkaxes(
        img,
        xmin=0,
        xmax=1,
        ymin=0,
        ymax=1,
        xlabel=None,
        ylabel=None,
        figsize=(
            512,
            512),
    log=None,
    text=None,
    x=0,
    y=0,
    fontsize=12,
    color='w',
        texts=None):

    if not is_ptools:
        raise Error(000, 'module ptools needed for function img_mplmkaxes !')

    ################################################
    # matplotlib part

    # init Ptool
    pt.InitPlot(files=[''], opt=None)

    # set size
    pt.figure(figsize=(figsize[0] / 100., figsize[1] / 100.))

    fig = pt.gcf()

    fig.subplots_adjust(left=0.07)
    fig.subplots_adjust(right=0.93)
    fig.subplots_adjust(bottom=0.07)
    fig.subplots_adjust(top=0.93)

    fig.subplots_adjust(wspace=0.0)
    fig.subplots_adjust(hspace=0.0)

    # add labels
    pt.SetAxis(xmin, xmax, ymin, ymax, log=log)

    # add text
    if text is not None:
        pt.text(
            x,
            y,
            text,
            fontdict=None,
            color=color,
            withdash=False,
            fontsize=fontsize,
            verticalalignment='center',
            horizontalalignment='center')

    if texts is not None:
        for text in texts:
            string = text['text']
            x = text['x']
            y = text['y']
            color = text['color']
            fontsize = text['fontsize']
            pt.text(
                x,
                y,
                string,
                fontdict=None,
                color=color,
                withdash=False,
                fontsize=fontsize,
                verticalalignment='center',
                horizontalalignment='center')

    if xlabel is not None:
        pt.xlabel(xlabel, fontsize=pt.labelfont)
    if ylabel is not None:
        pt.ylabel(ylabel, fontsize=pt.labelfont)

    # end of matplotlib part
    ################################################

    # now, create a PIL image
    import io
    ram = io.StringIO()
    pt.savefig(ram, format='png')
    ram.seek(0)

    img = Image.open(ram)

    # close the matplotlib plot
    pt.clf()
    pt.close('all')

    return img


##################################################################
# Transition
##################################################################


class Transition:

    def __init__(self, i, duration=0, type='default', active=False, fps=24):
        self.active = active
        self.type = type

        self.number_of_frames = duration * fps

        # first frame of last sequence
        self.i0 = int(i - self.number_of_frames)
        self.i1 = self.i0 + self.number_of_frames - 1
        self.di = self.i1 - self.i0

    def __call__(self):
        return self.active

    def fct(self, i, img1, img2):

        if self.type == 'default':
            f = (i - self.i0) / float(self.number_of_frames)
            return img_merge(img1, img2, f)

        if self.type == 'shading':

            if (i < self.i0 + self.di / 2):  # first part
                f = 1 - (i - self.i0) / float(self.di / 2)
                return img_shade(img1, f)
            else:			# second part
                f = (i - self.i0 - self.di / 2) / float(self.di / 2)
                return img_shade(img2, f)

        else:
            return img2

    def checkend(self, i):
        if i >= self.i1:
            self.stop()
            print("end of transition")

    def stop(self):
        self.active = False


class Shading():

    def __init__(self, i, t1, t2, type='default', active=False, fps=24):

        self.active = active
        self.type = type

        # first frame of last sequence
        self.i0 = i
        self.t1 = t1
        self.t2 = t2

        self.n1 = int(fps * self.t1)
        self.n2 = int(fps * self.t2)

    def __call__(self):
        return self.active

    def getf(self, i, nf):

        f = 1.

        if i - self.i0 < self.n1:
            f = float(i - self.i0) / self.n1
        if i - self.i0 > nf - self.n2:
            if self.n2 == 0:
                return 1.
            f = 1 - float(i - self.i0 - (nf - self.n2)) / self.n2

        return f

    def fct(self, i, nf, img):
        '''
        nf : number of frames in the current movie
        '''

        f = self.getf(i, nf)

        if i == self.i0 + nf - 1:
            print("stop shading")
            self.stop()

        if f < 1:
            img = img_shade(img, f)

        return img

    def stop(self):
        self.active = False


##################################################################
# other functions
##################################################################


def normalize(mat, scale='log', mn=None, mx=None, cd=None):
    '''
    Transform an n x m float array into an n x m int array that will be
    used to create an image. The float values are rescaled and cutted in order to range
    between 0 and 255.

    mat   : the matrice
    scale	: lin or log
    mn  	: lower value for the cutoff
    mx 	: higer value for the cutoff
    cd	: parameter

    '''

    rm = ravel(mat)

    if mn is None:
        mn = min(rm)
    if mx is None:
        mx = max(rm)

    if mn == mx:
        mn = min(rm)
        mx = max(rm)

    mat = clip(mat, mn, mx)
    if mn == 0 and mx == 0:
        return mat, mn, mx, 0

    if scale == 'log':

        if cd is None or cd == 0:
            cd = rm.mean()

        try:
            mat = log(1. + (mat - mn) / (cd)) / log(1. + (mx - mn) / (cd))
        except BaseException:
            mat = mat * 0.

    elif scale == 'lin':

        mat = (mat - mn) / (mx - mn)
        cd = 0

    return mat, mn, mx, cd


def fits_apply_palette(
        mat,
        scale='log',
        mn=0,
        mx=0,
        cd=0,
        palette='rainbow4',
        mode='RGB'):
    '''
    matint,mn_opt,mx_opt,cd_opt = set_ranges(img,scale=scale,cd=cd,mn=mn,mx=mx)
    img = get_image(matint,palette_name=palette)
    '''

    mat, mn, mx, cd = normalize(mat, scale=scale, mn=mn, mx=mx, cd=cd)
    mat = mat * 255

    # create a PIL object

    mat = transpose(mat)
    mat = mat.astype(int8)

    image = Image.frombytes("P", (mat.shape[1], mat.shape[0]), mat.tostring())

    # include the palette
    palette = Palette(palette)
    image.putpalette(palette.palette)

    # set mode
    if mode == 'RGB':			# to convert with ImageQt, need to be in RGB
        image = image.convert('RGB')

    return image


def fits_compose_rgb_img(files, cfact=1., mode="RGB"):
    """
    compose 3 fits images, assuming that their represent
    the 3 R,G,B channels.
    """

    if len(files) != 3:
        raise ValueError(
            1, 'length of argument files (=%d) must be equal to 3' %
            (len(files)))

    datas = []

    for i, file in enumerate(files):

        # open image
        if isinstance(file, str):
            fitsimg = pyfits.open(file)
            data = fitsimg[0].data
        else:
            data = file

        datas.append(data)

    r = 255. * datas[0] * cfact
    g = 255. * datas[1] * cfact
    b = 255. * datas[2] * cfact

    # create image and save it
    r = uint8(clip(r, 0, 255))
    g = uint8(clip(g, 0, 255))
    b = uint8(clip(b, 0, 255))

    size = (datas[0].shape[1], datas[0].shape[0])

    image_r = Image.frombytes("L", size, r)
    image_g = Image.frombytes("L", size, g)
    image_b = Image.frombytes("L", size, b)

    img = Image.merge(mode, (image_r, image_g, image_b))

    return img


def fits_compose_colors_img(files, args, cmode='normal', mode="RGB"):

    if len(files) != len(args):
        raise ValueError(
            1, 'length of argument files (=%d) must be equal to the lengh of argument args (=%d)' %
            (len(files), len(args)))

    datas = []

    for i, file in enumerate(files):

        cd = args[i]['cd']
        mn = args[i]['mn']
        mx = args[i]['mx']
        scale = args[i]['scale']

        # open image
        if isinstance(file, str):
            fitsimg = pyfits.open(file)

            data = fitsimg[0].data
        else:
            data = file

        data = transpose(data)

        size = (data.shape[1], data.shape[0])
        data, tmp_mn, tmp_mx, tmp_cd = normalize(
            data, scale=scale, mn=mn, mx=mx, cd=cd)
        print((tmp_mn, tmp_mx, tmp_cd))
        args[i]['mn'] = mn
        args[i]['mx'] = mx
        args[i]['cd'] = cd

        datas.append(data)

    r = zeros(data.shape)
    g = zeros(data.shape)
    b = zeros(data.shape)

    for i, data in enumerate(datas):

        ar = float(args[i]['ar'])
        ag = float(args[i]['ag'])
        ab = float(args[i]['ab'])
        f = float(args[i]['f'])

        # normalize weights
        n = sqrt(ar**2 + ag**2 + ab**2)
        if n > 0:
            ar = ar / n * 255. * f
            ag = ag / n * 255. * f
            ab = ab / n * 255. * f
        else:
            ar = 0.
            ag = 0.
            ab = 0.

        if cmode == 'normal':
            r = r + ar * data
            g = g + ag * data
            b = b + ab * data
        else:

            # composition rules :
            # 1) if old data is  empty  -> f2=1
            # 2) if old data not empty
            #      if new data is  empty -> f2=0
            #      if new data not empty -> f2 varies
            #

            mx2 = max(ravel(data))
            mn2 = 0.

            if ar + ag + ab == 0:
                f2 = 0
            else:
                if max(ravel(r)) + max(ravel(g)) + max(ravel(b)) == 0:
                    f2 = 1
                else:
                    f2 = (mn2 - data) / (mn2 - mx2)

            f1 = 1 - f2

            r = r * f1 + ar * data * f2
            g = g * f1 + ag * data * f2
            b = b * f1 + ab * data * f2

    # create image and save it
    r = uint8(clip(r, 0, 255))
    g = uint8(clip(g, 0, 255))
    b = uint8(clip(b, 0, 255))

    #r = transpose(r)
    #g = transpose(g)
    #b = transpose(b)

    image_r = Image.frombytes("L", size, r)
    image_g = Image.frombytes("L", size, g)
    image_b = Image.frombytes("L", size, b)

    img = Image.merge(mode, (image_r, image_g, image_b))

    return img, args


##################################################################
# Movie class
##################################################################


class Movie:

    def __init__(
            self,
            fps=24,
            size=None,
            mode="RGB",
            outputdirectory=None,
            background=(
                0,
                0,
                0),
            shading=None,
            cmd=None):

        self.fps = fps
        self.size = size
        self.mode = mode
        self.outputdirectory = outputdirectory
        self.background = background
        self.shading = Shading(0, 0, 0)
        self.transition = Transition(0)
        self.cmd = cmd

        self.img = None

        self.curdir = os.path.abspath(os.path.curdir)

        self.i = 0
        self.i0 = 0
        self.pos = (0, 0)
        self.a = 0.

        self.number_of_frames = 0

    def setimage(self, img, pos=(0, 0), angle=0):

        print(("set image %s" % img))

        if isinstance(img, str):
            img = Image.open(img)

        img = img.convert(self.mode)

        if self.size is not None:
            img = img.resize(self.size)

        self.img = img
        self.pos = (0, 0)
        self.a = 0

    def setshading(self, shading=None):
        if shading is not None:
            t1 = shading[0]
            t2 = shading[1]
            self.shading = Shading(
                self.i,
                t1=t1,
                t2=t2,
                type=type,
                active=True,
                fps=self.fps)

    def set_cmd(self, cmd):
        self.cmd = cmd

    def settransition(self, duration=0, type=None):

        self.transition = Transition(
            self.i,
            duration=duration,
            type=type,
            active=True,
            fps=self.fps)

        # now set also the new i
        self.i = self.transition.i0

    def write(self, img):

        if isinstance(img, str):
            img = Image.open(img)
            img = img.convert(self.mode)

        # apply cmd
        if self.cmd is not None:
            print(("                           apply : %s" % (self.cmd)))
            exec(self.cmd)

        # resize if needed
        if self.size is not None:
            print(("                           set size to (%d,%d)" % (self.size[0], self.size[1])))
            img = img.resize(self.size)

        # apply shading if needed
        if self.shading():
            img = self.shading.fct(self.i, self.number_of_frames, img)

        # apply transition if needed
        if self.transition():

            img1 = os.path.join(self.outputdirectory, "%08d.png" % self.i)

            if not os.path.isfile(img1):
                raise Exception("%s does not exists" % img1)

            img = self.transition.fct(self.i, img1, img)
            print(("(i=%08d t=%7.2f sec) transition using %s" % (self.i, float(self.i) / self.fps, img1)))
            self.transition.checkend(self.i)

        name = os.path.join(self.outputdirectory, "%08d.png" % self.i)
        print(("(i=%08d t=%7.2f sec) write %s" % (self.i, float(self.i) / self.fps, name)))

        if os.path.isfile(name):
            os.remove(name)

        img.save(name)
        self.i = self.i + 1

    def wait(self, duration=0):
        self.number_of_frames = int(duration * self.fps)
        for k in range(self.number_of_frames):
            self.write(self.img)

    def move(self, speedx=0, speedy=0, duration=0):
        """
        move an image

        speed : number of pixel per second

        """

        speedx = float(speedx)
        speedy = float(speedy)
        self.number_of_frames = int(duration * self.fps)

        dx = self.img.size[0]
        dy = self.img.size[1]

        x = self.pos[0]
        y = self.pos[1]

        vx = (speedx / self.fps)
        vy = (speedy / self.fps)

        for k in range(self.number_of_frames):

            img = Image.new(
                self.mode,
                (self.size[0],
                 self.size[1]),
                self.background)
            box = (int(x), int(y), int(x) + dx, int(y) + dy)
            img.paste(self.img, box)
            self.write(img)

            x = x + vx
            y = y + vy

        self.pos = (int(x), int(y))

    def rotate(self, speed=0, duration=0):
        """
        rotate an image

        speed : degree per second

        """

        speed = float(speed)
        self.number_of_frames = int(duration * self.fps)

        dx = self.img.size[0]
        dy = self.img.size[1]

        x = self.pos[0]
        y = self.pos[1]

        a = self.a
        va = (speed / self.fps)

        for k in range(self.number_of_frames):

            img = Image.new(
                self.mode,
                (self.size[0],
                 self.size[1]),
                self.background)
            box = (int(x), int(y), int(x) + dx, int(y) + dy)

            imgr = self.img.rotate(a)

            img.paste(imgr, box)
            self.write(img)

            a = a + va

        self.a = a

    def addimages(
            self,
            directory,
            tstart=None,
            tstop=None,
            tlen=None,
            istart=None,
            istop=None,
            ilen=None):
        """

        tstart = time of first image
        tstop  = time of last image count from the end of the movie
        tlen   = duration of the movie

        if tstart,tstop,tlen are not defined

        istart = number of first frame
        istop  = number of last frame, count from the end
        ilen   = number of frames

        """
        print(("add images from %s" % directory))

        files = sorted(glob.glob(os.path.join(directory, "*")))

        print(("number of files = %d" % (len(files))))
        print(("duration        = %f s" % (len(files) / float(self.fps))))

        # take only a subset
        if ilen is not None:
            if istop is not None:
                istop = len(files) - istop
                istart = istop - ilen
            elif istart is not None:
                istop = istart + ilen
            else:                             # nothing defined
                istart = 0
                istop = istart + ilen
        else:
            if istart is None:
                istart = 0
            if istop is None:
                istop = 0
            istop = len(files) - istop

        # here, istart, istop are now defined
        if tstart is not None:
            istart = int(tstart * self.fps)
        if tstop is not None:
            istop = len(files) - int(tstop * self.fps)
        if tlen is not None:
            if tstop is not None:
                # define istart from istop and ilen
                istart = istop - int(tlen * self.fps)
            else:
                # define istop from istart and ilen
                istop = istart + int(tlen * self.fps)

        # here, istart,istop are defined
        # 1) from tstart,tstop,tlen
        # or
        # 2) from istart,istop,ilen

        # now cut if needed
        if istart != 0 or istop != len(files):
            files = files[istart:istop]
            print(("cut movie (istart=%d istop=%d)" % (istart, istop)))
            print(("number of files = %d" % (len(files))))
            print(("duration        = %f s" % (len(files) / float(self.fps))))

        self.number_of_frames = len(files)

        for file in files:
            # create a link
            name = os.path.join(self.outputdirectory, "%08d.png" % self.i)

            # create a soft link if the image is kept unchanged
            noshading = self.shading.getf(self.i, self.number_of_frames) == 1
            if not self.transition() and noshading and self.size is None:
                os.symlink(os.path.join(self.curdir, file), name)
                print(("(i=%08d t=%7.2f sec) link %s" % (self.i, float(self.i) / self.fps, name)))
                self.i = self.i + 1
            else:
                self.write(file)

        # set the current image as the last one
        self.setimage(file)
