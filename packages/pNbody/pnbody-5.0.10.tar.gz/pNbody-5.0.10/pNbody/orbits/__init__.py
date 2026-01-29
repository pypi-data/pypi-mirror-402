#!/usr/bin/env python3
###########################################################################################
#  package:   orbits
#  file:      __init__.py
#  brief:     init file
#  copyright: GPLv3
#             Copyright (C) 2023 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@epfl.ch>
#
###########################################################################################

from scipy.integrate import solve_ivp
import numpy as np
from ..mass_models import MWPotential2014 as MW
from pNbody.orbits import integration_utils

from pNbody.mass_models import miyamoto as mn
from pNbody.mass_models import nfw
from pNbody.mass_models import powerSphericalCutoff as psc
from scipy import special

def ydot(t, y, rho_0, r_s, M_disk, a, b, alpha, r_c, amplitude, r_1, f_1,f_2, f_3, G, potential_choice, dynamical_friction, lnLambda, satellite_mass,df_core_radius,df_sigma_floor):
    """Function for solving the ODE for Newton equations : dy/dt = f(t)."""
    
    # y = (x y z v_x v_y v_z)
    position = y[0:3]
    velocity = y[3:]

    if potential_choice == "MWPotential2014":
      
        acceleration = - MW.GradPot(rho_0, r_s, M_disk,a, b, alpha, r_c, amplitude, r_1, f_1, f_2,f_3, position, t, G)
        
        if dynamical_friction:
          
          # Note: for velocities lower that the velocity dispersion sigma, the dynamical friction
          # timescale converges to a constant. This constant is equal to :
          # tau_th = sigma*sigma*sigma * 3/2 * np.sqrt(np.pi)*np.sqrt(2) 
          # tau_th = tau_th/(4*np.pi*G**2 *rho* lnLambda * satellite_mass)
          
          
          coeffs = [-2.96536595e-31,  8.88944631e-28, -1.18280578e-24,  9.29479457e-22,
                    -4.82805265e-19,  1.75460211e-16, -4.59976540e-14,  8.83166045e-12,
                    -1.24747700e-09,  1.29060404e-07, -9.65315026e-06,  5.10187806e-04,
                    -1.83800281e-02,  4.26501444e-01, -5.78038064e+00,  3.57956721e+01,
                     1.85478908e+02]
           
          r = np.sqrt(position[0]**2+position[1]**2+position[2]**2)
          z = position[2]
          R = np.sqrt(position[0]**2+position[1]**2)
          v = np.sqrt(velocity[0]**2+velocity[1]**2+velocity[2]**2)
          
                      
          sigma = np.polyval(coeffs, r)
          sigma = max(sigma,df_sigma_floor)
                    
          # the previous line is equivalent to
          #sigma=0
          #for i,coeff in enumerate(coeffs):
          #  sigma = sigma + coeffs[len(coeffs)-1-i]*r**i    

          
          X = v/(np.sqrt(2)*sigma)       
          amp1 =   special.erf(X) - (2*X/np.sqrt(np.pi)*np.exp(-X**2))          
          amp1  *= max(0,special.erf((r-df_core_radius)/df_core_radius/2.0));
          
                    
          # compute density
          rho_NFW = nfw.Density(rho_0, r_s, r, G)
          rho_MN = mn.Density(M_disk, a, b, R, z, G)
          rho_PSC = psc.Density(alpha, r_c, amplitude, r_1, r, G)
          rho =  f_1*rho_NFW + f_2*rho_MN + f_3*rho_PSC
          
          amp = -4*np.pi*G**2/v**3 *rho* lnLambda * amp1 * satellite_mass
                              
          if amp > 0:
            print("The dynamical force is negative ! amp=%g"%amp)
            exit()
          
          acceleration[0] = acceleration[0] + amp*velocity[0]
          acceleration[1] = acceleration[1] + amp*velocity[1]
          acceleration[2] = acceleration[2] + amp*velocity[2]
          
  

    elif potential_choice == "MWPotential2014_time_evolved":
        acceleration = - integration_utils.GradPot_time_evolved(rho_0, r_s, M_disk,a, b, alpha, r_c, amplitude,r_1, f_1, f_2, f_3, position, t, G)

    else:
        raise ValueError("Potential model not implemented")

    return np.array([velocity, acceleration]).ravel()
    
    
class orbit():

  def __init__(self,potential_arguments):
    
    self.potential_arguments = potential_arguments
    self.solution = None
    
  def CheckIntegrationIsDone(self):
    if self.solution is None:
      raise ValueError("Please integrate orbit before.")   
      
  
  def GetTimes(self):
    """
    return the times
    """
    self.CheckIntegrationIsDone()
    return self.solution.t

        
  def GetPositions(self):
    """
    return the positions
    """
    self.CheckIntegrationIsDone()
    return self.solution.y[0:3]
      
  def GetVelocities(self):
    """
    return the velocities
    """
    self.CheckIntegrationIsDone()
    return self.solution.y[3:]    
        
  
  def Integrate(self,t0,t1,y0,npoints):
    """
    Do the integration
    """
    t_eval =  np.linspace(t0,t1,npoints)
    self.solution = solve_ivp(ydot, [t0, t1], y0, t_eval=t_eval, args=self.potential_arguments, method="Radau")  
  



