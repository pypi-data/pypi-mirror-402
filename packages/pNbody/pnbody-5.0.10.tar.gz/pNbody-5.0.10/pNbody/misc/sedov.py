#!/usr/bin/python

import numpy as np
from matplotlib import pyplot as plt
import sys as sys


import scipy.integrate as integ
import scipy.optimize as opt


class Sedov:
  """
  This class is a routine to compute a sedov solution following the implementation of Kamm 2000
  """
  def __init__(self,E_0=10., rho_0=0.1,gamma=5./3., j=3., omega=0.,Np=100):
    
    print("initialisation of the Sedov computation")
    ###########################################
    # init the constants for the computations
    ###########################################

    self.E_0 	= E_0 	#injected energy
    self.rho_0 	= rho_0	#medium density
    self.gamma	= gamma	#adiabatic index
    self.j 		= j	#simulation dimension (1,2 or 3)
    self.omega 	= omega #power for the density profile \rho=\rho_0 r^{-\omega}
    self.Np		= Np 	#number of point for the spatial computation
    
    ##################################
    # compute other useful parameters
    ##################################
    
    
    self.a = (self.j + 2. - self.omega) * (self.gamma + 1.) / 4.
    
    self.b = (self.gamma + 1.) / (self.gamma - 1.)
    
    self.c = (self.j + 2. - self.omega) * self.gamma / 2.
    
    self.d = (self.j + 2. - self.omega) * (self.gamma + 1.) / (( self.j + 2. - self.omega) * (self.gamma + 1.) - 2. * (2. + self.j * (self.gamma - 1.)))
    
    self.e = (2. + self.j * (self.gamma - 1.))/ 2.
    
    
    self.alpha_0 = 2. / (self.j + 2. - self.omega)
    
    self.alpha_2 = - (self.gamma - 1.)/ ( 2.*(self.gamma-1.) + self.j - self.gamma * self.omega)
    
    self.alpha_1 = (self.j + 2. - self.omega) *self.gamma / (2. + self.j*(self.gamma-1.)) * ( 2. * (self.j*(2.-self.gamma) - self.omega)/ (self.gamma * (self.j + 2. - self.omega)**2.) - self.alpha_2)
    
    self.alpha_3 = (self.j - self.omega) / ( 2*(self.gamma-1) + self.j - self.gamma * self.omega)
    
    self.alpha_4 = (self.j + 2. - self.omega) * (self.j - self.omega)/ (self.j*(2.-self.gamma) - self.omega) * self.alpha_1
    
    self.alpha_5 = (self.omega * (1. + self.gamma) - 2.*self.j) / (self.j*(2.-self.gamma) - self.omega)
    
    #min and max velocity
    self.V_0 = 2. / (self.j + 2. - self.omega) / self.gamma
    self.V_2 = 4./ (j + 2. - self.omega) / (self.gamma + 1.)
    
    #compute the alpha coeff now
    self.compute_alpha()


  def J_1_int(self,V):
    # integrand of the J_1 energy integral
    return - (self.gamma + 1.) / (self.gamma - 1.) * V**2. * ( self.alpha_0 / V + self.alpha_2 * self.c / (self.c*V - 1. ) - self.alpha_1 * self.e / (1. - self.e * V) )* ( (self.a* V)**self.alpha_0 *(self.b * (self.c*V -1.))**self.alpha_2 * (self.d*(1. - self.e*V))**self.alpha_1)**(-(self.j+2.-self.omega)) * (self.b*(self.c*V - 1.))**self.alpha_3 * (self.d*(1. - self.e*V))**self.alpha_4 * (self.b*(1. - self.c/self.gamma*V))**self.alpha_5

  def J_2_int(self,V):
    # integrand of the J_1 energy integral
    return - (self.gamma + 1.) / (2. * self.gamma) * V**2. * (self.c* V - self.gamma)/ (1. - self.c*V) * ( self.alpha_0 / V + self.alpha_2 * self.c / (self.c*V - 1. ) - self.alpha_1 * self.e / (1. - self.e* V)) * ( (self.a* V)**self.alpha_0 *(self.b * (self.c*V -1.))**self.alpha_2 * (self.d*(1. - self.e*V))**self.alpha_1)**(-(self.j+2.-self.omega)) * (self.b*(self.c*V - 1.))**self.alpha_3 * (self.d*(1. - self.e*V))**self.alpha_4 * (self.b*(1. - self.c/self.gamma*V))**self.alpha_5

  def compute_alpha(self):
    #compute the alpha parameter in relation with energy conservation
    
    #compute the integrals form V_0 to V_2
    J_1 = integ.quad(self.J_1_int, self.V_0,self.V_2)
    J_2 = integ.quad(self.J_2_int, self.V_0,self.V_2)
    
    #compute the I's, WARNING FALSE for j=1 !!!!!! needs some delta
    I_1 = 2.**(self.j-2.) * ( np.pi * J_1[0])
    I_2 = 2.**(self.j-1.) / (self.gamma - 1.) * ( np.pi * J_2[0])
    
    self.alpha = I_1 + I_2

  def compute_rankin(self,t):
    #compute the values at the shock position with the rankin-hugenot boundary conditions
    self.r_2 	= (self.E_0 / (self.alpha * self.rho_0))**(1./(self.j+2.- self.omega)) * t**(2./(self.j + 2.- self.omega)) #radius of the shock front
    self.U 		= (2./ ( self.j + 2. - self.omega)) * self.r_2/t #velocity of the shock front
    self.v_2 	= (2. / (self.gamma + 1.))* self.U #velocity of the post-shock medium (just after the shock)
    self.rho_1 	= self.rho_0 * self.r_2**(-self.omega) #density of the initial medium
    self.rho_2 	= ((self.gamma + 1.) / (self.gamma - 1.)) * self.rho_1 #density of the post-shock medium (just after the shock)
    self.p_2 	= (2. / (self.gamma + 1.)) * self.rho_1 * self.U**2. #pressure just after the shock

  #here is some other useful parameter combination for the spatial solution
  def x_1(self,V):
    return self.a * V

  def x_2(self,V):
    return self.b * ( self.c*V - 1.)

  def x_3(self,V):
    return self.d*(1. - self.e*V)

  def x_4(self,V):
    return self.b*(1.- self.c/self.gamma * V)

  #spatial solution as a function of V
  def r(self,V):
    #radius
    return self.r_2 * self.x_1(V)**(-self.alpha_0) * self.x_2(V)**(-self.alpha_2) * self.x_3(V)**(-self.alpha_1)

  def v(self,V):
    #velocity
    return self.v_2 * self.x_1(V) * self.r(V) / self.r_2

  def rho(self,V):
    #density
    return self.rho_2 * self.x_1(V)**(self.alpha_0*self.omega) * self.x_2(V)**(self.alpha_3 + self.alpha_2*self.omega) * self.x_3(V)**(self.alpha_4 + self.alpha_1*self.omega) * self.x_4(V)**self.alpha_5

  def p(self,V):
    #pressure
    return self.p_2 * self.x_1(V)**(self.alpha*self.j) * self.x_3(V)**(self.alpha_4 + self.alpha_1*(self.omega-2.)) * self.x_4(V)**(1.+self.alpha_5)


  def compute_V(self):
    # it compute the V array correponding to the positions self.R, as it is implicit it needs a root finding method
    
    def V_find(V,R):
      #function to minimize
      return abs(R-self.r(V))
    
    #compute the V array HOW TO AVOID THE LOOP!!!!!!
    self.V=np.empty(self.Np)
    for i in range(self.Np):
            #self.V[i] = opt.fmin(V_find,self.V_0,args=[self.R[i]],disp=0)
      self.V[i] = opt.fmin(V_find,self.V_0,args=(self.R[i],),disp=0)

  def set_time(self,t):
    self.t = t #set the time
    
    self.compute_rankin(t) #compute the boundary condition at that time
    self.R = np.linspace(0,self.r_2,self.Np) #create the radius array from 0 to the shock front 
    
    self.compute_V() #find the corresponding V array

  def get_v(self):
    return self.v(self.V)

  def get_rho(self):
    return self.rho(self.V)

  def get_p(self):
    return self.p(self.V)

  def get_r(self):
    return self.R


if __name__ == '__main__':
  sedov=Sedov()
  sedov.set_time(0.07)
  R=sedov.get_r()
  v=sedov.get_v()
  p=sedov.get_p()
  rho=sedov.get_rho()
  
  plt.figure(figsize=(5,4))
  plt.plot(R,v/sedov.v_2,label=r'\rm{v}_\rm{r}')
  plt.plot(R,rho/sedov.rho_2,label=r'$\rho')
  plt.plot(R,p/sedov.p_2,label=r'$\rm{P}')
  plt.ylabel(r'$\rm{Normalized\ quantities')
  plt.xlabel(r'$R/R_s$')
  plt.axis([0.0,1.0,0.0,1.0])
  plt.legend(loc="best")
  plt.show()
