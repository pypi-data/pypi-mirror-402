###########################################################################################
#  package:   Mockimags
#  file:      object.py
#  brief:     telescope class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

from astropy import units as u
from .los import LineOfSights
from .spoints import sPoints
from scipy.spatial.transform import Rotation
from pNbody import *
import pickle

class Object(Nbody):
  """
  Define an object "object". the latter derives from the Nbody class
  """
  
  def __init__(self,name=None,filename=None,unitsfile=None,nb=None,adjust_coords='remove_identical',
          distance=1*u.Mpc,unit=u.kpc,ref="universe",los=LineOfSights(),rsp_opts={"mode":None,"fac":1},
          ftype='gh5',verbose=0,local=False,status='old'):

    # init an empty object
    super().__init__(ftype=ftype,verbose=verbose,local=local,status=status)

    # additional parameters
    self.name      = name
    self.filename  = filename
    self.distance  = distance
    self.unitsfile = unitsfile
    self.verbose   = verbose
    self.ftype     = ftype

    self.unit     = unit
    self.ref      = ref

    #if adjust_coords is not None:
    #    # APC: optionally remove particles with identical radii. This was
    #    # APC: a hack to work around limitiations of the neighbor-finding
    #    # APC: tree code.
    #    self._remove_identical_coords = 'remove_identical' in adjust_coords
    #    if self._remove_identical_coords:
    #        self.message('WARNING: will remove particles with identical 3D radii')

    # line of sights
    self.los      = los
    # rsp (smoothing options)    
    self.rsp_opts = rsp_opts
        
    # line of sight idx
    self.los_idx  = 0
    
    
    # link towards an instrument
    self.instrument = None
    
    # test nb
    if nb is not None:
      raise ValueError("The option 'nb' is no longer supported.")

  
  def open(self,getAgeMH=False):
    '''  
    Open the N-body model and eventually compute missing quantities. 
    '''  

    if self.filename is not None:
      msg = 'Reading input file(s): {:s}'.format(str(self.filename))
      message.message('Reading input file(s): {:s}'.format(str(self.filename)))
    else:
      return None  
    
    if self.unitsfile is not None:
      message.message('Reading units file: {:s}'.format(str(self.unitsfile)))

    # now open the file
    super().__init__(p_name=self.filename,unitsfile=self.unitsfile,ftype=self.ftype,verbose=self.verbose)
    
    # Remove particles with identical 3D radii
    # APC: This is a hack to work around a limitation of the tree
    # APC: code, which can't cope with identical coordiantes.
    #if self._remove_identical_coords:
    #    self.warning('WARNING: excluding particles with identical 3D radii')
    #    n_before = len(self.rxyz())
    #    u,idx = np.unique(self.rxyz(),return_index=True)
    #    n_after = len(u)
    #    self = self.selectp(lst=self.num[idx])
    #    self.warning('WARNING: removed {:d} of {:d} particles with identical 3D radii'.format(n_before-n_after,n_before))

    
    if not self.has_array("rsp"):
      self.ComputeRsp(5)

    if getAgeMH:

      if not self.has_array("age"):
        # compute Age [in Gyr]
        self.message("Compute ages...")
        self.age = self.StellarAge(units="Gyr")
          
      # compute the metallicity
      if not self.has_array("mh"):   
        self.mh = self.MetalsH()
    

  def info(self):
    """
    give info on the telescope
    """  
    print("object name        : %s"%self.name)
    print("object filename    : %s"%self.filename)
    print("object distance    : %s"%self.distance)
    print("object los         : %s"%self.los.list())


  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters
    """
    params = {}

    if fmt=="fits":
      params["OBJ_NAME"]           = (self.name,"Object name")
    else:
      params["object_name"]        = self.name
    
    if fmt=="fits":
      params["OBJ_DIST"]           = (self.distance.to(u.Mpc).value,"Object distance in Mpc")
    else:
      params["object_distance"]    = self.distance

    if fmt=="fits":
      params["OBJ_NLOS"]           = (self.los.n(),"Number of line of sights used")
    else:    
      params["object_nlos"]        = self.los.n()
      
    if fmt=="fits":
      los = self.los.get()
      params["OBJ_LOS"]            = ("[%5.3f,%5.3f,%5.3f]"%(los[0],los[1],los[2]),"line of sight used")
    else:    
      params["object_nlos"]        = self.los.get()     
    
    
    if fmt=="fits":
      params["RSPMODE"]            = (str(self.rsp_opts["mode"]),"RSP mode")
      if self.rsp_opts["mode"]=="const":  
        params["RSPVAL"]           = (self.rsp_opts["val"],"RSP value")
      elif self.rsp_opts["mode"]=="arctan":
        params["RSPMAX"]           = (self.rsp_opts["max"],"RSP max")
        params["RSPSCA"]           = (self.rsp_opts["sca"],"RSP scale")
      elif self.rsp_opts["mode"]=="ln":
        params["RSPSCA"]           = (self.rsp_opts["sca"],"RSP scale")
      else:
        params["RSPFAC"]           = (self.rsp_opts["fac"],"RSP factor")

    else:  
      params["rsp_opts"]           = self.rsp_opts
    
    
    # record time
    
    try:
      tnow = self.Time(units="Gyr")
    except:  
      tnow = -1
      
    if fmt=="fits":  
      params["OBJ_TNOW"]            = (str(tnow),"Simulation Time [Gyr]")
    else:  
      params["obj_tnow "]           = tnow      
    
    
    return params



  def set_los(self,los):
    """
    set line of sights
    """
    self.los = los 

  def set_rsp_opts(self,rsp_opts):
    """
    set rsp options
    """
    self.rsp_opts = rsp_opts



  def getDistance(self):
    """
    return the object distance
    """
    return self.distance
  

  def getFocal(self):
    """
    if defined, get the instrument focal
    """
    if self.instrument is not None:
      return self.instrument.getFocal()
    else:
      raise ValueError("no instrument defined. Cannot get the telescope focal.")
    
    

  def ScaleSmoothingLength(self,x,opt):
    """
    Scale the smoothing length.
    opt : a dictionary
    """
    
    if opt["mode"]=="const":  
      #print("smoothing const: %g"%opt["val"])
      rsp =  np.ones(len(x))* opt["val"]
    
    elif opt["mode"]=="arctan":
      #print("smoothing arctan : %g %g"%(opt["max"],opt["sca"]))
      xmax  = opt["max"]
      scale = opt["sca"]
      rsp =  xmax/(np.pi/2) *np.arctan(x/scale)
  
    elif opt["mode"]=="ln":
      rsp = opt["sca"] * np.log(x/opt["sca"]+1)
    
    else:
      rsp = x
     
    # finally scale with respect to the frsp factor
    rsp = rsp *  opt["fac"]
    
    return rsp
  

  def align(self,pos,axis,axis_ref=[0,0,1]):
    """
    rotate the model with a rotation that align axis with axis_ref
    
    pos      : a set of positions
    axis     : the axis
    axis_ref : the reference axis
    """
    axis1 = axis_ref
    axis2 = axis

    a1 = np.array(axis1, float)
    a2 = np.array(axis2, float)

    a3 = np.array([0, 0, 0], float)
    a3[0] = a1[1] * a2[2] - a1[2] * a2[1]
    a3[1] = a1[2] * a2[0] - a1[0] * a2[2]
    a3[2] = a1[0] * a2[1] - a1[1] * a2[0]

    n1 = np.sqrt(a1[0]**2 + a1[1]**2 + a1[2]**2)
    n2 = np.sqrt(a2[0]**2 + a2[1]**2 + a2[2]**2)
    angle = -np.arccos(np.inner(a1, a2) / (n1 * n2))

    if angle==0:
      return pos
      
    # set the norm of a3 to be angle
    norm = np.sqrt(a3[0]**2 + a3[1]**2 + a3[2]**2)
    a3 = a3/norm*angle  
      
    # create the rotation matix
    R = Rotation.from_rotvec(a3)
    
    # do the rotation
    pos = R.apply(pos)
    
    return pos



    
  def set_for_exposure(self):
    '''
    Set the object for exposure.
    Rotate according to a given los.
    Scale according to a given distance.
    Initial values of the model are modified.
    '''
        
    
    ###################################
    # pos
    
    if self.has_array("pos"):
    
      # rotate
      self.pos = self.align(self.pos,axis=self.los.get())  
      
      # transform in appropriate units
      self.pos  = self.Pos(units="kpc")
        
      x = self.pos[:,0] * u.kpc
      y = self.pos[:,1] * u.kpc 
      z = self.pos[:,2] * u.kpc
          
      # scale the model : kpc -> arcsec
      x = np.arctan(x/self.distance).to(u.arcsec).value
      y = np.arctan(y/self.distance).to(u.arcsec).value
      z = np.arctan(z/self.distance).to(u.arcsec).value
      
      # move back to pos
      self.pos = np.transpose((x,y,z))
      self.pos = self.pos.astype(np.float32)
  
  
    ###################################
    # rsp
    
    if self.has_array("rsp"):
  
      # scale the smoothing length
      self.rsp = self.ScaleSmoothingLength(self.rsp,self.rsp_opts)
    
      # scale : kpc -> arcsec
      self.rsp = self.rsp * u.kpc
      self.rsp = np.arctan(self.rsp/self.distance).to(u.arcsec).value
  
  
    ###################################
    # mass  
  
    if self.has_array("mass"):
      # set proper units
      self.mass = self.Mass(units="Msol")


  
  
  def x(self,mode=None,unit=None):
    """
    get x coordinates of the object
    we assume that x is in kpc
    """
    if mode is None or mode=="phys":
      val = self.pos[:,0]*u.kpc
      
    elif mode=="angle":
      val = np.arctan(self.x()/self.getDistance())
        
    elif mode=="detector":
      val = self.x()/self.getDistance()*self.getFocal()
    
    if unit is not None:
      val = val.to(unit)
    
    return val
      

  def y(self,mode=None,unit=None):
    """
    get y coordinates of the object
    we assume that y is in kpc
    """
    if mode is None or mode=="phys":
      val = self.pos[:,1]*u.kpc
      
    elif mode=="angle":
      val = np.arctan(self.y()/self.getDistance())
        
    elif mode=="detector":
      val = self.y()/self.getDistance()*self.getFocal()
    
    if unit is not None:
      val = val.to(unit)
    
    return val
      
  
  def getPoints(self):
    
    # assume kpc here
    xs = self.pos[:,0]*self.unit
    ys = self.pos[:,1]*self.unit
    
    pts = sPoints(xs,ys,ref=self.ref)
    
    return pts    
        
        

  def draw(self,ax,mode=None,unit=None):
    """
    draw in matplotlib
    do a simple scatter plot
    """

    focal    = self.getFocal()
    distance = self.getDistance()
    
    pts = self.getPoints()
    xs = pts.x(mode=mode,unit=unit,focal=focal,distance=distance)
    ys = pts.y(mode=mode,unit=unit,focal=focal,distance=distance)
      
    ax.scatter(xs,ys,s=2)

    









class oldObject():
  '''
  Define the object class.
  '''
  
  def __init__(self,name=None,filename=None,unitsfile=None,nb=None,adjust_coords='remove_identical',
          distance=1*u.Mpc,unit=u.kpc,ref="universe",los=LineOfSights(),rsp_opts={"mode":None,"fac":1}):
    """
    adjust_coords: string or iterable checked for the following values
        (can be combined):

        'remove' : remove particles with identical 3D radii;
    """
    self.name      = name
    self.filename  = filename
    self.distance  = distance
    self.unitsfile = unitsfile

    self.unit     = unit
    self.ref      = ref

    if adjust_coords is not None:
        # APC: optionally remove particles with identical radii. This was
        # APC: a hack to work around limitiations of the neighbor-finding
        # APC: tree code.
        self._remove_identical_coords = 'remove_identical' in adjust_coords
        if self._remove_identical_coords:
            message.message('WARNING: will remove particles with identical 3D radii',verbosity=1,level=2,color="r")

    # line of sights
    self.los      = los
    # rsp (smoothing options)    
    self.rsp_opts = rsp_opts
        
    # line of sight idx
    self.los_idx  = 0
    
    # if nb is given, make it global
    self.nb = nb
    
    # link towards an instrument
    self.instrument = None
    
    

  def info(self):
    """
    give info on the telescope
    """  
    print("object name        : %s"%self.name)
    print("object filename    : %s"%self.filename)
    print("object distance    : %s"%self.distance)
    print("object los         : %s"%self.los.list())


  def get_parameters(self,fmt=None):
    """
    return a dictionary containing usefull parameters
    """
    params = {}
    
    if fmt=="fits":
      params["OBJ_DIST"]           = (self.distance.to(u.Mpc).value,"Object distance in Mpc")
    else:
      params["object_distance"]    = self.distance

    if fmt=="fits":
      params["OBJ_NLOS"]           = (self.los.n(),"Number of line of sights used")
    else:    
      params["object_nlos"]        = self.los.n()
      
    if fmt=="fits":
      los = self.los.get()
      params["OBJ_LOS"]            = ("[%5.3f,%5.3f,%5.3f]"%(los[0],los[1],los[2]),"line of sight used")
    else:    
      params["object_nlos"]        = self.los.get()     
    
    
    if fmt=="fits":
      params["RSPMODE"]            = (str(self.rsp_opts["mode"]),"RSP mode")
      if self.rsp_opts["mode"]=="const":  
        params["RSPVAL"]           = (self.rsp_opts["val"],"RSP value")
      elif self.rsp_opts["mode"]=="arctan":
        params["RSPMAX"]           = (self.rsp_opts["max"],"RSP max")
        params["RSPSCA"]           = (self.rsp_opts["sca"],"RSP scale")
      elif self.rsp_opts["mode"]=="ln":
        params["RSPSCA"]           = (self.rsp_opts["sca"],"RSP scale")
      else:
        params["RSPFAC"]           = (self.rsp_opts["fac"],"RSP factor")

    else:  
      params["rsp_opts"]           = self.rsp_opts
    
    
    return params



  def set_los(self,los):
    """
    set line of sights
    """
    self.los = los 

  def set_rsp_opts(self,rsp_opts):
    """
    set rsp options
    """
    self.rsp_opts = rsp_opts

  def open(self):
    '''  
    Open the N-body model and eventually compute missing quantities. 
    '''  
    if self.filename is not None:
      msg = 'Reading input file(s): {:s}'.format(str(self.filename))
      message.message('Reading input file(s): {:s}'.format(str(self.filename)))
    else:
      return None  
    
    if self.unitsfile is not None:
      message.message('Reading units file: {:s}'.format(str(self.unitsfile)))

    # open the object
    nb = Nbody(self.filename,unitsfile=self.unitsfile)

    # Remove particles with identical 3D radii
    # APC: This is a hack to work around a limitation of the tree
    # APC: code, which can't cope with identical coordiantes.
    if self._remove_identical_coords:
        message.message('WARNING: excluding particles with identical 3D radii',verbosity=1,level=2,color="r")
        n_before = len(nb.rxyz())
        u,idx = np.unique(nb.rxyz(),return_index=True)
        n_after = len(u)
        nb = nb.selectp(lst=nb.num[idx])
        message.message('WARNING: removed {:d} of {:d} particles with identical 3D radii'.format(n_before-n_after,n_before),verbosity=1,level=2,color="r")

    if not nb.has_array("rsp"):
      nb.ComputeRsp(5)

    if not nb.has_array("age"):
      # compute Age [in Gyr]
      print("Compute ages...")
      nb.age = nb.StellarAge(units="Gyr")
      print("done.")
  
  
    # compute the metallicity
    if not nb.has_array("mh"):   
      nb.mh = nb.MetalsH()
    
    # make global
    self.nb = nb  
  

  def getDistance(self):
    """
    return the object distance
    """
    return self.distance
  

  def getFocal(self):
    """
    if defined, get the instrument focal
    """
    if self.instrument is not None:
      return self.instrument.getFocal()
    else:
      raise ValueError("no instrument defined. Cannot get the telescope focal.")
    
    

  def ScaleSmoothingLength(self,x,opt):
    """
    Scale the smoothing length.
    opt : a dictionary
    """
    
    if opt["mode"]=="const":  
      #print("smoothing const: %g"%opt["val"])
      rsp =  np.ones(len(x))* opt["val"]
    
    elif opt["mode"]=="arctan":
      #print("smoothing arctan : %g %g"%(opt["max"],opt["sca"]))
      xmax  = opt["max"]
      scale = opt["sca"]
      rsp =  xmax/(np.pi/2) *np.arctan(x/scale)
  
    elif opt["mode"]=="ln":
      rsp = opt["sca"] * np.log(x/opt["sca"]+1)
    
    else:
      rsp = x
     
    # finally scale with respect to the frsp factor
    rsp = rsp *  opt["fac"]
    
    return rsp
  

  def align(self,pos,axis,axis_ref=[0,0,1]):
    """
    rotate the model with a rotation that align axis with axis_ref
    
    pos      : a set of positions
    axis     : the axis
    axis_ref : the reference axis
    """
    axis1 = axis_ref
    axis2 = axis

    a1 = np.array(axis1, float)
    a2 = np.array(axis2, float)

    a3 = np.array([0, 0, 0], float)
    a3[0] = a1[1] * a2[2] - a1[2] * a2[1]
    a3[1] = a1[2] * a2[0] - a1[0] * a2[2]
    a3[2] = a1[0] * a2[1] - a1[1] * a2[0]

    n1 = np.sqrt(a1[0]**2 + a1[1]**2 + a1[2]**2)
    n2 = np.sqrt(a2[0]**2 + a2[1]**2 + a2[2]**2)
    angle = -np.arccos(np.inner(a1, a2) / (n1 * n2))

    if angle==0:
      return pos
      
    # set the norm of a3 to be angle
    norm = np.sqrt(a3[0]**2 + a3[1]**2 + a3[2]**2)
    a3 = a3/norm*angle  
      
    # create the rotation matix
    R = Rotation.from_rotvec(a3)
    
    # do the rotation
    pos = R.apply(pos)
    
    return pos



    
  def set_for_exposure(self):
    '''
    Set the object for exposure.
    Rotate according to a given los.
    Scale according to a given distance.
    Initial values of the model are modified.
    '''
    
    nb = self.nb
    
    
    ###################################
    # pos
    
    if nb.has_array("pos"):
    
      # rotate
      nb.pos = self.align(nb.pos,axis=self.los.get())  
      
      # transform in appropriate units
      nb.pos  = nb.Pos(units="kpc")
        
      x = nb.pos[:,0] * u.kpc
      y = nb.pos[:,1] * u.kpc 
      z = nb.pos[:,2] * u.kpc
          
      # scale the model : kpc -> arcsec
      x = np.arctan(x/self.distance).to(u.arcsec).value
      y = np.arctan(y/self.distance).to(u.arcsec).value
      z = np.arctan(z/self.distance).to(u.arcsec).value
      
      # move back to pos
      nb.pos = np.transpose((x,y,z))
      nb.pos = nb.pos.astype(np.float32)
  
  
    ###################################
    # rsp
    
    if nb.has_array("rsp"):
  
      # scale the smoothing length
      nb.rsp = self.ScaleSmoothingLength(nb.rsp,self.rsp_opts)
    
      # scale : kpc -> arcsec
      nb.rsp = nb.rsp * u.kpc
      nb.rsp = np.arctan(nb.rsp/self.distance).to(u.arcsec).value
  
  
    ###################################
    # mass  
  
    if nb.has_array("mass"):
      # set proper units
      nb.mass = nb.Mass(units="Msol")


  
    # make global
    self.nb = nb
  
  
  def x(self,mode=None,unit=None):
    """
    get x coordinates of the object
    we assume that x is in kpc
    """
    if mode is None or mode=="phys":
      val = self.nb.x()*u.kpc
      
    elif mode=="angle":
      val = np.arctan(self.x()/self.getDistance())
        
    elif mode=="detector":
      val = self.x()/self.getDistance()*self.getFocal()
    
    if unit is not None:
      val = val.to(unit)
    
    return val
      

  def y(self,mode=None,unit=None):
    """
    get y coordinates of the object
    we assume that y is in kpc
    """
    if mode is None or mode=="phys":
      val = self.nb.y()*u.kpc
      
    elif mode=="angle":
      val = np.arctan(self.y()/self.getDistance())
        
    elif mode=="detector":
      val = self.y()/self.getDistance()*self.getFocal()
    
    if unit is not None:
      val = val.to(unit)
    
    return val
      
  
  def getPoints(self):
    
    # assume kpc here
    xs = self.nb.x()*self.unit
    ys = self.nb.y()*self.unit
    
    pts = sPoints(xs,ys,ref=self.ref)
    
    return pts    
        
        

  def draw(self,ax,mode=None,unit=None):
    """
    draw in matplotlib
    do a simple scatter plot
    """

    focal    = self.getFocal()
    distance = self.getDistance()
    
    pts = self.getPoints()
    xs = pts.x(mode=mode,unit=unit,focal=focal,distance=distance)
    ys = pts.y(mode=mode,unit=unit,focal=focal,distance=distance)
      
    ax.scatter(xs,ys,s=2)
