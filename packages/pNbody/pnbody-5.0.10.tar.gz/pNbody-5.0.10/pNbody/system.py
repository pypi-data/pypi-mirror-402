###########################################################################################
#  package:   pNbody
#  file:      system.py
#  brief:     some useful system routines
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


def runCommand(cmd):
  """
  This function guarantee that the exit code will not be 0.
  Essential to really fail when os.system fails.
  """
  import os,sys
  
  exit_status = os.system(cmd)
  if exit_status != 0:
    print("runPythonScript: command\n\n%s\n\nfailed with exit status:"%cmd, exit_status) 
    sys.exit(sys.exit(os.waitstatus_to_exitcode(exit_status)))
