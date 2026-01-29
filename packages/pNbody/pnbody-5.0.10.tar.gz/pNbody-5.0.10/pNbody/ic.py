#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      ic.py
#  brief:     generating initial conditions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


from pNbody import *
from pNbody import iclib
import numpy as np

import sys


from scipy.integrate import quad
from scipy import special
from scipy import optimize



"""
# isotropic velocities
random2 = np.random.random([n])
random3 = np.random.random([n])
p = 2*pi*random2
costh = 1.-2.*random3
sinth = np.sqrt(1.-costh**2)
vx = v*sinth*np.cos(p)
vy = v*sinth*np.sin(p)
vz = v*costh

# radial velocities
x = nb.pos[:,0]
y = nb.pos[:,1]
z = nb.pos[:,2]
vx = v*x/r
vy = v*y/r
vz = v*z/r



Some notes on the generation of initial conditions:

Spherical case
--------------

1) if M(r) is known analytically :

  1.1) if it is invertible analytically
       --> for a given x between 0 and 1, find r from M(r)

  1.2) if it is not invertible analytically


       1.2.1) use a Monte-Carlo approach
              (warning : may take time if the model is cuspy)

       1.2.2) invert M(r) numerically and create a vector of r and Mr
              then, use generic_Mr

       1.2.3) for a given x between 0 and 1, find r from M(r),
              by inverting M(r). May take time.







"""


def get_local_n(n):
    """
    This function set the global number of particle each
    node must hand.
    """

    # set the number of particles per procs
    n0 = n
    npercpu = n / mpi.mpi_NTask()

    if mpi.mpi_IsMaster():
        npercpu = npercpu + (n - npercpu * mpi.mpi_NTask())

    n = npercpu

    ntot = mpi.mpi_allreduce(n)

    if ntot != n0:
        print(("ntot=%d while n0=%d" % (ntot, n0)))
        sys.exit()

    return int(n), int(ntot)


def ComputeGridParameters(n, args, rmax, M, pr_fct, mr_fct, Neps_des, rc, ng):
    """

    This function computes dR, the appropriate grid used to approximate Mr.

    The grid is set in order to have "Neps_des" particles
    in the first division of the grid. Then, the radius of the grid
    follows an exponnential distribution up to rmax.

    1) from the density distribution, the total mass and the number of particles,
       using a newton algorithm, it computes eps, the radius that will contains "Neps_des" particles


    2) once eps is set, we determine rc (the grid scale length) from eps and ng, in order to
       have a grid with the a first cell equal to eps.


       if the computation of rc fails, we use the default value of rc


    The function takes the following arguments

    n 		: number of particles
    M		: total mass
    rmax          : max radius
    args		: list of args for the profile
    pr_fct	: profile function
    mr_fct	: mass-radius function

    Neps_des	: desired number of point in the first beam
    rc		: default size of the first beam
    ng		: number of grid divisions


    it returns :


    Rs		: grid points
    eps		: radius containing about  Neps_des particles
    Neps		: number of particles in eps
    """



    ###########################
    # some considerations
    ###########################

    # central density
    rho0 = M / mr_fct(*(rmax,) + args)

    # mass of particles
    m = M / float(n)

    args = args + (rho0,)
    rs = args[0]

    ##########################################################################
    # find eps in order to have Neps_des particles in eps
    def RfromN(r, args, m, N):
        return mr_fct(*(r,) + args) / m - N

    try:
        eps = optimize.newton(
            RfromN,
            x0=rs,
            args=(
                args,
                m,
                Neps_des),
            fprime=None,
            tol=1e-10,
            maxiter=500)
    except BaseException:
        print("fail to get eps from newton, trying bisection.")
        try:
            eps = optimize.bisection(
                RfromN,
                a=1e-10,
                b=rs,
                args=(
                    args,
                    m,
                    Neps_des),
                xtol=1e-5,
                maxiter=500)
            print("ok")
        except BaseException:
            print("fail to get eps from bisection.")
            print("quit")
            sys.exit()

    ##########################################################################

    ##########################################################################
    # compute the number of particles that will fall in eps
    Meps = mr_fct(*(eps,) + args)
    Neps = Meps / m
    ##########################################################################

    ##########################################################################
    # parameters for the adaptative grid

    # find eps in order to have Neps_des particles in eps

    def GetRc(rc, n, rmax, eps):
        return (np.exp((1. / (ng - 1)) / rc) - 1) / \
            (np.exp(1. / rc) - 1) * rmax - eps

    try:
        #rc = optimize.newton(GetRc, x0=0.1, args = (n,rmax,eps), fprime = None, tol = 1e-20, maxiter = 500)
        rc = optimize.bisection(
            GetRc,
            a=1e-4,
            b=rmax,
            args=(
                n,
                rmax,
                eps),
            xtol=1e-3,
            maxiter=500)
    except BaseException:
        print(("fail to get rc, using rc=%g." % rc))

    def gm(i): return (np.exp((i / float(ng - 1)) / rc) - 1) / \
        (np.exp(1. / rc) - 1) * rmax

    def g(r): return float(ng - 1) * rc * \
        np.log(r / rmax * (np.exp(1. / rc) - 1.) + 1.)
    Rs = gm(np.arange(ng))

    return Rs, rc, eps, Neps, g, gm


def ComputeGridParameters2(
        eps,
        nmax,
        args,
        rmax,
        M,
        pr_fct,
        mr_fct,
        Neps_des,
        rc,
        ng):
    """

    This function computes dR, the appropriate grid used to approximate Mr.

    The number of particle of the model is set in order to have "Neps_des" particles
    in the first division of the grid. Then, the radius of the grid
    follows an exponential distribution up to rmax.

    1) n is set from the total mass and Neps_des

    2) once n is set, we determine rc (the grid scale length) from eps and ng, in order to
       have a grid with the a first cell equal to eps.


       if the computation of rc fails, we use the default value of rc


    The function takes the following arguments

    eps 		: the desired grid resolution
    nmax		: max number of particles
    M		: total mass
    rmax          : max radius
    args		: list of args for the profile
    pr_fct	: profile function
    mr_fct	: mass-radius function

    Neps_des	: desired number of point in the first beam
    rc		: default size of the first beam
    ng		: number of grid divisions


    it returns :

    n		: number of particles
    Rs		: grid points
    rc		: parameter of the scaling fct
    g		: scaling fct
    gm		: inverse of scaling fct
    """



    ###########################
    # some considerations
    ###########################

    # central density
    rho0 = M / mr_fct(*(rmax,) + args)

    args = args + (rho0,)
    rs = args[0]

    # number of particles
    n = int(Neps_des * M / mr_fct(*(eps,) + args))

    # if n> nmax, find eps containing Neps_des particles
    if n > nmax:

        n = nmax

        # mass of particles
        m = M / float(n)

        #######################################################################
        # find eps in order to have Neps_des particles in eps

        def RfromN(r, args, m, N):
            return mr_fct(*(r,) + args) / m - N

        try:
            eps = optimize.newton(
                RfromN,
                x0=rs,
                args=(
                    args,
                    m,
                    Neps_des),
                fprime=None,
                tol=1e-10,
                maxiter=500)
        except BaseException:
            print("fail to get eps from newton, trying bisection.")
            try:
                eps = optimize.bisection(
                    RfromN,
                    a=1e-10,
                    b=rs,
                    args=(
                        args,
                        m,
                        Neps_des),
                    xtol=1e-5,
                    maxiter=500)
                print("ok")
            except BaseException:
                print("fail to get eps from bisection.")
                print("quit")
                sys.exit()

        #######################################################################

        #######################################################################
        # compute the number of particles that will fall in eps
        Meps = mr_fct(*(eps,) + args)
        Neps = Meps / m
        #######################################################################

    # mass of particles
    m = M / float(n)

    ##########################################################################
    # parameters for the adaptative grid

    # find eps in order to have Neps_des particles in eps

    def GetRc(rc, ng, rmax, eps):
        return (np.exp((1. / (ng - 1)) / rc) - 1) / \
            (np.exp(1. / rc) - 1) * rmax - eps

    try:
        #rc = optimize.newton(GetRc, x0=0.1, args = (n,rmax,eps), fprime = None, tol = 1e-20, maxiter = 500)
        rc = optimize.bisection(
            GetRc,
            a=1e-4,
            b=rmax,
            args=(
                ng,
                rmax,
                eps),
            xtol=1e-3,
            maxiter=500)
    except BaseException:
        print(("fail to get rc, using rc=%g." % rc))

    def gm(i): return (np.exp((i / float(ng - 1)) / rc) - 1) / \
        (np.exp(1. / rc) - 1) * rmax

    def g(r): return float(ng - 1) * rc * \
        np.log(r / rmax * (np.exp(1. / rc) - 1.) + 1.)
    Rs = gm(np.arange(ng))

    return n, eps, Rs, rc, g, gm


def invert(x, rmin, rmax, fct, args, eps=1e-10):
    """
    return vector r that corresponds to
    fct(r,args)=x
    This routine uses a simple bissector algorithm
    """
    n = len(x)
    rrmin = rmin * np.ones(n)
    rrmax = rmax * np.ones(n)
    xxmin = fct(rrmin, args) - x
    xxmax = fct(rrmax, args) - x

    if np.sum((xxmin * xxmax >= 0)) != 0:
        print("No max between rmin and rmax ! for some points")
        sys.exit()

    k = 0

    while max(abs(rrmax - rrmin)) > eps:

        print(("it = %3d err = %8.1e" % (k, max(abs(rrmax - rrmin)))))

        k = k + 1
        rr = (rrmax + rrmin) / 2.

        xx = fct(rr, args) - x

        rrmax = np.where(xxmin * xx <= 0, rr, rrmax)
        rrmin = np.where(xxmin * xx > 0, rr, rrmin)
        xxmin = np.where(xxmin * xx > 0, xx, xxmin)

    return rr


def box(n, a, b, c, irand=1, name='box.h5py', ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in an homogeneous box of dimension a,b,c, centred at the origin
    radius rmax.
    """

    if isinstance(n, np.ndarray):
        rand_vec = n
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:
        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)
        # generate random numbers
        rand_vec = np.random.random([n, 3])

    pos = rand_vec - [0.5, 0.5, 0.5]
    pos = pos * np.array([2 * a, 2 * b, 2 * c])

    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def homodisk(
    n,
    a,
    b,
    dz,
    irand=1,
    name='homodisk.hdf5',
    ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in an homogeneous oval of radius a and b, and of thickness dz.
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    xx = random1**(1. / 2.)

    theta = 2. * random2 * np.pi

    x = a * xx * np.cos(theta)
    y = b * xx * np.sin(theta)
    z = dz * random3 - dz / 2.

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def disklrrc(
    n,
    a,
    b,
    dz,
    irand=1,
    name='homodisk.hdf5',
    ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in a disk having a linear rising rotation curve.
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    xx = random1**(1. / 3)

    theta = 2. * random2 * np.pi

    x = a * xx * np.cos(theta)
    y = b * xx * np.sin(theta)
    z = dz * random3 - dz / 2.

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def mestel(
    n,
    rmax=1,
    dz=0,
    V0=1,
    G=1,
    irand=1,
    name='mestel.dat',
    ftype='gadget'):
    """
    Return an Nbody object that contains n particles distributed
    such as they reproduce a Mestel disk (1/R surface density).
    
    V0 : rotation curve at infinity
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])
    
    Mtot = V0*V0/G * rmax

    xx = random1

    theta = 2. * random2 * np.pi

    x = rmax * xx * np.cos(theta)
    y = rmax * xx * np.sin(theta)
    z = dz * random3 - dz / 2.

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot  * Mtot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb



def pseudomestel(
    n,
    rmax=1,
    dz=0,
    V0=1,
    a=0.1,
    G=1,
    irand=1,
    name='pseudomestel.dat',
    ftype='gadget'):
    """
    Return an Nbody object that contains n particles distributed
    such as they reproduce a Mestel disk (1/sqrt(a^2 + R^2) surface density).
    
    V0 : rotation curve at infinity
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])
    
    Mtot = V0*V0/G * ( np.sqrt(rmax**2 + a**2) -a   )
    xx =  np.sqrt( (G*random1*Mtot/(V0**2) + a )**2 - a**2 )
    
    theta = 2. * random2 * np.pi

    x = xx * np.cos(theta)
    y = xx * np.sin(theta)
    z = dz * random3 - dz / 2.

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot  * Mtot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb



def homosphere(
    n,
    a,
    b,
    c,
    irand=1,
    name='homosphere.hdf5',
    ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in an homogeneous triaxial sphere of axis a,b,c.
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    xm = (random1)**(1. / 3.)
    phi = random2 * np.pi * 2.
    costh = 1. - 2. * random3

    sinth = np.sqrt(1. - costh**2)
    axm = a * xm * sinth
    bxm = b * xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = c * xm * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def ring(n, r, M=1.0, irand=1, name='ring.hdf5', ftype='swift'):
    """
    Ring of radius r
    """

    if isinstance(n, np.ndarray):
        random2 = n[:, 0]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:
        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)
        random2 = np.random.random(n)

    phi = random2 * np.pi * 2.

    x = r *np.cos(phi)
    y = r *np.sin(phi)
    z = np.zeros(n)

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = M*np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb





def shell(n, r, irand=1, name='shell.hdf5', ftype='swift'):
    """
    Shell of radius r
    """

    if isinstance(n, np.ndarray):
        random2 = n[:, 0]
        random3 = n[:, 1]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:
        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)
        random2 = np.random.random(n)
        random3 = np.random.random(n)

    phi = random2 * np.pi * 2.
    costh = 1. - 2. * random3

    sinth = np.sqrt(1. - costh**2)

    x = r * sinth * np.cos(phi)
    y = r * sinth * np.sin(phi)
    z = r * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def plummer(
    n,
    a,
    b,
    c,
    eps,
    rmax,
    M=1.,
    irand=1,
    vel='no',
    name='plummer.hdf5',
    ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in a triaxial plummer model of axis a,b,c and core radius eps
    and max radius of rmax.

    rho = (1.+(r/eps)**2)**(-5/2)

    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    # positions
    rmax = float(rmax)
    eps = float(eps)

    eps = eps / rmax
    xm = 1. / (1. + (eps)**2) * random1**(2. / 3.)
    xm = eps * np.sqrt(xm / (1. - xm))
    phi = 2 * np.pi * random2

    costh = 1. - 2. * random3
    sinth = np.sqrt(1. - costh**2)
    axm = rmax * a * xm * sinth
    bxm = rmax * b * xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = rmax * c * xm * costh

    pos = np.transpose(np.array([x, y, z]))
    # velocities
    if vel == 'yes':

        R = np.sqrt(x**2 + y**2)
        rho = (3. * M / (4. * np.pi * eps**3)) * \
            (1 + (R**2 + z**2) / eps**2)**(-5. / 2.)
        C2 = z**2 + eps**2
        C = np.sqrt(C2)

        TD = M * C / (R**2 + C2)**(3. / 2.)
        sz = np.sqrt(eps**2 / (8. * np.pi * C2) / rho) * TD

        vx = sz * np.random.standard_normal([n])
        vy = sz * np.random.standard_normal([n])
        vz = sz * np.random.standard_normal([n])
        vel = np.transpose(np.array([vx, vy, vz]))

    else:
        vel = np.ones([n, 3]) * 0.0

    # masses
    mass = np.ones([n]) * M / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def kuzmin(
        n,
        eps,
        dz,
        irand=1,
        name='kuzmin.hdf5',
        ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed
    in a Kuzmin (infinitely thin) disk

    rho = eps*M/(2*pi*(R**2+eps**2)**(3/2))

    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    rmax = 1
    xx = random1
    xx = np.sqrt((eps / (1 - xx))**2 - eps**2)
    theta = 2. * random2 * np.pi

    x = rmax * xx * np.cos(theta)
    y = rmax * xx * np.sin(theta)
    z = dz * random3 - dz / 2.

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def expd(
        n,
        Hr,
        Hz,
        Rmax,
        Zmax,
        irand=1,
        name='expd.hdf5',
        ftype='swift'):
    """
    Exonential disk

    rho = 1/(1+(r/rc)**2)
    """

    # set random seed
    irand = irand + mpi.mpi_Rank()
    # set the number of particles per procs
    n, ntot = get_local_n(n)

    pos = iclib.exponential_disk(n, Hr, Hz, Rmax, Zmax, irand)
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def miyamoto_nagai(
    n, a, b, Rmax,
    Zmax, irand=1,
    fct=None,
    fRmax=0,
    name='miyamoto.hdf5',
    ftype='swift'):
    """
    Miyamoto Nagai distribution
    """

    # set random seed
    irand = irand + mpi.mpi_Rank()
    # set the number of particles per procs
    n, ntot = get_local_n(n)

    if fct is None:
        pos = iclib.miyamoto_nagai(n, a, b, Rmax, Zmax, irand)
    else:
        pos = iclib.miyamoto_nagai_f(n, a, b, Rmax, Zmax, irand, fct, fRmax)

    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def generic_alpha(
        n,
        a,
        e,
        rmax,
        irand=1,
        fct=None,
        name='generic_alpha.hdf5',
        ftype='swift'):
    """
    Generic alpha distribution : rho ~ (r+e)^a
    """

    # set random seed
    irand = irand + mpi.mpi_Rank()
    # set the number of particles per procs
    n, ntot = get_local_n(n)

    pos = iclib.generic_alpha(n, a, e, rmax, irand)

    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def dl2_mr(r, args):
    """
    Mass in the radius r for the distribution

    rho = (1.-eps*(r/rmax)**2)
    """
    eps = args[0]
    rmax = args[1]
    return ((4. / 3.) * r**3 - (4. / 5.) * eps * r**5 / rmax**2) / \
        (((4. / 3.) - (4. / 5.) * eps) * rmax**3)


def dl2(
    n,
    a,
    b,
    c,
    eps,
    rmax,
    irand=1,
    name='dl2.hdf5',
    ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed as

    rho = (1.-eps*(r/rmax)**2)
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    x = random1
    xm = invert(x, 0, rmax, dl2_mr, [eps, rmax])
    phi = 2 * np.pi * random2

    costh = 1. - 2. * random3
    sinth = np.sqrt(1. - costh**2)
    axm = a * xm * sinth
    bxm = b * xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = c * xm * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def isothm_mr(r, args):
    """
    Mass in the radius r for the distribution

    rho = 1/(1+r/rc)**2
    """
    rc = args[0]
    rm = args[1]

    cte = 2 * rc**3 * np.log(rc) + rc**3

    Mr = r * rc**2 - 2 * rc**3 * np.log(rc + r) - rc**4 / (rc + r) + cte
    Mx = rm * rc**2 - 2 * rc**3 * np.log(rc + rm) - rc**4 / (rc + rm) + cte

    return Mr / Mx


def isothm(
        n,
        rc,
        rmax,
        irand=1,
        name='isothm.hdf5',
        ftype='swift'):
    """
    Return an Nbody object that contains n particles distributed as

    rho = 1/(1+r/rc)**2
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    x = random1
    xm = invert(x, 0, rmax, isothm_mr, [rc, rmax])
    phi = 2 * np.pi * random2

    costh = 1. - 2. * random3
    sinth = np.sqrt(1. - costh**2)
    axm = xm * sinth
    bxm = xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = xm * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def pisothm_mr(r, args):
    """
    Mass in the radius r for the distribution

    rho = 1/(1+(r/rc)**2)
    """
    rc = args[0]
    rmn = args[1]
    rmx = args[2]

    Mr = rc**3 * (r / rc - np.arctan(r / rc))
    Mmn = rc**3 * (rmn / rc - np.arctan(rmn / rc))
    Mmx = rc**3 * (rmx / rc - np.arctan(rmx / rc))

    return (Mr - Mmn) / (Mmx - Mmn)


def pisothm(
        n,
        rc,
        rmax,
        rmin=0,
        irand=1,
        name='pisothm.hdf5',
        ftype='swift'):
    """
    Pseudo-isothermal sphere
    Mass in the radius r for the distribution

    rho = 1/(1+(r/rc)**2)
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    x = random1
    xm = invert(x, rmin, rmax, pisothm_mr, [rc, rmin, rmax])
    phi = 2 * np.pi * random2

    costh = 1. - 2. * random3
    sinth = np.sqrt(1. - costh**2)
    axm = xm * sinth
    bxm = xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = xm * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb


def nfw(
        n,
        rs,
        Rmax,
        dR,
        Rs=None,
        irand=1,
        name='nfw.hdf5',
        ftype='swift',
        verbose=False):
    """
    Return an Nbody object that contains n particles following
    an nfw profile.

    rho = 1/[ (r/rs)(1+r/rs)^2 ]

    """

    def Mr(r, rs):
        return 4 * np.pi * rs**3 * (np.log(1. + r / rs) - r / (rs + r))

    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], rs)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)

    return nb


def hernquist(
        n,
        rs,
        Rmax,
        dR,
        Rs=None,
        irand=1,
        name='hernquist.hdf5',
        ftype='swift',
        verbose=False):
    """
    Return an Nbody object that contains n particles following
    a hernquist modifed profile.

    rho =  1/( (r/rs) * (1+r/rs)**3 )

    """

    def Mr(r, rs):
        return rs**3 * 0.5 * (r / rs)**2 / (1 + r / rs)**2

    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], rs)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)

    return nb


def burkert(
        n,
        rs,
        Rmax,
        dR,
        Rs=None,
        irand=1,
        name='burkert.hdf5',
        ftype='swift',
        verbose=False):
    """
    Return an Nbody object that contains n particles following
    a burkert profile.

    rhob = 1 / ( ( 1 + r/rs  ) * ( 1 + (r/rs)**2  ) )

    """

    def Mr(r, rs):
        return 4 * np.pi * rs**3 * \
            (0.25 * np.log((r / rs)**2 + 1) - 0.5 * np.arctan(r / rs) + 0.5 * np.log((r / rs) + 1))

    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], rs)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)

    return nb


def nfwg(
        n,
        rs,
        gamma,
        Rmax,
        dR,
        Rs=None,
        irand=1,
        name='nfwg.hdf5',
        ftype='swift',
        verbose=False):
    """
    Return an Nbody object that contains n particles following
    an nfw modifed profile.

    rho = 1/[ ((r/rs))**(gamma)(1+r/rs)^2 ]**(0.5*(3-gamma))

    """


    def Mr(r, rs, gamma):
        aa = 1.5 - 0.5 * gamma
        cc = 2.5 - 0.5 * gamma
        z = -r**2 / rs**2
        return 2 * np.pi * (r / rs)**-gamma * r**3 * \
            special.hyp2f1(aa, aa, cc, z) / aa

    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], rs, gamma)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)

    return nb



def gen_2_slopes(
    n,
    rs,
    a,
    b,
    Rmax,
    dR,
    Rcut=None,
    power_cut=None,
    Rs=None,
    NR=1e4,
    irand=1,
    name='gen_2_slopes.hdf5',
    ftype='swift',
    verbose=False):
    """
    Return an Nbody object that contains n particles following
    an generic 2 slope profile.

    rho = 1/( (r/rs)**a * (1+r/rs)**(b-a) )

    Note : this is a re-implementation of generic2c

    """
        
    from scipy.integrate import quad
    from .mass_models import gen_2_slopes

    def exp_cutoff(x, x_cut, speed):
      if x_cut is None or speed is None:
        return 1.
      else:  
        return np.exp( - (x / x_cut)**speed)
      

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:
        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)
        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])


    gen2slopes = gen_2_slopes.GEN2SLOPES(alpha=a,beta=b,rho0=1,rs=rs,G=1)
    gen2slopes.info()
    
    # model density
    fctDensity_gen_2_slopes_cutoff = lambda x:gen2slopes.Density(x)*exp_cutoff(x, Rcut, power_cut)
    fctDensity = fctDensity_gen_2_slopes_cutoff
    fctMr = np.vectorize(lambda x: 4*np.pi *  quad( lambda r: r*r * fctDensity(r)/1 , 0., x)[0]  )
    Mmax = fctMr(Rmax)
    fctMr = np.vectorize(lambda x: 4*np.pi *  quad( lambda r: r*r * fctDensity(r)/Mmax , 0., x)[0]  )    

    if not isinstance(Rs, np.ndarray):      
      R = np.logspace(np.log10(dR),np.log10(Rmax),num=int(NR))   
    
    
    # cumulative mass  
    Mcum = fctMr(R)
    xm = np.interp(random1 ,Mcum ,R) 
    
    phi = random2 * np.pi * 2.
    costh = 1. - 2. * random3

    sinth = np.sqrt(1. - costh**2)
    axm = xm * sinth
    bxm = xm * sinth
    x = axm * np.cos(phi)
    y = bxm * np.sin(phi)
    z = xm * costh

    pos = np.transpose(np.array([x, y, z]))
    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype)

    return nb



def generic2c(
    n,
    rs,
    a,
    b,
    Rmax,
    dR,
    Rs=None,
    irand=1,
    name='nfwg.hdf5',
    ftype='swift',
    verbose=False):
    """
    Return an Nbody object that contains n particles following
    an nfw modifed profile.

    rho = 1/( (r/rs)**a * (1+r/rs)**(b-a) )

    """


    def Mr(r, rs, a, b):
        a = float(a)
        b = float(b)

        aa = b - a
        bb = -a + 3
        cc = 4 - a
        z = -r / rs

        return 4 * np.pi * (r / rs)**(-a) * r**3 * \
            special.hyp2f1(aa, bb, cc, z) / bb

    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], rs, a, b)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)

    return nb



def deprojsersic(
    n,
    re,
    nindex,
    Rmax,
    M,
    dR,
    Rs=None,
    irand=1,
    name='nfwg.hdf5',
    ftype='swift',
    verbose=False):
    """
    Return an Nbody object that contains n particles following
    a 3D deprojected sersic profile.
    """
    
    from pNbody.mass_models import deprojsersic as sersic

    def Mr(r, re, nindex):
      return sersic.CumulativeMass(1, re, nindex, r)


    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i], re, nindex)
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0

    # now use Mr
    nb = generic_Mr(
        n,
        rmax=Rmax,
        R=Rs,
        Mr=Mrs,
        irand=irand,
        name=name,
        ftype=ftype,
        verbose=verbose)
    
    # set proper mass
    nb.mass = nb.mass/nb.mass.sum()*M 

    return nb


def power_spherical(
    n,
    alpha,
    r_c,
    amplitude,
    r_1,
    Rmax,
    dR,
    Rs=None,
    irand=1,
    name='psc.hdf5',
    ftype='swift',
    verbose=False):
    """
    Return an Nbody object that contains n particles following
    a power law with an exponentital cutoff following the density:
        \rho(r) = A (\frac{r_1}{r})^\alpha \exp(- \frac{r^2}{r_c^2})

    alpha  (alpha)     
    r_c    (r_c)        
    A      (amplitude)  
    
    """
    
    from pNbody.mass_models import powerSphericalCutoff as psc

    def Mr(r):
      return psc.CumulativeMass(alpha, r_c, amplitude, r_1, r)
          
    # total mass      
    M = Mr(Rmax)         
          
    if not isinstance(Rs, np.ndarray):
        Rs = np.arange(0, Rmax + dR, dR)		  # should use a non linear grid

    Mrs = np.zeros(len(Rs))
    ntot = len(Rs)

    for i in range(len(Rs)):
        Mrs[i] = Mr(Rs[i])
        if verbose:
            print((Rs[i], Mrs[i], i, '/', ntot))

    # normalisation
    Mrs = Mrs / Mrs[-1]
    Mrs[0] = 0
    
    
    # now use Mr
    nb = generic_Mr(n,rmax=Rmax,R=Rs,Mr=Mrs,irand=irand,name=name,ftype=ftype,verbose=verbose)
        
    # set proper mass
    nb.mass = nb.mass/nb.mass.sum()*M 

    return nb  
  
  



# def generic_MxHyHz(n,xmax,ymax,zmax,x=None,Mx=None,name='box_Mx.hdf5',ftype='swift',verbose=False):
#  """
#  Distribute particles in a box. The density in x is defined in order to reproduce M(x) given by Mx.
#  Here, contrary to generic_Mx, the size of the box is defined.
#  """
#
#  if type(nx) == np.ndarray:
#    random1 = nx
#    random2 = ny
#    random3 = nz
#    n = len(n)
#  else:
#    random1 = np.random.random([nx])
#    random2 = np.random.random([ny])
#    random3 = np.random.random([nz])
#
#  pos = iclib.generic_MxHyHz(n,xmax,ymax,zmax,x.astype(np.float32),Mx.astype(np.float32),random1.astype(np.float32),random2.astype(np.float32),random3.astype(np.float32),verbose)
#
#  vel =  np.ones([n,3])*0.0
#  mass = np.ones([n])*1./n
#
#  nb = Nbody(status='new',p_name=name,pos=pos,vel=vel,mass=mass,ftype=ftype)
#
#  return nb


#################################
# geometric distributions
#################################


def generic_Mx(
        n,
        xmax,
        x=None,
        Mx=None,
        irand=1,
        name='box_Mx.hdf5',
        ftype='swift',
        verbose=False):
    """
    Distribute particles in a box. The density in x is defined in order to reproduce M(x) given by Mx
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    pos = iclib.generic_Mx(
        n,
        xmax,
        x.astype(np.float32),
        Mx.astype(np.float32),
        random1.astype(np.float32),
        random2.astype(np.float32),
        random3.astype(np.float32),
        verbose)

    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype,
        verbose=verbose)

    return nb


def generic_Mr(
        n,
        rmax,
        R=None,
        Mr=None,
        irand=1,
        name='sphere_Mr.hdf5',
        ftype='swift',
        verbose=False):
    """
    Distribute particles in order to reproduce M(R) given by Mr
    """

    if isinstance(n, np.ndarray):
        random1 = n[:, 0]
        random2 = n[:, 1]
        random3 = n[:, 2]
        n = len(n)
        ntot = mpi.mpi_allreduce(n)
    else:

        # set random seed
        np.random.seed(irand + mpi.mpi_Rank())
        # set the number of particles per procs
        n, ntot = get_local_n(n)

        random1 = np.random.random([n])
        random2 = np.random.random([n])
        random3 = np.random.random([n])

    pos = iclib.generic_Mr(
        n,
        rmax,
        R.astype(np.float32),
        Mr.astype(np.float32),
        random1.astype(np.float32),
        random2.astype(np.float32),
        random3.astype(np.float32),
        verbose)

    vel = np.ones([n, 3]) * 0.0
    mass = np.ones([n]) * 1. / ntot

    nb = Nbody(
        status='new',
        p_name=name,
        pos=pos,
        vel=vel,
        mass=mass,
        ftype=ftype,
        verbose=verbose)

    return nb


#################################
# geometric primitives
#################################


def line(M=1., name='line.hdf5', ftype='swift'):

    x = np.array([-0.5, 0.5])
    y = np.array([0, 0])
    z = np.array([0, 0])

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)
    return nb


def square(M=1., name='square.hdf5', ftype='swift'):

    x = np.array([-0.5, +0.5, +0.5, -0.5])
    y = np.array([-0.5, -0.5, +0.5, +0.5])
    z = np.array([0, 0, 0, 0])

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)
    return nb


def circle(n=10, M=1., name='circle.hdf5', ftype='swift'):

    t = np.arange(0, 2 * np.pi, 2 * np.pi / n)

    x = np.cos(t)
    y = np.sin(t)
    z = np.zeros(n)

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)
    return nb


def grid(n=10, m=10, M=1., name='grid.hdf5', ftype='swift'):

    dx = 1 / float(n)
    dy = 1 / float(m)

    xx = np.arange(0, 1 + dx, dx)
    yy = np.arange(0, 1 + dy, dy)

    x = np.zeros(4 * n * m)
    y = np.zeros(4 * n * m)
    z = np.zeros(4 * n * m)

    k = 0
    for i in range(n):
        for j in range(m):
            x[k + 0] = xx[i + 0] - 0.5
            y[k + 0] = yy[j + 0] - 0.5

            x[k + 1] = xx[i + 1] - 0.5
            y[k + 1] = yy[j + 0] - 0.5

            x[k + 2] = xx[i + 1] - 0.5
            y[k + 2] = yy[j + 1] - 0.5

            x[k + 3] = xx[i + 0] - 0.5
            y[k + 3] = yy[j + 1] - 0.5
            k = k + 4

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)
    return nb


def cube(M=1., name='cube.hdf5', ftype='swift'):
    x = np.array([0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1,
               0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, ]) - 0.5
    y = np.array([0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1,
               1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, ]) - 0.5
    z = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
               1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, ]) - 0.5

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)
    return nb


def sphere(n=10, m=10, M=1., name='sphere.hdf5', ftype='swift'):

    pos = np.zeros((2 * n * m, 3), np.float32)

    ts = np.arange(0, 2 * np.pi, 2 * np.pi / n)
    zs = 2 * np.arange(m) / float(m - 1) - 1

    k = 0

    # parallels
    for i in range(m):
        for j in range(n):
            r = np.sin(np.arccos(zs[i]))
            x = r * np.cos(ts[j])
            y = r * np.sin(ts[j])
            z = zs[i]

            pos[k] = [x, y, z]
            k = k + 1

    # meridians
    for j in range(n):
        for i in range(m):
            r = np.sin(np.arccos(zs[i]))
            x = r * np.cos(ts[j])
            y = r * np.sin(ts[j])
            z = zs[i]

            pos[k] = [x, y, z]
            k = k + 1

    nb = Nbody(status='new', pos=pos, p_name=name, ftype=ftype)
    nb.mass = M * nb.mass

    return nb


def arrow(M=1., name='arrow.hdf5', ftype='swift'):

    q = (1 + np.sqrt(5)) / 2.  # golden number

    lx = 1 / q
    x1 = lx / 3.
    x2 = 2 * lx / 3.
    y1 = 1. / q

    x = np.array([x1, x2, x2, lx, 0.5 * lx, 0, x1, x1])
    y = np.array([0, 0, y1, y1, 1, y1, y1, 0])
    z = np.zeros(len(x))

    n = len(x)
    pos = np.transpose((x, y, z))
    mass = M * np.ones(n)
    nb = Nbody(status='new', pos=pos, mass=mass, p_name=name, ftype=ftype)

    nb.translate([-lx / 2, -1, 0])
    nb.rotate(axis='z', angle=np.pi)

    return nb
