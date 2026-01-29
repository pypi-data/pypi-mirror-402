#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      message.py
#  brief:     Defines the message class
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import inspect
import sys
    
bc = {}
bc["p"] = '\033[95m' # PINK  
bc["b"] = '\033[94m' # BLUE  
bc["g"] = '\033[92m' # GREEN 
bc["y"] = '\033[93m' # YELLOW
bc["r"] = '\033[91m' # RED   
bc["k"] = '\033[0m'  # BLACK   
bc["c"] = '\033[0;36m' # CYAN 

    
def message(msg,verbose=0,verbosity=1,level=0,isMaster=True,color=None):
  """
  Print a formatted message conditionally based on verbosity thresholds.

  This function checks the current application verbosity against the message
  threshold. If conditions are met, it inspects the call stack to provide
  context (function name, and optionally filename/line number at high
  verbosity) and prints to standard output.

  Parameters
  ----------
  msg : object
      The content to be printed. Will be converted to string.
  verbose : int, optional, default: 0
      The current operating verbosity level of the application. Higher values
      enable more output.
  verbosity : int, optional, default: 1
      The minimum threshold required to print this specific message. The
      message is skipped if `verbosity > verbose`.
  level : int, optional, default: 0
      The stack depth index used to retrieve calling frame information with
      `inspect.stack()`. Use 0 for the immediate caller; increase if wrapping
      this function.
  isMaster : bool, optional, default: True
      Flag indicating if the current process is deemed the "master" process.
      If False, output is suppressed. Used primarily in parallel/MPI
      environments.
  color : str or None, optional, default: None
      A key corresponding to an entry in a global dictionary named `bc`
      containing ANSI escape codes. If provided, the output gets wrapped in
      the specified color and reset with `bc["k"]`.

  Returns
  -------
  None

  Notes
  -----
  This function requires the standard library `inspect` module to be imported.
  It also relies on the existence of a global dictionary named `bc` (base
  colors) containing ANSI color codes, specifically needing a "k" key for
   color reset.
  """  
  
  
  if verbosity > verbose:
    return
  
  if isMaster:
  
    frame = inspect.stack()[level]
    
    txt = str(msg)
    
    if verbose >= 4:
      txt = '%s ("%s", line %d): %s'%(frame.function,frame.filename,frame.lineno,msg)
    else:
      txt = "%s: %s"%(frame.function,msg)
    
    
    # add color
    if color is not None:
      txt = bc[color] + txt + bc["k"]
    
    # print the text
    print(txt)
    
    
    
def todo_warning(verbose=1, color='c'):
  """
  Print a prominent warning and optional traceback for incomplete functions.

  This function serves as a loud reminder for developers when they hit a
  part of the code that hasn't been fully implemented yet. It utilizes global
  ANSI color codes for emphasis.

  Parameters
  ----------
  verbose : int, optional, default: 1
      Control the verbosity level of the warning.
      If 0, the function returns immediately without printing.
      If > 0, prints a framed warning message to standard output.
      If > 1, additionally calculates and prints the current stack traceback
      (excluding the call to this function itself).
  color : str, optional, default: 'c'
      A key corresponding to an entry in a global dictionary named `bc`
      containing ANSI escape codes used to color the warning text.

  Returns
  -------
  None

  Notes
  -----
  This function relies on the existence of a global dictionary named `bc`
  (base colors) containing ANSI color codes, specifically needing the provided
  `color` key and a "k" key for color reset.
  """
  import traceback

  if verbose == 0:
      return

  else:
      print(bc[color] + "================================================================================="+ bc["k"])
      print(bc[color] + "TODO WARNING: A function that has not been fully written has been called."+ bc["k"])
      print(bc[color] + "TODO WARNING: This is most likely no reason to worry, but hopefully this message "+ bc["k"])
      print(bc[color] + "TODO WARNING: will annoy the developers enough to start clean their code up."+ bc["k"])
      print(bc[color] + "TODO WARNING: Meanwhile, you can just carry on doing whatever you were up to."+ bc["k"])

      if verbose > 1:
          print(bc[color] + "TODO WARNING: Printing traceback:"+ bc["k"])

          st = traceback.extract_stack()
          reduced_stack = st[:-1]  # skip call to traceback.extract_stack() in stack trace
          traceback.print_list(reduced_stack)

          print(bc[color] + "TODO WARNING: End of (harmless) warning."+ bc["k"])
      
      print(bc[color] + "================================================================================="+ bc["k"])
      
  return
  
  
    
    
    
    
    



