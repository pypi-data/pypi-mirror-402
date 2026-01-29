###########################################################################################
#  package:   Mockimgs
#  file:      parameters.py
#  brief:     Parameters class
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


class Parameters():
  '''
  Define a parameters container, a slightly extended simple object.
  
  Note: part of this file is a copy/paste of 
  the argparse.Namespace class
  '''
  
  def __init__(self, **kwargs):
    for name in kwargs:
        setattr(self, name, kwargs[name])
  
  
  def __repr__(self):
      type_name = type(self).__name__
      arg_strings = []
      star_args = {}
      for arg in self._get_args():
          arg_strings.append(repr(arg))
      for name, value in self._get_kwargs():
          if name.isidentifier():
              arg_strings.append('%s=%r' % (name, value))
          else:
              star_args[name] = value
      if star_args:
          arg_strings.append('**%s' % repr(star_args))
      return '%s(%s)' % (type_name, ', '.join(arg_strings))

  def _get_kwargs(self):
      return list(self.__dict__.items())

  def _get_args(self):
      return []

  def __eq__(self, other):
      if not isinstance(other, Namespace):
          return NotImplemented
      return vars(self) == vars(other)

  def __contains__(self, key):
      return key in self.__dict__
        
  
  def update_from_dic(self,dic):
    '''
    update the parameter from a dictionary
    '''       
    for p in dic:
      if not hasattr(self,p):
        msg = "parameter %s is not a valid parameter"%p
        raise NameError(msg)
      else:
        setattr(self,p,dic[p])      


  def update_from_options(self,opt,skip_None=False):
    '''
    update the parameter from options
    '''      
    for key in opt.__dict__: 
      if self.__contains__(key):
        if skip_None and getattr(opt,key) is None: continue
        # update the value    
        setattr(self,key,getattr(opt,key))
        
        


