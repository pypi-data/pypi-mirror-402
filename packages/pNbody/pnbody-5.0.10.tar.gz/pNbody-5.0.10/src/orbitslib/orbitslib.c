#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>



int NDIM=3;




double forces(double T, double *Y, double *YP, double *GM, int n, 
	      double wx2,double wy2,double wz2,
              double GM_pm,
	      double GM_plummer,double e,
	      double GM_miyamoto,double a, double b,
	      double V0, double Rc, double q, double p,double Lz,
	      double Omega
	      )
  {
    
    int I,idx,idy,idz,idvx,idvy,idvz;
    double x,y,z;
    double Fx,Fy,Fz;
    double r,r2;
       
    double pCte;
    double pmCte;
    double R2,Z2,C1,F,Lz2;   
    double lCte;
        
       
    for (I=0;I<6*n;I=I+6) 
    
      {
         
        idx    = I;
        idy    = idx + 1;
        idz    = idx + 2;
        idvx   = idx + 3;
        idvy   = idx + 4;
        idvz   = idx + 5;
       
      
 
        /* init forces */
        Fx = 0.;
        Fy = 0.;
        Fz = 0.;
        
        
        if (Lz==0)
          {
            
            x = Y[idx];
            y = Y[idy];
            z = Y[idz];
        
            r2 = (x*x + y*y + z*z);
            r  = sqrt(r2);
            R2 = (x*x + y*y); 
            
            
            /* harmonic */
            Fx = Fx - wx2 * x;
            Fy = Fy - wy2 * y;
            Fz = Fz - wz2 * z;
            
            /* Material point */
            pmCte = -GM_pm/(r2*r);
            Fx = Fx + pmCte * x;
            Fy = Fy + pmCte * y;
            Fz = Fz + pmCte * z;
            
            /* plummer */
            pCte = -GM_plummer*pow(r2+e*e,-1.5);
            Fx = Fx + pCte * x;
            Fy = Fy + pCte * y;
            Fz = Fz + pCte * z;
            
            /* Miyamoto nagai */     
            //R5 = pow(R2,0.5);
            Z2 = z*z;
            C1 = sqrt(Z2+b*b);
            
            F  = -GM_miyamoto*     pow((R2+(a+C1)*(a+C1)),-1.5);
            
            Fx = Fx + F*x; 
            Fy = Fy + F*y; 
            Fz = Fz + F*(1.+a/C1) * z;  
              
            
            /* Logarithmic */     
            lCte = -(V0*V0)/(Rc*Rc + x*x + (y*y)/(q*q) + (z*z)/(p*p)); 
            
            Fx = Fx + lCte*x; 
            Fy = Fy + lCte*y/(q*q); 
            Fz = Fz + lCte*z/(p*p); 
            
            
            /* dx/dt = v	 */ 
            YP[idx] = Y[idvx] + Omega*Y[idy];
            YP[idy] = Y[idvy] - Omega*Y[idx];
            YP[idz] = Y[idvz] ;

            /* dv/dt = F	  */
            YP[idvx] = Fx	 + Omega*Y[idvy];
            YP[idvy] = Fy	 - Omega*Y[idvx];
            YP[idvz] = Fz	  ;
            
        
          }
        else     /* in this case, we integrate in cylindrical coord x = r, y = theta, z = z */
          {
            
            
            x = Y[idx];   // R
            z = Y[idy];   // z
            y = Y[idz];   // phi
            
            R2 = x*x;
            
            /* harmonic */
            //Fx = Fx - wx2 * x;
            //Fy = Fy - wy2 * y;
            //Fz = Fz - wz2 * z;
            
            /* Material point */
            //pmCte = -GM_pm/(r2*r);
            //Fx = Fx + pmCte * x;
            //Fy = Fy + pmCte * y;
            //Fz = Fz + pmCte * z;
            
            /* plummer */
            //pCte = -GM_plummer*pow(r2+e*e,-1.5);
            //Fx = Fx + pCte * x;
            //Fy = Fy + pCte * y;
            //Fz = Fz + pCte * z;
            
            /* Miyamoto nagai */     
            //R5 = pow(R2,0.5);
            //Z2 = z*z;
            //C1 = sqrt(Z2+b*b);
            
            //F  = -GM_miyamoto*     pow((R2+(a+C1)*(a+C1)),-1.5);
            
            //Fx = Fx + F*x; 
            //Fy = Fy + F*y; 
            //Fz = Fz + F*(1.+a/C1) * z;  
            
            
            /* Logarithmic */     
            lCte = -(V0*V0)/(Rc*Rc + R2 + (z*z)/(p*p)); 
                        
            Fx = Fx + lCte*x;         // force in R
            Fy = Fy + lCte*z/(p*p);   // force in z
            Fz = Fz + 0;              // force in phi
            
            /* Add the contribution of the effective potential */
            Lz2 = Lz*Lz;
            Fx = Fx + Lz2/(R2*x);     // force in R
            Fy = Fy + 0;              // force in z
            Fz = Fz + 0;              // force in phi
            
            
            /* dx/dt = v	 */ 
            YP[idx] = Y[idvx];        // rp = Pr
            YP[idy] = Y[idvy];        // zp = Pz   
            YP[idz] = Lz/R2;          // pp = Lz/R^2  = Pp/R^2

            /* dv/dt = F	  */
            YP[idvx] = Fx;
            YP[idvy] = Fy;
            YP[idvz] = 0;             // allways zero
                        
            //printf(">> Y0 %g %g\n",Y[idx],Fx);
            //printf(">> Y1 %g %g\n",Y[idy],Fy);
            //printf(">> Y2 %g\n",Y[idz]);
          
            //printf(">> Y3 %g\n",Y[idvx]);
            //printf(">> Y4 %g\n",Y[idvy]);
            //printf(">> Y5 %g\n",Y[idvz]);
            
            
          }
        


  
      }
  
  
  return(1);
  }






void rk78(int *IR, double *T, double *DT, double *X, int N, double *TOL, 
          double (* DER)(double t, double *y, double *yp, double *gm, int n, double wx2,double wy2,double wz2,double GM_pm,double GM_plummer,double e,double GM_miyamoto,double a, double b, double V0, double Rc, double q, double p, double Lz, double Omega), 
	  double *GM, double wx2,double wy2,double wz2,double GM_pm,double GM_plummer,double e,double GM_miyamoto,double a, double b, double V0, double Rc, double q, double p, double Lz, double Omega)
  {
  
    /*
    	Variable step-size automatic one-step integrator for a system of
    	6*N first order ordinary differential equations with initial values
    	The Runge-Kutta-Fehlberg formula 7(8) is used
    	REF   E. FEHLBERG, NASA TECHNICAL REPORT TR R-287, 1968
    	Description of parameters list
    		(All floating variables in DOUBLE PRECISION)
    	IR	O    NUMBER OF REJECTIONS OF THE LAST STEP
    		     (IN CASE  DT WAS TOO LARGE)
    	T	I-O  INDEPENDENT VARIABLE
    	DT	I-O  STEP SIZE
    		     A RECOMMENDED VALUE FOR THE NEXT STEP IS OUTPUT
    	X(N6)	I-O  DEPENDENT VARIABLES
    	FM(N6)       AUXILIARY ARRAYS	WITH M = 0 TO 6
    	F7(N6)       ABSOLUTE ESTIMATED TRUNCATION ERROR ON EACH COMPONENT
    	N6	I    ORDER OF THE DIFFERENTIAL EQUATIONS SYSTEM
    	TOL	I    RELATIVE TOLERATED ERROR ON EACH COMPONENT
    	DER	I    NAME OF THE SUBROUTINE COMPUTING THE DERIVATIVES. THIS
    		     SUBROUTINE HAS TO HAVE THE STANDARD CALLING SEQUENCE
    	CALL DER(T,X,F0)  
    */

    int I;
    int N6 = N;
    double F0[N6],F1[N6],F2[N6],F3[N6],F4[N6],F5[N6],F6[N6],F7[N6];
    
    
  
    double CH1 = 34e0/105e0,   CH2 = 9e0/35e0,    CH3 = 9e0/280e0,
    	   CH4 = 41e0/840e0,   AL2 = 2e0/27e0,    AL3 = 1e0/9e0,
    	   AL4 = 1e0/6e0,      AL5 = 5e0/12e0,    AL6 = 5e-1,
    	   AL7 = 5e0/6e0,      AL9 = 2e0/3e0,     ALA = 1e0/3e0,
    	   B21 = 2e0/27e0,     B31 = 1e0/36e0,    B41 = 1e0/24e0,
    	   B51 = 5e0/12e0,     B61 = 5e-2,	  B71 = -25e0/108e0,
    	   B81 = 31e0/3e2,     B101= -91e0/108e0, B111= 2383e0/41e2,
    	   B121= 3e0/205e0,    B131= -1777e0/41e2,B32 = 1e0/12e0,
    	   B43 = .125e0,       B53 = -25e0/16e0,  B64 = 25e-2,
    	   B74 = 125e0/108e0,  B94 = -53e0/6e0,   B104= 23e0/108e0,
    	   B114= -341e0/164e0, B65 = 2e-1,	  B75 = -65e0/27e0,
    	   B85 = 61e0/225e0,   B95 = 704e0/45e0,  B105= -976e0/135e0,
    	   B115= 4496e0/1025e0,B76 = 125e0/54e0,  B86 = -2e0/9e0,
    	   B96 = -107e0/9e0,   B106= 311e0/54e0,  B116= -301e0/82e0,
    	   B126= -6e0/41e0,    B136= -289e0/82e0, B87 = 13e0/9e2,
    	   B97 = 67e0/9e1,     B107= -19e0/6e1,   B117= 2133e0/41e2,
    	   B127= -3e0/205e0,   B137= 2193e0/41e2, B108= 17e0/6e0,
    	   B118= 45e0/82e0,    B128= -3e0/41e0,   B138= 51e0/82e0,
    	   B119= 45e0/164e0,   B139= 33e0/164e0,  B1110= 18e0/41e0,
    	   B1310= 12e0/41e0;
    
      double X1,X4,X5,X6,X7,X8,X9;

      *IR = 0;
      DER(*T, X, F1, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      /* begin loop 20 */
      while(1)
        {
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*B21*F1[I]; 
      
      	  DER(*T + AL2* *DT, F0, F2, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);

      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B31*F1[I] + B32*F2[I]); 
	    
      	  DER(*T + AL3* *DT, F0, F3, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B41*F1[I] + B43*F3[I]);
      
      	  DER(*T + AL4* *DT, F0, F4, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      	 
	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B51*F1[I] + B53*(F3[I] - F4[I]));
      
      	  DER(*T + AL5* *DT, F0, F5, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
	  
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B61*F1[I] + B64*F4[I] + B65*F5[I]);
      
      	  DER(*T + AL6* *DT, F0, F6, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      	  
	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B71*F1[I] + B74*F4[I] + B75*F5[I] + B76*F6[I]);
         
      	  DER(*T + AL7* *DT, F0, F7, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B81*F1[I] + B85*F5[I] + B86*F6[I] + B87*F7[I]);
      
      	  DER(*T + AL4* *DT, F0, F2, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(2e0*F1[I] + B94*F4[I] + B95*F5[I] + B96*F6[I] + B97*F7[I] + 3e0*F2[I]);
      
      	  DER(*T + AL9* *DT, F0, F3, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    {
      	      X1 = F1[I];
      	      X4 = F4[I];
      	      X5 = F5[I];
      	      X6 = F6[I];
      	      X7 = F7[I];
      	      X8 = F2[I];
      	      X9 = F3[I];
      	      F2[I] = CH1*X6 + CH2*(X7 + X8) + CH3*X9;
      	      F0[I] = X[I] + *DT*(B101*X1 + B104*X4 + B105*X5 + B106*X6 + B107*X7 + B108*X8 - B32*X9);
      	      F4[I] = B111*X1 + B114*X4 + B115*X5 + B116*X6 + B117*X7 + B118*X8 + B119*X9;
      	      F5[I] = B121*X1 + B126*X6 + B127*X7 + B128*(X8 - X9);
      	      F6[I] = B131*X1 + B114*X4 + B115*X5 + B136*X6 + B137*X7 + B138*X8 + B139*X9;
      	    }
      
      	  DER(*T + ALA* *DT, F0, F3, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    {
      	      F7[I] = X[I] + *DT*(F4[I] + B1110*F3[I]);
      	      F0[I] = X[I] + *DT*(F5[I] - B126*F3[I]);
      	    }
	    
      	  DER(*T + *DT, F7, F4, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      	  DER(*T,       F0, F5, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(F6[I] + B1310*F3[I] + F5[I]);
      
      	  DER(*T + *DT, F0, F6, GM, N6/6, wx2,wy2,wz2,GM_pm,GM_plummer,e,GM_miyamoto,a,b,V0,Rc,q,p,Lz,Omega);
      
      	  X7 = 1e-30;
      
      	  for (I=0;I<N6;I++)
      	    {
      	      F0[I] = X[I];
      	      X[I] = X[I] + *DT*(CH3*F3[I] + CH4*(F5[I] + F6[I]) + F2[I]);
      	      F7[I] = *DT*(F1[I] + F4[I] - F5[I] - F6[I])*CH4;
      	      X7 = X7 + pow((F7[I]/TOL[I]),2);
      	    }
	  
	    
      	  X9 = *DT;
      	  *DT = *DT*pow((25e-4/X7),625e-4);
	        
      	  if (X7 > 1e0) 
      	    {
      	     
	      for (I=0;I<N6;I++)
	  	X[I] = F0[I];
      	      *IR = *IR + 1;
      	      
	      /*GOTO 20*/
      	    
	    
	    }
      	  else
      	    {	    
      	      *T = *T + X9;
	      return ;
	    }  
      
        }	    
	
  }




/*

DER must be a fct with following arguments :

double t,
double Y
double YP
autres arguments


der retourne dY/dt(T,Y)

*/




void rk78fext(int *IR, double *T, double *DT, double *X, double *GM, int N, double *TOL, PyObject *DER, PyObject *der_arglist)

  {
  
    /*
    	Variable step-size automatic one-step integrator for a system of
    	6*N first order ordinary differential equations with initial values
    	The Runge-Kutta-Fehlberg formula 7(8) is used
    	REF   E. FEHLBERG, NASA TECHNICAL REPORT TR R-287, 1968
    	Description of parameters list
    		(All floating variables in DOUBLE PRECISION)
    	IR	O    NUMBER OF REJECTIONS OF THE LAST STEP
    		     (IN CASE  DT WAS TOO LARGE)
    	T	I-O  INDEPENDENT VARIABLE
    	DT	I-O  STEP SIZE
    		     A RECOMMENDED VALUE FOR THE NEXT STEP IS OUTPUT
    	X(N6)	I-O  DEPENDENT VARIABLES
    	FM(N6)       AUXILIARY ARRAYS	WITH M = 0 TO 6
    	F7(N6)       ABSOLUTE ESTIMATED TRUNCATION ERROR ON EACH COMPONENT
    	N6	I    ORDER OF THE DIFFERENTIAL EQUATIONS SYSTEM
    	TOL	I    RELATIVE TOLERATED ERROR ON EACH COMPONENT
    	DER	I    NAME OF THE SUBROUTINE COMPUTING THE DERIVATIVES. THIS
    		     SUBROUTINE HAS TO HAVE THE STANDARD CALLING SEQUENCE
    	CALL DER(T,X,F0)  
    */

    int I;
    int N6 = N;
    double *F0,*F1,*F2,*F3,*F4,*F5,*F6,*F7;
    size_t bytes;
    
    PyObject      *arglist;
    PyArrayObject *result;
    
    PyObject *OX;
    PyObject *OF;
    PyObject *OM;
    
    npy_intp   ld[1];
   
  
    double CH1 = 34e0/105e0,   CH2 = 9e0/35e0,    CH3 = 9e0/280e0,
    	   CH4 = 41e0/840e0,
    	   B21 = 2e0/27e0,     B31 = 1e0/36e0,    B41 = 1e0/24e0,
    	   B51 = 5e0/12e0,     B61 = 5e-2,	  B71 = -25e0/108e0,
    	   B81 = 31e0/3e2,     B101= -91e0/108e0, B111= 2383e0/41e2,
    	   B121= 3e0/205e0,    B131= -1777e0/41e2,B32 = 1e0/12e0,
    	   B43 = .125e0,       B53 = -25e0/16e0,  B64 = 25e-2,
    	   B74 = 125e0/108e0,  B94 = -53e0/6e0,   B104= 23e0/108e0,
    	   B114= -341e0/164e0, B65 = 2e-1,	  B75 = -65e0/27e0,
    	   B85 = 61e0/225e0,   B95 = 704e0/45e0,  B105= -976e0/135e0,
    	   B115= 4496e0/1025e0,B76 = 125e0/54e0,  B86 = -2e0/9e0,
    	   B96 = -107e0/9e0,   B106= 311e0/54e0,  B116= -301e0/82e0,
    	   B126= -6e0/41e0,    B136= -289e0/82e0, B87 = 13e0/9e2,
    	   B97 = 67e0/9e1,     B107= -19e0/6e1,   B117= 2133e0/41e2,
    	   B127= -3e0/205e0,   B137= 2193e0/41e2, B108= 17e0/6e0,
    	   B118= 45e0/82e0,    B128= -3e0/41e0,   B138= 51e0/82e0,
    	   B119= 45e0/164e0,   B139= 33e0/164e0,  B1110= 18e0/41e0,
    	   B1310= 12e0/41e0;
    
      double X1,X4,X5,X6,X7,X8,X9;
      

      
      
      /* allocate buffers */
      F0  = malloc(bytes = N6 * sizeof(double));
      F1  = malloc(bytes = N6 * sizeof(double));
      F2  = malloc(bytes = N6 * sizeof(double));
      F3  = malloc(bytes = N6 * sizeof(double));
      F4  = malloc(bytes = N6 * sizeof(double));
      F5  = malloc(bytes = N6 * sizeof(double));
      F6  = malloc(bytes = N6 * sizeof(double));
      F7  = malloc(bytes = N6 * sizeof(double));
      
      ld[0]= N6;
      
      

      *IR = 0;
      OX = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  X);
      OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F1);
      OM = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  GM);
      arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
      //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 
      result = (PyArrayObject*) PyObject_CallObject(DER, arglist); 
      //F1 = (double *) (result->data);
      F1 = (double *)PyArray_GETPTR1(result,0);
      
      /* begin loop 20 */
      while(1)
        {
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*B21*F1[I]; 
          
	  OX = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F0);
      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F2);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);	 
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist);
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist); 
	  //F2 = (double *) (result->data);
    F2 = (double *)PyArray_GETPTR1(result,0);

      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B31*F1[I] + B32*F2[I]); 

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F3);
          arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 	
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);    
	  //F3 = (double *) (result->data);
    F3 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B41*F1[I] + B43*F3[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F4);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);	
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist);
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);       
	  //F4 = (double *) (result->data); 
    F4 = (double *)PyArray_GETPTR1(result,0);
      	 
	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B51*F1[I] + B53*(F3[I] - F4[I]));

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F5);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist);  
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);     
	  //F5 = (double *) (result->data);
    F5 = (double *)PyArray_GETPTR1(result,0);
	  
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B61*F1[I] + B64*F4[I] + B65*F5[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F6);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);      
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist);
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);       
	  //F6 = (double *) (result->data);
    F6 = (double *)PyArray_GETPTR1(result,0);
      	  
	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B71*F1[I] + B74*F4[I] + B75*F5[I] + B76*F6[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F7);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist);
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);         
	  //F7 = (double *) (result->data);
    F7 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(B81*F1[I] + B85*F5[I] + B86*F6[I] + B87*F7[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F2);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);       
	  //F2 = (double *) (result->data);
    F2 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(2e0*F1[I] + B94*F4[I] + B95*F5[I] + B96*F6[I] + B97*F7[I] + 3e0*F2[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F3);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);     
	  //F3 = (double *) (result->data);
    F3 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    {
      	      X1 = F1[I];
      	      X4 = F4[I];
      	      X5 = F5[I];
      	      X6 = F6[I];
      	      X7 = F7[I];
      	      X8 = F2[I];
      	      X9 = F3[I];
      	      F2[I] = CH1*X6 + CH2*(X7 + X8) + CH3*X9;
      	      F0[I] = X[I] + *DT*(B101*X1 + B104*X4 + B105*X5 + B106*X6 + B107*X7 + B108*X8 - B32*X9);
      	      F4[I] = B111*X1 + B114*X4 + B115*X5 + B116*X6 + B117*X7 + B118*X8 + B119*X9;
      	      F5[I] = B121*X1 + B126*X6 + B127*X7 + B128*(X8 - X9);
      	      F6[I] = B131*X1 + B114*X4 + B115*X5 + B136*X6 + B137*X7 + B138*X8 + B139*X9;
      	    }

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F3);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);      
	  //F3 = (double *) (result->data);
    F3 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    {
      	      F7[I] = X[I] + *DT*(F4[I] + B1110*F3[I]);
      	      F0[I] = X[I] + *DT*(F5[I] - B126*F3[I]);
      	    }

      	  OX = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F7);
      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F4);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 	 
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);   
	  //F4 = (double *) (result->data);
    F4 = (double *)PyArray_GETPTR1(result,0);

      	  OX = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F0);
      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F5);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 	  
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);
	  //F5 = (double *) (result->data);
    F5 = (double *)PyArray_GETPTR1(result,0);
      
      	  for (I=0;I<N6;I++)
      	    F0[I] = X[I] + *DT*(F6[I] + B1310*F3[I] + F5[I]);

      	  OF = PyArray_SimpleNewFromData(1, ld, NPY_DOUBLE,  F6);
      	  arglist = Py_BuildValue("(dOOOi)", *T, OX, OF, OM, N6/6);
	  //result = (PyArrayObject*) PyEval_CallObject(DER, arglist); 	  
    result = (PyArrayObject*) PyObject_CallObject(DER, arglist);
	  //F6 = (double *) (result->data);
    F6 = (double *)PyArray_GETPTR1(result,0);
      
      	  X7 = 1e-30;
      
      	  for (I=0;I<N6;I++)
      	    {
      	      F0[I] = X[I];
      	      X[I] = X[I] + *DT*(CH3*F3[I] + CH4*(F5[I] + F6[I]) + F2[I]);
      	      F7[I] = *DT*(F1[I] + F4[I] - F5[I] - F6[I])*CH4;
      	      X7 = X7 + pow((F7[I]/TOL[I]),2);
      	    }
	  
	    
      	  X9 = *DT;
      	  *DT = *DT*pow((25e-4/X7),625e-4);
	        
      	  if (X7 > 1e0) 
      	    {
      	     
	      for (I=0;I<N6;I++)
	  	X[I] = F0[I];
      	      *IR = *IR + 1;
      	      
	      /*GOTO 20*/
      	    
	    
	    }
      	  else
      	    {	    
      	      *T = *T + X9;
	      return ;
	    }  
      
        }	    
	
  }














/*********************************/
/*                               */
/*********************************/
      
static PyObject *
      orbitslib_test(PyObject *self, PyObject *args)
      {
      	  
	  
	  PyArrayObject *pos,*vel,*mass;	  
	  
	  PyObject *forces;
	  PyObject *result;
	  PyObject *arglist;
	  
	  double epsx,epsv;
	  
	  int ir;
	  int n;
	  int i,j; 
	  double t,dt;
	  double *x,*xx,*tol,*gm;
	  
	  size_t bytes;
	  
	  /* parse arguments */    
	        
	  if (! PyArg_ParseTuple(args, "OOOOOdd",&forces,&arglist,&pos,&vel,&mass,&epsx,&epsv))		
              return NULL;
	    
          
	  if (!PyFunction_Check(forces))
	    {
	      printf("this is not a python function\n");
            }





	  /* check number of bodies = number of dim of pos,vel,mass */
	
	  if (PyArray_NDIM(pos) != 2)
	    {
	      PyErr_SetString(PyExc_ValueError,"dimension of pos must be 2.");
	      return NULL;
	    }
	
	  if (PyArray_NDIM(vel) != 2)
	    {
	      PyErr_SetString(PyExc_ValueError,"dimension of vel must be 2.");
	      return NULL;
	    }	  
	
	  if (PyArray_NDIM(mass) != 1)
	    {
	      PyErr_SetString(PyExc_ValueError,"dimension of mass must be 1.");
	      return NULL;
	    }	  
	    
	  if ((PyArray_DIM(pos, 0)!=PyArray_DIM(vel, 0))||(PyArray_DIM(vel, 0)!=PyArray_DIM(mass, 0)))  
	    {
	      PyErr_SetString(PyExc_ValueError,"size of pos,vel and mass must be identical");
	      return NULL;
	    }	  
        
	
          n = PyArray_DIM(pos, 0);
	
	  /* allocate memory */
	  if(!(x  = malloc(bytes = 6*n * sizeof(double))))
    	    {
    	      printf("failed to allocate memory for `x' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	      exit(-1);
    	    }	  
	    
	  if(!(xx  = malloc(bytes = 6*n * sizeof(double))))
    	    {
    	      printf("failed to allocate memory for `xx' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	      exit(-1);
    	    }		    


	  if(!(tol  = malloc(bytes = 6*n * sizeof(double))))
    	    {
    	      printf("failed to allocate memory for `tol' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	      exit(-1);
    	    }

	  if(!(gm  = malloc(bytes = 6*n * sizeof(double))))
    	    {
    	      printf("failed to allocate memory for `gm' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	      exit(-1);
    	    }			  
	
	
	  /* read data */  
	  	  
	
          for (i = 0; i < n; i++) 
	    {
	      x[0+6*i] = *(double *)PyArray_GETPTR2(pos, i, 0);
	      x[1+6*i] = *(double *)PyArray_GETPTR2(pos, i, 1);
	      x[2+6*i] = *(double *)PyArray_GETPTR2(pos, i, 2);

	      x[3+6*i] = *(double *)PyArray_GETPTR2(vel, i, 0);
	      x[4+6*i] = *(double *)PyArray_GETPTR2(vel, i, 1);
	      x[5+6*i] = *(double *)PyArray_GETPTR2(vel, i, 2);
	      
	      gm[i]    = *(double *)PyArray_GETPTR1(mass, i);        
	    } 
	    
        
	  /* some init */
  	  for (i=0;i<6*n;i=i+6)  
  	    {
  	      for(j=i;j<i+3;j++)
  	  	{
  	  	  tol[j  ] = epsx;
  	  	  tol[j+3] = epsv;
  	  	}
  	    }	 
  
  	  for (i=0;i<6*n;i++)
  	    xx[i] = x[i]; 
 


	  /* now integrates */
	  
	  t = 0;
	  
	  rk78fext(&ir, &t, &dt, x, gm, 6*n, tol, forces, arglist);	  
	  
	  
	  return result=NULL;
	  	        	  
	  //return Py_BuildValue("d",1);
      }






/*********************************/
/* IntegrateOverDt */
/*********************************/

static PyObject *
      orbitslib_IntegrateOverDt(PyObject *self, PyObject *args)
      {

	PyObject *forces;
	PyObject *arglist;
        
        PyArrayObject *pos,*vel,*mass;
	int n;
	int i,j;  
	int ir; 																	        
  	double t,dt,tstart,tend;
  	//double x[6*NDIM],xx[6*NDIM],xp[6*NDIM],tol[6*NDIM],gm[NDIM];
	double *x,*xx,*xp,*tol,*gm;
  	double epsx,epsv;
	size_t bytes;
	
	
        if (! PyArg_ParseTuple(args, "OOOOOddddd",&forces,&arglist,&pos,&vel,&mass,&tstart,&tend,&dt,&epsx,&epsv))
	  {
	    PyErr_SetString(PyExc_ValueError,"Error in arguments");
	    return NULL;
	  }  		
	
	/* check number of bodies = number of dim of pos,vel,mass */
	
	if (PyArray_NDIM(pos) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of pos must be 2.");
	    return NULL;
	  }
	
	if (PyArray_NDIM(vel) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of vel must be 2.");
	    return NULL;
	  }	
	
	if (PyArray_NDIM(mass) != 1)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of mass must be 1.");
	    return NULL;
	  }	
	  
	if ((PyArray_DIM(pos, 0)!=PyArray_DIM(vel, 0))||(PyArray_DIM(vel, 0)!=PyArray_DIM(mass, 0)))  
	  {
	    PyErr_SetString(PyExc_ValueError,"size of pos,vel and mass must be identical");
	    return NULL;
	  }	
        
	
        n = PyArray_DIM(pos, 0);
	
	/* allocate memory */
	if(!(x  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `x' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	
	  
	if(!(xx  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xx' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }		  

	if(!(xp  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xp' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	

	if(!(tol  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `tol' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }

	if(!(gm  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `gm' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	  		
		
	/* read data */  
	  	
	
        for (i = 0; i < n; i++) 
	  {
      x[0+6*i] = *(double *)PyArray_GETPTR2(pos, i, 0);
      x[1+6*i] = *(double *)PyArray_GETPTR2(pos, i, 1);
      x[2+6*i] = *(double *)PyArray_GETPTR2(pos, i, 2);

      x[3+6*i] = *(double *)PyArray_GETPTR2(vel, i, 0);
      x[4+6*i] = *(double *)PyArray_GETPTR2(vel, i, 1);
      x[5+6*i] = *(double *)PyArray_GETPTR2(vel, i, 2);
	      
      gm[i]    = *(double *)PyArray_GETPTR1(mass, i); 
	  } 
	  
	/* some init */
  	for (i=0;i<6*n;i=i+6)  
  	  {
  	    for(j=i;j<i+3;j++)
  	      {
  		tol[j  ] = epsx;
  		tol[j+3] = epsv;
  	      }
  	  }    
  
  	for (i=0;i<6*n;i++)
  	  xx[i] = x[i]; 

  	/* first loop to determine dt */
	t=tstart;
	rk78fext(&ir, &t, &dt, x, gm, 6*n, tol, forces, arglist);	 
	

  	/* main loop */
  	t=tstart; 
	
	
		
  	while (t<tend)
  	  {
  
  	    if ((t+dt>tend)&&(t!=tstart) )
  	      {
		dt = tend-t;
  	      }
  
	    rk78fext(&ir, &t, &dt, x, gm, 6*n, tol, forces, arglist);	 
	     	    
	  }
       	
	/* return pos,vel,time */
	
        for (i = 0; i < n; i++) 
	  {
	    *(double *)PyArray_GETPTR2(pos, i, 0) = x[0+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 1) = x[1+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 2) = x[2+6*i] ;
                                            
	    *(double *)PyArray_GETPTR2(vel, i, 0) = x[3+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 1) = x[4+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 2) = x[5+6*i] ;
	  } 
			  
	return Py_BuildValue("OOdd",pos,vel,t,dt);
      }               



/*********************************/
/* IntegrateOneOrbit */
/*********************************/

static PyObject *
      orbitslib_IntegrateOneOrbit(PyObject *self, PyObject *args)
      {

	PyObject *forces;
	PyObject *arglist;
        
        PyArrayObject *pos,*vel,*mass;
	int n;
	int i,j;  
	int ir; 																	        
  	double t,dt;
	int stop;
  	//double x[6*NDIM],xx[6*NDIM],xp[6*NDIM],tol[6*NDIM],gm[NDIM];
	double *x,*xx,*xp,*tol,*gm;
  	double epsx,epsv;
	size_t bytes;
	
	int ncross;
	
	
        if (! PyArg_ParseTuple(args, "OOOOOdd",&forces,&arglist,&pos,&vel,&mass,&epsx,&epsv))
	  {
	    PyErr_SetString(PyExc_ValueError,"Error in arguments");
	    return NULL;
	  }  		
	
	/* check number of bodies = number of dim of pos,vel,mass */
	
	if (PyArray_NDIM(pos) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of pos must be 2.");
	    return NULL;
	  }
	
	if (PyArray_NDIM(vel) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of vel must be 2.");
	    return NULL;
	  }	
	
	if (PyArray_NDIM(mass) != 1)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of mass must be 1.");
	    return NULL;
	  }	
	  
	if ((PyArray_DIM(pos, 0)!=PyArray_DIM(vel, 0))||(PyArray_DIM(vel, 0)!=PyArray_DIM(mass, 0)))  
	  {
	    PyErr_SetString(PyExc_ValueError,"size of pos,vel and mass must be identical");
	    return NULL;
	  }	
        
	
        n = PyArray_DIM(pos, 0);
	
	/* allocate memory */
	if(!(x  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `x' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	
	  
	if(!(xx  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xx' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }		  

	if(!(xp  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xp' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	

	if(!(tol  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `tol' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }

	if(!(gm  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `gm' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	  		
		
	/* read data */  
	  	
	
        for (i = 0; i < n; i++) 
	  {
      x[0+6*i] = *(double *)PyArray_GETPTR2(pos, i, 0);
      x[1+6*i] = *(double *)PyArray_GETPTR2(pos, i, 1);
      x[2+6*i] = *(double *)PyArray_GETPTR2(pos, i, 2);

      x[3+6*i] = *(double *)PyArray_GETPTR2(vel, i, 0);
      x[4+6*i] = *(double *)PyArray_GETPTR2(vel, i, 1);
      x[5+6*i] = *(double *)PyArray_GETPTR2(vel, i, 2);
	      
      gm[i]    = *(double *)PyArray_GETPTR1(mass, i); 
	  } 
	  
	/* some init */
  	for (i=0;i<6*n;i=i+6)  
  	  {
  	    for(j=i;j<i+3;j++)
  	      {
  		tol[j  ] = epsx;
  		tol[j+3] = epsv;
  	      }
  	  }    
  
  	for (i=0;i<6*n;i++)
  	  xx[i] = x[i]; 

  	/* first loop to determine dt */
	t=0;
	rk78fext(&ir, &t, &dt, xx, gm, 6*n, tol, forces, arglist);	 
	

  	/* main loop */
  	t=0; 
	stop = 0;
	ncross = 0;
	
        for (i=0;i<6*n;i++)
  	  xx[i] = x[i]; 
		
  	while (stop==0)
  	  {
  
	    rk78fext(&ir, &t, &dt, x, gm, 6*n, tol, forces, arglist);	 
	    
	    if (xx[1]*x[1]<0)
	      ncross++;
	    
	    if (ncross == 2)
	      stop=1;
	      
	    /*printf("%g %g %g %g %d\n",x[0],x[1],xx[0],xx[1],ncross);*/  
	    
	    
            for (i=0;i<6*n;i++)
  	      xx[i] = x[i]; 
	     	    
	  }
	  
	  
	  
       	
	/* return pos,vel,time */
	
        for (i = 0; i < n; i++) 
	  {
	    *(double *)PyArray_GETPTR2(pos, i, 0) = x[0+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 1) = x[1+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 2) = x[2+6*i] ;
                                            
	    *(double *)PyArray_GETPTR2(vel, i, 0) = x[3+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 1) = x[4+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 2) = x[5+6*i] ;       
	  } 
			  
	return Py_BuildValue("OOdd",pos,vel,t,dt);
      }               








/*********************************/
/* IntegrateOneOrbitUsingForces */
/*********************************/

static PyObject *
      orbitslib_IntegrateOneOrbitUsingForces(PyObject *self, PyObject *args)
      {
        
        PyArrayObject *pos,*vel,*mass;
	PyArrayObject *posi,*veli;
	PyArrayObject *posz,*velz;
	
	int n;
	int i,j;  
	int ir; 																	        
  	double t,dt;
	int stop;
  	//double x[6*NDIM],xx[6*NDIM],xp[6*NDIM],tol[6*NDIM],gm[NDIM];
	double z[6];
	double *x,*xx,*xp,*tol,*gm;
  	double epsx,epsv;
	double wx2,wy2,wz2;
	double GMpm;
	double GMplummer,e;
	double GMmiyamoto,a,b;
	double V0,Rc,q,p,Lz;
	double Omega;
	double aa;
	size_t bytes;
	
	int ncross,nsteps;
	npy_intp   ld[2],ldz[1];
	
	
        if (! PyArg_ParseTuple(args, "OOOdddddddddddddddddd",&pos,&vel,&mass,
	                       &wx2,&wy2,&wz2,
			       &GMpm,
			       &GMplummer,&e,
			       &GMmiyamoto,&a,&b,
			       &V0,&Rc,&q,&p,&Lz,
			       &Omega,
			       &epsx,&epsv,&dt))
	  {
	    PyErr_SetString(PyExc_ValueError,"Error in arguments");
	    return NULL;
	  }  		
		
	/* check number of bodies = number of dim of pos,vel,mass */
	
	if (PyArray_NDIM(pos) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of pos must be 2.");
	    return NULL;
	  }
	
	if (PyArray_NDIM(vel) != 2)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of vel must be 2.");
	    return NULL;
	  }	
	
	if (PyArray_NDIM(mass) != 1)
	  {
	    PyErr_SetString(PyExc_ValueError,"dimension of mass must be 1.");
	    return NULL;
	  }	
	  
	if ((PyArray_DIM(pos, 0)!=PyArray_DIM(vel, 0))||(PyArray_DIM(vel, 0)!=PyArray_DIM(mass, 0)))  
	  {
	    PyErr_SetString(PyExc_ValueError,"size of pos,vel and mass must be identical");
	    return NULL;
	  }	
        
	
        n = PyArray_DIM(pos, 0);
	
	/* allocate memory */
	if(!(x  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `x' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	
	  
	if(!(xx  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xx' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }		  

	if(!(xp  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `xp' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	

	if(!(tol  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `tol' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }

	if(!(gm  = malloc(bytes = 6*n * sizeof(double))))
    	  {
    	    printf("failed to allocate memory for `gm' (%g MB).\n", bytes / (1024.0 * 1024.0));
    	    exit(-1);
    	  }	  		
		
	/* create posi, veli */
	ld[0] = 10000;
	ld[1] = 3;
	posi = (PyArrayObject *) PyArray_SimpleNew(2,ld,NPY_DOUBLE);
	veli = (PyArrayObject *) PyArray_SimpleNew(2,ld,NPY_DOUBLE);	
		
	ldz[0] = 3;	
	posz = (PyArrayObject *) PyArray_SimpleNew(1,ldz,NPY_DOUBLE);
	velz = (PyArrayObject *) PyArray_SimpleNew(1,ldz,NPY_DOUBLE);		
				

  for (i = 0; i < 10000; i++) 
	  {	  
	    *(double *)PyArray_GETPTR2(posi, i, 0) = 0 ;
	    *(double *)PyArray_GETPTR2(posi, i, 1) = 0 ;
	    *(double *)PyArray_GETPTR2(posi, i, 2) = 0 ;
                                            
	    *(double *)PyArray_GETPTR2(veli, i, 0) = 0 ;
	    *(double *)PyArray_GETPTR2(veli, i, 1) = 0 ;
	    *(double *)PyArray_GETPTR2(veli, i, 2) = 0 ;      
	  } 
	      		
		
	/* read data */  
  	
  for (i = 0; i < n; i++) 
	  {
      x[0+6*i] = *(double *)PyArray_GETPTR2(pos, i, 0);
      x[1+6*i] = *(double *)PyArray_GETPTR2(pos, i, 1);
      x[2+6*i] = *(double *)PyArray_GETPTR2(pos, i, 2);

      x[3+6*i] = *(double *)PyArray_GETPTR2(vel, i, 0);
      x[4+6*i] = *(double *)PyArray_GETPTR2(vel, i, 1);
      x[5+6*i] = *(double *)PyArray_GETPTR2(vel, i, 2);
	      
      gm[i]    = *(double *)PyArray_GETPTR1(mass, i);
	  } 
    
	  
	/* some init */
  for (i=0;i<6*n;i=i+6)  
  	  {
  	    for(j=i;j<i+3;j++)
  	      {
  		tol[j  ] = epsx;
  		tol[j+3] = epsv;
  	      }
  	  }    

  
  for (i=0;i<6*n;i++)
  	  xx[i] = x[i]; 
      

  /* first loop to determine dt */
	t=0;
	rk78(&ir, &t, &dt, xx, 6*n, tol, &forces, gm, wx2,wy2,wz2,GMpm,GMplummer,e,GMmiyamoto,a,b,V0,Rc,q,p,Lz,Omega);
  

		
  /* main loop */
  t=0; 
	stop = 0;
	ncross = 0;
	
  for (i=0;i<6*n;i++)
  	  xx[i] = x[i]; 
	
	nsteps = 0;
		
  while (stop==0)
    {
  
	    rk78(&ir, &t, &dt, x, 6*n, tol, &forces, gm, wx2,wy2,wz2,GMpm,GMplummer,e,GMmiyamoto,a,b,V0,Rc,q,p,Lz,Omega); 
      	    
	    if ((xx[1]*x[1]<0) && (x[4]>0))
	      {
          ncross++;
          stop=1;
           
          aa = xx[1]/(xx[1]-x[1]);
 
          for (j=0;j<6;j++)
            {
              z[j] =  xx[j] - aa * (xx[j]-x[j]); 
            }
	      }
        
	    //if (ncross == 2)
	    //  stop=1;
	      
	    /*printf("%g %g %g %g %d\n",x[0],x[1],xx[0],xx[1],ncross);*/  
	    
	    
      for (i=0;i<6*n;i++)
          xx[i] = x[i]; 

      /* record position */

      //for (i = 0; i < n; i++) 
      i = 0;
        {	              
	        *(double *)PyArray_GETPTR2(posi, nsteps, 0) = x[0+6*i] ;
	        *(double *)PyArray_GETPTR2(posi, nsteps, 1) = x[1+6*i] ;
	        *(double *)PyArray_GETPTR2(posi, nsteps, 2) = x[2+6*i] ;
                                          
	        *(double *)PyArray_GETPTR2(veli, nsteps, 0) = x[3+6*i] ;
	        *(double *)PyArray_GETPTR2(veli, nsteps, 1) = x[4+6*i] ;
	        *(double *)PyArray_GETPTR2(veli, nsteps, 2) = x[5+6*i] ;          
        } 	

      nsteps++;  
  
    }
	  	  
  for (i=0;i<3*n;i++)
      {
        *(double *)PyArray_GETPTR1(posz,i) = z[i] ;
        *(double *)PyArray_GETPTR1(velz,i) = z[i+3] ;
      }  
	
	
	
	/* return pos,vel,time */
	
  for (i = 0; i < n; i++) 
	  {      
	    *(double *)PyArray_GETPTR2(pos, i, 0) = x[0+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 1) = x[1+6*i] ;
	    *(double *)PyArray_GETPTR2(pos, i, 2) = x[2+6*i] ;
                                          
	    *(double *)PyArray_GETPTR2(vel, i, 0) = x[3+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 1) = x[4+6*i] ;
	    *(double *)PyArray_GETPTR2(vel, i, 2) = x[5+6*i] ;         
	  } 
					  
	return Py_BuildValue("OOOOOOdd",pos,vel,posi,veli,posz,velz,t,dt);
      }               







/* definition of the method table */      
        
static PyMethodDef orbitslibMethods[] = {
	   
          {"test",  orbitslib_test, METH_VARARGS,
           "compute cooling."}, 

          {"IntegrateOverDt",  orbitslib_IntegrateOverDt, METH_VARARGS,
           "Integrate the system over dt."},

          {"IntegrateOneOrbit",  orbitslib_IntegrateOneOrbit, METH_VARARGS,
           "Integrate the system during one orbit (using python function for forces)."},

          {"IntegrateOneOrbitUsingForces",  orbitslib_IntegrateOneOrbitUsingForces, METH_VARARGS,
           "Integrate the system during one orbit (plummer + harmonic)."},
	   
          {NULL, NULL, 0, NULL}        /* Sentinel */
      };      
      
      


static struct PyModuleDef orbitslibmodule = {
    PyModuleDef_HEAD_INIT,
    "orbitslib",
    "Defines some orbitslib functions",
    -1,
    orbitslibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};




PyMODINIT_FUNC PyInit_orbitslib(void) {
  PyObject *m;
  m = PyModule_Create(&orbitslibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}


