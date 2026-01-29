#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      geometry.py
#  brief:     Geometry transformation/computation
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import numpy as np


def norm(x):
    """
    return the norm of vector x
    """
    return np.sqrt(x[0]**2 + x[1]**2 + x[2]**2)


def rotate(x, angle=0, axis=[1, 0, 0], point=[0, 0, 0]):
    """
    Rotate the positions and/or the velocities of the object around a specific axis
    with respect to a specific point

    angle : rotation angle in radian
    axis  : [x,y,z] : around this axis
    point : [x,y,z] : rotation origin

    use the euler rotation matrix
    """

    # center point
    x = x - point

    # construction of the rotation matrix
    norm = np.sqrt(axis[0]**2 + axis[1]**2 + axis[2]**2)
    if norm == 0:
        return x
    sn = np.sin(-angle / 2.)

    e0 = np.cos(-angle / 2.)
    e1 = axis[0] * sn / norm
    e2 = axis[1] * sn / norm
    e3 = axis[2] * sn / norm

    a = np.zeros((3, 3), float)
    a[0, 0] = e0**2 + e1**2 - e2**2 - e3**2
    a[1, 0] = 2. * (e1 * e2 + e0 * e3)
    a[2, 0] = 2. * (e1 * e3 - e0 * e2)
    a[0, 1] = 2. * (e1 * e2 - e0 * e3)
    a[1, 1] = e0**2 - e1**2 + e2**2 - e3**2
    a[2, 1] = 2. * (e2 * e3 + e0 * e1)
    a[0, 2] = 2. * (e1 * e3 + e0 * e2)
    a[1, 2] = 2. * (e2 * e3 - e0 * e1)
    a[2, 2] = e0**2 - e1**2 - e2**2 + e3**2
    a = a.astype(float)

    # multiply x
    x = np.dot(x, a)

    # decenter point
    return x + point


def align(x, axis1=[1, 0, 0], axis2=[0, 0, 1], point=[0, 0, 0]):
    """
    Rotate the object around point in order to align the axis 'axis1' with the axis 'axis2'.

    axis1 : [x,y,z]
    axis2 : [x,y,z]
    """

    a1 = np.array(axis1, float)
    a2 = np.array(axis2, float)

    a3 = np.array([0, 0, 0], float)
    a3[0] = a1[1] * a2[2] - a1[2] * a2[1]
    a3[1] = a1[2] * a2[0] - a1[0] * a2[2]
    a3[2] = a1[0] * a2[1] - a1[1] * a2[0]

    n1 = np.sqrt(a1[0]**2 + a1[1]**2 + a1[2]**2)
    n2 = np.sqrt(a2[0]**2 + a2[1]**2 + a2[2]**2)
    angle = np.arccos(np.inner(a1, a2) / (n1 * n2))

    return rotate(x, angle=angle, axis=a3, point=point)


def expose(obj, obs, eye=None, dist_eye=None, foc=None):
    """
    Rotate and translate the object in order to be seen as if the
    observer was in x0, looking at a point in xp.

    obj	      : object array to expose
    obs         : representation of the observer
    eye	      : 'right' or 'left'
    dist_eye    : distance between eyes (separation = angle))
    foc         : focal

    """

    # first : put x0 at the origin
    obj = obj - obs[0]
    obs = obs - obs[0]

    # second : anti-align e1 with z
    obj = align(obj, axis1=obs[1], axis2=[0, 0, -1])
    obs = align(obs, axis1=obs[1], axis2=[0, 0, -1])

    # third : align e3 with y
    obj = align(obj, axis1=obs[3], axis2=[0, 1, 0])

    # fourth if eye is defined
    if eye == 'right':
        if foc is not None:
            Robs = foc
        else:
            Robs = np.sqrt((obs[0][0] - obs[1][0])**2 + (obs[0]
                                                      [1] - obs[1][1])**2 + (obs[0][2] - obs[1][2])**2)
        phi = -np.arctan(dist_eye)
        obj = rotate(obj, -phi, axis=[0, 1, 0], point=[0, 0, -Robs])
    elif eye == 'left':
        if foc is not None:
            Robs = foc
        else:
            Robs = np.sqrt((obs[0][0] - obs[1][0])**2 + (obs[0]
                                                      [1] - obs[1][1])**2 + (obs[0][2] - obs[1][2])**2)
        phi = -np.arctan(dist_eye)
        obj = rotate(obj, +phi, axis=[0, 1, 0], point=[0, 0, -Robs])

    return obj


#  def perspective(r_obs=100., foc=50., view='xz'):
#      """
#      Project the N-body model in order to get a perspective view.
#
#      r_obs = distance of the observer to the looking point
#      foc	= focal
#      view  = 'xz' , 'xy' , 'yz'
#      """
#      from pNbody.nbodymodule import perspective as perspec
#
#      if view == 'xz':
#          view = 1
#      elif view == 'xy':
#          view = 2
#      elif view == 'yz':
#          view = 3
#      elif view != 'xz'and view != 'xy'and view != 'yz':
#          view = 1
#
#      return perspec(pos, r_obs, foc, view)


def frustum(pos, clip, size):
    """
    Project using a frustrum matrix

    clip = near and far planes
    size = size of the box
    """

    tmp = np.ones((pos.shape[0], pos.shape[1] + 1), float)
    tmp[:, :-1] = pos
    pos = tmp

    n = float(clip[0])
    f = float(clip[1])
    l = -float(size[0])
    r = float(size[0])
    b = -float(size[1])
    t = float(size[1])

    # frustum
    m1 = np.zeros((4, 4), float)

    m1[0, 0] = 2. * n / (r - l)
    m1[1, 0] = 0.
    m1[2, 0] = (r + l) / (r - l)
    m1[3, 0] = 0.

    m1[0, 1] = 0.
    m1[1, 1] = 2. * n / (t - b)
    m1[2, 1] = (t + b) / (t - b)
    m1[3, 1] = 0.

    m1[0, 2] = 0.
    m1[1, 2] = 0.
    m1[2, 2] = -(f + n) / (f - n)
    m1[3, 2] = -(2. * f * n) / (f - n)

    m1[0, 3] = 0.
    m1[1, 3] = 0.
    m1[2, 3] = -1
    m1[3, 3] = 0.

    m1 = m1.astype(float)

    posc = np.dot(pos, m1)
    posc = np.transpose(np.transpose(posc) / posc[:, 3])[:, :-1]

    return posc


def ortho(pos, clip, size):
    """
    Project using an ortho matrix

    clip = near and far planes
    size = size of the box
    """

    tmp = np.ones((pos.shape[0], pos.shape[1] + 1), float)
    tmp[:, :-1] = pos
    pos = tmp

    n = float(clip[0])
    f = float(clip[1])
    l = -float(size[0])
    r = float(size[0])
    b = -float(size[1])
    t = float(size[1])

    # ortho
    m1 = np.zeros((4, 4), float)

    m1[0, 0] = 2. / (r - l)
    m1[1, 0] = 0.
    m1[2, 0] = 0.
    m1[3, 0] = -(r + l) / (r - l)

    m1[0, 1] = 0.
    m1[1, 1] = 2. / (t - b)
    m1[2, 1] = 0
    m1[3, 1] = -(t + b) / (t - b)

    m1[0, 2] = 0.
    m1[1, 2] = 0.
    m1[2, 2] = -2. / (f - n)
    m1[3, 2] = -(f + n) / (f - n)

    m1[0, 3] = 0.
    m1[1, 3] = 0.
    m1[2, 3] = 0.
    m1[3, 3] = 1.

    m1 = m1.astype(float)

    posc = np.dot(pos, m1)
    posc = np.transpose(np.transpose(posc) / posc[:, 3])[:, :-1]

    return posc


def viewport(xn, shape=None):
    """
    viewport transformation

    xn    = position (output from frustum or ortho)
    shape = shape of the image
    """

    x = xn[:, 0]
    y = xn[:, 1]
    z = xn[:, 2]

    if shape is None:
        wx = 1
        wy = 1
    else:
        wx = shape[0]
        wy = shape[1]

    winx = (x + 1) / 2. * wx
    winy = -(y - 1) / 2. * wy
    winz = (z + 1) / 2.

    return np.transpose(np.array([winx, winy, winz]))


def inv_viewport(xw, yw, zw, shape):
    """
    viewport transformation

    xn    = position (output from frustum or ortho)
    shape = shape of the image
    """

    wx = shape[0]
    wy = shape[1]

    x = 2. * xw / wx - 1
    y = -2. * yw / wy + 1
    z = 2. * zw - 1

    return x, y, z


def boxcut(pos, args):
    """
    Return only particles that are inside box 1:1:1
    """

    c = np.logical_not((np.fabs(pos[:, 0]) > 1) | (
        np.fabs(pos[:, 1]) > 1) | (np.fabs(pos[:, 2]) > 1))
    pos = np.compress(c, pos, axis=0)
    newargs = ()
    for arg in args:
        newargs = newargs + (np.compress(c, arg, axis=0),)

    return pos, newargs


def boxcut_segments(pos, args):
    """
    Return only particles that are inside box 1:1:1
    """

    n = len(pos)
    p = int(n / 2)

    newpos = np.zeros(pos.shape)
    cs = np.zeros(len(pos))
    NP = 0

    for j in range(p):
        i = 2 * j

        f0 = False
        f1 = False
        if (np.fabs(pos[i, 0]) > 1) or (
                np.fabs(pos[i, 1]) > 1) or (np.fabs(pos[i, 2]) > 1):
            f0 = True
        if (np.fabs(pos[i + 1, 0]) > 1) or (np.fabs(pos[i + 1, 1])
                                         > 1) or (np.fabs(pos[i + 1, 2]) > 1):
            f1 = True

        if f0 and f1:
            # both outside : remove the segment
            # print "remove"
            pass
        elif f0 and not f1:
            # 0 outside 1 inside : change 0
            # print "change 0"
            newpos[i] = pos[i]
            newpos[i + 1] = pos[i + 1]
            cs[i] = 0		# remove
            cs[i + 1] = 0
            NP += 2
        elif not f0 and f1:
            # 0 inside 1 outside : change 1
            # print "change 1"
            newpos[i] = pos[i]
            newpos[i + 1] = pos[i + 1]
            cs[i] = 0		# remove
            cs[i + 1] = 0
            NP += 2
        else:
            # both inside  : keep
            newpos[i] = pos[i]
            newpos[i + 1] = pos[i + 1]
            cs[i] = 1
            cs[i + 1] = 1
            NP += 2

    pos = np.compress(cs, newpos, axis=0)

    newargs = ()
    for arg in args:
        newargs = newargs + (np.compress(cs, arg, axis=0),)

    return pos, newargs


def get_obs(x0=[0., -50., 0.], xp=[0., 0., 0.], alpha=0, view='xz', r_obs=50):
    """
    From some parameters, return an obs matrix

    {x0,xp,alpha} or {xz}

    """

    # use view and r_obs
    if (x0 is None or xp is None or alpha is None) and (
            view is not None and r_obs is not None):
        if view == 'xz':
            e0 = np.array([0, -r_obs, 0], float)
            e1 = np.array([0, 0, 0], float)
            e2 = np.array([-1, -r_obs, 0], float)
            e3 = np.array([0, -r_obs, 1], float)
        elif view == 'xy':
            e0 = np.array([0, 0, r_obs], float)
            e1 = np.array([0, 0, 0], float)
            e2 = np.array([-1, 0, r_obs], float)
            e3 = np.array([0, 1, r_obs], float)
        elif view == 'yz':
            e0 = np.array([r_obs, 0, 0], float)
            e1 = np.array([0, 0, 0], float)
            e2 = np.array([r_obs, -1, 0], float)
            e3 = np.array([r_obs, 0, 1], float)
        else:
            e0 = np.array([0, -r_obs, 0], float)
            e1 = np.array([0, 0, 0], float)
            e2 = np.array([-1, -r_obs, 0], float)
            e3 = np.array([0, -r_obs, 1], float)

        # create the matrix
        obs = np.array([e0, e1, e2, e3], float)

        # center xp
        if xp is not None:
            obs = obs + xp

    # use x0,xp,alpha
    else:

        x0 = np.array(x0, float)
        xp = np.array(xp, float)

        Robs = np.sqrt((x0[0] - xp[0])**2 + (x0[1] - xp[1])
                    ** 2 + (x0[2] - xp[2])**2)

        e0 = np.array([0, 0, 0], float)
        e1 = np.array([Robs, 0, 0], float)
        e2 = np.array([0, 1, 0], float)
        e3 = np.array([0, 0, 1], float)

        # create the matrix
        obs = np.array([e0, e1, e2, e3], float)

        #####################

        yp = xp - x0
        rxy = np.sqrt(yp[0]**2 + yp[1]**2)
        z = yp[2]

        a = np.arctan2(yp[1], yp[0])

        if rxy != 0:
            b = np.arctan(z / rxy)
        else:
            b = 0.

        # rotate azimuth
        obs = rotate(obs, angle=a, axis=[0, 0, 1])

        # rotate elevation
        obs = rotate(obs, angle=-b, axis=obs[2])

        # rotate (xa around e1)
        obs = rotate(obs, angle=alpha, axis=obs[1])

        # translate to x0
        obs = obs + x0


    # # old version (bad)
    #
    # # create the matrix
    # obs =  np.array([e0,e1,e2,e3],float)
    #
    # # rotate (align e1 with xp-x0 )
    # obs = align(obs,axis1=obs[1],axis2=xp-x0)
    #
    # # rotate (xa around e1)
    # obs = rotate(obs,angle=alpha,axis=obs[1])
    #
    # # translate to x0
    # obs = obs + x0



        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!! e2 may not be parallel to the plane z=0 !!!
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    return obs
