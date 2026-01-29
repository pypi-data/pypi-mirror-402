''' 
 @package   pNbody
 @file      liblog.py
 @brief     Log File
 @copyright GPLv3
 @author    Yves Revaz <yves.revaz@epfl.ch>
 @section   COPYRIGHT  Copyright (C) 2017 EPFL (Ecole Polytechnique Federale de Lausanne)  LASTRO - Laboratory of Astrophysics of EPFL

 This file is part of pNbody. 
'''

import glob
import os
import sys
import string
import time
import traceback


try:
  import Tkinter as tk
  is_tk = True
except ImportError:
  is_tk = False 
  
  
###########################

class Log:

###########################

  '''
  a log class
  '''


  def __init__(self,directory,show='yes',append='no',filename=None,logframe=None):
    '''
    open the log file
    '''
    
    self.logframe = None
    self.filename = filename
        
    if show == 'yes':
      self.show = 1
    else:
      self.show = 0
      
    if not os.path.exists(directory):
      os.makedirs(directory)      
    
    t = time.localtime()
    if self.filename is None:
      #self.filename = "%00004d-%002d-%002dT%002d:%002d:%002d.log"%(t[0],t[1],t[2],t[3],t[4],t[5])
      self.filename = "log.dat"
    
    self.filename = os.path.join(directory,self.filename)
    
    if append == 'yes':
      self.f = open(self.filename,'a')
    else:
      self.f = open(self.filename,'w')   


  def write(self,line,name=None):
    '''
    write a line
    '''
        
    if self.show:
        
      if self.logframe is None:
        print(line)
      else:
        line = line.rstrip()
        line = line+'\n'

    if is_tk:
      self.logframe.config(state=tk.NORMAL)
      self.logframe.insert(tk.INSERT,line)
      self.logframe.yview(tk.MOVETO,1) 
      self.logframe.config(state=tk.DISABLED)
    else:
      print(line)  


    '''
    t = time.localtime()
    tnow = "%00004d-%002d-%002dT%002d:%002d:%002d"%(t[0],t[1],t[2],t[3],t[4],t[5])

    if name is not None:
       self.f.write("%s %s %s\n"%(tnow,name,line))     
    else:  
      self.f.write("%s %s\n"%(tnow,line)) 
    
    self.f.flush()
    '''
 
  def write_traceback(self):
    
    traceback.print_tb(sys.exc_info()[2],file=self.f)
    self.write_content()
      
  def write_content(self):
  
    if self.show:
      self.f.close()

      self.f = open(self.filename,'r')
      lines = self.f.readlines()
      self.f.close()
     
      for line in lines:
        self.write(line) 
	
      self.f = open(self.filename,'w')	
    

  def clear(self):
    if self.show:
      if self.logframe is not None:
        
        if is_tk:
          self.logframe.config(state=tk.NORMAL)
          self.logframe.delete(1.0,tk.END)
          #self.logframe.yview(MOVETO,1) 
          self.logframe.config(state=tk.DISABLED)
        else:
          pass
    
  def close(self):
    '''
    close the file
    '''
    
    self.f.close()
    
    
    
