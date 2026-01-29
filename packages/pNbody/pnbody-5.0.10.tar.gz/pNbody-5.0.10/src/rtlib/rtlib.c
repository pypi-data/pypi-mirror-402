#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>


#include "constants.h"
#include "cross_sections.h"
#include "photon_interaction_rates.h"


static PyObject *
rtlib_info(PyObject *self, PyObject *args)
{

    printf("Welcome to the rtlib module.\n");
    
    return PyLong_FromLong(1);
}


static PyObject *
rtlib_getNuiHI(void)
{
  return PyFloat_FromDouble(const_NuiHI);
}

static PyObject *
rtlib_getNuiHeI(void)
{
  return PyFloat_FromDouble(const_NuiHeI);
}

static PyObject *
rtlib_getNuiHeII(void)
{
  return PyFloat_FromDouble(const_NuiHeII);
}


static PyObject *
rtlib_getEiHI(void)
{
  return PyFloat_FromDouble(const_EiHI);
}

static PyObject *
rtlib_getEiHeI(void)
{
  return PyFloat_FromDouble(const_EiHeI);
}

static PyObject *
rtlib_getEiHeII(void)
{
  return PyFloat_FromDouble(const_EiHeII);
}

static PyObject *
rtlib_getkB(void)
{
  return PyFloat_FromDouble(const_kboltz);
}

static PyObject *
rtlib_geth_planck(void)
{
  return PyFloat_FromDouble(const_planck_h);
}

static PyObject *
rtlib_getc(void)
{
  return PyFloat_FromDouble(const_speed_light_c);
}

static PyObject *
rtlib_getL_Sol(void)
{
  return PyFloat_FromDouble(const_L_Sun);
}










static PyObject *
rtlib_get_cross_sections(PyObject *self, PyObject *args, PyObject *kwds)
{
  
  /* Blackbody temperature */
  double T_blackbody = 1e5; /* K */
  double NuiHI   = const_NuiHI;
  double NuiHeI  = const_NuiHeI;
  double NuiHeII = const_NuiHeII;
  
  PyArrayObject *array_cse;
  PyArrayObject *array_csn;
  PyArrayObject *array_mean_photon_energies;
    
  npy_intp ld[1];
  ld[0] = RT_NGROUPS;
  array_cse                  = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  array_csn                  = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  array_mean_photon_energies = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  
  
  static char *kwlist[] = {"T_blackbody","NuiHI","NuiHeI","NuiHeII", NULL};

  if (! PyArg_ParseTupleAndKeywords(args, kwds, "|dddd",kwlist,&T_blackbody,&NuiHI,&NuiHeI,&NuiHeII))
    {
      PyErr_SetString(PyExc_ValueError,"rtlib_get_cross_sections, error in parsing arguments.");
      return NULL;
    }
      
  /* Ionization frequency for HI, HeI, HeII */
  double frequency_bins_Hz[3] = {NuiHI, NuiHeI, NuiHeII}; /* Hz */


  /* Get photon cross sections and mean energies */
  /* ------------------------------------------- */
  /* Note that the result is always in cgs. */
  double **cse = malloc(RT_NGROUPS * sizeof(double *));
  double **csn = malloc(RT_NGROUPS * sizeof(double *));
  double mean_photon_energies[RT_NGROUPS];
  for (int group = 0; group < RT_NGROUPS; group++) {
    cse[group] = malloc(RT_NIONIZING_SPECIES * sizeof(double));
    csn[group] = malloc(RT_NIONIZING_SPECIES * sizeof(double));
    mean_photon_energies[group] = 0.;
  }

  get_cross_sections(T_blackbody, frequency_bins_Hz, cse, csn,mean_photon_energies);


  /* transform to numpy arrays */
  for (int i = 0; i < ld[0]; i++) {
    *(float *)PyArray_GETPTR1(array_cse, i) = (float)*cse[i];
    *(float *)PyArray_GETPTR1(array_csn, i) = (float)*csn[i];
    *(float *)PyArray_GETPTR1(array_mean_photon_energies, i) = (float)mean_photon_energies[i];
  }
  
  return Py_BuildValue("(OOO)", array_cse, array_csn, array_mean_photon_energies);
}




static PyObject *
rtlib_get_interaction_rates(PyObject *self, PyObject *args, PyObject *kwds)
{
  
  /* Blackbody temperature */
  double T_blackbody = 1e5; /* K */
  double NuiHI   = const_NuiHI;
  double NuiHeI  = const_NuiHeI;
  double NuiHeII = const_NuiHeII;
  
  double HI_densities_cgs     = 1.67262e-24; //g/cm3 //HI   grackle_fields.HI_density[0] * density_units;
  double HII_densities_cgs    = 0;  //HII  grackle_fields.HII_density[0] * density_units;
  double HeI_densities_cgs    = 0;  //HeI  grackle_fields.HeI_density[0] * density_units;
  double HeII_densities_cgs   = 0;  //HeII grackle_fields.HeII_density[0] * density_units;
  double HeIII_densities_cgs  = 0;  //HeII grackle_fields.HeIII_density[0] * density_units;
  double e_densities_cgs      = 0;  //e grackle_fields.e_density[0] * density_units;
  
  double LHI_cgs              = 1.350e+01; /* photon energy in the 1st group erg / cm^2 / s */
  double LHeI_cgs             = 2.779e+01; /* photon energy in the 2nd group erg / cm^2 / s */
  double LHeII_cgs            = 6.152e+00; /* photon energy in the 3rd group erg / cm^2 / s */
  
  
  static char *kwlist[] = {"T_blackbody",
                           "NuiHI",
                           "NuiHeI",
                           "NuiHeII",
                           "HI_densities_cgs",
                           "HII_densities_cgs",
                           "HeI_densities_cgs",
                           "HeII_densities_cgs",
                           "HeIII_densities_cgs",
                           "e_densities_cgs",
                           "LHI_cgs",
                           "LHeI_cgs",
                           "LHeII_cgs",
                            NULL};
  
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "|ddddddddddddd",kwlist,&T_blackbody,&NuiHI,&NuiHeI,&NuiHeII,
                                                                     &HI_densities_cgs,&HII_densities_cgs,
                                                                     &HeI_densities_cgs,  
                                                                     &HeII_densities_cgs,&HeIII_densities_cgs,
                                                                     &e_densities_cgs,&LHI_cgs,&LHeI_cgs,&LHeII_cgs))
 



 
    {
      PyErr_SetString(PyExc_ValueError,"rtlib_get_cross_sections, error in parsing arguments.");
      return NULL;
    }
      

        
  /* Ionization frequency for HI, HeI, HeII */
  double frequency_bins_Hz[3] = {NuiHI, NuiHeI, NuiHeII}; /* Hz */

  printf("rtlib_get_interaction_rates: origin of those values!\n");
  double fixed_luminosity_cgs[3] = {LHI_cgs, LHeI_cgs, LHeII_cgs}; /* erg / cm^2 / s */


  double radiation_energy_density_cgs[3] = {0., 0., 0.};
  for (int g = 0; g < RT_NGROUPS; g++) {
    radiation_energy_density_cgs[g] =
        fixed_luminosity_cgs[g] / const_speed_light_c;
  }



  /* Get photon cross sections and mean energies */
  /* ------------------------------------------- */
  /* Note that the result is always in cgs. */
  double **cse = malloc(RT_NGROUPS * sizeof(double *));
  double **csn = malloc(RT_NGROUPS * sizeof(double *));
  double mean_photon_energies[RT_NGROUPS];
  for (int group = 0; group < RT_NGROUPS; group++) {
    cse[group] = malloc(RT_NIONIZING_SPECIES * sizeof(double));
    csn[group] = malloc(RT_NIONIZING_SPECIES * sizeof(double));
    mean_photon_energies[group] = 0.;
  }

  get_cross_sections(T_blackbody, frequency_bins_Hz, cse, csn,mean_photon_energies);


  /* densities in cgs. */
  float ion_densities_cgs[6];
  ion_densities_cgs[0] = HI_densities_cgs;    //g/cm3 //HI   grackle_fields.HI_density[0] * density_units;
  ion_densities_cgs[1] = HII_densities_cgs;   //HII  grackle_fields.HII_density[0] * density_units;
  ion_densities_cgs[2] = HeI_densities_cgs;   //HeI  grackle_fields.HeI_density[0] * density_units;
  ion_densities_cgs[3] = HeII_densities_cgs;  //HeII grackle_fields.HeII_density[0] * density_units;
  ion_densities_cgs[4] = HeIII_densities_cgs; //HeII grackle_fields.HeIII_density[0] * density_units;
  ion_densities_cgs[5] = e_densities_cgs;     //e grackle_fields.e_density[0] * density_units;


  float iact_rates[5] = {0., 0., 0., 0., 0.};
  
  get_interaction_rates(radiation_energy_density_cgs, ion_densities_cgs,
                        cse, csn, mean_photon_energies,
                        iact_rates);



  PyArrayObject *rates_cgs;
  PyArrayObject *rates_grackle;
    
  npy_intp ld[1];
  ld[0] = 5;
  rates_cgs         = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  rates_grackle     = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* rates in cgs */  
  for (int i = 0; i < ld[0]; i++)
    *(float *)PyArray_GETPTR1(rates_cgs, i) = (float)iact_rates[i];



  /* Unit conversions for grackle */
  /* Grackle wants heating rate in units of / nHI_cgs */
  iact_rates[0] /= (ion_densities_cgs[0] / const_mh);
  
  
  /* Unit conversions for grackle */
  /* Grackle wants them in 1/internal_time_units */
  
  double length_units = 3.08567758e24;  /* Mpc in centimeters */
  double velocity_units = 1.e5;
  double time_units = length_units / velocity_units;
  
  iact_rates[1] /= (1. / time_units);
  iact_rates[2] /= (1. / time_units);
  iact_rates[3] /= (1. / time_units);
  iact_rates[4] /= (1. / time_units);

  /* rates for grackle */  
  for (int i = 0; i < ld[0]; i++)
    *(float *)PyArray_GETPTR1(rates_grackle, i) = (float)iact_rates[i];

  return Py_BuildValue("(OO)", rates_cgs,rates_grackle);

}





static PyMethodDef rtlibMethods[] = {

    {"info",  (PyCFunction)rtlib_info, METH_VARARGS,
     "Normalized 1D cubic kernel"},
     
    {"getNuiHI",  (PyCFunction)rtlib_getNuiHI, METH_VARARGS,
     "Return the ionized frequency of Hydrogen in Hz"},

    {"getNuiHeI",  (PyCFunction)rtlib_getNuiHeI, METH_VARARGS,
     "Return the ionized frequency of neutral Helium in Hz"},
     
    {"getNuiHeII",  (PyCFunction)rtlib_getNuiHeII, METH_VARARGS,
     "Return the ionized frequency of 1-ionized Helium in Hz"},               

    {"getEiHI",  (PyCFunction)rtlib_getEiHI, METH_VARARGS,
     "Return the ionized energy of Hydrogen in eV"},

    {"getEiHeI",  (PyCFunction)rtlib_getEiHeI, METH_VARARGS,
     "Return the ionized energy of neutral Helium in eV"},
     
    {"getEiHeII",  (PyCFunction)rtlib_getEiHeII, METH_VARARGS,
     "Return the ionized energy of 1-ionized Helium in eV"},   

    {"getkB",  (PyCFunction)rtlib_getkB, METH_VARARGS,
     "Return the Boltzman constant in CGS"},  

    {"geth_planck",  (PyCFunction)rtlib_geth_planck, METH_VARARGS,
     "Return the Planck constant in CGS"},
     
    {"getc",  (PyCFunction)rtlib_getc, METH_VARARGS,
     "Return the lightspeed constant in CGS"},     

    {"getL_Sol",  (PyCFunction)rtlib_getL_Sol, METH_VARARGS,
     "Return the solar luminosity in CGS"},  
     
 
     
    {"get_cross_sections",  (PyCFunction)rtlib_get_cross_sections, METH_VARARGS|METH_KEYWORDS,
     "allocate and compute the averaged cross sections for each photon group and ionizing species."},     
     
    {"get_interaction_rates",  (PyCFunction)rtlib_get_interaction_rates, METH_VARARGS|METH_KEYWORDS,
     "compute the heating, ionization, and dissassociation rates for the particle radiation field as needed by grackle, and the net absorption/emission rates for each photon group"},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};


static struct PyModuleDef rtlibmodule = {
    PyModuleDef_HEAD_INIT,
    "rtlib",   /* name of module */
    "Defines some rt functions", /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    rtlibMethods
};


PyMODINIT_FUNC
PyInit_rtlib(void)
{
  PyObject *m;
  m = PyModule_Create(&rtlibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
