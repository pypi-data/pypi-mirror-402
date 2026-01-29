#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      plot.py
#  brief:     plot functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import interpolate

##########################################################################
#
# command arguments routines
#
##########################################################################


def add_arguments_units(parser):
    '''
    This function allow to add postscript options to a parser object
    '''

    parser.add_argument("--UnitLength_in_cm",
                      action="store",
                      dest="UnitLength_in_cm",
                      type=float,
                      default=None,
                      help="UnitLength in cm")

    parser.add_argument("--UnitMass_in_g",
                      action="store",
                      dest="UnitMass_in_g",
                      type=float,
                      default=None,
                      help="UnitMass in g")

    parser.add_argument("--UnitVelocity_in_cm_per_s",
                      action="store",
                      dest="UnitVelocity_in_cm_per_s",
                      type=float,
                      default=None,
                      help="UnitVelocity in cm per s")

    parser.add_argument("--param",
                      action="store",
                      dest="GadgetParameterFile",
                      type=str,
                      default=None,
                      help="Gadget parameter file",
                      metavar=" FILE")

    return parser




def apply_arguments_units(options):
    '''
    This function allow to extract units options from option object
    '''

    try:
        UnitLength_in_cm = options.UnitLength_in_cm
    except BaseException:
        UnitLength_in_cm = None

    try:
        UnitMass_in_g = options.UnitMass_in_g
    except BaseException:
        UnitMass_in_g = None

    try:
        UnitVelocity_in_cm_per_s = options.UnitVelocity_in_cm_per_s
    except BaseException:
        UnitVelocity_in_cm_per_s = None

    try:
        GadgetParameterFile = options.GadgetParameterFile
    except BaseException:
        GadgetParameterFile = None

    if GadgetParameterFile is not None:
        params = io.read_params(GadgetParameterFile)
    else:
        if UnitLength_in_cm is None or UnitMass_in_g is None or UnitVelocity_in_cm_per_s is None:
            params = None
        else:
            params = {}
            params['UnitLength_in_cm'] = UnitLength_in_cm
            params['UnitMass_in_g'] = UnitMass_in_g
            params['UnitVelocity_in_cm_per_s'] = UnitVelocity_in_cm_per_s

    return params


def add_arguments_reduc(parser):
    '''
    This function allow to reduc the number of particles
    '''

    parser.add_argument("--reduc",
                      action="store",
                      dest="reduc",
                      type=int,
                      default=None,
                      help="reduc from a factor n")

    return parser
    
    

def apply_arguments_reduc(nb, opt, verbose=True):

    if not hasattr(opt, "reduc"):
        print("Skipping reduc options..")
        return nb

    if isinstance(opt.reduc, int):
        if verbose:
            print(("reducing %s" % (opt.reduc)))
        nb = nb.reduc(opt.reduc)

    return nb



def add_arguments_center(parser):
    '''
    This function allow to center the model
    '''

    parser.add_argument(
        "--center",
        action="store",
        dest="center",
        type=str,
        default=None,
        help="center the model (histocenter,hdcenter,cmcenter,cmhistocenter)")

    parser.add_argument(
        "--inertial",
        action="store_true",
        dest="inertial",
        default=False,
        help="Switch to an inertial reference frame (not the case if PERIODICOUTER was used)")

    return parser
    
    

def apply_arguments_center(nb, opt, verbose=True):

    if not hasattr(opt, "center"):
        print("Skipping center options..")
        return nb

    # center the model
    if opt.center == 'hdcenter':
        if verbose:
            print(("centering %s" % (opt.center)))
        nb.hdcenter()

    elif opt.center == 'histocenter':
        if verbose:
            print(("centering %s" % (opt.center)))
        nb.histocenter()

    elif opt.center == 'cmcenter':
        if verbose:
            print(("centering %s" % (opt.center)))
        nb.cmcenter()

    elif opt.center == 'cmhistocenter':
        if verbose:
            print(("centering %s" % (opt.center)))
        nb.cmcenter()
        nb.histocenter()

    elif opt.center == 'rebox':
        if verbose:
            print(("centering %s" % (opt.center)))
        nb.rebox(mode='centred')

    if opt.inertial:
        print("Removing referential rotation")
        trace = nb.selectp(nb.trace_ids)
        tpos = np.mean(trace.pos, axis=0)
        pos = nb.pos - tpos
        nb.vel += np.cross(nb.trace_angular[:3], pos)
    return nb




def add_arguments_select(parser):
    '''
    This function allow to select particles from the model
    '''

    parser.add_argument(
        "--select",
        action="store",
        dest="select",
        type=str,
        default=None,
        help="select particles from the model ('gas','sph','sticky',...)")

    parser.add_argument("--ids_file",
                      action="store",
                      dest="ids_file",
                      type=str,
                      default=None,
                      help="File containing the requested IDs",
                      metavar="STR")

    parser.add_argument("--radius",
                      action="store",
                      dest="radius",
                      type=float,
                      default=None,
                      help="Max selection radius",
                      metavar="FLOAT")

    return parser



def apply_arguments_select(nb, opt, verbose=True):

    if not hasattr(opt, "select"):
        print("Skipping select options..")
        return nb

    # select
    if opt.select is not None:
        if verbose:
            print(("select %s" % (opt.select)))
        nb = nb.select(opt.select)

    if opt.ids_file is not None:
        if verbose:
            print(("selecting particles from %f" % opt.ids_file))
        nb = nb.selectp(file=opt.ids_file)

    if opt.radius is not None:
        if verbose:
            print(("removing particles at radius > %g" % opt.radius))
        nb = nb.selectc(nb.rxzy() < opt.radius)

    return nb


def add_arguments_info(parser):
    '''
    This function allow to select particles from the model
    '''

    parser.add_argument("--info",
                      action="store_true",
                      dest="info",
                      default=False,
                      help="print info on the model")

    return parser


def apply_arguments_info(nb, opt, verbose=True):

    if not hasattr(opt, "info"):
        print("Skipping info options..")
        return nb

    # select
    if opt.info:
        nb.info()

    return nb

def add_arguments_cmd(parser):
    '''
    This function allow to execute a command on the model
    '''

    parser.add_argument("--cmd",
                      action="store",
                      dest="cmd",
                      type=str,
                      default=None,
                      help="python command 'nb = nb.selectc((nb.T()>10))'")

    return parser


def apply_arguments_cmd(nb, opt, verbose=True):

    if not hasattr(opt, "cmd"):
        print("Skipping cmd options..")
        return nb

    # cmd
    if (opt.cmd is not None) and (opt.cmd != 'None'):
        if verbose:
            print(("exec : %s" % opt.cmd))
        
        # note : this is the new way of doing stuff in python3 :-(    
        namespace = {"nb":nb}
        exec(opt.cmd,namespace)
        nb = namespace["nb"]    
            
    return nb


def add_arguments_display(parser):
    '''
    This function allow to display the model
    '''

    parser.add_option("--display",
                      action="store",
                      dest="display",
                      type=str,
                      default=None,
                      help="display the model")

    return parser


def apply_arguments_display(nb, opt, verbose=True):

    if not hasattr(opt, "display"):
        print("Skipping display options..")
        return nb

    # display
    if (opt.display is not None) and (opt.display != 'None'):
        nb.display(
            obs=None,
            view=opt.display,
            marker='cross',
            pt=None,
            xp=None)

    return nb





def add_files_options(parser):
    '''
    This function allow to add color options to a parser object
    '''

    parser.add_argument("-t", "--ftype",
                      action="store",
                      dest="ftype",
                      type=str,
                      default='gh5',
                      help="type of the file",
                      metavar=" TYPE")

    parser.add_argument("--skip_io_block",
                      action="store",
                      dest="skip_io_block",
                      type=str,
                      default="",
                      help="Skip IO block (comma separated list)",
                      metavar="STR")

    parser.add_argument("--verbose",
                      action="store",
                      dest="verbose",
                      type=int,
                      default=0,
                      help="Define the verbose level (0: minimal, 1: standard,"
                      " 2: details 10:maximal)",
                      metavar="INT")

    return parser



def apply_arguments_verbose(nb, opt, verbose=True):

    if not hasattr(opt, "verbose"):
        print("Skipping verbose options..")
        return nb

    nb.verbose=opt.verbose

    return nb





def add_comoving_options(parser):
    """
    This function allow to force comoving integration for a snapshot.
    """

    parser.add_argument("--forceComovingIntegrationOn",
                      action="store_true",
                      dest="forceComovingIntegrationOn",
                      default=False,
                      help="force the model to be in in comoving integration")

    parser.add_argument(
        "--forceComovingIntegrationOff",
        action="store_true",
        dest="forceComovingIntegrationOff",
        default=False,
        help="force the model not to be in in comoving integration")

    return parser


def apply_arguments_comoving(nb, opt):

    if not hasattr(opt, "forceComovingIntegrationOn"):
        print("Skipping comoving options..")
        return nb

    if opt.forceComovingIntegrationOn:
        nb.setComovingIntegrationOn()

    if opt.forceComovingIntegrationOff:
        nb.setComovingIntegrationOff()

    return nb



def add_arguments_legend(parser):
    '''
    This function allow to add legend options to a parser object
    '''

    parser.add_argument("--legend",
                      action="store_true",
                      dest="legend",
                      default=False,
                      help="add a legend")

    parser.add_argument("--legend_ncol",
                      action="store",
                      dest="legend_ncol",
                      default=1,
                      type=int,
                      help="number of columns for the legend")

    parser.add_argument("--legend_txt",
                      action="store",
                      dest="legend_txt",
                      type=str,
                      default=None,
                      help="legend text",
                      metavar=" LIST of STRINGS")

    parser.add_argument("--legend_loc",
                      action="store",
                      type=str,
                      dest="legend_loc",
                      default=None,
                      help="legend location 'upper right'... ")

    return parser



def add_arguments_icshift(parser):
    '''
    This function allow to shift the model if needed
    '''

    parser.add_argument("--remove_ic_shift",
                      action="store_true",
                      dest="remove_ic_shift",
                      default=False,
                      help="remove the shift applied on the initial conditions.")

    return parser

def apply_arguments_icshift(nb, opt):

    if nb.has_var("InitialConditions_shift"):
      if opt.remove_ic_shift:
        nb.message("translate back : %s"%nb.InitialConditions_shift)
        nb.translate(-nb.InitialConditions_shift)
    
    return nb


##########################################################################
#
# graph limits routines
#
##########################################################################


def SetLimitsFromDataPoints(datas, xmin, xmax, ymin, ymax, log=None):
    
  if len(datas) == 1:
      x = datas[0].x
      y = datas[0].y
  else:
      x = np.array([], float)
      y = np.array([], float)
  
      for data in datas:
          x = np.concatenate((x, data.x))
          y = np.concatenate((y, data.y))
  
  return SetLimits(xmin, xmax, ymin, ymax, x, y, log=log)


def SetLimits(xmin, xmax, ymin, ymax, x, y, log=None):

    if log is not None:
        if str.find(log, 'x') != -1:

            x, y = CleanVectorsForLogX(x, y)

            x = np.log10(x)
            if xmin is not None:
                xmin = np.log10(xmin)
            if xmax is not None:
                xmax = np.log10(xmax)

    #############################
    # set x

    if xmin is None:
        xmin = min(x)

    if xmax is None:
        xmax = max(x)

    if xmin == xmax:
        xmin = xmin - 0.05 * xmin
        xmax = xmax + 0.05 * xmax
    else:
        xmin = xmin - 0.05 * (xmax - xmin)
        xmax = xmax + 0.05 * (xmax - xmin)

    # cut y values based on x
    #c = (x>=xmin)*(x<=xmax)
    #y = compress(c,y)

    if log is not None:
        if str.find(log, 'x') != -1:
            # if log=='x' or log=='xy':

            xmin = 10**xmin
            xmax = 10**xmax

    #############################
    # set y

    if log is not None:
        if str.find(log, 'y') != -1:

            x, y = CleanVectorsForLogY(x, y)

            y = np.log10(y)
            if ymin is not None:
                ymin = np.log10(ymin)
            if ymax is not None:
                ymax = np.log10(ymax)

    if ymin is None:
        ymin = min(y)

    if ymax is None:
        ymax = max(y)

    if ymin == ymax:
        ymin = ymin - 0.05 * ymin
        ymax = ymax + 0.05 * ymax
    else:
        ymin = ymin - 0.05 * (ymax - ymin)
        ymax = ymax + 0.05 * (ymax - ymin)

    if log is not None:
        if str.find(log, 'y') != -1:
            # if log=='y' or log=='xy':
            ymin = 10**ymin
            ymax = 10**ymax

    return xmin, xmax, ymin, ymax, log






def SetAxis(ax,xmin, xmax, ymin, ymax, log=None, extend=True):
  """
  Set ticks for the axis
  (this is the new routine)
  """
  
  #####################################
  # first : slightly extend the limits
  #####################################
  
  if extend:
      
    if log is not None:
        if str.find(log, 'x') != -1:
            if xmin is not None:
                xmin = np.log10(xmin)
            if xmax is not None:
                xmax = np.log10(xmax)
    
    if log is not None:
        if str.find(log, 'y') != -1:
            if ymin is not None:
                ymin = np.log10(ymin)
            if ymax is not None:
                ymax = np.log10(ymax)
                
    
    if xmin is not None and xmax is not None:
      if xmin == xmax:
          xmin = xmin - 0.05 * xmin
          xmax = xmax + 0.05 * xmax
      else:
          xmin = xmin - 0.05 * (xmax - xmin)
          xmax = xmax + 0.05 * (xmax - xmin)  
    
    if ymin is not None and ymax is not None:
      if ymin == ymax:
          ymin = ymin - 0.05 * ymin
          ymax = ymax + 0.05 * ymax
      else:
          ymin = ymin - 0.05 * (ymax - ymin)
          ymax = ymax + 0.05 * (ymax - ymin)
    
    
    if log is not None:
        if str.find(log, 'x') != -1:
            xmin = 10**xmin
            xmax = 10**xmax
    
    if log is not None:
        if str.find(log, 'y') != -1:
            ymin = 10**ymin
            ymax = 10**ymax


  #####################################
  # second : set log log or lin log
  #####################################


  if log is not None:
      if str.find(log, 'x') != -1 and str.find(log, 'y') != -1:
          ax.loglog()
      elif str.find(log, 'x') != -1:
          ax.semilogx()
      else:
          ax.semilogy()

  plt.axis([xmin, xmax, ymin, ymax])


  if log is None:
      log = 'None'

  #####################################
  # third : adapt ticks
  #####################################
  
  if str.find(log, 'x') == -1:
      ax.xaxis.set_major_locator(plt.AutoLocator())
      x_major = ax.xaxis.get_majorticklocs()
      dx_minor = (x_major[-1] - x_major[0]) / (len(x_major) - 1) / 5.
      ax.xaxis.set_minor_locator(plt.MultipleLocator(dx_minor))


  if str.find(log, 'y') == -1:
      ax.yaxis.set_major_locator(plt.AutoLocator())
      y_major = ax.yaxis.get_majorticklocs()
      dy_minor = (y_major[-1] - y_major[0]) / (len(y_major) - 1) / 5.
      ax.yaxis.set_minor_locator(plt.MultipleLocator(dy_minor))









##########################################################################
#
# Vector Cleaning
#
##########################################################################

def CleanVectors(x, y):
    '''
    remove bad values
    '''

    c = np.isfinite(x) * np.isfinite(y)
    x = np.compress(c, x)
    y = np.compress(c, y)

    return x.astype(float), y.astype(float)


def CleanVectorsForLogX(x, y):
    '''
    remove negative values
    '''

    c = (x > 0)
    x = np.compress(c, x)
    y = np.compress(c, y)

    return x.astype(float), y.astype(float)


def CleanVectorsForLogY(x, y):
    '''
    remove negative values
    '''

    c = (y > 0)
    x = np.compress(c, x)
    y = np.compress(c, y)

    return x.astype(float), y.astype(float)




##########################################################################
#
# The Colors class
#
##########################################################################


class ColorList():    
    '''
    Handle a list of colors
    '''

    def __init__(self, colormap=None, n=256, clist=None, reverse=False):
        '''
        Initialize with two modes :

        1) give number + eventually palette name
        2) give the list of colors
        '''

        if clist is not None:
            self.ls = clist
        else:
          if colormap is None:
            self.ls = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
          else:
            
            cmap = mpl.colormaps[colormap]

            if reverse:
              cmap = cmap.reversed()
          
            self.ls = []
          
            # set colors
            ii = np.linspace(0,255,n).astype(int)
            for i in ii:
              self.ls.append(cmap(i/255))

              
        self.i = 0



    def set(self, i):
        try:
            self.i = self.ls.index(i)
        except BaseException:
            pass

    def current(self):
        return self.ls[self.i]

    def __next__(self):
        self.i = self.i + 1
        if self.i == len(self.ls):
            self.i = 0
        return self.ls[self.i]

    def get(self):

        ls = self.ls[self.i]

        self.i = self.i + 1
        if self.i == len(self.ls):
            self.i = 0

        return ls



##########################################################################
#
# Data point class
#
##########################################################################


class DataPoints():

    def __init__(
            self,
            x,
            y,
            z=None,
            yerr=None,
            color='k',
            linestyle='-',
            pointmarker='.',
            label='',
            tpe='line',
            linewidth=1):

        self.x = x
        self.y = y
        self.z = z
        self.yerr = yerr

        self.color = color
        self.linestyle = linestyle
        self.linewidth = linewidth
        self.pointmarker = pointmarker
        self.label = label

        self.tpe = tpe

    def reduc(self, rf, n=None, mn=None, mx=None, dx=None):

        if dx is not None:
            n = int((max(self.x) - min(self.x)) / dx)
            yh, xh = np.histogram(
                self.x, n, (min(
                    self.x), max(
                    self.x)), weights=self.y)
        else:
            if mn is None and mx is None and n is None:
                yh, xh = np.histogram(self.x, int(
                    len(self.x) / float(rf)), (min(self.x), max(self.x)), weights=self.y)
            else:
                yh, xh = np.histogram(self.x, n, (mn, mx), weights=self.y)

        xh = xh[:-1]

        self.x = xh
        self.y = yh

    def integrate(self):
        self.y = add.accumulate(self.y)

    def interpolate(self, xi):

        n = len(self.x)
        s1 = n - np.sqrt(2 * n)
        s2 = n + np.sqrt(2 * n)

        tck = interpolate.fitpack.splrep(self.x, self.y, s=s2, k=2)
        yi = interpolate.fitpack.splev(xi, tck)

        self.xi = xi
        self.yi = yi

    def derive(self):

        dx = self.x[1:] - self.x[0:-1]
        dy = self.y[1:] - self.y[0:-1]

        self.x = self.x[1:]
        self.y = dy / dx

        c = np.isfinite(self.y)

        self.x = np.compress(c, self.x)
        self.y = np.compress(c, self.y)

    def xy(self,):
        return self.x, self.y

    def get_x(self,):
        return self.x

    def get_y(self,):
        return self.y





def LegendFromDataPoints(ax,datas=None, loc=None, protect=True, opt=None):

    if opt is None:
        ncol = 1
    else:
        ncol = opt.legend_ncol

    if opt is not None and loc is None:
        if hasattr(opt, "legend_loc"):
            loc = opt.legend_loc

    if datas is not None:
        tags = []
        for data in datas:
            if protect:
                txt = data.label.replace("_", "\_")
            else:
                txt = data.label

            tags.append("%s" % txt)
        ax.legend(tags, loc=loc, ncol=ncol)
    else:
        ax.legend(loc=loc, ncol=ncol)


##########################################################################
#
# PALETTES FUNCTIONS
#
##########################################################################

def GetPalette(name='rainbow4', directory=None):
    """list of available palettes:
       aips0 backgr bgyrw blue blulut color green heat idl2 idl4
       idl5 idl6 idl11 idl12 idl14 idl15 isophot light manycol
       pastel rainbow rainbow1 rainbow2 rainbow3 rainbow4 ramp
       random random1 random2 random3 random4 random5 random6
       real red smooth smooth1 smooth2 smooth3 staircase stairs8
       stairs9 standard
    """
    from ..parameters import PALETTEDIR

    if directory is None:
      directory = os.path.join(PALETTEDIR)

    _name = os.path.normpath((os.path.join(directory, name)))

    _r = []
    _g = []
    _b = []

    try:
        _f = open(_name)
    except BaseException:
        return
    _f.readline()
    for i in range(255):
        line = _f.readline()
        line = str.split(line)
        _r.append(float(line[0]))
        _g.append(float(line[1]))
        _b.append(float(line[2]))
        del line

    _r = np.array(_r)
    _g = np.array(_g)
    _b = np.array(_b)
    _f.close()

    return np.transpose(np.array([_r, _g, _b])) / 255.



def GetColormap(name='rainbow4', directory=None, revesed=False):
    """return a matplolib color map from a palette
    """
    import matplotlib.colors as colors

    
    LUTSIZE = plt.rcParams['image.lut']

    palette = GetPalette(name, directory=directory)

    red = []
    green = []
    blue = []

    if not revesed:

        for i in range(len(palette)):
            r, g, b = palette[i][0], palette[i][1], palette[i][2]
            x = i / float(len(palette) - 1)
            red.append((x, r, r))
            green.append((x, g, g))
            blue.append((x, b, b))

    else:

        for i in range(len(palette)):
            r = palette[len(palette) - i -1][0]
            g = palette[len(palette) - i -1][1]
            b = palette[len(palette) - i -1][2]
            x = i / float(len(palette) - 1)
            red.append((x, r, r))
            green.append((x, g, g))
            blue.append((x, b, b))

    cmapdata = {'red': red, 'green': green, 'blue': blue}
    cmap = colors.LinearSegmentedColormap(name, cmapdata, LUTSIZE)

    return cmap



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

