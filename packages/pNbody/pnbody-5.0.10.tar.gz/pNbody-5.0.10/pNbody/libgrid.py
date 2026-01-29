#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      libgrid.py
#  brief:     Grid operations
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

##########################################################
# grid functions
##########################################################

import numpy as np
from numpy import clip as numclip
from pNbody import mapping
from . import libutil
import pNbody.treelib
import pNbody.myNumeric as myNumeric
import sys

from . import mpiwrapper as mpi




# definition of indexes and corresponding physical values
# 
# ix   =  int( (x-xmin)/(xmax-xmin)* nx )
# x    = ix*(xmax-xmin)/(nx) + xmin
# 
# center of cell
# 
# xc    = (ix+0.5)*(xmax-xmin)/(nx) + xmin
# 
# physical size of cells
# 
# dx    = ((arange(nx)+1)*(xmax-xmin)/(nx) + xmin )
#       - ((arange(nx)  )*(xmax-xmin)/(nx) + xmin )
# 
#       = (xmax-xmin)/nx * np.ones(nx)
# 
# 
# # linear density of spherical density
# 
# lambda(r) = 4*np.pi*r**2*rho(r)
# 
# 
# 
# 
# here we may deal the following grids :
# 
#   - carthesian 2d
#   - carthesian 3d
# 
#   - cylindrical 2d
#   - cylindrical 3d
# 
#   - spherical	3d
# 
# 
# 
# 
# !!! when computing the potential, in some 1d/2d grid,
# !!! we do not take into account the fact that the model
# !!! may be asymmetric
# !!! We should better compute potential on 3d grid
# !!! and take the mean.
# 
# !!! the cylindrical grid is not symmetric in z



##########################################################################
#
# GENERIC 1D GRID
#
##########################################################################

class Generic_1d_Grid:

    def __init__(self, rmin, rmax, nr, g=None, gm=None):
        """
        f(rmin) = f(rmin)
        f(rmax) = f(rmax)
        """

        self.nr = int(nr)
        self.rmin = float(rmin)
        self.rmax = float(rmax)
        self.g = g
        self.gm = gm
        self.f = lambda r: r  # by default, identity
        self.fm = lambda r: r  # by default, identity

        if self.g is not None and self.gm is not None:
            self.f = lambda r: (self.g(r) - self.g(self.rmin)) / (
                self.g(self.rmax) - self.g(self.rmin)) * (self.rmax - self.rmin) + self.rmin
            self.fm = lambda f: self.gm((f -
                                         self.rmin) *
                                        (self.g(self.rmax) -
                                         self.g(self.rmin)) /
                                        (self.rmax -
                                         self.rmin) +
                                        self.g(self.rmin))

    def get_r(self, offr=0):

        ir = np.arange(self.nr)
        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin

        return self.fm(r)

    def get_Points(self, offr=0):
        """
        Return an array of points corresponding to the nodes of
        a 1d spherical grid

        To get a nt X nr array from the returned vector (pos), do

        x = pos[:,0]
        y = pos[:,0]
        z = pos[:,0]

        x.shape = (nr,NP,nt)
        y.shape = (nr,NP,nt)
        z.shape = (nr,NP,nt)
        """

        ir = np.indices((self.nr,))
        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        r = np.ravel(r)
        r = self.fm(r)

        x = r
        y = np.zeros(len(x))
        z = np.zeros(len(x))

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, r, mass):
        """
        Return an array of points containing mass of particles
        """

        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = mass.astype(np.float32)
        shape = (self.nr,)

        # make the map
        mat = mapping.mkmap1d(pos, mass, val, shape)
        mat = mpi.mpi_allreduce(mat)

        return mat

    def get_GenericMap(self, r, mass, val):
        """
        Return an array of points containing mass of particles
        """

        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        val = val.astype(np.float32)
        mass = mass.astype(np.float32)
        shape = (self.nr,)

        # make the map
        mat = mapping.mkmap1d(pos, mass, val, shape)
        mat = mpi.mpi_allreduce(mat)

        return mat

    def get_MeanMap(self, r, mass, val):
        """
        Return an array of points containing mean of val
        """

        mv = self.get_GenericMap(r, mass, val)
        m = self.get_MassMap(r, mass)

        # compute mean
        mv = np.where(mv == 0, 0, mv)
        m = np.where(m == 0, 1, m)
        mean = mv / m

        return mean, m, mv

    def get_SigmaMap(self, r, mass, val):
        """
        Return an array of points containing sigma of val
        """

        mv = self.get_GenericMap(r, mass, val)
        mv2 = self.get_GenericMap(r, mass, val * val)
        m = self.get_MassMap(r, mass)

        # compute sigma
        mv = np.where(mv == 0, 0, mv)
        mv2 = np.where(mv2 == 0, 0, mv2)
        m = np.where(m == 0, 1, m)
        sigma = mv2 / m - (mv / m)**2
        sigma = np.sqrt(numclip(sigma, 0, 1e10))

        return sigma, m, mv, mv2

    def get_LinearMap(self):
        """
        Return an array of points containing corresponding physical
        size of each cell (usefull to compute linear density)
        """

        r1 = self.get_r(offr=0)
        r2 = self.get_r(offr=1)

        mat = r2 - r1
        mat = mat.astype(np.float32)

        return mat

    def get_LinearDensityMap(self, r, mass):
        """
        Return an array of points containing density in each cell
        """

        m = self.get_MassMap(r, mass)
        v = self.get_LinearMap()

        return m / v


##########################################################################
#
# CYLINDRICAL IRREGULAR 1D GRID
#
##########################################################################


class CylindricalIrregular_1dr_Grid():

  def __init__(self, R, n_per_bin=30,rmode='uniform'):
    """
    R         : 1-D position of the points 
    n_per_bin : number of points per bin   
    
    mode : 'uniform' = randomly choose a radius in the bin
           'mean'    = take the mean of values in the bin    
     
    """
    
    # sort the radius
    self.sidx = R.argsort()
    R = R[self.sidx]
    
    # the magic trick  
    i = np.arange(len(R))
    b = np.fmod(i,n_per_bin)
    
    # a vector that contains the bin indice for each particles
    self.d = (-(b-i)/n_per_bin).astype(int)
    
    # the number of bins
    self.nbins = int(np.ceil(len(i)/n_per_bin))
    
    # make r global
    self.R = R 
    
    # position of the bins
    self.compute_R(mode=rmode)
            

    
  def compute_R(self,mode='center'):
    '''
    mode : 'uniform'  = randomly choose a radius in the bin
           'mean'     = take the mean of values in the bin
           'center'   = take the center of the bin
    '''
    
    Rcs  = np.zeros(self.nbins)
    Rls  = np.zeros(self.nbins)    # left  boundary
    Rrs  = np.zeros(self.nbins)    # right boundary    
    Rmns = np.zeros(self.nbins)
    Rmxs = np.zeros(self.nbins)    

    # area
    As   = np.zeros(self.nbins)


    for i in range(self.nbins):
      
      # keep only values in the bin
      Ri = self.compress(i,self.R)
            
      Rmns[i] = min(Ri) 
      Rmxs[i] = max(Ri) 
      
      if i==0:
        Rls[0] = 0
      else:
        Rrs[i-1]  = 0.5*(Rmxs[i-1]+Rmns[i])
        Rls[i]    = Rrs[i-1]      
          
    
      if mode=='center':
        Rcs[i]     = Ri.mean()
        if i>0:
          Rcs[i-1]     = 0.5*(Rls[i-1] + Rrs[i-1])    
      elif mode=='uniform':
        Rcs[i]     = np.random.uniform(min(Ri),max(Ri))
      elif mode=='mean':
        Rcs[i]     = Ri.mean()    
        
    # last bin
    Rrs[self.nbins-1] = Rcs[self.nbins-1] + (Rcs[self.nbins-1]-Rls[self.nbins-1])
    
    
    # compute the surface
    As = np.pi * (Rrs**2 - Rls**2)
    
    # make global    
    self.Rcs = Rcs    
    #self.Rrs = Rrs
    #self.Rls = Rls
    self.As  = As
 
  def compress(self,i,val):   
    '''
    return only values in a bin
    '''
    c = self.d==i
    return np.compress(c,val)   
    
    
  def get_R(self):

    return self.Rcs
        
  def get_Area(self):

    return self.As    
    


  def get_Sum(self,val):
    
    # sort the value
    val = val[self.sidx]

    s = np.zeros(self.nbins)
    for i in range(self.nbins):
      vali = self.compress(i,val)                  
      s[i]   = vali.sum()
    
    return s
    
    
  def get_IntegratedSum(self,val):
    
    s = self.get_Sum(val)
    return np.add.accumulate(s)
    
    
  def get_Mean(self,val):
    
    # sort the value
    val = val[self.sidx]

    s = np.zeros(self.nbins)
    for i in range(self.nbins):
      vali = self.compress(i,val)                
      s[i]   = vali.mean()
    
    return s    


  def get_Std(self,val):
    
    # sort the value
    val = val[self.sidx]

    s = np.zeros(self.nbins)
    for i in range(self.nbins):
      vali = self.compress(i,val)                
      s[i]   = vali.std()

    return s  
  
  def get_MeanAndStd(self,val):
    
    # sort the value
    val = val[self.sidx]

    mean = np.zeros(self.nbins)
    std  = np.zeros(self.nbins)
    for i in range(self.nbins):
      vali = self.compress(i,val)                
      mean[i]   = vali.mean()
      std[i]    = vali.std()
    
    return mean,std


  def get_SurfaceDensity(self,val):
    return self.get_Sum(val)/self.get_Area()





##########################################################################
#
# SPHERICAL 1D GRID
#
##########################################################################

class Spherical_1d_Grid:

    def __init__(self, rmin, rmax, nr, g=None, gm=None):
        """
        f(rmin) = f(rmin)
        f(rmax) = f(rmax)
        """

        self.nr = int(nr)
        self.rmin = float(rmin)
        self.rmax = float(rmax)
        self.g = g
        self.gm = gm
        self.f = lambda r: r  # by default, identity
        self.fm = lambda r: r  # by default, identity

        if self.g is not None and self.gm is not None:
            self.f = lambda r: (self.g(r) - self.g(self.rmin)) / (
                self.g(self.rmax) - self.g(self.rmin)) * (self.rmax - self.rmin) + self.rmin
            self.fm = lambda f: self.gm((f -
                                         self.rmin) *
                                        (self.g(self.rmax) -
                                         self.g(self.rmin)) /
                                        (self.rmax -
                                         self.rmin) +
                                        self.g(self.rmin))

    def get_r(self, offr=0):

        ir = np.arange(self.nr)
        #r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        r = (ir + offr) * (self.rmax - self.rmin) / (self.nr-1) + self.rmin

        return self.fm(r)

    def get_Points(self, offr=0):
        """
        Return an array of points corresponding to the nodes of
        a 1d spherical grid

        To get a nt X nr array from the returned vector (pos), do

        x = pos[:,0]
        y = pos[:,0]
        z = pos[:,0]

        x.shape = (nr,NP,nt)
        y.shape = (nr,NP,nt)
        z.shape = (nr,NP,nt)
        """

        ir = np.indices((self.nr,))
        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        r = np.ravel(r)
        r = self.fm(r)

        x = r
        y = np.zeros(len(x))
        z = np.zeros(len(x))

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, nb):
        """
        Return an array of points containing mass of particles
        """

        r = nb.rxyz()
        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        shape = (self.nr,)

        # make the map
        mat = mapping.mkmap1d(pos, mass, val, shape)

        return mat

    def get_NumberMap(self, nb):
        """
        Return an array of points containing number of particles
        """

        r = nb.rxyz()
        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nr,)

        # make the map
        mat = mapping.mkmap1d(pos, mass, val, shape)

        return mat

    def get_ValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing val of particles
        """

        r = nb.rxyz()
        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr,)

        # make the map
        mat = mapping.mkmap1d(pos, mass, val, shape)

        return mat

    def get_MeanValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing mean val of particles
        """

        r = nb.rxyz()
        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr,)

        # compute zero momentum
        m0 = mapping.mkmap1d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap1d(pos, mass, val, shape)

        return libutil.GetMeanMap(m0, m1)

    def get_SigmaValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing sigma val of particles
        """

        r = nb.rxyz()
        r = self.f(r)

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin)

        # compute values
        pos = np.transpose(np.array(r)).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr,)

        # compute zero momentum
        m0 = mapping.mkmap1d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap1d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap1d(pos, mass, val * val, shape)

        return libutil.GetSigmaMap(m0, m1, m2)

    def get_PotentialMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing potential
        """

        if AdaptativeSoftenning:

            print("AdaptativeSoftenning not defined !")
            sys.exit()

        else:
            pos = self.get_Points()

            if UseTree:
                pot = nb.TreePot(pos, eps)
            else:
                pot = nb.Pot(pos, eps)

        # transform back into array
        pot.shape = (self.nr,)

        return pot

    def get_SurfaceMap(self):
        """
        Return an array of points containing surface (volume)
        of each cell.
        """

        r1 = self.get_r(offr=0)
        r2 = self.get_r(offr=1)

        mat = r2 - r1
        mat = mat.astype(np.float32)

        return mat

    def get_VolumeMap(self):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        r1 = self.get_r(offr=0)
        r2 = self.get_r(offr=1)

        mat = 4.0 / 3.0 * np.pi * ((r2)**3 - (r1)**3)
        mat = mat.astype(np.float32)

        return mat

    def get_DensityMap(self, nb):
        """
        Return an array of points containing density in each cell
        """

        m = self.get_MassMap(nb)
        v = self.get_VolumeMap()

        return m / v

    def get_LinearDensityMap(self, nb):
        """
        Return an array of points containing the linear density in each cell
        """

        m = self.get_MassMap(nb)
        s = self.get_SurfaceMap()

        return m / s

    def get_AccumulatedMassMap(self, nb):
        """
        Return an array of points containing M(r) in each cell
        """

        m = self.get_MassMap(nb)
        mr = get_Accumulation_Along_Axis(m, axis=0)

        return mr

    def get_Interpolation(self, pos, mat, offr=0):
        """
        Interpolates continuous value of pos, using matrix mat
        """

        r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2 + pos[:, 2]**2)
        r = self.f(r)

        ir = (r - self.rmin) / (self.rmax - self.rmin) * self.nr - offr

        return myNumeric.Interpolate_From_1d_Array(
            ir.astype(np.float32), mat.astype(np.float32))

    def get_AccelerationMap(self, nb, eps, UseTree=True, Tree=None):
        """
        Return an array of points containing accelerations
        """

        pos = self.get_Points()

        if UseTree:
            acc = nb.TreeAccel(pos, eps)
        else:
            acc = nb.Accel(pos, eps)

        accx = np.copy(acc[:, 0])
        accy = np.copy(acc[:, 1])
        accz = np.copy(acc[:, 2])

        # transform back into array
        accx.shape = (self.nr,)
        accy.shape = (self.nr,)
        accz.shape = (self.nr,)

        return accx, accy, accz


##########################################################################
#
# CYLINDRICAL 2D GRID (r-z)
#
##########################################################################

class Cylindrical_2drz_Grid:

    def __init__(self, rmin, rmax, nr, zmin, zmax, nz, g=None, gm=None):
        """
        f(rmin) = f(rmin)
        f(rmax) = f(rmax)
        """

        self.nr = int(nr)
        self.rmin = float(rmin)
        self.rmax = float(rmax)

        self.nz = int(nz)
        self.zmin = float(zmin)
        self.zmax = float(zmax)

        self.g = g
        self.gm = gm
        self.f = lambda r: r  # by default, identity
        self.fm = lambda r: r  # by default, identity

        if self.g is not None and self.gm is not None:
            self.f = lambda r: (self.g(r) - self.g(self.rmin)) / (
                self.g(self.rmax) - self.g(self.rmin)) * (self.rmax - self.rmin) + self.rmin
            self.fm = lambda f: self.gm((f -
                                         self.rmin) *
                                        (self.g(self.rmax) -
                                         self.g(self.rmin)) /
                                        (self.rmax -
                                         self.rmin) +
                                        self.g(self.rmin))

    def get_rz(self, offr=0, offz=0):

        ir = np.arange(self.nr)
        iz = np.arange(self.nz)
        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        z = (iz + offz) * (self.zmax - self.zmin) / self.nz + self.zmin

        r = self.fm(r)

        return r, z

    def get_Points(self, offr=0, offz=0):
        """
        Return an array of points corresponding to the nodes of
        a 2d cylindrical grid

        To get a nt X nr array from the returned vector (pos), do

        x = np.copy(pos[:,0])
        y = np.copy(pos[:,1])
        z = np.copy(pos[:,2])

        x.shape = (nr,nt)
        y.shape = (nr,nt)
        z.shape = (nr,nt)

        # to get r and theta
        r = np.sqrt(x**2+y**2+z**2)
        t = arctan2(y,x)*180/np.pi

        """

        ir, iz = np.indices((self.nr, self.nz))

        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        z = (iz + offz) * (self.zmax - self.zmin) / self.nz + self.zmin

        r = np.ravel(r)
        z = np.ravel(z)

        r = self.fm(r)

        x = r
        y = np.zeros(len(x))
        z = z

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, nb, offr=0, offz=0):
        """
        Return an array of points containing mass of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([r, z, t])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        shape = (self.nr, self.nz)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_NumberMap(self, nb, offr=0, offz=0):
        """
        Return an array of points containing mass of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([r, z, t])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nr, self.nz)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_PotentialMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing potential
        """

        if AdaptativeSoftenning:

            pos = self.get_Points()
            pot = np.zeros(len(pos), float)

            # define eps
            R1, z1 = self.get_rz(offr=0)
            R2, z2 = self.get_rz(offr=1)
            epss = R2 - R1
            epss = epss / epss[0] * eps

            pos = self.get_Points()

            for ir in range(self.nr):
                for iz in range(self.nz):
                    # print ir*self.nz + iz, pos[ir*self.nz + iz], epss[ir]

                    if UseTree:
                        pot[ir * self.nz + \
                            iz] = nb.TreePot(np.array([pos[ir * self.nz + iz]]), epss[ir])
                    else:
                        pot[ir * self.nz +
                            iz] = nb.Pot(np.array([pos[ir * self.nz + iz]]), epss[ir])

        else:
            pos = self.get_Points()

            if UseTree:
                pot = nb.TreePot(pos, eps)
            else:
                pot = nb.Pot(pos, eps)

        # transform back into array
        pot.shape = (self.nr, self.nz)

        return pot

    def get_AccelerationMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing accelerations
        """

        if AdaptativeSoftenning:

            pos = self.get_Points()
            acc = pos * 0

            # define eps
            R1, z1 = self.get_rz(offr=0)
            R2, z2 = self.get_rz(offr=1)
            epss = R2 - R1
            epss = epss / epss[0] * eps

            pos = self.get_Points()

            for ir in range(self.nr):
                for iz in range(self.nz):
                    # print ir*self.nz + iz, pos[ir*self.nz + iz], epss[ir]

                    if UseTree:
                        acc[ir *
                            self.nz +
                            iz] = nb.TreeAccel(np.array([pos[ir *
                                                          self.nz +
                                                          iz]]), epss[ir])
                    else:
                        acc[ir * self.nz +
                            iz] = nb.Accel(np.array([pos[ir * self.nz + iz]]), epss[ir])

        else:
            pos = self.get_Points()

            if UseTree:
                acc = nb.TreeAccel(pos, eps)
            else:
                acc = nb.Accel(pos, eps)

        accx = np.copy(acc[:, 0])
        accy = np.copy(acc[:, 1])
        accz = np.copy(acc[:, 2])

        # transform back into array
        accx.shape = (self.nr, self.nz)
        accy.shape = (self.nr, self.nz)
        accz.shape = (self.nr, self.nz)

        return accx, accy, accz

    def get_VolumeMap(self, offr=0, offz=0):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        rs, zs = self.get_rz(offr, offz)

        def volume(ir, iz):
            if ir == self.nr - 1:
                r1 = rs[ir - 1]		# un peu bricolage...
                r2 = rs[ir]
            else:
                r1 = rs[ir]
                r2 = rs[ir + 1]

            if iz == self.nz - 1:
                z1 = zs[iz - 1]		# un peu bricolage...
                z2 = zs[iz]
            else:
                z1 = zs[iz]
                z2 = zs[iz + 1]

            return np.pi * (r2**2 - r1**2) * (z2 - z1)

        # make the map
        mat = np.zeros((self.nr, self.nz))
        for ir in range(self.nr):
            for iz in range(self.nz):
                mat[ir, iz] = volume(ir, iz)
        mat = mat.astype(np.float32)

        return mat

    def get_SurfaceMap(self, offr=0, offz=0):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        rs, zs = self.get_rz(offr, offz)

        def surface(ir):
            if ir == self.nr - 1:
                r1 = rs[ir - 1]		# un peu bricolage...
                r2 = rs[ir]
            else:
                r1 = rs[ir]
                r2 = rs[ir + 1]

            return np.pi * (r2**2 - r1**2)

        # make the map
        mat = np.zeros(self.nr)
        for ir in range(self.nr):
            mat[ir] = surface(ir)
        mat = mat.astype(np.float32)

        return mat

    def get_DensityMap(self, nb, offr=0, offz=0):
        """
        Return an array of points containing density in each cell
        """

        m = self.get_MassMap(nb, offr=offr, offz=offz)
        v = self.get_VolumeMap(offr=offr, offz=offz)

        return m / v

    def get_SurfaceDensityMap(self, nb, offr=0, offz=0):
        """
        Return an array (1d) of points containing the surface density along r
        """

        m = self.get_MassMap(nb, offr=offr, offz=offz)
        m = get_Sum_Along_Axis(m)
        s = self.get_SurfaceMap(offr=offr, offz=offz)
        return m / s

    def get_Interpolation(self, pos, mat, offr=0, offz=0):
        """
        Interpolates continuous value of pos, using matrix mat
        """

        r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)
        r = self.f(r)

        z = pos[:, 2]

        ir = (r - self.rmin) / (self.rmax - self.rmin) * self.nr - offr
        iz = (z - self.zmin) / (self.zmax - self.zmin) * self.nz - offz

        return myNumeric.Interpolate_From_2d_Array(
            ir.astype(np.float32), iz.astype(np.float32), mat.astype(np.float32))

    def get_r_Interpolation(self, pos, mat, offr=0):
        """
        Interpolates continuous value of pos, using matrix mat
        only along first axis.
        """

        r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)
        r = self.f(r)

        ir = (r - self.rmin) / (self.rmax - self.rmin) * self.nr - offr

        return myNumeric.Interpolate_From_1d_Array(
            ir.astype(np.float32), mat.astype(np.float32))


##########################################################################
#
# CYLINDRICAL 2D GRID (r-t)
#
##########################################################################

class Cylindrical_2drt_Grid:

    def __init__(self, rmin, rmax, nr, nt, z=0, g=None, gm=None):
        """
        f(rmin) = f(rmin)
        f(rmax) = f(rmax)
        """

        tmin = 0
        tmax = 2 * np.pi
        self.z = z

        self.nr = int(nr)
        self.rmin = float(rmin)
        self.rmax = float(rmax)

        self.nt = int(nt)
        self.tmin = float(tmin)
        self.tmax = float(tmax)

        self.g = g
        self.gm = gm
        self.f = lambda r: r  # by default, identity
        self.fm = lambda r: r  # by default, identity

        if self.g is not None and self.gm is not None:
            self.f = lambda r: (self.g(r) - self.g(self.rmin)) / (
                self.g(self.rmax) - self.g(self.rmin)) * (self.rmax - self.rmin) + self.rmin
            self.fm = lambda f: self.gm((f -
                                         self.rmin) *
                                        (self.g(self.rmax) -
                                         self.g(self.rmin)) /
                                        (self.rmax -
                                         self.rmin) +
                                        self.g(self.rmin))

    def get_rt(self, offr=0, offt=0):

        ir = np.arange(self.nr)
        it = np.arange(self.nt)

        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        t = (it + offt) * (self.tmax - self.tmin) / self.nt + self.tmin

        r = self.fm(r)

        return r, t

    def get_xyz(self, offr=0, offt=0):
        """
        Return arrays corresponding to the coordonates nodes of
        a 2d cylindrical grid
        """

        ir, it = np.indices((self.nr, self.nt))

        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        t = (it + offt) * (self.tmax - self.tmin) / self.nt + self.tmin

        r = self.fm(r)

        x = r * np.cos(t)
        y = r * np.sin(t)
        z = np.ones((self.nr, self.nt)) * self.z

        return x, y, z

    def get_Points(self, offr=0, offt=0):
        """
        Return an array of points corresponding to the nodes of
        a 2d cylindrical grid

        To get a nt X nr array from the returned vector (pos), do

        x = np.copy(pos[:,0])
        y = np.copy(pos[:,1])
        z = np.copy(pos[:,2])

        x.shape = (nr,nt)
        y.shape = (nr,nt)
        z.shape = (nr,nt)

        # to get r and theta
        r = np.sqrt(x**2+y**2+z**2)
        t = arctan2(y,x)*180/np.pi

        """

        ir, it = np.indices((self.nr, self.nt))

        r = (ir + offr) * (self.rmax - self.rmin) / self.nr + self.rmin
        t = (it + offt) * (self.tmax - self.tmin) / self.nt + self.tmin

        r = np.ravel(r)
        t = np.ravel(t)

        r = self.fm(r)

        x = r * np.cos(t)
        y = r * np.sin(t)
        z = np.ones(len(x)) * self.z

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, nb, offr=0, offt=0):
        """
        Return an array of points containing mass of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        t = (t - self.tmin) / (self.tmax - self.tmin) - offt / self.nt

        # compute values
        pos = np.transpose(np.array([r, t, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        shape = (self.nr, self.nt)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_NumberMap(self, nb, offr=0, offt=0):
        """
        Return an array of points containing mass of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        t = (t - self.tmin) / (self.tmax - self.tmin) - offt / self.nt

        # compute values
        pos = np.transpose(np.array([r, t, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nr, self.nt)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_ValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing val of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        t = (t - self.tmin) / (self.tmax - self.tmin) - offt / self.nt

        # compute values
        pos = np.transpose(np.array([r, t, z])).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr, self.nt)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_MeanValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing mean val of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        t = (t - self.tmin) / (self.tmax - self.tmin) - offt / self.nt

        # compute values
        pos = np.transpose(np.array([r, t, z])).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr, self.nt)

        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)

        return libutil.GetMeanMap(m0, m1)

    def get_SigmaValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array of points containing sigma val of particles
        """

        r = nb.rxy()
        r = self.f(r)

        t = nb.phi_xy() + np.pi
        z = nb.pos[:, 2]

        # scale between 0 and 1
        r = (r - self.rmin) / (self.rmax - self.rmin) - offr / self.nr
        t = (t - self.tmin) / (self.tmax - self.tmin) - offt / self.nt

        # compute values
        pos = np.transpose(np.array([r, t, z])).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        val = val.astype(np.float32)
        shape = (self.nr, self.nt)

        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap2d(pos, mass, val * val, shape)

        return libutil.GetSigmaMap(m0, m1, m2)

    def get_PotentialMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing potential
        """

        if AdaptativeSoftenning:

            pos = self.get_Points()
            pot = np.zeros(len(pos), float)

            # define eps
            R1, t1 = self.get_rt(offr=0)
            R2, t2 = self.get_rt(offr=1)
            epss = R2 - R1
            epss = epss / epss[0] * eps

            pos = self.get_Points()

            for ir in range(self.nr):
                for it in range(self.nt):
                    # print ir*self.nt + it, pos[ir*self.nt + it], epss[ir]
                    if UseTree:
                        pot[ir * self.nt + \
                            it] = nb.TreePot(np.array([pos[ir * self.nt + it]]), epss[ir])
                    else:
                        pot[ir * self.nt +
                            it] = nb.Pot(np.array([pos[ir * self.nt + it]]), epss[ir])

        else:
            pos = self.get_Points()

            if UseTree:
                pot = nb.TreePot(pos, eps)
            else:
                pot = nb.Pot(pos, eps)

        # transform back into array
        pot.shape = (self.nr, self.nt)

        return pot

    def get_AccelerationMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing accelerations
        """

        if AdaptativeSoftenning:

            pos = self.get_Points()
            acc = pos * 0

            # define eps
            R1, t1 = self.get_rt(offr=0)
            R2, t2 = self.get_rt(offr=1)
            epss = R2 - R1
            epss = epss / epss[0] * eps

            pos = self.get_Points()

            for ir in range(self.nr):
                for it in range(self.nt):
                    # print ir*self.nt + it, pos[ir*self.nt + it], epss[ir]
                    if UseTree:
                        acc[ir *
                            self.nt +
                            it] = nb.TreeAccel(np.array([pos[ir *
                                                          self.nt +
                                                          it]]), epss[ir])
                    else:
                        acc[ir * self.nt + \
                            it] = nb.Accel(np.array([pos[ir * self.nt + it]]), epss[ir])

        else:

            pos = self.get_Points()

            if UseTree:
                acc = nb.TreeAccel(pos, eps)
            else:
                acc = nb.Accel(pos, eps)

        accx = np.copy(acc[:, 0])
        accy = np.copy(acc[:, 1])
        accz = np.copy(acc[:, 2])

        # transform back into array
        accx.shape = (self.nr, self.nt)
        accy.shape = (self.nr, self.nt)
        accz.shape = (self.nr, self.nt)

        return accx, accy, accz

    def get_SurfaceMap(self, nb, offr=0, offt=0):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        rs, ts = self.get_rt(offr, offt)

        def surface(ir):
            if ir == self.nr - 1:
                r1 = rs[ir - 1]		# un peu bricolage...
                r2 = rs[ir]
            else:
                r1 = rs[ir]
                r2 = rs[ir + 1]

            return np.pi * (r2**2 - r1**2) / self.nt

        # make the map
        mat = np.zeros(self.nr)
        for ir in range(self.nr):
            mat[ir] = surface(ir)
        mat = mat.astype(np.float32)

        mat = np.transpose(np.ones((self.nt, self.nr)) * mat)

        return mat

    def get_SurfaceValMap(self, nb, val, offr=0, offt=0):
        """
        Return an array (1d) of points containing the surface density along r
        """

        m = self.get_ValMap(nb, val, offr=0, offt=0)
        s = self.get_SurfaceMap(nb, offr=0, offt=0)

        return m / s

    def get_SurfaceDensityMap(self, nb, offr=0, offt=0):
        """
        Return an array of points containing density in each cell
        """

        m = self.get_MassMap(nb, offr=0, offt=0)
        s = self.get_SurfaceMap(nb, offr=0, offt=0)

        return m / s

    def get_ReducedSurfaceDensityMap(self, nb, offr=0, offt=0):
        """
        Return an array of points containing density in each cell
        """

        m = self.get_MassMap(nb, offr=0, offt=0)
        m = np.sum(m, axis=1)
        s = self.get_SurfaceMap(nb, offr=0, offt=0)
        s = np.sum(s, axis=1)

        return m / s

    def get_r_Interpolation(self, pos, mat, offr=0):
        """
        Interpolates continuous value of pos, using matrix mat
        only along first axis.
        """

        r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)
        r = self.f(r)

        ir = (r - self.rmin) / (self.rmax - self.rmin) * self.nr - offr

        return myNumeric.Interpolate_From_1d_Array(
            ir.astype(np.float32), mat.astype(np.float32))


##########################################################################
#
# CARTHESIAN 2D GRID (x-y)
#
##########################################################################

class Carthesian_2dxy_Grid:

    def __init__(self, xmin, xmax, nx, ymin, ymax, ny, z=0, g=None, gm=None):
        """

        """

        self.nx = int(nx)
        self.xmin = float(xmin)
        self.xmax = float(xmax)

        self.ny = int(ny)
        self.ymin = float(ymin)
        self.ymax = float(ymax)

        self.z = z

        #self.g    = g
        #self.gm   = gm
        # self.f    = lambda r:r	# by default, identity
        # self.fm   = lambda r:r	# by default, identity

        # if self.g != None and self.gm != None:
        #  self.f  = lambda x: ( self.g(x)-self.g(self.xmin) )/( self.g(self.xmax)-self.g(self.xmin) ) *(self.xmax-self.xmin) + self.xmin
        #  self.fm = lambda f: self.gm( (f-self.xmin)*( self.g(self.xmax)-self.g(self.xmin) )/( self.xmax-self.xmin ) + self.g(self.xmin) )

    def get_xy(self, offx=0, offy=0):

        ix = np.arange(self.nx)
        iy = np.arange(self.ny)

        x = (ix + offx) * (self.xmax - self.xmin) / self.nx + self.xmin
        y = (iy + offy) * (self.ymax - self.ymin) / self.ny + self.ymin

        #x = self.fm(x)

        return x, y

    def get_Points(self, offx=0, offy=0):
        """
        Return an array of points corresponding to the nodes of
        a 2d cylindrical grid

        To get a nt X nr array from the returned vector (pos), do

        x = np.copy(pos[:,0])
        y = np.copy(pos[:,1])
        z = np.copy(pos[:,2])

        x.shape = (nr,nt)
        y.shape = (nr,nt)
        z.shape = (nr,nt)

        # to get r and theta
        r = np.sqrt(x**2+y**2+z**2)
        t = arctan2(y,x)*180/np.pi

        """

        ix, iy = np.indices((self.nx, self.ny))

        x = (ix + offx) * (self.xmax - self.xmin) / self.nx + self.xmin
        y = (iy + offy) * (self.ymax - self.ymin) / self.ny + self.ymin
        z = np.ones(len(x) * len(y)) * self.z

        x = np.ravel(x)
        y = np.ravel(y)
        z = np.ravel(z)

        #x = self.fm(x)

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, nb, offx=0, offy=0):
        """
        Return an array of points containing mass of particles
        """

        x = nb.x()
        y = nb.y()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = np.zeros(len(x))

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        shape = (self.nx, self.ny)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_NumberMap(self, nb, offx=0, offy=0):
        """
        Return an array of points containing mass of particles
        """

        x = nb.x()
        y = nb.y()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = np.zeros(len(x))

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_PotentialMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing potential
        """
        print("not implemented")
        return

    def get_AccelerationMap(self, nb, eps, UseTree=True, Tree=None):
        """
        Return an array of points containing accelerations
        """
        print("not implemented")
        return

    def get_SurfaceMap(self, offx=0, offy=0):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        """
    # the following lines may be used if the grid is non linear

    xs,ys,zs = self.get_xyz(offx,offy,offz)
    def volume(ix,iy,iz):
      if ix==self.nx-1:
        x1 = xs[ix-1]		# un peu bricolage...
        x2 = xs[ix]
      else:
        x1 = xs[ix]
        x2 = xs[ix+1]

      if iy==self.ny-1:
        y1 = ys[iy-1]		# un peu bricolage...
        y2 = ys[iy]
      else:
        y1 = ys[iy]
        y2 = ys[iy+1]

      if iz==self.nz-1:
        z1 = zs[iz-1]		# un peu bricolage...
        z2 = zs[iz]
      else:
        z1 = zs[iz]
        z2 = zs[iz+1]

      return (x2-x1) * (y2-y1) * (z2-z1)

    # make the map
    mat = np.zeros((self.nx,self.ny,self.nz))
    for ix in range(self.nx):
      for iy in range(self.ny):
        for iz in range(self.nz):
          mat[ix,iy,iz]=volume(ix,iy,iz)
    mat = mat.astype(np.float32)
    """

        # compute volume (surface)
        dx = (self.xmax - self.xmin) / self.nx
        dy = (self.ymax - self.ymin) / self.ny
        s = dx * dy

        # make the map
        mat = np.ones((self.nx, self.ny)) * s
        mat = mat.astype(np.float32)

        return mat

    def get_ValMap(self, nb, val, offx=0, offy=0):
        """
        Return an array of points containing val of particles
        """

        x = nb.x()
        y = nb.y()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = np.zeros(len(x))

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny)

        # make the map
        mat = mapping.mkmap2d(pos, mass, val, shape)

        return mat

    def get_MeanValMap(self, nb, val, offx=0, offy=0):
        """
        Return an array of points containing mean val of particles
        """

        x = nb.x()
        y = nb.y()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = np.zeros(len(x))

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny)

        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)

        return libutil.GetMeanMap(m0, m1)

    def get_SigmaValMap(self, nb, val, offx=0, offy=0):
        """
        Return an array of points containing sigma val of particles
        """

        x = nb.x()
        y = nb.y()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = np.zeros(len(x))

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny)

        # compute zero momentum
        m0 = mapping.mkmap2d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap2d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap2d(pos, mass, val * val, shape)

        return libutil.GetSigmaMap(m0, m1, m2)

    def get_SurfaceDensityMap(self, nb, offx=0, offy=0):
        """
        Return an array of points containing density in each cell
        """
        m = self.get_MassMap(nb, offx=0, offy=0)
        s = self.get_SurfaceMap(offx=0, offy=0)

        return m / s


##########################################################################
#
# CARTHESIAN 3D GRID (x-y-z)
#
##########################################################################

class Carthesian_3dxyz_Grid:

    def __init__(
            self,
            xmin,
            xmax,
            nx,
            ymin,
            ymax,
            ny,
            zmin,
            zmax,
            nz,
            g=None,
            gm=None):
        """

        """

        self.nx = int(nx)
        self.xmin = float(xmin)
        self.xmax = float(xmax)

        self.ny = int(ny)
        self.ymin = float(ymin)
        self.ymax = float(ymax)

        self.nz = int(nz)
        self.zmin = float(zmin)
        self.zmax = float(zmax)

        #self.g    = g
        #self.gm   = gm
        # self.f    = lambda r:r	# by default, identity
        # self.fm   = lambda r:r	# by default, identity

        # if self.g != None and self.gm != None:
        #  self.f  = lambda x: ( self.g(x)-self.g(self.xmin) )/( self.g(self.xmax)-self.g(self.xmin) ) *(self.xmax-self.xmin) + self.xmin
        #  self.fm = lambda f: self.gm( (f-self.xmin)*( self.g(self.xmax)-self.g(self.xmin) )/( self.xmax-self.xmin ) + self.g(self.xmin) )

    def get_xyz(self, offx=0, offy=0, offz=0):

        ix = np.arange(self.nx)
        iy = np.arange(self.ny)
        iz = np.arange(self.nz)

        x = (ix + offx) * (self.xmax - self.xmin) / self.nx + self.xmin
        y = (iy + offy) * (self.ymax - self.ymin) / self.ny + self.ymin
        z = (iz + offz) * (self.zmax - self.zmin) / self.nz + self.zmin

        #x = self.fm(x)

        return x, y, z

    def get_Points(self, offx=0, offy=0, offz=0):
        """
        Return an array of points corresponding to the nodes of
        a 2d cylindrical grid

        To get a nt X nr array from the returned vector (pos), do

        x = np.copy(pos[:,0])
        y = np.copy(pos[:,1])
        z = np.copy(pos[:,2])

        x.shape = (nr,nt)
        y.shape = (nr,nt)
        z.shape = (nr,nt)

        # to get r and theta
        r = np.sqrt(x**2+y**2+z**2)
        t = arctan2(y,x)*180/np.pi

        """

        ix, iy, iz = np.indices((self.nx, self.ny, self.nz))

        x = (ix + offx) * (self.xmax - self.xmin) / self.nx + self.xmin
        y = (iy + offy) * (self.ymax - self.ymin) / self.ny + self.ymin
        z = (iz + offz) * (self.zmax - self.zmin) / self.nz + self.zmin

        x = np.ravel(x)
        y = np.ravel(y)
        z = np.ravel(z)

        #x = self.fm(x)

        return np.transpose(np.array([x, y, z])).astype(np.float32)

    def get_MassMap(self, nb, offx=0, offy=0, offz=0):
        """
        Return an array of points containing mass of particles
        """

        x = nb.x()
        y = nb.y()
        z = nb.z()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = nb.mass.astype(np.float32)
        shape = (self.nx, self.ny, self.nz)

        # make the map
        mat = mapping.mkmap3d(pos, mass, val, shape)

        return mat

    def get_NumberMap(self, nb, offx=0, offy=0, offz=0):
        """
        Return an array of points containing mass of particles
        """

        x = nb.x()
        y = nb.y()
        z = nb.z()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        val = np.ones(pos.shape).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny, self.nz)

        # make the map
        mat = mapping.mkmap3d(pos, mass, val, shape)

        return mat

    def get_PotentialMap(
            self,
            nb,
            eps,
            UseTree=True,
            Tree=None,
            AdaptativeSoftenning=False):
        """
        Return an array of points containing potential
        """
        print("not implemented")
        return

    def get_AccelerationMap(self, nb, eps, UseTree=True, Tree=None):
        """
        Return an array of points containing accelerations
        """
        print("not implemented")
        return

    def get_VolumeMap(self, offx=0, offy=0, offz=0):
        """
        Return an array of points containing corresponding physical
        volumes of each cell (usefull to compute density)
        """

        """
    # the following lines may be used if the grid is non linear

    xs,ys,zs = self.get_xyz(offx,offy,offz)
    def volume(ix,iy,iz):
      if ix==self.nx-1:
        x1 = xs[ix-1]		# un peu bricolage...
        x2 = xs[ix]
      else:
        x1 = xs[ix]
        x2 = xs[ix+1]

      if iy==self.ny-1:
        y1 = ys[iy-1]		# un peu bricolage...
        y2 = ys[iy]
      else:
        y1 = ys[iy]
        y2 = ys[iy+1]

      if iz==self.nz-1:
        z1 = zs[iz-1]		# un peu bricolage...
        z2 = zs[iz]
      else:
        z1 = zs[iz]
        z2 = zs[iz+1]

      return (x2-x1) * (y2-y1) * (z2-z1)

    # make the map
    mat = np.zeros((self.nx,self.ny,self.nz))
    for ix in range(self.nx):
      for iy in range(self.ny):
        for iz in range(self.nz):
          mat[ix,iy,iz]=volume(ix,iy,iz)
    mat = mat.astype(np.float32)
    """

        # compute volume (surface)
        dx = (self.xmax - self.xmin) / self.nx
        dy = (self.ymax - self.ymin) / self.ny
        dz = (self.zmax - self.zmin) / self.nz
        v = dx * dy * dz

        # make the map
        mat = np.ones((self.nx, self.ny, self.nz)) * v
        mat = mat.astype(np.float32)

        return mat

    def get_ValMap(self, nb, val, offx=0, offy=0, offz=0):
        """
        Return an array of points containing val of particles
        """

        x = nb.x()
        y = nb.y()
        z = nb.z()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny, self.nz)

        # make the map
        mat = mapping.mkmap3d(pos, mass, val, shape)

        return mat

    def get_MeanValMap(self, nb, val, offx=0, offy=0, offz=0):
        """
        Return an array of points containing mean val of particles
        """

        x = nb.x()
        y = nb.y()
        z = nb.z()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny, self.nz)

        # compute zero momentum
        m0 = mapping.mkmap3d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap3d(pos, mass, val, shape)

        return libutil.GetMeanMap(m0, m1)

    def get_SigmaValMap(self, nb, val, offx=0, offy=0, offz=0):
        """
        Return an array of points containing sigma val of particles
        """

        x = nb.x()
        y = nb.y()
        z = nb.z()

        # scale between 0 and 1
        x = (x - self.xmin) / (self.xmax - self.xmin) - offx / self.nx
        y = (y - self.ymin) / (self.ymax - self.ymin) - offy / self.ny
        z = (z - self.zmin) / (self.zmax - self.zmin) - offz / self.nz

        # compute values
        pos = np.transpose(np.array([x, y, z])).astype(np.float32)
        mass = np.ones(pos.shape).astype(np.float32)
        shape = (self.nx, self.ny, self.nz)

        # compute zero momentum
        m0 = mapping.mkmap3d(pos, mass, np.ones(len(pos), np.float32), shape)
        # compute first momentum
        m1 = mapping.mkmap3d(pos, mass, val, shape)
        # compute second momentum
        m2 = mapping.mkmap3d(pos, mass, val * val, shape)

        return libutil.GetSigmaMap(m0, m1, m2)

    def get_DensityMap(self, nb, offx=0, offy=0, offz=0):
        """
        Return an array of points containing density in each cell
        """
        m = self.get_MassMap(nb, offx=0, offy=0, offz=0)
        v = self.get_VolumeMap(offx=0, offy=0, offz=0)

        return m / v


##########################################################################
#
# GRID CLASS (not used and not finished)
#
##########################################################################


class Grid:

    def __init__(self, dim=1, params={}, f=None, fm=None):
        """
        Main grid object


        parameters

        xmin,xmax,nx
        ymin,ymax,ny
        zmin,zmax,nz


        """

        # example : 1d grid
        self.xmin = float(params['xmin'])
        self.xmax = float(params['xmax'])
        self.nx = int(params['nx'])
        self.offx = 0.

        self.f = f
        self.fm = fm

        ix = np.indices((self.nx,))

        # apply indx-phys transformation
        if self.f is not None:
            x = self.f(ix, self.nx, self.xmin, self.xmax)
        else:
            x = (ix + self.offx) * (self.xmax - self.xmin) / \
                (self.nx - 1) + self.xmin

        x = np.ravel(x)

        x = x
        y = np.zeros(len(x))
        z = np.zeros(len(x))

        self.pos = np.transpose(np.array([x, y, z])).astype(np.float32)

        self.shape = (self.nx,)

    def GetPoints(self):
        return self.pos

    def GetNumberMap(self, x):

        x = x.astype(np.float32)
        val = np.ones(x.shape).astype(np.float32)

        # apply phys-indx transformation and tranform between 0 and 1
        if self.fm is not None:
            x = self.fm(x, self.nx, self.xmin, self.xmax) / (self.nx - 1)
        else:
            x = (x - self.xmin) / (self.xmax - self.xmin)

        mat = mapping.mkmap1dw(x, val, val, self.shape)
        return mat

    def GetMassMap(self, x, mass):

        x = x.astype(np.float32)
        mass = mass.astype(np.float32)
        val = np.ones(x.shape).astype(np.float32)

        # apply phys-indx transformation and tranform between 0 and 1
        if self.fm is not None:
            x = self.fm(x, self.nx, self.xmin, self.xmax) / (self.nx - 1)
        else:
            x = (x - self.xmin) / (self.xmax - self.xmin)

        mat = mapping.mkmap1dw(x, mass, val, self.shape)
        return mat

    def GetSurfaceMap(self):

        # !!!!!!!!!!!! this is for carthesian  grid !!!!!!!!!!!!!!!

        ix = np.arange(self.nx - 1) + 0.5
        ix = np.concatenate(([0], ix, [self.nx - 1]))

        # apply indx-phys transformation
        if self.f is not None:
            ix = self.f(ix, self.nx, self.xmin, self.xmax)
        else:
            ix = (ix + self.offx) * (self.xmax - self.xmin) / \
                (self.nx - 1) + self.xmin

        # compute diff.
        s = ix[1:] - ix[:-1]

        return s

    def GetVolumeMap(self):

        # !!!!!!!!!!!! this is for spherical  grid !!!!!!!!!!!!!!!

        ix = np.arange(self.nx - 1) + 0.5
        ix = np.concatenate(([0], ix, [self.nx - 1]))

        # apply indx-phys transformation
        if self.f is not None:
            ix = self.f(ix, self.nx, self.xmin, self.xmax)
        else:
            ix = (ix + self.offx) * (self.xmax - self.xmin) / \
                (self.nx - 1) + self.xmin

        # compute volume.
        v = 4 / 3. * np.pi * (ix[1:]**3 - ix[:-1]**3)

        return v

    def GetSurfaceDensityMap(self, x, mass):

        return self.GetMassMap(x, mass) / self.GetSurfaceMap()

    def GetDensityMap(self, x, mass):

        return self.GetMassMap(x, mass) / self.GetVolumeMap()

    def GetPotential(self, nb, eps, force_computation=False, ErrTolTheta=0.8):

        Tree = nb.getTree(
            force_computation=force_computation,
            ErrTolTheta=ErrTolTheta)
        pot = Tree.Potential(self.pos, eps)

        # transform back into array
        #pot.shape = (nx,ny)

        return pot

    def write(self, name='grid.dat', ftype='gadget'):
        """
        it cant work, because one need pNbody
        and pNbody uses libgrid !!!
        """

        # create an Nbody object
        #nb = Nbody(status='new',p_name=name,pos=self.pos,ftype=ftype)
        # and save it
        # nb.write()

        pass


#######################################
# general functions
#######################################

def get_First_Derivative(f, x, s=None, k=2):
    """
    First derivative of f(x)
    """

    # if s!=None:
    #  tck = interpolate.fitpack.splrep(x,f,s=s,k=k)
    #  f  = interpolate.fitpack.splev(x,tck)

    fp = np.zeros(len(x), x.dtype)

    fp[0] = (f[1] - f[0]) / (x[1] - x[0])
    fp[-1] = (f[-1] - f[-2]) / (x[-1] - x[-2])

    f1 = f[2:]
    f2 = f[:-2]
    x1 = x[2:]
    x2 = x[:-2]

    fp[1:-1] = (f1 - f2) / (x1 - x2)

    return fp


def get_Mean_Along_Axis(mat, axis=0):

    if len(mat.shape) == 1:

        return mat

    elif len(mat.shape) == 2:

        a = np.fmod((axis + 1), 2)
        n = mat.shape[a]

        s = mat
        s = np.sum(s, axis=a) / n

    elif len(mat.shape) == 3:

        a = sorted(np.array([np.fmod((axis + 1), 3), np.fmod((axis + 2), 3)]))
        a1 = a[0]
        a2 = a[1]
        n1 = mat.shape[a1]
        n2 = mat.shape[a2]

        s = mat
        s = np.sum(s, axis=a2) / n2
        s = np.sum(s, axis=a1) / n1

    return s


def get_Sum_Along_Axis(mat, axis=0):

    if len(mat.shape) == 1:

        return mat

    elif len(mat.shape) == 2:

        a = np.fmod((axis + 1), 2)

        s = mat
        s = np.sum(s, axis=a)

    elif len(mat.shape) == 3:

        a = sorted(np.array([np.fmod((axis + 1), 3), np.fmod((axis + 2), 3)]))
        a1 = a[0]
        a2 = a[1]

        s = mat
        s = np.sum(s, axis=a2)
        s = np.sum(s, axis=a1)

    return s


def get_Accumulation_Along_Axis(mat, axis=0):
    """
    Accumulate values along an axis
    """
    v = get_Sum_Along_Axis(mat, axis=axis)
    return np.add.accumulate(v)


def get_Integral(v, dr, ia, ib):
    """
    Integrate the vector v, between ia and ib.

    v  : values of cells (must be 1 dimensional)
    dr : corresponding physical size of cells
    ia : lower  real indice
    ib : higher real indice
    """

    print("WARNING : libgrid.get_Integral : you should not use this function !!!")

    ia = max(0, ia)
    ib = min(len(v), ib)

    if ia == ib:
        return 0.0

    if ia > ib:
        raise Exception("ia must be < ib")

    iap = int(np.ceil(ia))
    ibp = int(np.floor(ib))

    dra = iap - ia
    drb = ib - ibp

    Ia = 0.0
    if dra != 0:
        Ia = v[iap - 1] * dra

    Ib = 0.0
    if drb != 0:
        Ib = v[ibp] * drb

    I = v[iap:ibp] * dr[iap:ibp]

    return np.sum(I) + Ia + Ib


def get_Symetrisation_Along_Axis(mat, axis=1):
    """
    Return an array where the two half are symetrized
    """

    nx, ny = mat.shape

    odd = np.fmod(ny, 2)

    if odd:
        mat1 = mat[:, 1:(ny // 2) + 1]
        mat2 = mat[:, (ny // 2) + 1:]
    else:
        mat1 = mat[:, 1:ny // 2]
        mat2 = mat[:, ny // 2:]

    #mat2 = myNumeric.turnup(mat2,0)
    mat2 = np.fliplr(mat2)

    # take the mean
    matm = (mat1 + mat2) / 2

    #mat = np.ones(mat.shape,mat.dtype)

    if odd:
        mat[:, 1:(ny // 2) + 1] = matm
        mat[:, (ny // 2) + 1:] = np.fliplr(matm)		       # myNumeric.turnup(matm,0)
    else:
        mat[:, 1:ny // 2] = matm
        mat[:, ny // 2 + 1:] = np.fliplr(matm)		       # myNumeric.turnup(matm,0)

    return mat


def get_Symetrisation_Along_Axis_Old(mat, axis=1):
    """
    Return an array where the two half are symetrized
    Old but more correct than new one
    """

    nx, ny = mat.shape

    odd = np.fmod(ny, 2)

    if odd:
        mat1 = mat[:, 0:(ny - 1) // 2]
        mat2 = mat[:, (ny - 1) // 2 + 1:]
        mat3 = mat[:, (ny - 1) // 2]
    else:
        mat1 = mat[:, 0:ny // 2]
        mat2 = mat[:, ny // 2:]

    #mat2 = myNumeric.turnup(mat2,0)
    mat2 = np.fliplr(mat2)

    # take the mean
    matm = (mat1 + mat2) / 2

    mat = np.ones(mat.shape, mat.dtype)

    if odd:

        mat[:, 0:(ny - 1) // 2] = matm
        mat[:, (ny - 1) // 2 + 1:] = np.fliplr(matm)			# myNumeric.turnup(matm,0)
        mat[:, (ny - 1) // 2] = mat3
    else:
        mat[:, 0:ny // 2] = matm
        mat[:, ny // 2:] = np.fliplr(matm)		       # myNumeric.turnup(matm,0)

    return mat


#######################################
# carthesian grid
#######################################

##############
# 2 dimensions
##############

def get_xy_Of_Carthesian_2d_Grid(
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
        offx=0,
        offy=0):

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)

    ix = np.arange(nx)
    iy = np.arange(ny)

    x = (ix + offx) * (xmax - xmin) / nx + xmin
    y = (iy + offy) * (ymax - ymin) / ny + ymin

    return x, y


def get_Points_On_Carthesian_2d_Grid(
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
        offx=0,
        offy=0):
    """
    Return an array of points corresponding to the center of cells
    af a 2d carthesian grid.

    To get a nt X nr array from the returned vector (pos), do

    x = np.copy(pos[:,0])
    y = np.copy(pos[:,1])
    z = np.copy(pos[:,2])

    x.shape = (nx,ny)
    y.shape = (nx,ny)
    z.shape = (nx,ny)

    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    nx = int(nx)
    ny = int(ny)

    ix, iy = np.indices((nx, ny))

    x = (ix + offx) * (xmax - xmin) / nx + xmin
    y = (iy + offy) * (ymax - ymin) / ny + ymin

    x = np.ravel(x)
    y = np.ravel(y)
    z = np.zeros(len(x))

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Carthesian_2d_Grid(nb, nx, ny, xmin, xmax, ymin, ymax):
    """
    Return an array of points containing mass of particles
    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)

    x = nb.pos[:, 0]
    y = nb.pos[:, 1]
    z = nb.pos[:, 2]

    # scale between 0 and 1
    x = (x - xmin) / (xmax - xmin)
    y = (y - ymin) / (ymax - ymin)

    # compute values
    pos = np.transpose(np.array([x, y, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nx, ny)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Carthesian_2d_Grid(nb, nx, ny, xmin, xmax, ymin, ymax):
    """
    Return an array of points containing mass of particles
    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)

    x = nb.pos[:, 0]
    y = nb.pos[:, 1]
    z = nb.pos[:, 2]

    # scale between 0 and 1
    x = (x - xmin) / (xmax - xmin)
    y = (y - ymin) / (ymax - ymin)

    # compute values
    pos = np.transpose(np.array([x, y, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nx, ny)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Carthesian_2d_Grid(
        nb, nx, ny, xmin, xmax, ymin, ymax, eps, Tree=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Carthesian_2d_Grid(nx, ny, xmin, xmax, ymin, ymax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nx, ny)

    return pot


def get_SurfaceMap_On_Carthesian_2d_Grid(nb, nx, ny, xmin, xmax, ymin, ymax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)

    """
    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)

    # compute volume (surface)
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    v = dx * dy

    # make the map
    mat = np.ones((nx, ny)) * v
    mat = mat.astype(np.float32)

    return mat


def get_SurfaceDensityMap_On_Carthesian_2d_Grid(
        nb, nx, ny, xmin, xmax, ymin, ymax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Carthesian_2d_Grid(nb, nx, ny, xmin, xmax, ymin, ymax)
    s = get_SurfaceMap_On_Carthesian_2d_Grid(
        nb, nx, ny, xmin, xmax, ymin, ymax)

    return m / s

##############
# 3 dimensions
##############


def get_xyz_Of_Carthesian_3d_Grid(
        nx,
        ny,
        nz,
        xmin,
        xmax,
        ymin,
        ymax,
        zmin,
        zmax,
        offx=0,
        offy=0,
        offz=0):

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    zmax = float(zmax)
    zmin = float(zmin)

    ix = np.arange(nx)
    iy = np.arange(ny)
    iz = np.arange(nz)

    x = (ix + offx) * (xmax - xmin) / nx + xmin
    y = (iy + offy) * (ymax - ymin) / ny + ymin
    z = (iz + offz) * (zmax - zmin) / nz + zmin

    return x, y, z


def get_Points_On_Carthesian_3d_Grid(
        nx,
        ny,
        nz,
        xmin,
        xmax,
        ymin,
        ymax,
        zmin,
        zmax,
        offx=0,
        offy=0,
        offz=0):
    """
    Return an array of points corresponding to the center of cells
    af a 3d carthesian grid.

    To get a nt X nr array from the returned vector (pos), do

    x = np.copy(pos[:,0])
    y = np.copy(pos[:,1])
    z = np.copy(pos[:,2])

    x.shape = (nx,ny,nz)
    y.shape = (nx,ny,nz)
    z.shape = (nx,ny,nz)

    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    zmax = float(zmax)
    zmin = float(zmin)
    nx = int(nx)
    ny = int(ny)
    nz = int(nz)

    ix, iy, iz = np.indices((nx, ny, nz))

    x = (ix + offx) * (xmax - xmin) / nx + xmin
    y = (iy + offy) * (ymax - ymin) / ny + ymin
    z = (iz + offz) * (zmax - zmin) / nz + zmin

    x = np.ravel(x)
    y = np.ravel(y)
    z = np.ravel(z)

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Carthesian_3d_Grid(
        nb,
        nx,
        ny,
        nz,
        xmin,
        xmax,
        ymin,
        ymax,
        zmin,
        zmax):
    """
    Return an array of points containing mass of particles
    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    zmax = float(zmax)
    zmin = float(zmin)

    x = nb.pos[:, 0]
    y = nb.pos[:, 1]
    z = nb.pos[:, 2]

    # scale between 0 and 1
    x = (x - xmin) / (xmax - xmin)
    y = (y - ymin) / (ymax - ymin)
    z = (z - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([x, y, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nx, ny, nz)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax):
    """
    Return an array of points containing mass of particles
    """

    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    zmax = float(zmax)
    zmin = float(zmin)

    x = nb.pos[:, 0]
    y = nb.pos[:, 1]
    z = nb.pos[:, 2]

    # scale between 0 and 1
    x = (x - xmin) / (xmax - xmin)
    y = (y - ymin) / (ymax - ymin)
    z = (z - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([x, y, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nx, ny, nz)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Carthesian_3d_Grid(
        nb,
        nx,
        ny,
        nz,
        xmin,
        xmax,
        ymin,
        ymax,
        zmin,
        zmax,
        eps,
        Tree=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nx, ny, nz)

    return pot


def get_VolumeMap_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """
    xmax = float(xmax)
    xmin = float(xmin)
    ymax = float(ymax)
    ymin = float(ymin)
    zmax = float(zmax)
    zmin = float(zmin)

    # compute volume (surface)
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    dz = (zmax - zmin) / nz
    v = dx * dy * dz

    # make the map
    mat = np.ones((nx, ny, nz)) * v
    mat = mat.astype(np.float32)

    return mat


def get_DensityMap_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax)
    v = get_VolumeMap_On_Carthesian_3d_Grid(
        nb, nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax)

    return m / v

#######################################
# cylindrical grid
#######################################


######################
# 2 dimensions r,t (h)
######################

def get_rt_Of_Cylindrical_2dh_Grid(nr, nt, rmax, offr=0, offt=0):

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi

    ir = np.arange(nr)
    it = np.arange(nt)

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    t = (it + offt) * (tmax - tmin) / nt + tmin

    return r, t


def get_Points_On_Cylindrical_2dh_Grid(nr, nt, rmax, offr=0, offt=0):
    """
    Return an array of points corresponding to the nodes of
    a 2d cylindrical grid

    To get a nt X nr array from the returned vector (pos), do

    x = np.copy(pos[:,0])
    y = np.copy(pos[:,1])
    z = np.copy(pos[:,2])

    x.shape = (nr,nt)
    y.shape = (nr,nt)
    z.shape = (nr,nt)

    # to get r and theta
    r = np.sqrt(x**2+y**2+z**2)
    t = arctan2(y,x)*180/np.pi

    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi
    nr = int(nr)
    nt = int(nt)

    ir, it = np.indices((nr, nt))

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    t = (it + offt) * (tmax - tmin) / nt + tmin

    r = np.ravel(r)
    t = np.ravel(t)

    x = r * np.cos(t)
    y = r * np.sin(t)
    z = np.zeros(len(x))

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    t = (t - tmin) / (tmax - tmin)

    # compute values
    pos = np.transpose(np.array([r, t, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr, nt)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    t = (t - tmin) / (tmax - tmin)

    # compute values
    pos = np.transpose(np.array([r, t, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nr, nt)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax, eps, Tree=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Cylindrical_2dh_Grid(nr, nt, rmax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nr, nt)

    return pot


def get_SurfaceMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """

    rmax = float(rmax)

    # compute volume (surface)
    #dr = rmax/nr
    #rs = np.arange(nr+1)*dr
    #v = (np.pi*rs[1:]**2 - np.pi*rs[:-1]**2 )/nt

    def volume(ir, it):
        dr = (rmax / nr)
        r = ir * dr
        return np.pi * ((r + dr)**2 - (r)**2) / nt

    # make the map
    mat = np.fromfunction(volume, (nr, nt))
    mat = mat.astype(np.float32)

    return mat


def get_SurfaceDensityMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax)
    s = get_SurfaceMap_On_Cylindrical_2dh_Grid(nb, nr, nt, rmax)

    return m / s

######################
# 2 dimensions r,z (v)
######################


def get_rz_Of_Cylindrical_2dv_Grid(nr, nz, rmax, zmin, zmax):

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    ir = np.arange(nr)
    iz = np.arange(nz)

    r = (ir + 0.0) * (rmax - rmin) / nr + rmin
    z = (iz + 0.0) * (zmax - zmin) / nz + zmin

    return r, z


def get_Points_On_Cylindrical_2dv_Grid(
        nr, nz, rmax, zmin, zmax, offr=0, offz=0):
    """
    Return an array of points corresponding to the nodes of
    a 2d cylindrical grid

    To get a nt X nr array from the returned vector (pos), do

    x = np.copy(pos[:,0])
    y = np.copy(pos[:,1])
    z = np.copy(pos[:,2])

    x.shape = (nr,nt)
    y.shape = (nr,nt)
    z.shape = (nr,nt)

    # to get r and theta
    r = np.sqrt(x**2+y**2+z**2)
    t = arctan2(y,x)*180/np.pi

    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    ir, iz = np.indices((nr, nz))

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    z = (iz + offz) * (zmax - zmin) / nz + zmin

    r = np.ravel(r)
    z = np.ravel(z)

    x = r
    y = np.zeros(len(x))
    z = z

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    z = (z - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([r, z, t])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr, nz)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    z = (z - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([r, z, t])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nr, nz)

    # make the map
    mat = mapping.mkmap2d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Cylindrical_2dv_Grid(
        nb, nr, nz, rmax, zmin, zmax, eps, Tree=None):
    """
    Return an array of points containing potential
    """
    pos = get_Points_On_Cylindrical_2dv_Grid(nr, nz, rmax, zmin, zmax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nr, nz)

    return pot


def get_AccelerationMap_On_Cylindrical_2dv_Grid(
        nb, nr, nz, rmax, zmin, zmax, eps, Tree=None):
    """
    Return an array of points containing accelerations
    """
    pos = get_Points_On_Cylindrical_2dv_Grid(nr, nz, rmax, zmin, zmax)

    Tree = nb.getTree()

    acc = Tree.Acceleration(pos, eps)

    accx = np.copy(acc[:, 0])
    accy = np.copy(acc[:, 1])
    accz = np.copy(acc[:, 2])

    # transform back into array
    accx.shape = (nr, nz)
    accy.shape = (nr, nz)
    accz.shape = (nr, nz)

    return accx, accy, accz


def get_VolumeMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    # compute volume (surface)
    #dr = rmax/nr
    #rs = np.arange(nr+1)*dr
    #v = (np.pi*rs[1:]**2 - np.pi*rs[:-1]**2 )/nt

    def volume(ir, iz):
        dr = (rmax - rmin) / nr
        dz = (zmax - zmin) / nz
        r = ir * dr
        return np.pi * ((r + dr)**2 - (r)**2) * dz

    # make the map
    mat = fromfunction(volume, (nr, nz))
    mat = mat.astype(np.float32)

    return mat


def get_DensityMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax)
    v = get_VolumeMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax)

    return m / v


def get_SurfaceDensityMap_From_Cylindrical_2dv_Grid(
        nb, nr, nz, rmax, zmin, zmax):
    """
    Return an array of points containing the surface density along r
    """

    m = get_MassMap_On_Cylindrical_2dv_Grid(nb, nr, nz, rmax, zmin, zmax)
    m = get_Sum_Along_Axis(m)

    def surface(ir):
        dr = (rmax) / nr
        r = ir * dr
        return np.pi * ((r + dr)**2 - (r)**2)

    s = np.fromfunction(surface, (nr,))

    return m / s


def get_Interpolation_On_Cylindrical_2dv_Grid(
        pos, mat, nr, nz, rmax, zmin, zmax, offr=0, offz=0):
    """
    Interpolates continuous value of pos, using matrix mat
    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)
    z = pos[:, 2]

    ir = (r - rmin) / (rmax - rmin) * nr - offr
    iz = (z - zmin) / (zmax - zmin) * nz - offz

    return myNumeric.Interpolate_From_2d_Array(
        ir.astype(np.float32), iz.astype(np.float32), mat.astype(np.float32))


def get_r_Interpolation_On_Cylindrical_2dv_Grid(
        pos, mat, nr, nz, rmax, zmin, zmax, offr=0):
    """
    Interpolates continuous value of pos, using matrix mat
    only along first axis.
    """

    rmin = 0.0
    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nz = int(nz)

    r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)

    ir = (r - rmin) / (rmax - rmin) * nr - offr

    return myNumeric.Interpolate_From_1d_Array(
        ir.astype(np.float32), mat.astype(np.float32))

##############
# 3 dimensions
##############


def get_rtz_Of_Cylindrical_3d_Grid(
        nr,
        nt,
        nz,
        rmax,
        zmin,
        zmax,
        offr=0,
        offt=0,
        offz=0):

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi
    zmin = float(zmin)
    zmax = float(zmax)

    ir = np.arange(nr)
    it = np.arange(nt)
    iz = np.arange(nz)

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    t = (it + offt) * (tmax - tmin) / nt + tmin
    z = (iz + offz) * (zmax - zmin) / nz + zmin

    return r, t, z


def get_Points_On_Cylindrical_3d_Grid(
        nr,
        nt,
        nz,
        rmax,
        zmin,
        zmax,
        offr=0,
        offt=0,
        offz=0):
    """
    Return an array of points corresponding to the nodes of
    a 2d cylindrical grid

    To get a nt X nr array from the returned vector (pos), do

    x = pos[:,0]
    y = pos[:,0]
    z = pos[:,0]

    x.shape = (nr,nt,nz)
    y.shape = (nr,nt,nz)
    z.shape = (nr,nt,nz)

    # to get r and theta
    r = np.sqrt(x**2+y**2+z**2)
    t = arctan2(y,x)*180/np.pi

    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi
    zmin = float(zmin)
    zmax = float(zmax)
    nr = int(nr)
    nt = int(nt)
    nz = int(nz)

    ir, it, iz = np.indices((nr, nt, nz))

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    t = (it + offt) * (tmax - tmin) / nt + tmin
    z = (iz + offz) * (zmax - zmin) / nz + zmin

    r = np.ravel(r)
    t = np.ravel(t)
    z = np.ravel(z)

    x = r * np.cos(t)
    y = r * np.sin(t)
    z = z

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi
    zmin = float(zmin)
    zmax = float(zmax)

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    t = (t - tmin) / (tmax - tmin)
    z = (t - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([r, t, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr, nt, nz)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    tmin = 0.0
    tmax = 2 * np.pi
    zmin = float(zmin)
    zmax = float(zmax)

    r = nb.rxy()
    t = nb.phi_xy() + np.pi
    z = nb.pos[:, 2]

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    t = (t - tmin) / (tmax - tmin)
    z = (t - zmin) / (zmax - zmin)

    # compute values
    pos = np.transpose(np.array([r, t, z])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nr, nt, nz)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Cylindrical_3d_Grid(
        nb, nr, nt, nz, rmax, zmin, zmax, eps, Tree=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Cylindrical_3d_Grid(nr, nt, nz, rmax, zmin, zmax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nr, nt, nz)

    return pot


def get_VolumeMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """

    rmax = float(rmax)
    zmin = float(zmin)
    zmax = float(zmax)

    # compute volume (surface)
    #dr = rmax/nr
    #rs = np.arange(nr+1)*dr
    #v = (np.pi*rs[1:]**2 - np.pi*rs[:-1]**2 )/nt

    def volume(ir, it, iz):
        dr = (rmax / nr)
        dz = (zmax - zmin) / nz
        r = ir * dr
        return np.pi * ((r + dr)**2 - (r)**2) / nt * dz

    # make the map
    mat = np.fromfunction(volume, (nr, nt, nz))
    mat = mat.astype(np.float32)

    return mat


def get_DensityMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax)
    v = get_VolumeMap_On_Cylindrical_3d_Grid(nb, nr, nt, nz, rmax, zmin, zmax)

    return m / v


#######################################
# spherical grid
#######################################


##############
# 1 dimension
##############

def get_r_Of_Spherical_1d_Grid(nr, rmax, offr=0, f=None, fm=None):

    rmin = 0.0
    rmax = float(rmax)

    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)

    ir = np.arange(nr)

    r = (ir + offr) * (rmax - rmin) / nr + rmin

    if fm is not None:
        r = fm(r)

    return r


def get_Points_On_Spherical_1d_Grid(nr, rmax, offr=0, f=None, fm=None):
    """
    Return an array of points corresponding to the nodes of
    a 1d spherical grid

    To get a nt X nr array from the returned vector (pos), do

    x = pos[:,0]
    y = pos[:,0]
    z = pos[:,0]

    x.shape = (nr,NP,nt)
    y.shape = (nr,NP,nt)
    z.shape = (nr,NP,nt)
    """

    rmin = 0.0
    rmax = float(rmax)
    nr = int(nr)

    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)

    ir = np.indices((nr,))

    r = (ir + offr) * (rmax - rmin) / nr + rmin

    r = np.ravel(r)

    if fm is not None:
        r = fm(r)

    x = r
    y = np.zeros(len(x))
    z = np.zeros(len(x))

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)

    r = nb.rxyz()			# 0 -> rmax

    # here, we scale
    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)
        r = f(r)

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)

    # compute values
    pos = np.transpose(np.array(r)).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr,)

    # make the map
    mat = mapping.mkmap1d(pos, mass, val, shape)

    return mat


def get_GenericMap_On_Spherical_1d_Grid(nb, nr, rmax, val, f=None, fm=None):
    """
    Return an array of points containing mass*val
    """

    rmin = 0.0
    rmax = float(rmax)

    r = nb.rxyz()			# 0 -> rmax

    # here, we scale
    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)
        r = f(r)

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)

    # compute values
    pos = np.transpose(np.array(r)).astype(np.float32)
    val = val.astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr,)

    # make the map
    mat = mapping.mkmap1d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing number of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    r = nb.rxyz()			# 0 -> rmax

    # here, we scale
    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)
        r = f(r)

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)

    # compute values
    pos = np.transpose(np.array(r)).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nr,)

    # make the map
    mat = mapping.mkmap1d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Spherical_1d_Grid(
        nb, nr, rmax, eps, Tree=None, f=None, fm=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Spherical_1d_Grid(nr, rmax, f=f, fm=fm)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nr,)

    return pot


def get_SurfaceMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing surface (volume)
    of each cell.
    """
    rmin = 0.0
    rmax = float(rmax)

    # compute volume (surface)
    # def volume(ir):
    #  dr = (rmax/nr) + (ir-ir)
    #  return dr
    #
    # make the map
    #mat = np.fromfunction(volume,(nr,))
    #mat = mat.astype(np.float32)

    r1 = get_r_Of_Spherical_1d_Grid(nr, rmax, offr=0, f=f, fm=fm)
    r2 = get_r_Of_Spherical_1d_Grid(nr, rmax, offr=1, f=f, fm=fm)

    mat = r2 - r1
    mat = mat.astype(np.float32)

    return mat


def get_VolumeMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """
    rmin = 0.0
    rmax = float(rmax)

    # compute volume (surface)
    # def volume(ir):
    #  dr = (rmax/nr)
    #  r  = ir*dr
    #  return 4.0/3.0*np.pi*( (r+dr)**3 - (r)**3 )
    #
    # make the map
    #mat = np.fromfunction(volume,(nr,))
    #mat = mat.astype(np.float32)

    r1 = get_r_Of_Spherical_1d_Grid(nr, rmax, offr=0, f=f, fm=fm)
    r2 = get_r_Of_Spherical_1d_Grid(nr, rmax, offr=1, f=f, fm=fm)

    mat = 4.0 / 3.0 * np.pi * ((r2)**3 - (r1)**3)
    mat = mat.astype(np.float32)

    return mat


def get_DensityMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Spherical_1d_Grid(nb, nr, rmax, f=f, fm=fm)
    v = get_VolumeMap_On_Spherical_1d_Grid(nb, nr, rmax, f=f, fm=fm)

    return m / v


def get_LinearDensityMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing the linear density in each cell
    """

    m = get_MassMap_On_Spherical_1d_Grid(nb, nr, rmax, f=f, fm=fm)
    s = get_SurfaceMap_On_Spherical_1d_Grid(nb, nr, rmax, f=f, fm=fm)

    return m / s


def get_AccumulatedMassMap_On_Spherical_1d_Grid(nb, nr, rmax, f=None, fm=None):
    """
    Return an array of points containing M(r) in each cell
    """

    m = get_MassMap_On_Spherical_1d_Grid(nb, nr, rmax, f=f, fm=fm)
    mr = get_Accumulation_Along_Axis(m, axis=0)

    return mr


def get_Interpolation_On_Spherical_1d_Grid(
        pos, mat, nr, rmax, offr=0, f=None, fm=None):
    """
    Interpolates continuous value of pos, using matrix mat
    """

    rmin = 0.0
    rmax = float(rmax)
    nr = int(nr)

    r = np.sqrt(pos[:, 0]**2 + pos[:, 1]**2 + pos[:, 2]**2)

    # here, we scale
    if f is not None:
        rmin = f(rmin)
        rmax = f(rmax)
        r = f(r)

    ir = (r - rmin) / (rmax - rmin) * nr - offr

    return myNumeric.Interpolate_From_1d_Array(
        ir.astype(np.float32), mat.astype(np.float32))


##############
# 3 dimensions
##############


def get_rpt_Of_Spherical_3d_Grid(nr, NP, nt, rmax, offr=0, offp=0, offt=0):

    rmin = 0.0
    rmax = float(rmax)
    pmin = 0.0
    pmax = 2 * np.pi
    tmin = -np.pi / 2
    tmax = np.pi / 2

    ir = np.arange(nr)
    ip = np.arange(np)
    it = np.arange(nt)

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    p = (ip + offp) * (pmax - pmin) / NP + pmin
    t = (it + offt) * (tmax - tmin) / nt + tmin

    return r, p, t


def get_Points_On_Spherical_3d_Grid(nr, NP, nt, rmax, offr=0, offp=0, offt=0):
    """
    Return an array of points corresponding to the nodes of
    a 3d spherical grid

    To get a nt X nr array from the returned vector (pos), do

    x = pos[:,0]
    y = pos[:,0]
    z = pos[:,0]

    x.shape = (nr,NP,nt)
    y.shape = (nr,NP,nt)
    z.shape = (nr,NP,nt)
    """

    rmin = 0.0
    rmax = float(rmax)
    pmin = 0.0
    pmax = 2 * np.pi
    tmin = -np.pi / 2
    tmax = np.pi / 2
    nr = int(nr)
    NP = int(NP)
    nt = int(nt)

    ir, ip, it = np.indices((nr, NP, nt))

    r = (ir + offr) * (rmax - rmin) / nr + rmin
    p = (ip + offp) * (pmax - pmin) / NP + pmin
    t = (it + offt) * (tmax - tmin) / nt + tmin

    r = np.ravel(r)
    p = np.ravel(p)
    t = np.ravel(t)

    x = r * np.cos(p) * np.cos(t)
    y = r * np.sin(p) * np.cos(t)
    z = r * np.sin(t)

    return np.transpose(np.array([x, y, z])).astype(np.float32)


def get_MassMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    pmin = 0.0
    pmax = 2 * np.pi
    tmin = -np.pi / 2
    tmax = np.pi / 2

    r = nb.rxyz()			# 0 -> rmax
    p = nb.phi_xyz() + np.pi		# 0 -> pi
    t = nb.theta_xyz() 		# -pi/2 -> pi/2

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    p = (p - pmin) / (pmax - pmin)
    t = (t - tmin) / (tmax - tmin)

    # compute values
    pos = np.transpose(np.array([r, p, t])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = nb.mass.astype(np.float32)
    shape = (nr, NP, nt)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_NumberMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax):
    """
    Return an array of points containing mass of particles
    """

    rmin = 0.0
    rmax = float(rmax)
    pmin = 0.0
    pmax = 2 * np.pi
    tmin = -np.pi / 2
    tmax = np.pi / 2

    r = nb.rxyz()			# 0 -> rmax
    p = nb.phi_xyz() + np.pi		# 0 -> pi
    t = nb.theta_xyz() 		# -pi/2 -> pi/2

    # scale between 0 and 1
    r = (r - rmin) / (rmax - rmin)
    p = (p - pmin) / (pmax - pmin)
    t = (t - tmin) / (tmax - tmin)

    # compute values
    pos = np.transpose(np.array([r, p, t])).astype(np.float32)
    val = np.ones(pos.shape).astype(np.float32)
    mass = np.ones(pos.shape).astype(np.float32)
    shape = (nr, NP, nt)

    # make the map
    mat = mapping.mkmap3d(pos, mass, val, shape)

    return mat


def get_PotentialMap_On_Spherical_3d_Grid(
        nb, nr, NP, nt, rmax, eps, Tree=None):
    """
    Return an array of points containing potential
    """

    pos = get_Points_On_Spherical_3d_Grid(nr, NP, nt, rmax)

    Tree = nb.getTree()

    pot = Tree.Potential(pos, eps)

    # transform back into array
    pot.shape = (nr, NP, nt)

    return pot


def get_VolumeMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax):
    """
    Return an array of points containing corresponding physical
    volumes of each cell (usefull to compute density)
    """

    print("get_VolumeMap_On_Spherical_3d_Grid is probably wrong")
    print("we should add a np.cos(t) or somthing similar")
    sys.exit()

    rmin = 0.0
    rmax = float(rmax)
    pmin = 0.0
    pmax = 2 * np.pi
    tmin = -np.pi / 2
    tmax = np.pi / 2

    # compute volume (surface)

    def volume(ir, ip, it):
        dr = (rmax / nr)
        r = ir * dr
        return 4.0 / 3.0 * np.pi * ((r + dr)**3 - (r)**3) / NP / nt

    # make the map
    mat = np.fromfunction(volume, (nr, NP, nt))
    mat = mat.astype(np.float32)

    return mat


def get_DensityMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax):
    """
    Return an array of points containing density in each cell
    """

    m = get_MassMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax)
    v = get_VolumeMap_On_Spherical_3d_Grid(nb, nr, NP, nt, rmax)

    return m / v
