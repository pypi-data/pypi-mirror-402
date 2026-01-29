###########################################################################################
#  package:   Mockimgs
#  file:      scoords.py
#  brief:     scoords class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


from astropy import units
import numpy as np


SKY = "sky"
FOC = "focal plane"
UNI = "universe"


def checkUnit(x,unit,msg=""):
  """
  check the validity of the focal
  """
  if x is None:
    raise ValueError("The value x cannot be None.\n%s"%msg) 
  
  if type(x) is not units.quantity.Quantity:
    raise TypeError("The value x must be of type astropy.units.quantity.Quantity.\n%s"%msg)
  
  if not x.unit.is_equivalent(unit):
    raise ValueError("The unit of the x value must be %s. Found %s.\n%s"%(unit,x.unit,msg))
  
  return True    



def checkDistance(distance):
  return checkUnit(distance,units.cm,msg="The distance must be defined properly.")

def checkFocal(focal):
  return checkUnit(focal,units.cm,msg="The focal must be defined properly.")


  

class sCoords(units.quantity.Quantity):
  """
  This class which derive from the astropy units.quantity.Quantity class
  allows to define a quantity either on a focal plane, the sky or as physical quantities in the universe.
  Providing a focal plane or a distance it allow for a conversion between these three reference frames.
  
  example:
  
  from astropy import units as u
  import numpy as np
  from pNbody.Mockimgs.scoords import sCoords    

  x = sCoords(np.array([1])*u.arcsec,ref="sky")
  x.change_ref("sky")
  x.change_ref("focal plane",focal=1000*u.cm)
  x.change_ref("universe",distance=35*u.Mpc)
  
  x = sCoords(np.array([1])*u.cm,ref="focal plane")
  x.change_ref("universe",distance=35*u.Mpc,focal=1000*u.cm)
  
  """

  def __new__(cls,value,unit=None,dtype=np.inexact,copy=True,order=None,subok=False,ndmin=0,ref=None):  
    new = super().__new__(cls,value,unit=None,dtype=np.inexact,copy=True,order=None,subok=False,ndmin=0)
    # add a reference
    new.ref = ref
    return new

  def to_string(self, unit=None, precision=None, format=None, subfmt=None):
      """
      Generate a string representation of the quantity and its unit.

      The behavior of this function can be altered via the
      `numpy.set_printoptions` function and its various keywords.  The
      exception to this is the ``threshold`` keyword, which is controlled via
      the ``[units.quantity]`` configuration item ``latex_array_threshold``.
      This is treated separately because the numpy default of 1000 is too big
      for most browsers to handle.

      Parameters
      ----------
      unit : unit-like, optional
          Specifies the unit.  If not provided,
          the unit used to initialize the quantity will be used.

      precision : number, optional
          The level of decimal precision. If `None`, or not provided,
          it will be determined from NumPy print options.

      format : str, optional
          The format of the result. If not provided, an unadorned
          string is returned. Supported values are:

          - 'latex': Return a LaTeX-formatted string

          - 'latex_inline': Return a LaTeX-formatted string that uses
            negative exponents instead of fractions

      subfmt : str, optional
          Subformat of the result. For the moment, only used for
          ``format='latex'`` and ``format='latex_inline'``. Supported
          values are:

          - 'inline': Use ``$ ... $`` as delimiters.

          - 'display': Use ``$\\displaystyle ... $`` as delimiters.

      Returns
      -------
      str
          A string with the contents of this Quantity
      """
      
      refstr = " on "+str(self.ref)
      
      if unit is not None and unit != self.unit:
          return self.to(unit).to_string(
              unit=None, precision=precision, format=format, subfmt=subfmt
          )

      formats = {
          None: None,
          "latex": {
              None: ("$", "$"),
              "inline": ("$", "$"),
              "display": (r"$\displaystyle ", r"$"),
          },
      }
      formats["latex_inline"] = formats["latex"]
      
      if format not in formats:
          raise ValueError(f"Unknown format '{format}'")
      elif format is None:
          if precision is None:
              # Use default formatting settings
              return f"{self.value}{self._unitstr:s}{refstr}"
          else:
              # np.array2string properly formats arrays as well as scalars
              return (
                  np.array2string(self.value, precision=precision, floatmode="fixed")
                  + self._unitstr + refstr
              )

       
      # else, for the moment we assume format="latex" or "latex_inline".

      # Set the precision if set, otherwise use numpy default
      pops = np.get_printoptions()
      format_spec = f".{precision if precision is not None else pops['precision']}g"

      def float_formatter(value):
          return Latex.format_exponential_notation(value, format_spec=format_spec)

      def complex_formatter(value):
          return "({}{}i)".format(
              Latex.format_exponential_notation(value.real, format_spec=format_spec),
              Latex.format_exponential_notation(
                  value.imag, format_spec="+" + format_spec
              ),
          )
      
      # The view is needed for the scalar case - self.value might be float.
      latex_value = np.array2string(
          self.view(np.ndarray),
          threshold=(
              conf.latex_array_threshold
              if conf.latex_array_threshold > -1
              else pops["threshold"]
          ),
          formatter={
              "float_kind": float_formatter,
              "complex_kind": complex_formatter,
          },
          max_line_width=np.inf,
          separator=",~",
      )

      latex_value = latex_value.replace("...", r"\dots")

      # Format unit
      # [1:-1] strips the '$' on either side needed for math mode
      if self.unit is None:
          latex_unit = _UNIT_NOT_INITIALISED
      elif format == "latex":
          latex_unit = self.unit._repr_latex_()[1:-1]  # note this is unicode
      elif format == "latex_inline":
          latex_unit = self.unit.to_string(format="latex_inline")[1:-1]

      delimiter_left, delimiter_right = formats[format][subfmt]


      return rf"{delimiter_left}{latex_value} \; {latex_unit}{delimiter_right}"


  def __str__(self):
    return self.to_string()

  def __repr__(self):
      prefixstr = "<" + self.__class__.__name__ + " "
      arrstr = np.array2string(self.view(np.ndarray), separator=", ", prefix=prefixstr)
      refstr = "on "+str(self.ref)
      return f"{prefixstr}{arrstr}{self._unitstr:s} {refstr}>"


  # Arithmetic operations
  #def __mul__(self, other):
  #  """Multiplication between `Quantity` objects and other objects."""
  #  if isinstance(other, (UnitBase, str)):
  #    try:
  #      return self._new_view(self.value.copy(), other * self.unit, propagate_info=False)
  #    except UnitsError:  # let other try to deal with it
  #      return NotImplemented
  #  
  #  return super().__mul__(other)





  def to(self, unit, equivalencies=[], copy=True):
    new = super().to(unit, equivalencies, copy)
    # add a reference
    new.ref = self.ref
    return new


  def change_ref(self,ref,focal=None,distance=None):
    """
    operate some conversions allowing to change the reference system
    """
    
    if self.ref==FOC:

      if   ref==FOC:
        return sCoords(self.copy(),ref=FOC)
              
      elif ref==SKY:
        checkFocal(focal)
        return sCoords(np.arctan(self.copy()/focal),ref=SKY)
        
      elif ref==UNI:
        checkDistance(distance)
        checkFocal(focal)      
        return sCoords(self.copy()/focal*distance,ref=UNI) 
            
    
    elif self.ref==SKY:
      
      if   ref==FOC:
        checkFocal(focal)
        return sCoords(focal*np.tan(self.copy()),ref=FOC)        
      
      elif ref==SKY:
        return sCoords(self.copy(),ref=SKY)
        
      elif ref==UNI:
        checkDistance(distance)
        return sCoords(distance*np.tan(self.copy()),ref=UNI)
      
    elif self.ref==UNI:
      
      if   ref==FOC:
        checkDistance(distance)
        checkFocal(focal)       
        return sCoords(self.copy()/distance*focal,ref=FOC)
      
      elif ref==SKY:
        checkDistance(distance)
        return sCoords(np.arctan(self.copy()/distance),ref=SKY)
        
      elif ref==UNI:
        return sCoords(self.copy(),ref=UNI)      
  
      
