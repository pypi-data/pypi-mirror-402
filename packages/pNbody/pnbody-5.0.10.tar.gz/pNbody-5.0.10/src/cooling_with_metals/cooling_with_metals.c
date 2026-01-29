#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>
#include <stdio.h>
#include <string.h>

#include <gsl/gsl_errno.h>
#include <gsl/gsl_math.h>
#include <gsl/gsl_roots.h>
#include <gsl/gsl_spline.h>

#define TO_DOUBLE(a) \
  ((PyArrayObject *)PyArray_CastToType(a, PyArray_DescrFromType(NPY_DOUBLE), 0))

/* Write an error message compatible with python but does not return */
#define error(s, ...)                                                     \
  ({                                                                      \
    fflush(stdout);                                                       \
    char msg[400];                                                        \
    sprintf(msg, "%s:%s():%i: " s "\n", __FILE__, __FUNCTION__, __LINE__, \
            ##__VA_ARGS__);                                               \
    PyErr_SetString(PyExc_ValueError, msg);                               \
  })

/*
  ****************************************************
  these variables are already defined in Gadget
  ****************************************************
*/

#ifdef DOUBLEPRECISION /*!< If defined, the variable type FLOAT is set to \
                          "double", otherwise to FLOAT */
#define FLOAT double
#else
#define FLOAT float
#endif

#define MAXLEN_FILENAME 100

#define HYDROGEN_MASSFRAC 0.76
#define GAMMA (5.0 / 3)
#define GAMMA_MINUS1 (GAMMA - 1)

/* Some physical constants in cgs units */

#define GRAVITY 6.672e-8 /*!< Gravitational constant (in cgs units) */
#define SOLAR_MASS 1.989e33
#define SOLAR_LUM 3.826e33
#define RAD_CONST 7.565e-15
#define AVOGADRO 6.0222e23
#define BOLTZMANN 1.3806e-16
#define GAS_CONST 8.31425e7
#define C 2.9979e10
#define PLANCK 6.6262e-27
#define CM_PER_MPC 3.085678e24
#define PROTONMASS 1.6726e-24
#define ELECTRONMASS 9.10953e-28
#define THOMPSON 6.65245e-25
#define ELECTRONCHARGE 4.8032e-10
#define HUBBLE 3.2407789e-18      /* in h/sec */
#define YEAR_IN_SECOND 31536000.0 /* year in sec */
#define METALLICITY_SOLAR 0.02
#define FEH_SOLAR 0.001771 /*  0.00181 */
#define MGH_SOLAR 0.00091245

#define PI 3.1415926535897931
#define TWOPI 6.2831853071795862

#define FE 0

struct global_data_all_processes {
  double InitGasMetallicity;
  char CoolingFile[MAXLEN_FILENAME];
  double *logT;
  double *logL;
  gsl_interp_accel *acc_cooling_spline;
  gsl_spline *cooling_spline;

  /*
    new metal dependent cooling
  */
  double CoolingParameters_zmin;
  double CoolingParameters_zmax;
  double CoolingParameters_slz;
  double CoolingParameters_tmin;
  double CoolingParameters_tmax;
  double CoolingParameters_slt;
  double CoolingParameters_FeHSolar;
  double CoolingParameters_cooling_data_max;
  double CoolingParameters_cooling_data[9][171];
  int CoolingParameters_p;
  int CoolingParameters_q;

  double Boltzmann;
  double ProtonMass;
  double mumh;

  double UnitLength_in_cm;
  double UnitMass_in_g;
  double UnitVelocity_in_cm_per_s;
  double UnitTime_in_s;
  double UnitEnergy_in_cgs;

  double Timebase_interval;
  double MinEgySpec;

} All;

int ThisTask = 0;

/****************************************************************************************
 *
 *
 *
 *   				 GADGET COOLING PART
 *
 *
 *
 ****************************************************************************************/

/*! initialize cooling function (the metallicity is fixed)
 *
 * T  = temperature
 * L0 = m000  primordial metallicity
 * L1 = m-30
 * L2 = m-20
 * L3 = m-10
 * L4 = m-05
 * L5 = m-00  solar metallicity
 * L6 = m+05
 */
int init_cooling(FLOAT metallicity) {

  FILE *fd;
  int n, i;
  char line[72];
  float T, L0, L1, L2, L3, L4, L5, L6;
  int MetallicityIndex = 4;

  /* find the right index */
  if (All.InitGasMetallicity < -3)
    MetallicityIndex = 0;
  else {
    if (All.InitGasMetallicity < -2)
      MetallicityIndex = 1;
    else {
      if (All.InitGasMetallicity < -1)
        MetallicityIndex = 2;
      else {
        if (All.InitGasMetallicity < -0.5)
          MetallicityIndex = 3;
        else {
          if (All.InitGasMetallicity < 0)
            MetallicityIndex = 4;
          else {
            MetallicityIndex = 5;
          }
        }
      }
    }
  }

  fd = fopen(All.CoolingFile, "r");
  int test = fscanf(fd, "# %6d\n", &n);
  if (test != 1) {
    error("Failed to scan file %s", All.CoolingFile);
    return 1;
  }

  /* allocate memory */
  All.logT = malloc(n * sizeof(double));
  All.logL = malloc(n * sizeof(double));

  /* read empty line */
  char *test_c = fgets(line, sizeof(line), fd);
  if (test_c == NULL) {
    error("Failed to empty line");
    return 1;
  }

  /* read file */

  for (i = 0; i < n; i++) {

    test = fscanf(fd, "%f %f %f %f %f %f %f %f\n", &T, &L0, &L1, &L2, &L3, &L4,
                  &L5, &L6);

    if (test != 8) {
      error("Failed to scan line %i", i);
      return 1;
    }

    /* keep only solar values */
    All.logT[i] = (double)T;

    switch (MetallicityIndex) {
      case 0:
        All.logL[i] = (double)L0;
        break;
      case 1:
        All.logL[i] = (double)L1;
        break;
      case 2:
        All.logL[i] = (double)L2;
        break;
      case 3:
        All.logL[i] = (double)L3;
        break;
      case 4:
        All.logL[i] = (double)L4;
        break;
      case 5:
        All.logL[i] = (double)L5;
        break;
      case 6:
        All.logL[i] = (double)L6;
        break;
    }
  }

  fclose(fd);

  /* init interpolation */
  All.acc_cooling_spline = gsl_interp_accel_alloc();
  All.cooling_spline = gsl_spline_alloc(gsl_interp_cspline, n);
  gsl_spline_init(All.cooling_spline, All.logT, All.logL, n);

#ifdef OUTPUT_COOLING_FUNCTION
  /* test cooling */
  double logT;
  double l;
  logT = 1.;
  while (logT < 8) {

    T = pow(10, logT);
    l = log10(cooling_function(T));

    if (ThisTask == 0) printf("%8.3f %8.3f\n", logT, l);

    logT = logT + 0.05;
  }
#endif

  return 0;
}

/*! This function return the normalized cooling function, that depends on
 * metallicity
 */
double cooling_function_with_metals(double temperature, double metal) {

  double cooling;
  double T, Z;
  double rt, rz, ft, fz, v1, v2, v;
  int it, iz, itp, izp;

  double zmin, zmax, slz, tmin, slt, FeHSolar, cooling_data_max;

  zmin = All.CoolingParameters_zmin;
  zmax = All.CoolingParameters_zmax;
  slz = All.CoolingParameters_slz;
  tmin = All.CoolingParameters_tmin;
  slt = All.CoolingParameters_slt;
  FeHSolar = All.CoolingParameters_FeHSolar;
  cooling_data_max = All.CoolingParameters_cooling_data_max;

  cooling = 0.0;

  T = log10(temperature);
  Z = log10(metal / FeHSolar + 1.e-10);

  if (Z > zmax) {
    /*print *,'Warning: Z>Zmax for',i*/
    Z = zmax;
  }

  if (Z < zmin) {

    rt = (T - tmin) / slt;

    it = (int)rt;

    if (it < cooling_data_max)
      it = (int)rt;
    else
      it = cooling_data_max;

    itp = it + 1;

    ft = rt - it;

    fz = (10. + Z) / (10. + zmin);

    v1 = ft * (All.CoolingParameters_cooling_data[1][itp] -
               All.CoolingParameters_cooling_data[1][it]) +
         All.CoolingParameters_cooling_data[1][it];
    v2 = ft * (All.CoolingParameters_cooling_data[0][itp] -
               All.CoolingParameters_cooling_data[0][it]) +
         All.CoolingParameters_cooling_data[0][it];
    v = v2 + fz * (v1 - v2);

  } else {

    rt = (T - tmin) / slt;
    rz = (Z - zmin) / slz + 1.0;

    it = (int)rt;

    if (it < cooling_data_max)
      it = (int)rt;
    else
      it = cooling_data_max;

    iz = (int)rz;

    itp = it + 1;
    izp = iz + 1;

    ft = rt - it;
    fz = rz - iz;

    v1 = ft * (All.CoolingParameters_cooling_data[izp][itp] -
               All.CoolingParameters_cooling_data[izp][it]) +
         All.CoolingParameters_cooling_data[izp][it];
    v2 = ft * (All.CoolingParameters_cooling_data[iz][itp] -
               All.CoolingParameters_cooling_data[iz][it]) +
         All.CoolingParameters_cooling_data[iz][it];
    v = v2 + fz * (v1 - v2);
  }

  cooling = pow(10, v);

  return cooling;
}

int init_cooling_with_metals(void) {

  /*

  zmin zmax slz
  tmin tmax slt
  FeHSolar
  p k

  */

  FILE *fd;
  int p, k, i, j;
  float zmin, zmax, slz, tmin, tmax, slt, FeHSolar;
  float lbd;

  fd = fopen(All.CoolingFile, "r");
  int test = fscanf(fd, "%f %f %f\n", &zmin, &zmax, &slz);
  if (test != 3) {
    error("Failed to read zmin, zmax, slz");
    return 1;
  }

  test = fscanf(fd, "%f %f %f\n", &tmin, &tmax, &slt);
  if (test != 3) {
    error("Failed to read tmin, tmax, slt");
    return 1;
  }

  test = fscanf(fd, "%f\n", &FeHSolar);
  if (test != 1) {
    error("Failed to read FeHSolar");
    return 1;
  }

  test = fscanf(fd, "%d %d\n", &p, &k);
  if (test != 2) {
    error("Failed to read p, k");
    return 1;
  }

  All.CoolingParameters_zmin = zmin;
  All.CoolingParameters_zmax = zmax;
  All.CoolingParameters_slz = slz;
  All.CoolingParameters_tmin = tmin;
  All.CoolingParameters_tmax = tmax;
  All.CoolingParameters_slt = slt;
  All.CoolingParameters_FeHSolar = FEH_SOLAR; /* instead of FeHSolar*/
  All.CoolingParameters_cooling_data_max = k - 2;

  for (i = 0; i < p; i++)
    for (j = 0; j < k; j++) {
      test = fscanf(fd, "%f\n", &lbd);
      if (test != 1) {
        error("Failed to get lbd");
        return 1;
      }
      All.CoolingParameters_cooling_data[i][j] = lbd;
    }

  fclose(fd);

#ifdef OUTPUT_COOLING_FUNCTION
  /* test cooling */
  double logT, T;
  double l;
  double metal;
  logT = 1.;

  metal = (pow(10, All.InitGasMetallicity) - 1e-10) *
          All.CoolingParameters_FeHSolar;
  while (logT < 8) {

    T = pow(10, logT);
    l = log10(cooling_function_with_metals(T, metal));

    if (ThisTask == 0) printf("%8.3f %8.3f\n", logT, l);

    logT = logT + 0.05;
  }
#endif

  return 0;
}

/****************************************************************************************
 *
 *
 *
 *   				 OTHER C FUNCTIONS
 *
 *
 *
 ****************************************************************************************/

void set_default_parameters(void) {

  strcpy(All.CoolingFile, "/home/epfl/revaz/.pNbody/cooling_with_metals.dat");

  All.UnitLength_in_cm = 3.085e+21;
  All.UnitMass_in_g = 1.989e+43;
  All.UnitVelocity_in_cm_per_s = 20725573.785998672;

  All.Timebase_interval = 0.001;
  All.MinEgySpec = 0;
}

void set_parameters(PyObject *params_dict) {

  PyObject *key;
  PyObject *value;
  Py_ssize_t pos = 0;
  double dvalue;

  while (PyDict_Next(params_dict, &pos, &key, &value)) {

    if (PyUnicode_Check(key)) {

      if (strcmp(PyUnicode_AsUTF8(key), "UnitLength_in_cm") == 0)
        if (PyLong_Check(value) || PyLong_Check(value) ||
            PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          All.UnitLength_in_cm = dvalue;
        }

      if (strcmp(PyUnicode_AsUTF8(key), "UnitMass_in_g") == 0)
        if (PyLong_Check(value) || PyLong_Check(value) ||
            PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          All.UnitMass_in_g = dvalue;
        }

      if (strcmp(PyUnicode_AsUTF8(key), "UnitVelocity_in_cm_per_s") == 0)
        if (PyLong_Check(value) || PyLong_Check(value) ||
            PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          All.UnitVelocity_in_cm_per_s = dvalue;
        }

      if (strcmp(PyUnicode_AsUTF8(key), "CoolingFile") == 0)
        if (PyUnicode_Check(value)) {
          strcpy(All.CoolingFile, PyUnicode_AsUTF8(value));
        }
    }
  }
}

void set_units(void) {

  double meanweight;

  All.UnitTime_in_s = All.UnitLength_in_cm / All.UnitVelocity_in_cm_per_s;
  All.UnitEnergy_in_cgs = All.UnitMass_in_g * pow(All.UnitLength_in_cm, 2) /
                          pow(All.UnitTime_in_s, 2);

  meanweight =
      4.0 / (1 + 3 * HYDROGEN_MASSFRAC); /* note: we assume neutral gas here */
  /*meanweight = 4 / (8 - 5 * (1 - HYDROGEN_MASSFRAC));*/ /* note: we assume
                                                             FULL ionized gas
                                                             here */

  All.Boltzmann = BOLTZMANN / All.UnitEnergy_in_cgs;
  All.ProtonMass = PROTONMASS / All.UnitMass_in_g;
  All.mumh = All.ProtonMass * meanweight;
}

double lambda_from_Density_Entropy_FeH(FLOAT Density, FLOAT Entropy,
                                       FLOAT FeH) {
  /*
    Density and Entropy in code units

    return lambda in code units

    The function corresponds to
    double lambda(FLOAT Density,FLOAT Entropy,int phase,int i)
    in Gadget

  */

  double nH, nH2, T, l;

  nH = HYDROGEN_MASSFRAC * Density / All.ProtonMass;
  nH2 = nH * nH;

  T = All.mumh / All.Boltzmann * Entropy * pow(Density, GAMMA_MINUS1);

  l = cooling_function_with_metals(T, FeH);

  /* convert lambda' in user units */
  l = l / All.UnitEnergy_in_cgs / pow(All.UnitLength_in_cm, 3) *
      All.UnitTime_in_s;
  l = l * nH2;

  return l;
}

double lambda_from_Density_EnergyInt_FeH(FLOAT Density, FLOAT EnergyInt,
                                         FLOAT FeH) {
  /*
    Density and EnergyInt in code units

    return lambda in code units


  */

  double nH, nH2, T, l;

  nH = HYDROGEN_MASSFRAC * Density / All.ProtonMass;
  nH2 = nH * nH;

  T = GAMMA_MINUS1 * All.mumh / All.Boltzmann * EnergyInt;

  l = cooling_function_with_metals(T, FeH);

  /* convert lambda' in user units */
  l = l / All.UnitEnergy_in_cgs / pow(All.UnitLength_in_cm, 3) *
      All.UnitTime_in_s;
  l = l * nH2;

  return l;
}

double lambda_from_Density_Temperature_FeH(FLOAT Density, FLOAT Temperature,
                                           FLOAT FeH) {
  /*
    Density in code units

    return lambda in code units

  */

  double nH, nH2, T, l;

  nH = HYDROGEN_MASSFRAC * Density / All.ProtonMass;
  nH2 = nH * nH;

  T = Temperature;

  l = cooling_function_with_metals(T, FeH);

  /* convert lambda' in user units */
  l = l / All.UnitEnergy_in_cgs / pow(All.UnitLength_in_cm, 3) *
      All.UnitTime_in_s;
  l = l * nH2;

  return l;
}

double lambda_normalized_from_Temperature_FeH(FLOAT Temperature, FLOAT FeH) {
  /*

    return lambda normalized (in mks)

  */

  double T, l;

  T = Temperature;
  l = cooling_function_with_metals(T, FeH);

  return l;
}

double cooling_time_from_Density_Temperature_FeH(FLOAT Density,
                                                 FLOAT Temperature, FLOAT FeH) {
  /*
    Cooling time in code units

  */

  double u, l, dudt, tc;

  /* energy int */
  u = Temperature / GAMMA_MINUS1 / All.mumh * All.Boltzmann;

  /* lambda in user units */
  l = lambda_from_Density_Temperature_FeH(Density, Temperature, FeH);

  dudt = l / Density;

  tc = u / dudt;

  return tc;
}

double cooling_time_from_Density_EnergyInt_FeH(FLOAT Density, FLOAT EnergyInt,
                                               FLOAT FeH) {
  /*
    Cooling time in code units

  */

  double u, l, dudt, tc;

  /* energy int */
  u = EnergyInt;

  /* lambda in user units */
  l = lambda_from_Density_EnergyInt_FeH(Density, EnergyInt, FeH);

  dudt = l / Density;

  tc = u / dudt;

  return tc;
}

/****************************************************************************************
 *
 *
 *
 *   				 NEW C FUNCTIONS FOR COOLING INTEGRATION
 *
 *
 *
 ****************************************************************************************/

double a3inv = 1.;
double hubble_a = 1;

double lambda(FLOAT Density, FLOAT Entropy, FLOAT Metal) {

  double l;
  l = lambda_from_Density_Entropy_FeH(Density, Entropy, Metal);

  return l;
}

/*! returns the maximum of two double
 */
double dmax(double x, double y) {
  if (x > y)
    return x;
  else
    return y;
}

/*! returns the minimum of two double
 */
double dmin(double x, double y) {
  if (x < y)
    return x;
  else
    return y;
}

/*! returns the maximum of two integers
 */
int imax(int x, int y) {
  if (x > y)
    return x;
  else
    return y;
}

/*! returns the minimum of two integers
 */
int imin(int x, int y) {
  if (x < y)
    return x;
  else
    return y;
}

float cooling1(int tstart, int tend, FLOAT Entropy, FLOAT Density, FLOAT Metal,
               FLOAT DtEntropy, FLOAT *newEntropy, FLOAT *newDtEntropy) {

  double dt, dadt, tcool, dt_entr;
  double minentropy = 0;
  double MinSizeTimestep, ErrTolIntAccuracy;
  int ti_current, istep;
  int ti_step;
  FLOAT oldEntropy, oldDtEntropy, DEntropy;
  double lmbd = 0;

  if (All.MinEgySpec)
    minentropy =
        All.MinEgySpec * GAMMA_MINUS1 / pow(Density * a3inv, GAMMA_MINUS1);

  oldEntropy = Entropy;
  oldDtEntropy = DtEntropy;

  dt_entr = (tend - tstart) * All.Timebase_interval;

  ErrTolIntAccuracy = 0.02;
  MinSizeTimestep = 0.01 * dt_entr;

  /***************************************/
  /* integrate with adaptative timesteps */
  /***************************************/

  ti_current = tstart;
  istep = 0;

#ifdef CHIMIE_THERMAL_FEEDBACK
  if (SphP[i].ThermalTime > (All.Time - All.ChimieThermalTime)) {
    Entropy = Entropy + SphP[i].DtEntropy * dt_entr;

    /* avoid Entropy to be less than minentropy */
    if (All.MinEgySpec)
      if (Entropy < minentropy) Entropy = minentropy;

    /* update particle */
    SphP[i].DtEntropy = (Entropy - SphP[i].Entropy) / dt_entr;
    SphP[i].Entropy = Entropy;

    return;
  }
#endif

  printf("%g %g %g\n", ti_current * All.Timebase_interval, Entropy, lmbd);

  while (ti_current < tend) {

    /* compute lambda */
    lmbd = lambda(Density * a3inv, Entropy, Metal);

    /* compute da/dt */
    dadt = fabs(-GAMMA_MINUS1 * pow(Density * a3inv, -GAMMA) * lmbd / hubble_a);

    /* compute cooling time */
    /* this is similar in comobile integraction */
    tcool = Entropy / dadt;

    /* find dt */
    dt = dmax(MinSizeTimestep, tcool * ErrTolIntAccuracy);
    dt = dmin(dt, dt_entr);

    ti_step = dt / All.Timebase_interval;

    ti_step = imax(1, ti_step);
    ti_step = imin(ti_step, tend - ti_current);

    dt = ti_step * All.Timebase_interval;

    /* normal integration of Entropy */
    Entropy += DtEntropy * dt; /* viscosity */
    Entropy += -GAMMA_MINUS1 * pow(Density * a3inv, -GAMMA) * lmbd / hubble_a *
               dt; /* cooling	       */

    /* avoid Entropy to be less than minentropy */
    if (All.MinEgySpec)
      if (Entropy < minentropy) {
        Entropy = minentropy;
        break;
      }

    printf("%g %g %g\n", ti_current * All.Timebase_interval, Entropy, lmbd);

    ti_current += ti_step;
    istep = istep + 1;
  }

  printf("%g %g %g\n", ti_current * All.Timebase_interval, Entropy, lmbd);

  /* entropy only due to cooling */
  DEntropy = Entropy - oldEntropy - DtEntropy * dt_entr;
  DtEntropy = DEntropy / dt_entr;

  printf("Entropy Final %g\n", Entropy);

  /* update particle */

  *newEntropy = Entropy;
  *newDtEntropy = DtEntropy + oldDtEntropy;

  /* need to return */
  /* Entropy,  DtEntropy */
  return 0;
}

struct cooling_solver_params {
  double Entropy;
  double Density;
  double Metal;
  double DtEntropy;
  double dt;
  double hubble_a;
};

double cooling_solver_function(double EntropyVar, void *params) {
  struct cooling_solver_params *p = (struct cooling_solver_params *)params;
  double Entropy = p->Entropy;
  double Density = p->Density;
  double Metal = p->Metal;
  double DtEntropyVisc = p->DtEntropy;
  double dt = p->dt;
  double hubble_a = p->hubble_a;

  double DtEntropyRadSph = 0;

  DtEntropyRadSph = -GAMMA_MINUS1 * pow(Density, -GAMMA) *
                    lambda(Density, EntropyVar, Metal) / hubble_a;

  return Entropy + (DtEntropyVisc + DtEntropyRadSph) * dt - EntropyVar;
};

float cooling2(int tstart, int tend, FLOAT Entropy, FLOAT Density, FLOAT Metal,
               FLOAT DtEntropy, FLOAT *newEntropy, FLOAT *newDtEntropy) {

  double dt;
  FLOAT oldDtEntropy;

  oldDtEntropy = DtEntropy;

  /***********************************/

  double EntropyNew;
  double Entropy_lo = 0, Entropy_hi = 0;
  double lo, hi;

  int status;
  int iter = 0;
  int max_iter = 100;

  dt = (tend - tstart) * All.Timebase_interval;

  const gsl_root_fsolver_type *T;
  gsl_root_fsolver *s;
  gsl_function F;
  struct cooling_solver_params params = {(double)Entropy, (double)Density,
                                         (double)Metal,   (double)DtEntropy,
                                         (double)dt,      (double)hubble_a};

  F.function = &cooling_solver_function;
  F.params = &params;

  T = gsl_root_fsolver_brent;
  s = gsl_root_fsolver_alloc(T);

  Entropy_lo = 0.5 * Entropy;
  Entropy_hi = 1.1 * Entropy;

  lo = cooling_solver_function(Entropy_lo, &params);
  hi = cooling_solver_function(Entropy_hi, &params);

  if (lo * hi > 0) {

    do {
      Entropy_hi = 2 * Entropy_hi;
      Entropy_lo = 0.5 * Entropy_lo;

      lo = cooling_solver_function(Entropy_lo, &params);
      hi = cooling_solver_function(Entropy_hi, &params);

      // printf("here, we need to iterate...\n");

    } while (lo * hi > 0);
  }

  gsl_root_fsolver_set(s, &F, Entropy_lo, Entropy_hi);

  printf("----->%g\n", Entropy);

  do {
    iter++;
    status = gsl_root_fsolver_iterate(s);
    EntropyNew = gsl_root_fsolver_root(s);
    printf("----->%g\n", EntropyNew);
    Entropy_lo = gsl_root_fsolver_x_lower(s);
    Entropy_hi = gsl_root_fsolver_x_upper(s);
    status = gsl_root_test_interval(Entropy_lo, Entropy_hi, 0, 0.001);

  } while (status == GSL_CONTINUE && iter < max_iter);

  gsl_root_fsolver_free(s);

  if (status != GSL_SUCCESS) {
    printf("WARNING, HERE WE DO NOT CONVERGE...%g %g\n", Entropy_lo,
           Entropy_hi);
    // endrun(3737);
  }

  printf("--------->%g\n", EntropyNew);

  /***********************************/

  /* update particle */

  *newEntropy = Entropy;
  *newDtEntropy = DtEntropy + oldDtEntropy;

  /* need to return */
  /* Entropy,  DtEntropy */
  return 0;
}

/****************************************************************************************
 *
 *
 *
 *   				 PYTHON INTERFACE
 *
 *
 *
 ****************************************************************************************/

static PyObject *cooling_get_lambda_from_Density_EnergyInt_FeH(PyObject *self,
                                                               PyObject *args) {
  PyObject *densityO, *energyintO, *fehO;
  PyArrayObject *densityA, *energyintA, *fehA;

  double l;
  PyArrayObject *ls;

  int n, i;

  if (!PyArg_ParseTuple(args, "OOO", &densityO, &energyintO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(densityO) && PyArray_IsAnyScalar(energyintO) &&
      PyArray_IsAnyScalar(fehO)) {
    l = lambda_from_Density_EnergyInt_FeH(PyFloat_AsDouble(densityO),
                                          PyFloat_AsDouble(energyintO),
                                          PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", l);
  }
  /* an array scalar */
  if (PyArray_Check(densityO) && PyArray_Check(energyintO) &&
      PyArray_Check(fehO)) {

    /* convert into array */
    densityA = (PyArrayObject *)densityO;
    energyintA = (PyArrayObject *)energyintO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    densityA = TO_DOUBLE(densityA);
    energyintA = TO_DOUBLE(energyintA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(densityA) != 1) || (PyArray_NDIM(energyintA) != 1) ||
        (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(densityA, 0);

    if ((PyArray_DIM(energyintA, 0) != n) || (PyArray_DIM(fehA, 0) != n)) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    ls = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(densityA),
                                            PyArray_DIMS(densityA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(ls, i) = lambda_from_Density_EnergyInt_FeH(
          *(double *)PyArray_GETPTR1(densityA, i),
          *(double *)PyArray_GETPTR1(energyintA, i),
          *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", ls);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

static PyObject *cooling_get_lambda_from_Density_Entropy_FeH(PyObject *self,
                                                             PyObject *args) {
  PyObject *densityO, *entropyO, *fehO;
  PyArrayObject *densityA, *entropyA, *fehA;

  double l;
  PyArrayObject *ls;

  int n, i;

  if (!PyArg_ParseTuple(args, "OOO", &densityO, &entropyO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(densityO) && PyArray_IsAnyScalar(entropyO) &&
      PyArray_IsAnyScalar(fehO)) {
    l = lambda_from_Density_Entropy_FeH(PyFloat_AsDouble(densityO),
                                        PyFloat_AsDouble(entropyO),
                                        PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", l);
  }
  /* an array scalar */
  if (PyArray_Check(densityO) && PyArray_Check(entropyO) &&
      PyArray_Check(fehO)) {

    /* convert into array */
    densityA = (PyArrayObject *)densityO;
    entropyA = (PyArrayObject *)entropyO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    densityA = TO_DOUBLE(densityA);
    entropyA = TO_DOUBLE(entropyA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(densityA) != 1) || (PyArray_NDIM(entropyA) != 1) ||
        (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(densityA, 0);

    if ((PyArray_DIM(entropyA, 0) != n) || (PyArray_DIM(fehA, 0) != n)) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    ls = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(densityA),
                                            PyArray_DIMS(densityA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(ls, i) = lambda_from_Density_Entropy_FeH(
          *(double *)PyArray_GETPTR1(densityA, i),
          *(double *)PyArray_GETPTR1(entropyA, i),
          *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", ls);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

static PyObject *cooling_get_lambda_from_Density_Temperature_FeH(
    PyObject *self, PyObject *args) {
  PyObject *densityO, *temperatureO, *fehO;
  PyArrayObject *densityA, *temperatureA, *fehA;

  double l;
  PyArrayObject *ls;

  int n, i;

  if (!PyArg_ParseTuple(args, "OOO", &densityO, &temperatureO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(densityO) && PyArray_IsAnyScalar(temperatureO) &&
      PyArray_IsAnyScalar(fehO)) {
    l = lambda_from_Density_Temperature_FeH(PyFloat_AsDouble(densityO),
                                            PyFloat_AsDouble(temperatureO),
                                            PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", l);
  }
  /* an array scalar */
  if (PyArray_Check(densityO) && PyArray_Check(temperatureO) &&
      PyArray_Check(fehO)) {

    /* convert into array */
    densityA = (PyArrayObject *)densityO;
    temperatureA = (PyArrayObject *)temperatureO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    densityA = TO_DOUBLE(densityA);
    temperatureA = TO_DOUBLE(temperatureA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(densityA) != 1) || (PyArray_NDIM(temperatureA) != 1) ||
        (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(densityA, 0);

    if ((PyArray_DIM(temperatureA, 0) != n) || (PyArray_DIM(fehA, 0) != n)) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    ls = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(densityA),
                                            PyArray_DIMS(densityA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(ls, i) = lambda_from_Density_Temperature_FeH(
          *(double *)PyArray_GETPTR1(densityA, i),
          *(double *)PyArray_GETPTR1(temperatureA, i),
          *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", ls);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

static PyObject *cooling_get_lambda_normalized_from_Temperature_FeH(
    PyObject *self, PyObject *args) {
  PyObject *temperatureO, *fehO;
  PyArrayObject *temperatureA, *fehA;

  double l;
  PyArrayObject *ls;

  int n, i;

  if (!PyArg_ParseTuple(args, "OO", &temperatureO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(temperatureO) && PyArray_IsAnyScalar(fehO)) {
    l = lambda_normalized_from_Temperature_FeH(PyFloat_AsDouble(temperatureO),
                                               PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", l);
  }
  /* an array scalar */
  if (PyArray_Check(temperatureO) && PyArray_Check(fehO)) {

    /* convert into array */
    temperatureA = (PyArrayObject *)temperatureO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    temperatureA = TO_DOUBLE(temperatureA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(temperatureA) != 1) || (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(temperatureA, 0);

    if (PyArray_DIM(fehA, 0) != n) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    ls = (PyArrayObject *)PyArray_SimpleNew(
        PyArray_NDIM(temperatureA), PyArray_DIMS(temperatureA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(ls, i) =
          lambda_normalized_from_Temperature_FeH(
              *(double *)PyArray_GETPTR1(temperatureA, i),
              *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", ls);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

static PyObject *cooling_get_cooling_time_from_Density_Temperature_FeH(
    PyObject *self, PyObject *args) {
  PyObject *densityO, *temperatureO, *fehO;
  PyArrayObject *densityA, *temperatureA, *fehA;

  double tc;
  PyArrayObject *tcs;

  int n, i;

  if (!PyArg_ParseTuple(args, "OOO", &densityO, &temperatureO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(densityO) && PyArray_IsAnyScalar(temperatureO) &&
      PyArray_IsAnyScalar(fehO)) {
    tc = cooling_time_from_Density_Temperature_FeH(
        PyFloat_AsDouble(densityO), PyFloat_AsDouble(temperatureO),
        PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", tc);
  }
  /* an array scalar */
  if (PyArray_Check(densityO) && PyArray_Check(temperatureO) &&
      PyArray_Check(fehO)) {

    /* convert into array */
    densityA = (PyArrayObject *)densityO;
    temperatureA = (PyArrayObject *)temperatureO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    densityA = TO_DOUBLE(densityA);
    temperatureA = TO_DOUBLE(temperatureA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(densityA) != 1) || (PyArray_NDIM(temperatureA) != 1) ||
        (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(densityA, 0);

    if ((PyArray_DIM(temperatureA, 0) != n) || (PyArray_DIM(fehA, 0) != n)) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    tcs = (PyArrayObject *)PyArray_SimpleNew(
        PyArray_NDIM(densityA), PyArray_DIMS(densityA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(tcs, i) =
          cooling_time_from_Density_Temperature_FeH(
              *(double *)PyArray_GETPTR1(densityA, i),
              *(double *)PyArray_GETPTR1(temperatureA, i),
              *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", tcs);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

static PyObject *cooling_get_cooling_time_from_Density_EnergyInt_FeH(
    PyObject *self, PyObject *args) {
  PyObject *densityO, *energyintO, *fehO;
  PyArrayObject *densityA, *energyintA, *fehA;

  double tc;
  PyArrayObject *tcs;

  int n, i;

  if (!PyArg_ParseTuple(args, "OOO", &densityO, &energyintO, &fehO))
    return PyUnicode_FromString("error");

  /* a scalar */
  if (PyArray_IsAnyScalar(densityO) && PyArray_IsAnyScalar(energyintO) &&
      PyArray_IsAnyScalar(fehO)) {
    tc = cooling_time_from_Density_EnergyInt_FeH(PyFloat_AsDouble(densityO),
                                                 PyFloat_AsDouble(energyintO),
                                                 PyFloat_AsDouble(fehO));
    return Py_BuildValue("d", tc);
  }
  /* an array scalar */
  if (PyArray_Check(densityO) && PyArray_Check(energyintO) &&
      PyArray_Check(fehO)) {

    /* convert into array */
    densityA = (PyArrayObject *)densityO;
    energyintA = (PyArrayObject *)energyintO;
    fehA = (PyArrayObject *)fehO;

    /* convert arrays to double */
    densityA = TO_DOUBLE(densityA);
    energyintA = TO_DOUBLE(energyintA);
    fehA = TO_DOUBLE(fehA);

    /* check dimension and size */
    if ((PyArray_NDIM(densityA) != 1) || (PyArray_NDIM(energyintA) != 1) ||
        (PyArray_NDIM(fehA) != 1)) {
      PyErr_SetString(PyExc_ValueError,
                      "array objects must be of dimention 1.");
      return NULL;
    }

    n = PyArray_DIM(densityA, 0);

    if ((PyArray_DIM(energyintA, 0) != n) || (PyArray_DIM(fehA, 0) != n)) {
      PyErr_SetString(PyExc_ValueError, "arrays must have the same size.");
      return NULL;
    }

    /*  create output array */
    tcs = (PyArrayObject *)PyArray_SimpleNew(
        PyArray_NDIM(densityA), PyArray_DIMS(densityA), NPY_DOUBLE);

    for (i = 0; i < n; i++) {
      *(double *)PyArray_GETPTR1(tcs, i) =
          cooling_time_from_Density_EnergyInt_FeH(
              *(double *)PyArray_GETPTR1(densityA, i),
              *(double *)PyArray_GETPTR1(energyintA, i),
              *(double *)PyArray_GETPTR1(fehA, i));
    }

    return Py_BuildValue("O", tcs);
  }

  /* something else */
  PyErr_SetString(PyExc_ValueError,
                  "parameters must be either scalars or array objects.");
  return NULL;
}

/*********************************/
/*                               */
/*********************************/

static PyObject *cooling_init_cooling(PyObject *self, PyObject *args) {

  PyObject *params_dict = PyDict_New();

  set_default_parameters();

  if (!PyArg_ParseTuple(args, "|O", &params_dict)) {
    PyErr_SetString(PyExc_AttributeError, "error.");
    return NULL;
  }

  if (!PyDict_Check(params_dict)) {
    PyErr_SetString(PyExc_AttributeError, "argument is not a dictionary.");
    return NULL;
  }

  if (PyDict_Size(params_dict)) set_parameters(params_dict);

  set_units();
  init_cooling_with_metals();

  return Py_BuildValue("d", 0);
}

/*********************************/
/*                               */
/*********************************/

static PyObject *cooling_PrintParameters(PyObject *self, PyObject *args) {

  printf("UnitLength_in_cm         = %g\n", All.UnitLength_in_cm);
  printf("UnitMass_in_g            = %g\n", All.UnitMass_in_g);
  printf("UnitVelocity_in_cm_per_s = %g\n", All.UnitVelocity_in_cm_per_s);
  printf("CoolingFile              = %s\n", All.CoolingFile);

  return Py_BuildValue("i", 0);
}

/*********************************/
/*                               */
/*********************************/

static PyObject *cooling_integrate1(PyObject *self, PyObject *args) {

  double tstart, tend, Density, Entropy, Metal;
  double DtEntropy = 0;
  int itstart, itend;
  FLOAT newEntropy;
  FLOAT newDtEntropy;

  if (!PyArg_ParseTuple(args, "|ddddd", &tstart, &tend, &Density, &Entropy,
                        &Metal)) {
    PyErr_SetString(PyExc_AttributeError, "error.");
    return NULL;
  }

  itstart = tstart / All.Timebase_interval;
  itend = tend / All.Timebase_interval;

  cooling1(itstart, itend, (FLOAT)Entropy, (FLOAT)Density, (FLOAT)Metal,
           DtEntropy, &newEntropy, &newDtEntropy);

  return Py_BuildValue("i", 0);
}

/*********************************/
/*                               */
/*********************************/

static PyObject *cooling_integrate2(PyObject *self, PyObject *args) {

  double tstart, tend, Density, Entropy, Metal;
  double DtEntropy = 0;
  int itstart, itend;
  FLOAT newEntropy;
  FLOAT newDtEntropy;

  if (!PyArg_ParseTuple(args, "|ddddd", &tstart, &tend, &Density, &Entropy,
                        &Metal)) {
    PyErr_SetString(PyExc_AttributeError, "error.");
    return NULL;
  }

  itstart = tstart / All.Timebase_interval;
  itend = tend / All.Timebase_interval;

  cooling2(itstart, itend, (FLOAT)Entropy, (FLOAT)Density, (FLOAT)Metal,
           DtEntropy, &newEntropy, &newDtEntropy);

  return Py_BuildValue("i", 0);
}

/* definition of the method table */

static PyMethodDef coolingMethods[] = {

    {"init_cooling", cooling_init_cooling, METH_VARARGS, "Init cooling."},

    {"get_lambda_from_Density_EnergyInt_FeH",
     cooling_get_lambda_from_Density_EnergyInt_FeH, METH_VARARGS,
     "Get the lambda function in user units."},

    {"get_lambda_from_Density_Entropy_FeH",
     cooling_get_lambda_from_Density_Entropy_FeH, METH_VARARGS,
     "Get the lambda function in user units."},

    {"get_lambda_from_Density_Temperature_FeH",
     cooling_get_lambda_from_Density_Temperature_FeH, METH_VARARGS,
     "Get the lambda function in user units."},

    {"get_lambda_normalized_from_Temperature_FeH",
     cooling_get_lambda_normalized_from_Temperature_FeH, METH_VARARGS,
     "Get the normalized lambda function in mks."},

    {"get_cooling_time_from_Density_Temperature_FeH",
     cooling_get_cooling_time_from_Density_Temperature_FeH, METH_VARARGS,
     "Get the cooling time in user units."},

    {"get_cooling_time_from_Density_EnergyInt_FeH",
     cooling_get_cooling_time_from_Density_EnergyInt_FeH, METH_VARARGS,
     "Get the cooling time in user units."},

    {"PrintParameters", cooling_PrintParameters, METH_VARARGS,
     "Print parameters."},

    {"integrate1", cooling_integrate1, METH_VARARGS,
     "Integrate cooling during a timestep using first scheme of integration."},

    {"integrate2", cooling_integrate2, METH_VARARGS,
     "Integrate cooling during a timestep using second scheme of integration."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef cooling_with_metalsmodule = {
    PyModuleDef_HEAD_INIT,
    "cooling_with_metals",
    "",
    -1,
    coolingMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_cooling_with_metals(void) {
  PyObject *m;
  m = PyModule_Create(&cooling_with_metalsmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
