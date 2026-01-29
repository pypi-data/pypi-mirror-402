#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libutil.py
#  brief:     utilities function (contains plot functions)
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import types

from copy import deepcopy

import numpy as np
from pNbody.nbodymodule import *
from pNbody import mapping
from .palette import *
from pNbody.myNumeric import *
import pNbody

try:
    import tkinter as tk
    from PIL import ImageTk
    is_tk = True
except ImportError:
    is_tk = False


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImagePalette


from . import mpiwrapper as mpi
from . import param
import _thread

from scipy import signal
from scipy import ndimage


try:
    from . import libqt
    is_qt = True
except BaseException:
    is_qt = False


def get_fake_fct(nx=256, ny=256):
    # create a function
    mx = 2 * np.pi
    my = 2 * np.pi
    x, y = np.indices((nx, ny))
    x = mx * (x - nx / 2) / (nx / 2)
    y = my * (y - ny / 2) / (ny / 2)

    R = np.sqrt(x**2 + y**2)
    R1 = np.sqrt((x - np.pi)**2 + (y - np.pi)**2)
    mat = np.cos(R) / (1 + R) + 0.5 * np.cos(R1) / (1 + R1)
    return mat


def get_n_per_task(ntot, NTask):

    n_per_task = np.zeros(NTask, int)
    for Task in range(NTask - 1, -1, -1):
        n_per_task[Task] = ntot / NTask + ntot % NTask * (Task == 0)

    return n_per_task


def get_npart_all(npart, NTask):

    npart_all = np.zeros((NTask, len(npart)), int)

    i = 0
    for n in npart:
        npart_all[:, i] = get_n_per_task(n, mpi.mpi_NTask())
        i = i + 1

    return npart_all


def old_get_n_per_task(ntot, NTask):

    nleft = ntot
    n_per_task = np.zeros(NTask, int)

    for Task in range(NTask - 1, -1, -1):
        if nleft < 2 * ntot / NTask:
            n_per_task[Task] = nleft
        else:
            n_per_task[Task] = ntot / NTask
        nleft = nleft - n_per_task[Task]

    if nleft != 0:
        raise Exception("get_n_per_task : nleft != 0 (%d)" % (nleft))

    return n_per_task


def cross_product(x, y):

    if x.shape != y.shape:
        raise Exception(
            "cross_product error",
            "x and y do not have the same shape")

    n = len(x)
    p = np.zeros((n, 3), x.dtype)

    p[:, 0] = x[:, 1] * y[:, 2] - x[:, 2] * y[:, 1]
    p[:, 1] = x[:, 2] * y[:, 0] - x[:, 0] * y[:, 2]
    p[:, 2] = x[:, 0] * y[:, 1] - x[:, 1] * y[:, 0]

    return p


def myhistogram(a, bins):
    """
    Return the histogram (n x 1 float array) of the
    n x 1 array "a".
    "bins" (m x 1 array) specify the bins of the histogram.
    """
    n = np.searchsorted(np.sort(a), bins)
    n = np.concatenate([n, [len(a)]])
    return n[1:] - n[:-1]


def compress_from_lst(x, num, lst, reject=False):
    """
    Return the compression of x
    """

    # 1) sort the list
    ys = np.sort(lst)

    # 2) sort index in current file
    xs = np.sort(num)
    # sort 0,1,2,n following xs (or self.num)
    zs = np.take(np.arange(len(x)), np.argsort(num))

    # 3) apply mask on sorted lists (here, getmask need xs and ys to be sorted)
    m = np.getmask(xs.astype(int), ys.astype(int))
    if reject:
        m = np.logical_not(m)

    # 4) revert mask, following zs inverse transformation
    c = np.take(m, np.argsort(zs))

    return np.compress(c, x, axis=0)


def tranfert_functions(rmin, rmax, g=None, gm=None):
    """
    This function computes the normalized transfer function from g and gm
    It is very useful to transform a linear vector in a non linear one

    example of g:

      g  = lambda r:np.log(r/rc+1)
      gm = lambda r:rc*(np.exp(r)-1)

    """

    rmin = float(rmin)
    rmax = float(rmax)

    def f(r): return r	 # by default, identity

    def fm(r): return r	 # by default, identity

    if g is not None and gm is not None:
        def f(r): return (g(r) - g(rmin)) / \
            (g(rmax) - g(rmin)) * (rmax - rmin) + rmin

        def fm(f): return gm((f - rmin) *
                             (g(rmax) - g(rmin)) / (rmax - rmin) + g(rmin))

    return f, fm


def geter(n, rmin, rmax, g, gm):
    """
    Generate a one dimentional non linear array of r
    """

    n = int(n)
    dr = (rmax - rmin) / float(n - 1)

    f, fm = tranfert_functions(rmin, rmax, g, gm)

    Rs = np.arange(0, rmax + dr, dr)
    Rs = fm(Rs)

    return Rs


def geter2(n, rmin, rmax, g, gm):
    """
    Generate a one dimentional non linear array of r
    """

    n = int(n)
    dr = (rmax - rmin) / float(n - 1)

    f, fm = tranfert_functions(rmin, rmax, g, gm)

    Rs = np.arange(0, rmax + dr, dr)
    Rs = f(Rs)

    return Rs


def getr(nr=31, nt=32, rm=100.):
    """
    Return a sequence of number (n x 1 array),
    where n=nr+1 defined by: Pfenniger & Friedli (1994)
    """
    j = np.arange(nr + 1)
    ct1 = 0.5 + (nt / (np.pi + np.pi))
    ct2 = (np.exp((nr) / ct1) - 1.)
    r = rm * (np.exp(j / ct1) - 1) / ct2
    return r


def invgetr(r, nr=31, nt=32, rm=100.):
    """
    From r, return the corresponding indexes.
    Inverse of getr function.
    """

    ct1 = 0.5 + (nt / (np.pi + np.pi))
    ct2 = (np.exp((nr) / ct1) - 1.)

    i = ct1 * np.log(ct2 * r / rm + 1)

    return i


def get_eyes(x0, xp, alpha, dr):
    """
    Return the position of two eyes.

    x0 	: position of the head
    xp  	: looking point
    theta : rotation of the head
    dr    : distance of the eyes

    """

    x0 = np.array(x0, float)
    xp = np.array(xp, float)

    # distance between the observer and the looking point
    Robs = np.sqrt((x0[0] - xp[0])**2 + (x0[1] - xp[1])**2 + (x0[2] - xp[2])**2)

    # init
    x = np.array([[dr, -Robs, 0.], [-dr, -Robs, 0.]], np.float32)
    m = pNbody.Nbody(pos=x, status='new')

    # first : put xp in the origin
    x0 = x0 - xp
    # angle in azimuth
    phi = np.arctan2(x0[1], x0[0]) + np.pi / 2
    # angle in nutation
    R = np.sqrt(x0[0]**2 + x0[1]**2)
    if R == 0:
        if x0[2] >= 0:
            theta = np.pi
        else:
            theta = -np.pi
    else:
        theta = np.arctan(x0[2] / R)

    # rotate
    # rotations alpha
    if alpha != 0.:
        m.rotate(alpha, axis='y', mode='p')
    # rotation in nutation
    if theta != 0.:
        m.rotate(-theta, axis='x', mode='p')
    # rotation in azimuth
    if phi != 0.:
        m.rotate(phi, axis='z', mode='p')
    # translate
    m.translate(xp)

    x1 = m.pos[0, :]
    x2 = m.pos[1, :]

    return x1, x2


def apply_filter(mat, name=None, opt=None):
    """
    Apply a filter to an image
    """

    if name == "convol":

        nx = opt[0]
        ny = opt[1]
        sx = float(opt[2])
        sy = float(opt[3])

        nxd = int((nx - 1) / 2)
        nyd = int((ny - 1) / 2)

        # the kernel
        b = np.fromfunction(lambda j, i: np.exp(-(i - nxd)**2 / sx**2 + -(j - nyd)**2 / sy**2), (nx, ny))
        s = np.sum(sum(b))
        b = b / s				  # normalisation

        # conversion:
        b = b.astype(float)
        mat = mat.astype(float)

        return np.convol(mat, b)

    elif name == "convolve":
        nx = opt[0]
        ny = opt[1]
        sx = float(opt[2])
        sy = float(opt[3])

        nxd = int((nx - 1) / 2)
        nyd = int((ny - 1) / 2)

        # the kernel
        b = np.fromfunction(lambda j, i: np.exp(-(i - nxd)**2 / sx**2 + -(j - nyd)**2 / sy**2), (nx, ny))
        s = np.sum(sum(b))
        b = b / s				 # normalisation

        # conversion:
        b = b.astype(float)
        mat = mat.astype(float)

        return signal.convolve2d(mat, b, output=None, fft=0)

    if name == "boxcar":
        nx = opt[0]
        ny = opt[1]
        boxshape = (nx, ny)
        return signal.windows.boxcar(mat, boxshape, mode='reflect')

    if name == "gaussian":
        sigma = float(opt[0])
        return ndimage.gaussian_filter(mat, sigma, mode='nearest')

    if name == "uniform":
        sigma = float(opt[0])
        return ndimage.uniform_filter(mat, sigma, mode='nearest')

    elif name is None:
        pass
    else:
        print("unknown filter type")
        return mat


def set_ranges(mat, scale='log', mn=None, mx=None, cd=None):
    """
    Transform an n x m float array into an n x m int array that will be
    used to create an image. The float values are rescaled and cutted in order to range
    between 0 and 255.

    mat   : the matrice
    scale	: lin or log
    mn  	: lower value for the cutoff
    mx 	: higer value for the cutoff
    cd	: parameter

    """

    rm = np.ravel(mat)

    if mn is None:
        mn = min(rm)
    if mx is None:
        mx = max(rm)

    if mn == mx:
        mn = min(rm)
        mx = max(rm)

    mat = np.clip(mat, mn, mx)

    if scale == 'log':

        if cd is None or cd == 0:
            cd = rm.mean()

        try:
            mat = 255. * np.log(1. + (mat - mn) / (cd)) / \
                np.log(1. + (mx - mn) / (cd))
        except BaseException:
            mat = mat * 0.

    elif scale == 'lin':

        mat = 255. * (mat - mn) / (mx - mn)
        cd = 0

    return mat.astype(int), mn, mx, cd


def contours(m, matint, nl, mn, mx, kx, ky, color, crush='no'):
    """

    Compute iso-contours on a n x m float array.
    If "l_min" equal "l_max", levels are automatically between the minimum and
    maximum values of the matrix "mat".


    m 		= matrice (real values)
    matint	= matrice (interger values)
    kx		= num of sub-boxes
    ky		= num of sub-boxes
    nl		= # of levels
    mn		= min
    mx 		= max
    color		= color of contours

    """

    # create an empty matrix
    newm = np.zeros(m.shape, np.float32)

    if color != 0:

        # transform color
        color = np.array(color, np.int8)

        if mx == mn:
            rm = np.ravel(m)
            mn = min(rm)
            mx = max(rm)
            levels = np.arange(mn + (mx - mn) / nl, mx, (mx - mn) / (nl + 1))
        else:
            levels = np.arange(mn,
                            mx + (mx - mn) / (nl - 1),
                            (mx - mn) / (nl - 1))[:nl]

        # print levels

        m = np.transpose(m)		  # !!!

        X = [(), (), (), (), ()]
        rect = [(1, 2), (2, 3), (3, 4), (4, 1)]

        # number of sub-boxes per axis
        nx = int((m.shape[0] - 1) / (kx - 1))
        ny = int((m.shape[1] - 1) / (ky - 1))
      

        for i in range(0, nx):
            for j in range(0, ny):

                ix = (kx - 1) * i		  # here, we could add an offset
                iy = (ky - 1) * j

                X[1] = (ix, iy, m[iy][ix])
                X[2] = (ix + (kx - 1), iy, m[iy][ix + (kx - 1)])
                X[3] = (ix + (kx - 1), iy + (ky - 1),
                        m[iy + (ky - 1)][ix + (kx - 1)])
                X[4] = (ix, iy + (ky - 1), m[iy + (ky - 1)][ix])

                # find the center
                X[0] = (ix + 0.5 * kx, iy + 0.5 * ky, 0.25 *
                        (X[1][2] + X[2][2] + X[3][2] + X[4][2]))

                # loop over the levels
                for l in levels:
                    # loop over the triangles

                    for r in rect:

                        z1 = X[r[0]][2]
                        z2 = X[r[1]][2]
                        z3 = X[0][2]

                        # find the maximum

                        if z1 > z2:
                            if z1 > z3:
                                if z2 > z3:
                                    c = X[r[0]]
                                    b = X[r[1]]
                                    a = X[0]
                                else:
                                    c = X[r[0]]
                                    b = X[0]
                                    a = X[r[1]]

                            else:
                                c = X[0]
                                b = X[r[0]]
                                a = X[r[1]]

                        else:
                            if z2 > z3:
                                if z1 > z3:
                                    c = X[r[1]]
                                    b = X[r[0]]
                                    a = X[0]
                                else:
                                    c = X[r[1]]
                                    b = X[0]
                                    a = X[r[0]]
                            else:
                                c = X[0]
                                b = X[r[1]]
                                a = X[r[0]]

                        # a,b,c are the tree triangle points

                        # create_line(newm,a[0],a[1],b[0],b[1],color)
                        # create_line(newm,b[0],b[1],c[0],c[1],color)
                        # create_line(newm,c[0],c[1],a[0],a[1],color)

                        # the level cut the triangle
                        if l >= a[2] and l <= c[2] and a[2] != c[2]:

                            lamb = (l - a[2]) / (c[2] - a[2])

                            xx1 = int(lamb * (c[0] - a[0]) + a[0])
                            yy1 = int(lamb * (c[1] - a[1]) + a[1])

                            if l >= b[2] and l <= c[2] and b[2] != c[2]:

                                lamb = (l - b[2]) / (c[2] - b[2])
                                xx2 = int(lamb * (c[0] - b[0]) + b[0])
                                yy2 = int(lamb * (c[1] - b[1]) + b[1])

                            elif b[2] != a[2]:

                                lamb = (l - a[2]) / (b[2] - a[2])
                                xx2 = int(lamb * (b[0] - a[0]) + a[0])
                                yy2 = int(lamb * (b[1] - a[1]) + a[1])

                                mapping.create_line(newm, xx1, yy1, xx2, yy2, color)

    matc = newm.astype(np.int8)

    if crush == 'yes':
        matint = np.ones(matc.shape)
        matint = matint * 255
        matint = np.where(matc, matc, matint)
    else:
        matint = np.where(matc, matc, matint)

    return matint


def add_box(
    matint, shape=(
        256, 256), size=(
            30., 30.), center=None, box_opts=(
                1, None, None, 255)):
    """
    add a box on the frame
    """

    lweight = box_opts[0]
    xticks = box_opts[1]
    yticks = box_opts[2]
    color = box_opts[3]

    box = sbox(
        shape,
        size,
        lweight=lweight,
        xticks=xticks,
        yticks=yticks,
        color=color)
    matint = np.where(box != 0, box, matint)

    return matint


def mplot(mat, palette='light', save=None, marker=None, header=None):
    """
    plot a 2d array
    """

    from pNbody import iofunc as pnio

    if mpi.mpi_IsMaster():

        if save is not None:
            if os.path.splitext(save)[1] == ".fits":
                pnio.WriteFits(np.transpose(mat).astype(np.float32), save, header)
                return

        # if the matrix is real
        if mat.dtype != np.int32:
            matint, mn_opt, mx_opt, cd_opt = set_ranges(
                mat, scale='lin', cd=0, mn=0, mx=0)
            mat = matint

        # add marker
        if marker is not None:
            if marker == 'cross':
                nx, ny = mat.shape
                ix, iy = np.indices(mat.shape)
                mat = np.where((ix == nx / 2) + (ix == nx / 2 - 1) +
                            (iy == ny / 2) + (iy == ny / 2 - 1), 255, mat)

            if marker == 'circle':
                nx, ny = mat.shape
                ix, iy = np.indices(mat.shape)
                r = 100
                dr = 1
                Rs = np.sqrt((ix - nx / 2)**2 + (iy - ny / 2)**2)
                c = (Rs < r + dr) * (Rs > r - dr)

                mat = np.where(c, 255, mat)

        image = get_image(mat, name=None, palette_name=palette)

        if save is None:
            display(image)
        else:
            image.save(save)


def get_image(mat, name=None, palette_name='light', mode='RGB'):
    """
    Return an image (PIL object).

    data : numpy 2x2 object
    name : name of the output
    palette_name : name of a palette
    """

    # modif 09.03.05
    mat = np.transpose(mat)
    mat = mat.astype(np.int8)

    # mat = mat.astype(int)      # ok
    # mat = np.transpose(mat)        # la transposee fait changer aussi autre
    # chose ??? c'est peut-etre la sortie de Py_BuildValue("(Of)",mat,cdopt);
    # pas bon...

    image = Image.frombytes("P", (mat.shape[1], mat.shape[0]), mat.tostring())

    # include the palette
    palette = Palette(palette_name)
    image.putpalette(palette.palette)

    # set mode
    if mode == 'RGB':			# to convert with ImageQt, need to be in RGB
        image = image.convert('RGB')

    # save it
    if name is not None:
        image.save(name)

    return image


def display(image):

    if mpi.mpi_IsMaster():

        if is_qt:
            libqt.display(image)

        elif is_tk:

            #root = tk.Tk()
            root = tk.Toplevel()
            canvas = tk.Canvas(root)
            canvas.pack()
            imagetk = ImageTk.PhotoImage(image)
            canvas.config(width=image.size[0], height=image.size[1])
            canvas.create_image(0., 0., anchor=tk.NW, image=imagetk)
            root.mainloop()

        else:

            raise Exception("tk or qt not present")


def sbox(shape, size, lweight=1, xticks=None, yticks=None, color=255):
    """
    simple box

    return a matrix of integer, containing a box with labels

    xticks = (m0,d0,h0,m1,d1,h1)

    0 = big
    1 = small

    m0,m1 = dist between ticks
    d0,d1 = first tick
    h0,h1 = height of the ticks

    """
    center = None

    # parameters
    nn = 4.
    bticks = np.array([1., 2., 5.])

    color = int(color)

    # create matrix from scratch
    matint = np.zeros(shape, int)

    # add the outer box
    for l in range(lweight):
        # in x
        matint[:, l] = (np.zeros((shape[0],)) + color).astype(int)
        # may be commented
        matint[:, shape[1] - 1 - l] = (np.zeros((shape[0],)) + color).astype(int)
        # in y
        matint[l, :] = (np.zeros((shape[1],)) + color).astype(int)
        # may be commented
        matint[shape[0] - 1 - l, :] = (np.zeros((shape[1],)) + color).astype(int)

    # add the ticks in x
    if xticks is None:
        #cx = center[0]
        #cy = center[1]
        cx = 0
        cy = 0
        hx = shape[0]
        hy = shape[1]
        dx = size[0]
        dy = size[1]

        rat = (2. * dx) / nn					# dist between ticks
        ratn = rat / 10**int(np.log10(rat))
        d0 = bticks[np.argmin(np.fabs(bticks - ratn))] * 10**int(np.log10(rat))

        n0 = int(np.fmod(2. * dx / d0, 2) + (2. * dx / d0))		# number of ticks
        m0 = cx - (n0 * d0) / 2. 				# first tick
        h0 = hy / 20.						# height of the ticks

        d1 = d0 / 4.						# dist between ticks
        n1 = n0 * 4
        m1 = m0						# first tick
        h1 = h0 / 2.						# height of the ticks

    else:
        m0 = xticks[0]
        d0 = xticks[1]
        h0 = xticks[2]
        m1 = xticks[3]
        d1 = xticks[4]
        h1 = xticks[5]

    # big ticks x
    matint = drawxticks(matint, m0, d0, n0, h0, shape, size, center, color)
    # small ticks x
    matint = drawxticks(matint, m1, d1, n1, h1, shape, size, center, color)

    # print "dx = %8.3f"%(d0)

    # add the ticks in y
    if xticks is None:
        #cx = center[0]
        #cy = center[1]
        cx = 0
        cy = 0
        hx = shape[0]
        hy = shape[1]
        dx = size[0]
        dy = size[1]

        rat = (2. * dx) / nn					# dist between ticks
        ratn = rat / 10**int(np.log10(rat))
        d0 = bticks[np.argmin(np.fabs(bticks - ratn))] * 10**int(np.log10(rat))

        n0 = int(np.fmod(2. * dx / d0, 2) + (2. * dx / d0))		# number of ticks
        m0 = cy - (n0 * d0) / 2. 				# first tick
        h0 = hx / 20.						# height of the ticks

        d1 = d0 / 4.						# dist between ticks
        n1 = n0 * 4
        m1 = m0						# first tick
        h1 = h0 / 2.						# height of the ticks

    else:
        m0 = xticks[0]
        d0 = xticks[1]
        h0 = xticks[2]
        m1 = xticks[3]
        d1 = xticks[4]
        h1 = xticks[5]

    # big ticks y
    matint = drawyticks(matint, m0, d0, n0, h0, shape, size, center, color)
    # small ticks y
    matint = drawyticks(matint, m1, d1, n1, h1, shape, size, center, color)

    # print "dy = %8.3f"%(d0)

    return matint


def drawxticks(matint, m0, d0, n0, h0, shape, size, center, color):
    """
    draw x ticks in a matrix
    """

    x = m0
    for nx in range(n0):
        ix, iy = phys2img(shape, size, center, x, 0)
        try:  # !! version dependant !!
            ix = int(ix[0])
        except BaseException:
            ix = int(ix)

        for iy in range(int(h0)):
            matint[ix, iy] = np.array([color], int)[0]
            matint[ix, shape[0] - 1 - iy] = np.array([color], int)[0]

        x = x + d0

    return matint


def drawyticks(matint, m0, d0, n0, h0, shape, size, center, color):
    """
    draw x ticks in a matrix
    """

    x = m0
    for nx in range(n0):
        ix, iy = phys2img(shape, size, center, x, 0)
        try:  # !! version dependant !!
            ix = int(ix[0])
        except BaseException:
            ix = int(ix)

        for iy in range(int(h0)):
            matint[iy, ix] = np.array([color], int)[0]
            matint[shape[1] - 1 - iy, ix] = np.array([color], int)[0]

        x = x + d0

    return matint


def draw_line(m, x0, x1, y0, y1, c, z0=None, z1=None):

    dd = 0.5  # half a pixel

    imax = m.shape[0] - 1
    jmax = m.shape[1] - 1

    if abs(x0 - x1) > abs(y0 - y1):
        ixmin = int(round(min(x0, x1)))
        ixmax = int(round(max(x0, x1)))

        a = (y1 - y0) / (x1 - x0)
        #az = (z1-z0)/(x1-x0)

        for i in range(ixmin, ixmax + 1):
            j = round((i - x0) * a + y0)
            #jz =       (i - x0)*az + z0

            if (i <= imax) and (i >= 0) and (j <= jmax) and (j >= 0):
                m[i, j] = c

    elif abs(x0 - x1) <= abs(y0 - y1) and abs(y0 - y1) > 0:
        iymin = int(round(min(y0, y1)))
        iymax = int(round(max(y0, y1)))

        a = (x1 - x0) / (y1 - y0)
        #az = (z1-z0)/(y1-y0)

        for j in range(iymin, iymax + 1):
            i = round((j - y0) * a + x0)
            #iz =       (j - y0)*az + z0

            if (i <= imax) and (i >= 0) and (j <= jmax) and (j >= 0):
                m[i, j] = c

    else:
        i = round(x0)
        j = round(y0)
        if (i <= imax) and (i >= 0) and (j <= jmax) and (j >= 0):
            m[i, j] = c

    return m


def draw_points(m, x, y, c):
    n = len(x)
    for i in range(n):
        m = draw_line(m, x[i], x[i], y[i], y[i], c)
    return m


def draw_lines(m, x, y, c):
    n = len(x)
    for i in range(n - 1):
        m = draw_line(m, x[i], x[i + 1], y[i], y[i + 1], c)
    return m


def draw_polygon(m, x, y, c):
    n = len(x)
    for i in range(n - 1):
        m = draw_line(m, x[i], x[i + 1], y[i], y[i + 1], c)
    m = draw_line(m, x[n - 1], x[0], y[n - 1], y[0], c)
    return m


def draw_segments(m, x, y, c, zp=None):
    n = len(x)
    p = int(n / 2)

    for j in range(p):
        i = 2 * j
        if zp is not None:
            m = draw_line(m, x[i], x[i + 1], y[i],
                          y[i + 1], c, zp[i], zp[i + 1])
        else:
            m = draw_line(m, x[i], x[i + 1], y[i], y[i + 1], c)
    return m


def draw_polygonN(m, x, y, c, N):

    n = len(x)
    p = int(n / N)

    for j in range(p):
        i = N * j
        for k in range(N - 1):
            m = draw_line(m, x[i + k], x[i + k + 1], y[i + k], y[i + k + 1], c)
        m = draw_line(m, x[i + N - 1], x[i], y[i + N - 1], y[i], c)

    return m


def phys2img(shape, size, center, x, y):
    """
    convert physical position into the image pixel
    """
    #cx = center[0]
    #cy = center[1]
    cx = 0
    cy = 0
    hx = shape[0]
    hy = shape[1]
    dx = size[0]
    dy = size[1]

    ax = hx / (2. * dx)
    bx = (hx / 2.) * (1. - cx / dx)

    ay = hy / (2. * dy)
    by = (hy / 2.) * (1. - cy / dy)

    ix = int(ax * x + bx)
    iy = int(ay * y + by)

    ix = np.clip(ix, 0, hx - 1)
    iy = np.clip(iy, 0, hy - 1)

    return ix, iy


#################################
def can_to_carth(l, scale_fact, x_can, y_can):
    #################################

    x = float(x_can - l[0] / 2.) / scale_fact[0]
    y = float(-y_can + l[1] / 2.) / scale_fact[1]

    return x, y

#################################


def carth_to_can(l, scale_fact, x, y):
    #################################

    x_can = int(x * scale_fact[0] + l[0] / 2.)
    y_can = int(-y * scale_fact[1] + l[1] / 2.)

    return x_can, y_can

#################################


def getval(nb, mode='m', obs=None):
    #################################
    """
    For each point, return a specific value linked to this point

    Parameters 
    ----------

    mode : str
        m           : moment 0

        0           : moment 0
    
        x           : first moment in x

        y           : first moment in y

        z           : first moment in z
        

        y2  	: second moment in x

        y2  	: second moment in y

        z2  	: second moment in z

        vx		: first velocity moment in x

        vy		: first velocity moment in y

        vz		: first velocity moment in z

        vx2		: second velocity moment in x

        vy2		: second velocity moment in y
        
        vz2		: second velocity moment in z


        Lx   	: kinetic momemtum in x

        Ly   	: kinetic momemtum in y

        Lz   	: kinetic momemtum in z

        lx   	: specific kinetic momemtum in x

        ly   	: specific kinetic momemtum in y
        
        lz   	: specific kinetic momemtum in z


        u		: specific energy

        rho		: density

        T   	: temperature

        A   	: entropy
        
        P   	: pressure

        Tcool       : cooling time

        Lum         : luminosity

        Ne          : local electro density



        r		: first momemtum of radial distance [depends on projection]
        
        r2		: second momemtum of radial distance [depends on projection]

        vr		: first momemtum of radial velocity [depends on projection]

        vr2		: second momemtum of radial velocity [depends on projection]

        vxyr	: first momemtum of radial velocity in the plane [depends on projection]

        vxyr2	: second momemtum of radial velocity in the plane [depends on projection]

        vtr  	: first momemtum of tangential velocity in the plane [depends on projection]

        vtr2	: second momemtum of tangential velocity in the plane [depends on projection]



    Notes
    ------------------

    Three types of values:

    (1) scalar values

        pos,m,tem,u,rho,ne
        vx,vx2,vy,vy2,vz,vz2,vxyr,vxyr2,vxyt,vxyt2

    (2) values computed with respect to xp

        z,z2
        Lx,Ly,Lz,lx,ly,ly


    (3) values computed with respect to absolute position in space

        empty for the moment (do not have the initial positions...)


    """

    ######################################
    # values independent of angle of view
    ######################################

    ###########
    # scalar
    ###########

    # moment 0
    if mode == '0':
        val = np.ones(len(nb.pos))

    # moment 0
    elif mode == 'm':
        val = np.ones(len(nb.pos))

    # u
    elif mode == 'u':
        val = nb.U()

    # rho
    elif mode == 'rho':
        val = nb.Rho()

    # T
    elif mode == 'T':
        val = nb.T()

    # A
    elif mode == 'A':
        val = nb.A()

    # P
    elif mode == 'P':
        val = nb.P()

    # Tcool
    elif mode == 'Tcool':
        val = nb.Tcool()

    # Ne
    elif mode == 'Ne':
        val = nb.Ne()

    # Hsml
    elif mode == 'Hsml':
        val = nb.Hsml()

    # Lum
    elif mode == 'Lum':
        val = nb.Lum()

    ###########
    # vectors
    ###########

    # x
    elif mode == 'x':
        val = nb.pos[:, 0]

    # y
    elif mode == 'y':
        val = nb.pos[:, 1]

    # z
    elif mode == 'z':
        val = nb.pos[:, 2]

    # x2
    elif mode == 'x2':
        val = nb.pos[:, 0]**2

    # y2
    elif mode == 'y2':
        val = nb.pos[:, 1]**2

    # z2
    elif mode == 'z2':
        val = nb.pos[:, 2]**2

    # vx
    elif mode == 'vx':
        val = nb.vel[:, 0]

    # vy
    elif mode == 'vy':
        val = nb.vel[:, 1]

    # vz
    elif mode == 'vz':
        val = nb.vel[:, 2]

    # vx2
    elif mode == 'vx2':
        val = nb.vel[:, 0]**2

    # vy2
    elif mode == 'vy2':
        val = nb.vel[:, 1]**2

    # vz2
    elif mode == 'vz2':
        val = nb.vel[:, 2]**2

    # kinetic momentum in x
    elif mode == 'Lx':
        val = nb.mass * (nb.pos[:, 1] * nb.vel[:, 2] -
                         nb.pos[:, 2] * nb.vel[:, 1])

    # kinetic momentum in y
    elif mode == 'Ly':
        val = nb.mass * (nb.pos[:, 2] * nb.vel[:, 0] -
                         nb.pos[:, 0] * nb.vel[:, 2])

    # kinetic momentum in z
    elif mode == 'Lz':
        val = nb.mass * (nb.pos[:, 0] * nb.vel[:, 1] -
                         nb.pos[:, 1] * nb.vel[:, 0])

    # specific kinetic momentum in x
    elif mode == 'lx':
        val = (nb.pos[:, 1] * nb.vel[:, 2] - nb.pos[:, 2] * nb.vel[:, 1])

    # specific kinetic momentum in y
    elif mode == 'ly':
        val = (nb.pos[:, 2] * nb.vel[:, 0] - nb.pos[:, 0] * nb.vel[:, 2])

    # specific kinetic momentum in z
    elif mode == 'lz':
        val = (nb.pos[:, 0] * nb.vel[:, 1] - nb.pos[:, 1] * nb.vel[:, 0])

    # luminosity
    elif mode == 'lum':
        val = nb.luminosity_spec()

    ########################################
    # values dependent on the angle of view
    ########################################

    # first moment in z
    elif mode == 'r':
        # center xp
        nb.translate(obs[0] - obs[1])
        val = nb.pos[:, 2]

    # second moment in z
    elif mode == 'r2':
        # center xp
        nb.translate(obs[0] - obs[1])
        val = nb.pos[:, 2]**2

    # first moment in z
    elif mode == 'vr':
        val = nb.vel[:, 2]

    # second moment in z
    elif mode == 'vr2':
        # center xp
        val = nb.vel[:, 2]**2

    # first velocity moment in radial velocity in the plane
    elif mode == 'vxyr':
        val = (nb.pos[:, 0] * nb.vel[:, 0] + nb.pos[:, 1] *
               nb.vel[:, 1]) / np.sqrt(nb.pos[:, 0]**2 + nb.pos[:, 1]**2)

    # second velocity moment in radial velocity in the plane
    elif mode == 'vxyr2':
        val = ((nb.pos[:, 0] * nb.vel[:, 0] + nb.pos[:, 1] *
                nb.vel[:, 1]) / np.sqrt(nb.pos[:, 0]**2 + nb.pos[:, 1]**2))**2

    # first moment in tangential velocity in the plane
    elif mode == 'vtr':
        val = (nb.pos[:, 0] * nb.vel[:, 1] - nb.pos[:, 1] *
               nb.vel[:, 0]) / np.sqrt(nb.pos[:, 0]**2 + nb.pos[:, 1]**2)

    # second moment in tangential velocity in the plane
    elif mode == 'vtr2':
        val = ((nb.pos[:, 0] * nb.vel[:, 1] - nb.pos[:, 1] *
                nb.vel[:, 0]) / np.sqrt(nb.pos[:, 0]**2 + nb.pos[:, 1]**2))**2

    # other mode
    else:
        # print "getval : unknown mode %s"%(mode)
        val = eval(mode)

    del nb

    return val.astype(np.float32)


#################################
def getvaltype(mode='m'):
    #################################
    """
    list values that depends on projection
    """

    if mode == 'r':
        valtype = 'in projection'

    elif mode == 'r2':
        valtype = 'in projection'

    elif mode == 'vr':
        valtype = 'in projection'

    elif mode == 'vr2':
        valtype = 'in projection'

    elif mode == 'vxyr':
        valtype = 'in projection'

    elif mode == 'vxyr2':
        valtype = 'in projection'

    elif mode == 'vtr':
        valtype = 'in projection'

    elif mode == 'vtr2':
        valtype = 'in projection'

    # other mode
    else:
        valtype = 'normal'

    return valtype


#################################
def extract_parameters(arg, kw, defaultparams):
    #################################
    """
    this function extract parameters given to a function
    it returns a dictionary of parameters with respective value

    defaultparams : dictionary of default parameters


    """

    params = {}

    if len(kw) == 0 and len(arg) >= 1:
        if isinstance(arg[0], dict):
            params = arg[0]

    elif len(kw) >= 1 and len(arg) >= 1:

        if isinstance(arg[0], dict):
            params = arg[0]

            # add other keywords
            for key in list(kw.keys()):
                params[key] = kw[key]

    elif len(kw) >= 1 and len(arg) == 0:
        params = kw

    newparams = deepcopy(defaultparams)
    for key in list(params.keys()):
        if key in defaultparams:
            newparams[key] = params[key]

    return newparams


##########################################################
# functions relative to mapping
##########################################################

#################################
def GetNumberMap(pos, shape):
    #################################
    """
    """

    val = np.ones(pos.shape).astype(np.float32)

    if len(shape) == 1:
        # compute zero momentum
        m0 = mapping.mkmap1d(pos, val, val, shape)

    elif len(shape) == 2:
        # compute zero momentum
        m0 = mapping.mkmap2d(pos, val, val, shape)

    elif len(shape) == 3:
        # compute zero momentum
        m0 = mapping.mkmap3d(pos, val, val, shape)

    else:
        return

    return m0

#################################


def GetMassMap(pos, mass, shape):
    #################################
    """
    """

    val = np.ones(pos.shape).astype(np.float32)

    if len(shape) == 1:
        # compute zero momentum
        m0 = mapping.mkmap1d(pos, mass, val, shape)

    elif len(shape) == 2:
        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, val, shape)

    elif len(shape) == 3:
        # compute zero momentum
        m0 = mapping.mkmap3d(pos, mass, val, shape)

    else:
        return

    return m0

#################################


def GetMeanValMap(pos, mass, val, shape):
    #################################
    """
    """

    if len(shape) == 1:
        # compute zero momentum
        m0 = mapping.mkmap1d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap1d(pos, mass, val, shape)

    elif len(shape) == 2:
        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)

    elif len(shape) == 3:
        # compute zero momentum
        m0 = mapping.mkmap3d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap3d(pos, mass, val, shape)

    else:
        return

    # combi map
    return GetMeanMap(m0, m1)


#################################
def GetSigmaValMap(pos, mass, val, shape):
    #################################
    """
    """

    if len(shape) == 1:
        # compute zero momentum
        m0 = mapping.mkmap1d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap1d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap1d(pos, mass, val * val, shape)

    elif len(shape) == 2:
        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap2d(pos, mass, val * val, shape)

    elif len(shape) == 3:
        # compute zero momentum
        m0 = mapping.mkmap3d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap3d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap3d(pos, mass, val * val, shape)

    else:
        return

    # combi map
    return GetSigmaMap(m0, m1, m2)


#################################
def GetMeanMap(m0, m1):
    #################################
    """
    Return a MeanMap using the 0 and 1 momentum

    m0 : zero  momentum
    m1 : first momentum
    """
    m1 = np.where(m0 == 0, 0, m1)
    m0 = np.where(m0 == 0, 1, m0)
    mat = m1 / m0

    return mat

#################################


def GetSigmaMap(m0, m1, m2):
    #################################
    """
    Return a MeanMap using the 0 and 1 and 2 momentum

    m0 : zero   momentum
    m1 : first  momentum
    m2 : second momentum
    """
    m1 = np.where(m0 == 0, 0, m1)
    m2 = np.where(m0 == 0, 0, m2)
    m0 = np.where(m0 == 0, 1, m0)
    mat = m2 / m0 - (m1 / m0)**2
    mat = np.where((mat > 0), np.sqrt(mat), 0)

    return mat


##########################################################
# extract from map functions
##########################################################

def Extract1dMeanFrom2dMap(x, y, mass, val, kx, ky, nmin, momentum=0):
    """

    Extract the mean along one axis, from a 2d mean or sigma matrix

    x    : pos in first dim.  (beetween 0 and 1)
    y    : pos in sec   dim.  (beetween 0 and 1)
    mass : mass of particles
    val  : value to compute

    kx : number of bins in x
    ky : number of bins in y

    nmin : min number of particles needed to compute value

    momentum : 0,1,2 (-1=number)
    """

    shape = (kx, ky)

    # normalize values

    pos = np.transpose(np.array([x, y, y], np.float32))

    mat_num = GetNumberMap(pos, shape)

    if momentum == -1:
        mat_val = GetNumberMap(pos, shape)
    if momentum == 0:
        mat_val = GetMassMap(pos, mass, shape)
    elif momentum == 1:
        mat_val = GetMeanValMap(pos, mass, val, shape)
    elif momentum == 2:
        mat_val = GetSigmaValMap(pos, mass, val, shape)

    ################
    # 2d mean
    ################

    mat_num = np.transpose(mat_num)
    mat_val = np.transpose(mat_val)

    m1 = np.sum(mat_num, 0)
    m0 = np.sum(np.ones(mat_val.shape), 0)
    vec_num = np.where((m0 != 0), m1 / m0, 0)

    c = (mat_num > nmin)  # *(mat_val!=0)
    m1 = np.sum(mat_val * c, 0)
    m0 = np.sum(np.ones(mat_val.shape) * c, 0)
    vec_sigma = np.where((m0 != 0), m1 / m0, 0)

    return vec_sigma


def get1dMeanFrom2dMap(mat_val, mat_num, nmin=32, axis=0):

    m1 = np.sum(mat_num, axis)
    m0 = np.sum(np.ones(mat_val.shape), axis)
    vec_num = np.where((m0 != 0), m1 / m0, axis)

    c = (mat_num > nmin)
    m1 = np.sum(mat_val * c, axis)
    m0 = np.sum(np.ones(mat_val.shape) * c, axis)
    vec_sigma = np.where((m0 != 0), m1 / m0, axis)

    return vec_sigma


##########################################################
# filter
##########################################################

#################################
def log_filter(x, xmin, xmax, xc, kx=1.0):
    #################################
    """
    map a value between 0 and kx
    """

    if xc == 0:
        return kx * (x - xmin) / (xmax - xmin)
    else:
        return kx * np.log(1 + (x - xmin) / xc) / np.log(1 + (xmax - xmin) / xc)

#################################


def log_filter_inv(k, xmin, xmax, xc, kx=1.0):
    #################################
    """
    map a value betwen xmin and xmax
    """
    if xc == 0:
        return (k / kx * (xmax - xmin)) + xmin
    else:
        A = np.log(1 + (xmax - xmin) / xc)
        return xc * (np.exp(A * k / kx) - 1.0) + xmin


##########################################################
# change of coordinate
##########################################################


######################
# cylindrical coord
######################

def vel_cyl2cart(pos=None, vel=None):
    """
    Transform velocities in cylindrical coordinates vr,vt,vz into carthesian
    coodinates vx,vy,vz.
    Pos is the position of particles in cart. coord.
    Vel is the velocity in cylindrical coord.
    Return a 3xn float array.
    """

    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]

    vr = vel[:, 0]
    vt = vel[:, 1]
    vz = vel[:, 2]

    r = np.sqrt(x**2 + y**2)

    vx = np.where(r > 0, (vr * x - vt * y) / r, 0)
    vy = np.where(r > 0, (vr * y + vt * x) / r, 0)
    vz = vz

    return np.transpose(np.array([vx, vy, vz])).astype(np.float32)


def vel_cart2cyl(pos, vel):
    """
    Transform velocities in carthesian coordinates vx,vy,vz into cylindrical
    coodinates vr,vz,vz.
    Pos is the position of particles in cart. coord.
    Vel is the velocity in cart. coord.
    Return a 3xn float array.
    """

    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]

    vx = vel[:, 0]
    vy = vel[:, 1]
    vz = vel[:, 2]

    r = np.sqrt(x**2 + y**2 + z**2)

    vr = np.where(r > 0, (x * vx + y * vy) / r, 0)
    vt = np.where(r > 0, (x * vy - y * vx) / r, 0)
    vz = vz

    return np.transpose(np.array([vr, vt, vz])).astype(np.float32)


##########################################################
# gl2nbody
##########################################################


def RotateAround(angle, axis, point, ObsM):
    """
    this should be C
    """


    # this work with OpenGL
    #Q = np.ones(16,float)
    # glLoadIdentity();
    # glTranslated(point[0],point[1],point[2]);
    # glRotated(angle,axis[0],axis[1],axis[2]);
    # glTranslated(-point[0],-point[1],-point[2]);
    ##Q = glGetDoublev(GL_MODELVIEW_MATRIX);
    # glMultMatrixd(ObsM);
    #ObsM = glGetDoublev(GL_MODELVIEW_MATRIX);
    # return np.ravel(ObsM)

    angle = angle * np.pi / 180
    point = np.concatenate((point, np.array([0])))

    M = ObsM
    M.shape = (4, 4)

    # center point
    M = M - point

    # construction of the rotation matrix
    norm = np.sqrt(axis[0]**2 + axis[1]**2 + axis[2]**2)
    if norm == 0:
        raise ValueError("getting norm=sqrt(ax[0]^2+ax[1]^2+ax[2]^2) = 0, which I can't handle.")
    sn = np.sin(-angle / 2.)

    e0 = np.cos(-angle / 2.)
    e1 = axis[0] * sn / norm
    e2 = axis[1] * sn / norm
    e3 = axis[2] * sn / norm

    a = np.zeros((4, 4), float)
    a[0, 0] = e0**2 + e1**2 - e2**2 - e3**2
    a[1, 0] = 2. * (e1 * e2 + e0 * e3)
    a[2, 0] = 2. * (e1 * e3 - e0 * e2)
    a[3, 0] = 0.
    a[0, 1] = 2. * (e1 * e2 - e0 * e3)
    a[1, 1] = e0**2 - e1**2 + e2**2 - e3**2
    a[2, 1] = 2. * (e2 * e3 + e0 * e1)
    a[3, 1] = 0.
    a[0, 2] = 2. * (e1 * e3 + e0 * e2)
    a[1, 2] = 2. * (e2 * e3 - e0 * e1)
    a[2, 2] = e0**2 - e1**2 - e2**2 + e3**2
    a[3, 2] = 0.
    a[0, 3] = 0.
    a[1, 3] = 0.
    a[2, 3] = 0.
    a[3, 3] = 1.

    a = a.astype(float)

    # multiply x and v
    M = np.dot(M, a)

    # decenter point
    M = M + point

    return np.ravel(M)


def gl2pNbody(glparam, nbparam=None):

    EYE = 0
    PTS = 4
    HEA = 8
    ARM = 12

    gwinShapeX = 512				# to change...
    gwinShapeY = 512

    ProjectionMode = glparam["ProjectionMode"]

    if (ProjectionMode):
        # frustum
        gwinPerspectiveTop = glparam["PerspectiveNear"] * \
            np.tan(glparam["PerspectiveFov"] * 0.5 * np.pi / 180.)
        gwinPerspectiveRight = gwinPerspectiveTop * \
            float(gwinShapeX) / float(gwinShapeY)
    else:
        # ortho
        gwinPerspectiveLeft = -5 * glparam["PerspectiveNear"]
        gwinPerspectiveRight = -gwinPerspectiveLeft
        gwinPerspectiveTop = float(gwinShapeY) / \
            float(gwinShapeX) * gwinPerspectiveRight

    gwinClip1 = glparam["PerspectiveNear"]
    gwinClip2 = glparam["PerspectiveFar"]

    # /*********************/
    # /* observer position */
    # /*********************/

    # /* copy the observer matrix */
    # ObsObject.ComputeEyes();

    M = np.zeros(16, np.float32)
    axis = np.zeros(3, np.float32)
    point = np.zeros(3, np.float32)

    M[0] = glparam["M0"]
    M[1] = glparam["M1"]
    M[2] = glparam["M2"]
    M[3] = glparam["M3"]
    M[4] = glparam["M4"]
    M[5] = glparam["M5"]
    M[6] = glparam["M6"]
    M[7] = glparam["M7"]
    M[8] = glparam["M8"]
    M[9] = glparam["M9"]
    M[10] = glparam["M10"]
    M[11] = glparam["M11"]
    M[12] = glparam["M12"]
    M[13] = glparam["M13"]
    M[14] = glparam["M14"]
    M[15] = glparam["M15"]

    # rotate
    axis[0] = M[EYE + 0] - M[PTS + 0]
    axis[1] = M[EYE + 1] - M[PTS + 1]
    axis[2] = M[EYE + 2] - M[PTS + 2]
    point[0] = M[EYE + 0]
    point[1] = M[EYE + 1]
    point[2] = M[EYE + 2]

    M = RotateAround(90, axis, point, M)			# this is also bad !!!

    # this is not correct, dist must come from projec. params */
    dist = np.sqrt((M[0] - M[8])**2 + (M[1] - M[9])**2 + (M[2] - M[10])**2)

    # head
    obs1 = M[0]
    obs2 = M[1]
    obs3 = M[2]

    # lookat point */
    norm = np.sqrt((M[0] - M[4])**2 + (M[1] - M[5])**2 + (M[2] - M[6])**2)

    obs4 = obs1 + (M[4] - obs1) / norm * dist
    obs5 = obs2 + (M[5] - obs2) / norm * dist
    obs6 = obs3 + (M[6] - obs3) / norm * dist

    # arm
    norm = np.sqrt((M[0] - M[8])**2 + (M[1] - M[9])**2 + (M[2] - M[10])**2)

    obs7 = obs1 + (M[8] - obs1) / norm
    obs8 = obs2 + (M[9] - obs2) / norm
    obs9 = obs3 + (M[10] - obs3) / norm

    # head
    norm = np.sqrt((M[0] - M[12])**2 + (M[1] - M[13])**2 + (M[2] - M[14])**2)

    obs10 = obs1 + (M[12] - obs1) / norm
    obs11 = obs2 + (M[13] - obs2) / norm
    obs12 = obs3 + (M[14] - obs3) / norm

    obs = np.array([obs1, obs2, obs3, obs4, obs5, obs6, obs7,
                 obs8, obs9, obs10, obs11, obs12], float)
    obs.shape = (4, 3)

    if nbparam is None:
        nbparam = param.Params(PARAMETERFILE, None)

    nbparam.set('obs', obs)
    nbparam.set('X0', 'None')
    nbparam.set('xp', 'None')
    nbparam.set('alpha', 'None')
    nbparam.set('view', 'xy')
    nbparam.set('r_obs', dist)
    nbparam.set('clip', (gwinClip1, gwinClip2))
    nbparam.set('eye', 'None')
    nbparam.set('dist_eye', 0.1)
    nbparam.set('foc', 0.1)

    if ProjectionMode:
        nbparam.set('persp', 'on')
        nbparam.set('cut', 'yes')
    else:
        nbparam.set('persp', 'off')
        nbparam.set('cut', 'no')

    nbparam.set('shape', (gwinShapeX, gwinShapeY))
    nbparam.set('size', (gwinPerspectiveRight, gwinPerspectiveTop))

    return nbparam


def get_CommandLine():
  """
  return the command line from invocated
  """
  return " ".join(sys.argv)
  
def get_GitTag():
  """
  return the pNbody git tag
  """
  import pNbody
  return pNbody.__version__

def get_UserName():
  """
  return the user name
  """

  if "USER" in os.environ:
    username      = os.environ['USER']
  else:
    username      = 'unknown'
  
  return username
  

def get_Date():
  """
  get the date
  """
  import time
  return time.ctime()


  
#################################
def getLOS(nlos,seed=None):
#################################
  """
  return n line of sights in for of an nx3 array
  """
  
  # get points in a shell of size 1
  if seed is not None:
    np.random.seed(seed=seed)
    
  rand1 = np.random.random(nlos)
  rand2 = np.random.random(nlos)
  
  # define a shell
  phi = rand1 * np.pi * 2.
  costh = 1. - 2. * rand2
  sinth = np.sqrt(1. - costh**2)
  
  x = sinth * np.cos(phi)
  y = sinth * np.sin(phi)
  z = costh
  
  los = np.transpose(np.array([x, y, z]))

  return los  
  
  
  
    
  
    
  
