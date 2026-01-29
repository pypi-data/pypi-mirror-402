#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>


#define TO_DOUBLE(a)        ( (PyArrayObject*) PyArray_CastToType(a, PyArray_DescrFromType(NPY_DOUBLE)  ,0) )


#define  MAXPTS	10


/* global variables */
struct global_data
{
  double CMUtoMsol;				/*!< convertion factor from Code Mass Unit to Solar Mass >*/
  double MsoltoCMU;				/*!< convertion factor from Solar Mass to Code Mass Unit >*/
};


/* intern global variables */
struct local_params_chimie
{
  float  Mmin,Mmax;
  int    n;
  float  ms[MAXPTS];
  float  as[MAXPTS+1];
  float  bs[MAXPTS+1];
  float  fs[MAXPTS];
  double imf_Ntot;
};


struct global_data All;
struct local_params_chimie *Cp;



/*! returns the maximum of two double
 */
double dmax(double x, double y)
{
  if(x > y)
    return x;
  else
    return y;
}

/*! returns the minimum of two double
 */
double dmin(double x, double y)
{
  if(x < y)
    return x;
  else
    return y;
}




/*! This function init defaults IMF parameter
 */

static void init(void)
{
  
  Cp = malloc(sizeof(struct local_params_chimie));
    
  Cp->n     = 3;
  Cp->Mmax  = 50;
  Cp->Mmin  = 0.05;
  
  Cp->as[0] =  0.7;
  Cp->as[1] = -0.8;
  Cp->as[2] = -1.7;
  Cp->as[3] = -1.3;
  
  Cp->ms[0] =  0.08;
  Cp->ms[1] =  0.5;
  Cp->ms[2] =  1.0;

  /* use Msol mass units */
  All.CMUtoMsol=1;
  All.MsoltoCMU=1;

}



/*! This function returns the mass fraction of a star of mass m
 *  using the current IMF
 */




static double get_imf(double m)
{

  int i;
  int n;

  n = Cp->n;

  /* convert m in msol */
  m = m*All.CMUtoMsol;

  if (n==0)
    return Cp->bs[0]* pow(m,Cp->as[0]);
  else
    {
      for (i=0;i<n;i++)
        if (m < Cp->ms[i])
          return Cp->bs[i]* pow(m,Cp->as[i]);

      return Cp->bs[n]* pow(m,Cp->as[n]);
    }

}





/*! This function returns the mass fraction between m1 and m2
 *  per mass unit, using the current IMF
 */


static double get_imf_M(double m1, double m2)
{

  int i;
  int n;
  double p;
  double integral=0;
  double mmin,mmax;

  n = Cp->n;

  /* convert m in msol */
  m1 = m1*All.CMUtoMsol;
  m2 = m2*All.CMUtoMsol;


  if (n==0)
    {
      p =  Cp->as[0]+1;
      integral = (Cp->bs[0]/p) * ( pow(m2,p) - pow(m1,p) );
      //printf("--> %g %g %g %g int=%g\n",m1,m2,pow(m2,p), pow(m1,p),integral);
    }

  else
    {

      integral = 0;

      /* first */
      if (m1<Cp->ms[0])
        {
          mmin = m1;
          mmax = dmin(Cp->ms[0],m2);
          p = Cp->as[0] + 1;
          integral +=  (Cp->bs[0]/p) * ( pow(mmax,p) - pow(mmin,p) );
        }

      /* last */
      if (m2>Cp->ms[n-1])
        {
          mmin = dmax(Cp->ms[n-1],m1);
          mmax = m2;
          p = Cp->as[n] + 1;
          integral +=  (Cp->bs[n]/p) * ( pow(mmax,p) - pow(mmin,p) );
        }

      /* loop over other segments */
      for (i=0;i<n-1;i++)
        {
          mmin = dmax(Cp->ms[i  ],m1);
          mmax = dmin(Cp->ms[i+1],m2);
          if (mmin<mmax)
            {
              p = Cp->as[i+1] + 1;
              integral +=  (Cp->bs[i+1]/p) * ( pow(mmax,p) - pow(mmin,p) );
            }
        }


    }

  return integral;

}



/*! This function returns the number fraction between m1 and m2
 *  per mass unit, using the current IMF
 */


static double get_imf_N(double m1, double m2)
{

  int i;
  int n;
  double p;
  double integral=0;
  double mmin,mmax;

  n = Cp->n;

  /* convert m in msol */
  m1 = m1*All.CMUtoMsol;
  m2 = m2*All.CMUtoMsol;
    
  if (n==0)
    {
      p =  Cp->as[0];
      integral = (Cp->bs[0]/p) * ( pow(m2,p) - pow(m1,p) );
    }

  else
    {

      integral = 0;

      /* first */
      if (m1<Cp->ms[0])
        {
          mmin = m1;
          mmax = dmin(Cp->ms[0],m2);
          p = Cp->as[0];
          integral +=  (Cp->bs[0]/p) * ( pow(mmax,p) - pow(mmin,p) );
        }

      /* last */
      if (m2>Cp->ms[n-1])
        {
          mmin = dmax(Cp->ms[n-1],m1);
          mmax = m2;
          p = Cp->as[n];
          integral +=  (Cp->bs[n]/p) * ( pow(mmax,p) - pow(mmin,p) );
        }

      /* loop over other segments */
      for (i=0;i<n-1;i++)
        {
          mmin = dmax(Cp->ms[i  ],m1);
          mmax = dmin(Cp->ms[i+1],m2);
          if (mmin<mmax)
            {
              p = Cp->as[i+1];
              integral +=  (Cp->bs[i+1]/p) * ( pow(mmax,p) - pow(mmin,p) );
            }
        }

    }

  /* convert into mass unit mass unit */
  integral = integral *All.CMUtoMsol;

  return integral;

}





/*! Sample the imf using monte carlo approach
 */


static double imf_sampling(void)
{

  int i;
  int n;
  double m;
  double f;
  double pmin,pmax;

  n = Cp->n;

  /* init random */
  //srandom(irand);

  f = (double)random()/(double)RAND_MAX;


  if (n==0)
    {
      pmin = pow(Cp->Mmin,Cp->as[0]);
      pmax = pow(Cp->Mmax,Cp->as[0]);
      m    = pow(f*(pmax - pmin) + pmin ,1./Cp->as[0]);
      return m* All.MsoltoCMU;
    }

  else
    {


      if (f<Cp->fs[0])
        {
          pmin = pow(Cp->Mmin  ,Cp->as[0]);
          m	= pow(Cp->imf_Ntot*Cp->as[0]/Cp->bs[0]* (f-0) + pmin ,1./Cp->as[0]);
          return m* All.MsoltoCMU;

        }

      for (i=0;i<n-1;i++)
        {

          if (f<Cp->fs[i+1])
            {
              pmin = pow(Cp->ms[i]  ,Cp->as[i+1]);
              m    = pow(Cp->imf_Ntot*Cp->as[i+1]/Cp->bs[i+1]* (f-Cp->fs[i]) + pmin ,1./Cp->as[i+1]);
              return m* All.MsoltoCMU;
            }


        }


      /* last portion */
      pmin = pow(Cp->ms[n-1]  ,Cp->as[n]);
      m    = pow(Cp->imf_Ntot*Cp->as[n]/Cp->bs[n]* (f-Cp->fs[n-1]) + pmin ,1./Cp->as[n]);
      return m* All.MsoltoCMU;


    }



}


static double imf_sampling_from_random(double f)
{

  int i;
  int n;
  double m;
  double pmin,pmax;

  n = Cp->n;

  if (n==0)
    {
      pmin = pow(Cp->Mmin,Cp->as[0]);
      pmax = pow(Cp->Mmax,Cp->as[0]);
      m    = pow(f*(pmax - pmin) + pmin ,1./Cp->as[0]);
      return m* All.MsoltoCMU;
    }

  else
    {


      if (f<Cp->fs[0])
        {
          pmin = pow(Cp->Mmin  ,Cp->as[0]);
          m	= pow(Cp->imf_Ntot*Cp->as[0]/Cp->bs[0]* (f-0) + pmin ,1./Cp->as[0]);
          return m* All.MsoltoCMU;

        }

      for (i=0;i<n-1;i++)
        {

          if (f<Cp->fs[i+1])
            {
              pmin = pow(Cp->ms[i]  ,Cp->as[i+1]);
              m    = pow(Cp->imf_Ntot*Cp->as[i+1]/Cp->bs[i+1]* (f-Cp->fs[i]) + pmin ,1./Cp->as[i+1]);
              return m* All.MsoltoCMU;
            }


        }


      /* last portion */
      pmin = pow(Cp->ms[n-1]  ,Cp->as[n]);
      m    = pow(Cp->imf_Ntot*Cp->as[n]/Cp->bs[n]* (f-Cp->fs[n-1]) + pmin ,1./Cp->as[n]);
      return m* All.MsoltoCMU;

    }

}









/*! This function initializes the imf parameters
  defined in the chemistry file
*/


void init_imf(void)
{

  float integral = 0;
  float p;
  float cte;
  int i,n;
  double mmin,mmax;

  n = Cp->n;


  if (n==0)
    {
      p = Cp->as[0]+1;
      integral = integral + ( pow(Cp->Mmax,p)-pow(Cp->Mmin,p))/(p) ;
      Cp->bs[0] = 1./integral ;
    }
  else
    {
      cte = 1.0;

      if (Cp->Mmin < Cp->ms[0])
        {
          p = Cp->as[0]+1;
          integral = integral + (pow(Cp->ms[0],p) - pow(Cp->Mmin,p))/p;
        }


      for (i=0;i<n-1;i++)
        {
          cte = cte* pow( Cp->ms[i],( Cp->as[i] - Cp->as[i+1] ));
          p = Cp->as[i+1]+1;
          integral = integral + cte*(pow(Cp->ms[i+1],p) - pow(Cp->ms[i],p))/p;
        }


      if (Cp->Mmax > Cp->ms[n-1])
        {
          cte = cte* pow( Cp->ms[n-1] , ( Cp->as[n-1] - Cp->as[n] ) );
          p = Cp->as[n]+1;
          integral = integral + cte*(pow(Cp->Mmax,p) - pow(Cp->ms[n-1],p))/p;
        }

      /* compute all b */
      Cp->bs[0] = 1./integral;

      for (i=0;i<n;i++)
        {
          Cp->bs[i+1] = Cp->bs[i] * pow( Cp->ms[i],( Cp->as[i] - Cp->as[i+1] ));
        }

    }



  mmin = Cp->Mmin *All.MsoltoCMU;				/* in CMU */
  mmax = Cp->Mmax *All.MsoltoCMU;           /* in CMU */
  Cp->imf_Ntot = get_imf_N(mmin,mmax) *All.MsoltoCMU;     /* in CMU */


  /* init fs : mass fraction at ms */
  if (n>0)
    {

      for (i=0;i<n+1;i++)
        {
          mmax = Cp->ms[i] *All.MsoltoCMU;    /* in CMU */
          Cp->fs[i] = All.MsoltoCMU*get_imf_N(mmin,mmax)/Cp->imf_Ntot;
        }

    }



}














/*********************************/
/*                               */
/*********************************/

static PyObject *
chemistry_info(PyObject *self, PyObject *args)
{
 
  printf("This is pNbody.pychem !\n");

  return Py_BuildValue("O",Py_None);
}



static PyObject *
chemistry_init(PyObject *self, PyObject *args)
{
 
  init();
  
  return Py_BuildValue("O",Py_None);
}

static PyObject *
chemistry_set_parameters(PyObject *self, PyObject *args)
{
 
  PyObject *dict;


  if (! PyArg_ParseTuple(args, "O",&dict))
    return PyUnicode_FromString("error");

  /* check that it is a PyDictObject */
  if(!PyDict_Check(dict))
    {
      PyErr_SetString(PyExc_AttributeError, "argument is not a dictionary.");   
      return NULL;
    }  
  
  
  PyObject *key;
  PyObject *value;
  Py_ssize_t pos=0;
  Py_ssize_t i;

  while(PyDict_Next(dict,&pos,&key,&value))
    {
      
      if(PyUnicode_Check(key)) 
        if(strcmp(PyUnicode_AsUTF8(key), "Mmax")==0)
         if(PyLong_Check(value)||PyFloat_Check(value))
           Cp->Mmax = PyFloat_AsDouble(value); 

      if(PyUnicode_Check(key)) 
        if(strcmp(PyUnicode_AsUTF8(key), "Mmin")==0)
         if(PyLong_Check(value)||PyFloat_Check(value))
           Cp->Mmin = PyFloat_AsDouble(value); 

      if(PyUnicode_Check(key)) 
        if(strcmp(PyUnicode_AsUTF8(key), "as")==0)
         if(PyList_Check(value))
           {
            for (i=0;i<PyList_Size(value);i++)
              Cp->as[i]=PyFloat_AsDouble(  PyList_GetItem(value,i)); 
           }

      if(PyUnicode_Check(key)) 
        if(strcmp(PyUnicode_AsUTF8(key), "ms")==0)
         if(PyList_Check(value))
           {
            Cp->n = PyList_Size(value);
            for (i=0;i<PyList_Size(value);i++)
              Cp->ms[i]=PyFloat_AsDouble(  PyList_GetItem(value,i)); 
           }

    }


  init_imf();
  
  
  
  
  return Py_BuildValue("O",Py_None);
}




static PyObject *
chemistry_get_Mmax(PyObject *self, PyObject *args)
{
  return Py_BuildValue("d",(double)Cp->Mmax * All.MsoltoCMU);
}

static PyObject *
chemistry_get_Mmin(PyObject *self, PyObject *args)
{
  return Py_BuildValue("d",(double)Cp->Mmin * All.MsoltoCMU);
}


static PyObject *
chemistry_get_as(PyObject *self, PyObject *args)
{
  PyArrayObject *as;
  npy_intp   ld[1];
  int i;

  /* create output array */
  ld[0]= Cp->n+1;
  as  = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_DOUBLE);

  /* import values */
  for (i=0;i<Cp->n+1;i++)
    *(double *)PyArray_GETPTR1(as, i) = Cp->as[i];

  return PyArray_Return(as);
}

static PyObject *
chemistry_get_bs(PyObject *self, PyObject *args)
{
  PyArrayObject *bs;
  npy_intp   ld[1];
  int i;

  /* create output array */
  ld[0]= Cp->n+1;
  bs  = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_DOUBLE);

  /* import values */
  for (i=0;i<Cp->n+1;i++)
    *(double *)PyArray_GETPTR1(bs, i) = Cp->bs[i];

  return PyArray_Return(bs);
}

static PyObject *
chemistry_get_fs(PyObject *self, PyObject *args)
{
  PyArrayObject *fs;
  npy_intp   ld[1];
  int i;

  /* create output array */
  ld[0]= Cp->n;
  fs  = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_DOUBLE);

  /* import values */
  for (i=0;i<Cp->n;i++)
    *(double *)PyArray_GETPTR1(fs, i) = Cp->fs[i];

  return PyArray_Return(fs);
}




static PyObject *
chemistry_get_imf(PyObject *self, PyObject *args)
{

  PyArrayObject *m,*imf;
  int i,n;
  npy_intp ld[1];


  if (! PyArg_ParseTuple(args, "O",&m))
    return PyUnicode_FromString("error");

  m  = TO_DOUBLE(m);
  n  = PyArray_DIM(m, 0);

  /* create an output */
  ld[0] = n;
  imf = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_FLOAT);

  for(i = 0; i < n; i++)
    {
      *(double *)PyArray_GETPTR1(imf, i)  = get_imf(*(double *)PyArray_GETPTR1(m, i));
    }

  return PyArray_Return(imf);

}



static PyObject *
chemistry_get_imf_M(PyObject *self, PyObject *args)
{

  PyArrayObject *m1,*m2;
  double imf;
  
  if (! PyArg_ParseTuple(args, "OO",&m1,&m2))
    return PyUnicode_FromString("error");

  m1  = TO_DOUBLE(m1);
  m2  = TO_DOUBLE(m2);
  
  imf = get_imf_M(*(double *)PyArray_GETPTR1(m1, 0),*(double *)PyArray_GETPTR1(m2, 0));

  return Py_BuildValue("d", imf);
}




static PyObject *
chemistry_get_imf_N(PyObject *self, PyObject *args)
{

  PyArrayObject *m1,*m2;
  double imf;
  
  if (! PyArg_ParseTuple(args, "OO",&m1,&m2))
    return PyUnicode_FromString("error");

  m1  = TO_DOUBLE(m1);
  m2  = TO_DOUBLE(m2);
  
  imf = get_imf_N(*(double *)PyArray_GETPTR1(m1, 0),*(double *)PyArray_GETPTR1(m2, 0));

  return Py_BuildValue("d", imf);
}







static PyObject *
chemistry_get_imf_Ntot(PyObject *self, PyObject *args)
{
  return Py_BuildValue("d",(double)Cp->imf_Ntot*All.CMUtoMsol);		/* in code mass unit */
}


static PyObject *
chemistry_imf_sampling(PyObject *self, PyObject *args)
{
  PyArrayObject *ms;
  npy_intp   ld[1];
  int i;
  int n,seed;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "ii", &n,&seed))
    return NULL;

  /* create output array */
  ld[0]= n;
  ms  = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_DOUBLE);

  srandom(seed);

  /* import values */
  for (i=0;i<n;i++)
    *(double *)PyArray_GETPTR1(ms, i) = imf_sampling();

  return PyArray_Return(ms);
}


static PyObject *
chemistry_imf_sampling_with_boundaries(PyObject *self, PyObject *args)
{
  PyArrayObject *ms;
  npy_intp   ld[1];
  int i;
  int n,seed;
  double f1,f2,f;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iidd", &n,&seed,&f1,&f2))
    return NULL;

  /* create output array */
  ld[0]= n;
  ms  = (PyArrayObject *) PyArray_SimpleNew(1,ld,NPY_DOUBLE);

  srandom(seed);

  /* import values */
  for (i=0;i<n;i++) {
    f = f1 + ((double)rand() / (double)RAND_MAX) * (f2 - f1);
    *(double *)PyArray_GETPTR1(ms, i) = imf_sampling_from_random(f);
  }
  
  return PyArray_Return(ms);
}



static PyObject *
chemistry_imf_init_seed(PyObject *self, PyObject *args)
{
  int seed;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "i",&seed))
    return NULL;

  srandom(seed);

  return Py_BuildValue("i",1);
}


static PyObject *
chemistry_imf_sampling_single(PyObject *self, PyObject *args)
{

  return Py_BuildValue("f",imf_sampling());
}


static PyObject *
chemistry_imf_sampling_single_from_random(PyObject *self, PyObject *args)
{

  double f;

  if (!PyArg_ParseTuple(args, "d",&f))
    return NULL;

  return Py_BuildValue("f",imf_sampling_from_random(f));
}














/* definition of the method table */

static PyMethodDef pychemMethods[] = {

  {"info",  chemistry_info, METH_VARARGS,
   "Get info."},

  {"init",  chemistry_init, METH_VARARGS,
   "init."},

  {"set_parameters",  chemistry_set_parameters, METH_VARARGS,
   "set parameters."},   

  {"get_Mmax",  chemistry_get_Mmax, METH_VARARGS,
   "Get max star mass of the IMF, in code unit."},

  {"get_Mmin",  chemistry_get_Mmin, METH_VARARGS,
   "Get min star mass of the IMF, in code unit."},

  {"get_as",  chemistry_get_as, METH_VARARGS,
   "Get power coefficients."},

  {"get_bs",  chemistry_get_bs, METH_VARARGS,
   "Get normalisation coefficients."},

  {"get_fs",  chemistry_get_fs, METH_VARARGS,
   "Get fs, mass fraction at ms."},
   
  {"get_imf",  chemistry_get_imf, METH_VARARGS,
   "Compute corresponding imf value."},

  {"get_imf_M",  chemistry_get_imf_M, METH_VARARGS,
   "Compute the mass fraction between m1 and m2."},

  {"get_imf_N",  chemistry_get_imf_N, METH_VARARGS,
   "Compute the fraction number between m1 and m2."},

  {"get_imf_Ntot",  chemistry_get_imf_Ntot, METH_VARARGS,
   "Get number of stars in the imf, per unit mass."},
      
  {"imf_sampling",  chemistry_imf_sampling, METH_VARARGS,
   "Sample imf with n points."},

  {"imf_sampling_with_boundaries",  chemistry_imf_sampling_with_boundaries, METH_VARARGS,
   "Sample imf with n points in the probability range f1, f2"},
  
  {"imf_sampling_single",  chemistry_imf_sampling_single, METH_VARARGS,
   "Sample imf with a single point."},

  {"imf_init_seed",  chemistry_imf_init_seed, METH_VARARGS,
   "Init the random seed."},

  {"imf_sampling_single_from_random",  chemistry_imf_sampling_single_from_random, METH_VARARGS,
   "Sample imf with a single point from a given random number."},

   

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef pychemmodule = {
  PyModuleDef_HEAD_INIT,
  "chemistry",
  "C wraper of the chemistry Gear module",
  -1,
  pychemMethods,
  NULL, /* m_slots */
  NULL, /* m_traverse */
  NULL, /* m_clear */
  NULL  /* m_free */
};


PyMODINIT_FUNC PyInit_pychem(void) {
  PyObject *m;
  m = PyModule_Create(&pychemmodule);
  if (m == NULL) return NULL;

  import_array();
  init();
  init_imf();

  return m;
}
