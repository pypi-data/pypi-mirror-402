#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#define PLANCK 6.6262e-27
#define BOLTZMANN 1.3806e-16
#define PROTONMASS 1.6726e-24
#define TWOPI 6.2831853071795862

#define GAMMA (5.0 / 3)
#define GAMMA_MINUS1 (GAMMA - 1)

/* Write an error message compatible with python but does not return */
#define error(s, ...)                                                     \
  ({                                                                      \
    fflush(stdout);                                                       \
    char msg[400];                                                        \
    sprintf(msg, "%s:%s():%i: " s "\n", __FILE__, __FUNCTION__, __LINE__, \
            ##__VA_ARGS__);                                               \
    PyErr_SetString(PyExc_ValueError, msg);                               \
  })

/* system */
double dmax(double x, double y);
double dmin(double x, double y);

/* cooling */

void init_from_new_redshift(double Redshift);
double J_0(void);
double J_nu(double e);
double sigma_rad_HI(double e);
double sigma_rad_HeI(double e);
double sigma_rad_HeII(double e);
double cooling_bremstrahlung_HI(double T);
double cooling_bremstrahlung_HeI(double T);
double cooling_bremstrahlung_HeII(double T);
double cooling_ionization_HI(double T);
double cooling_ionization_HeI(double T);
double cooling_ionization_HeII(double T);
double cooling_recombination_HI(double T);
double cooling_recombination_HeI(double T);
double cooling_recombination_HeII(double T);
double cooling_dielectric_recombination(double T);
double cooling_excitation_HI(double T);
double cooling_excitation_HII(double T);
double cooling_compton(double T);
double A_HII(double T);
double A_HeIId(double T);
double A_HeII(double T);
double A_HeIII(double T);
double G_HI(double T);
double G_HeI(double T);
double G_HeII(double T);
double G_gHI(void);
double G_gHeI(void);
double G_gHeII(void);
double G_gHI_t(double J0);
double G_gHeI_t(double J0);
double G_gHeII_t(double J0);
double G_gHI_w(void);
double G_gHeI_w(void);
double G_gHeII_w(void);
double heating_radiative_HI(void);
double heating_radiative_HeI(void);
double heating_radiative_HeII(void);
double heating_radiative_HI_t(double J0);
double heating_radiative_HeI_t(double J0);
double heating_radiative_HeII_t(double J0);
double heating_radiative_HI_w(void);
double heating_radiative_HeI_w(void);
double heating_radiative_HeII_w(void);
double heating_compton(void);
void print_cooling(double T, double c1, double c2, double c3, double c4,
                   double c5, double c6, double c7, double c8, double c9,
                   double c10, double c11, double c12, double c13, double h1,
                   double h2, double h3, double h4);
void compute_densities(double T, double X, double *n_H, double *n_HI,
                       double *n_HII, double *n_HEI, double *n_HEII,
                       double *n_HEIII, double *n_E, double *mu);
void compute_cooling_from_T_and_Nh(double T, double X, double n_H, double *c1,
                                   double *c2, double *c3, double *c4,
                                   double *c5, double *c6, double *c7,
                                   double *c8, double *c9, double *c10,
                                   double *c11, double *c12, double *c13,
                                   double *h1, double *h2, double *h3,
                                   double *h4);
double compute_cooling_from_Temperature_and_HydrogenDensity(
    double Temperature, double HydrogenDensity, double hydrogen_massfrac,
    double *MeanWeight, double *ElectronDensity);
double compute_cooling_from_Egyspec_and_Density(double Egyspec, double Density,
                                                double hydrogen_massfrac,
                                                double *MeanWeight);

static double eV = 1.6022000e-12;
static double normfacJ0 = 0.74627;
static double J0min = 1.e-29;
static double alpha = 1.0;

static int Norderweinberg = 7; /* polynom order+1 */
static double coefweinberg[7][6];
static double z;
static double J0;

static double Cte_G_gHI;
static double Cte_G_gHeI;
static double Cte_G_gHeII;
static double Cte_heating_radiative_HI;
static double Cte_heating_radiative_HeI;
static double Cte_heating_radiative_HeII;

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

/*
 * init some variables that depends only on redshift
 */
void init_from_new_redshift(double Redshift) {

  /* init weinberg coeff */

  coefweinberg[0][0] = -0.31086729929951613e+002;
  coefweinberg[1][0] = 0.34803667059463761e+001;
  coefweinberg[2][0] = -0.15145716066316397e+001;
  coefweinberg[3][0] = 0.54649951450632972e+000;
  coefweinberg[4][0] = -0.16395924120387340e+000;
  coefweinberg[5][0] = 0.25197466148524143e-001;
  coefweinberg[6][0] = -0.15352763785487806e-002;

  coefweinberg[0][1] = -0.31887274113252204e+002;
  coefweinberg[1][1] = 0.44178493140927095e+001;
  coefweinberg[2][1] = -0.20158132553082293e+001;
  coefweinberg[3][1] = 0.64080497292269134e+000;
  coefweinberg[4][1] = -0.15981267091909040e+000;
  coefweinberg[5][1] = 0.22056900050237707e-001;
  coefweinberg[6][1] = -0.12837570029562849e-002;

  coefweinberg[0][2] = -0.35693331167978656e+002;
  coefweinberg[1][2] = 0.20207245722165794e+001;
  coefweinberg[2][2] = -0.76856976101363744e-001;
  coefweinberg[3][2] = -0.75691470654320359e-001;
  coefweinberg[4][2] = -0.54502220282734729e-001;
  coefweinberg[5][2] = 0.20633345104660583e-001;
  coefweinberg[6][2] = -0.18410307456285177e-002;

  coefweinberg[0][3] = -0.56967559787460921e+002;
  coefweinberg[1][3] = 0.38601174525546353e+001;
  coefweinberg[2][3] = -0.18318926655684415e+001;
  coefweinberg[3][3] = 0.67360594266440688e+000;
  coefweinberg[4][3] = -0.18983466813215341e+000;
  coefweinberg[5][3] = 0.27768907786915147e-001;
  coefweinberg[6][3] = -0.16330066969315893e-002;

  coefweinberg[0][4] = -0.56977907250821026e+002;
  coefweinberg[1][4] = 0.38686249565302266e+001;
  coefweinberg[2][4] = -0.13330942368518774e+001;
  coefweinberg[3][4] = 0.33988839029092172e+000;
  coefweinberg[4][4] = -0.98997915675929332e-001;
  coefweinberg[5][4] = 0.16781612113050747e-001;
  coefweinberg[6][4] = -0.11514328893746039e-002;

  coefweinberg[0][5] = -0.59825233828609278e+002;
  coefweinberg[1][5] = 0.21898162706563347e+001;
  coefweinberg[2][5] = -0.42982055888598525e+000;
  coefweinberg[3][5] = 0.50312144291614215e-001;
  coefweinberg[4][5] = -0.61550639239553132e-001;
  coefweinberg[5][5] = 0.18017109270959387e-001;
  coefweinberg[6][5] = -0.15438891584271634e-002;

  z = Redshift;
  J0 = J_0();

  /* here, we initialize the ctes that uses J_nu(z) */

  /* Tessier */
  /*
  Cte_G_gHI			    = G_gHI();
  Cte_G_gHeI			    = G_gHeI();
  Cte_G_gHeII			    = G_gHeII();
  Cte_heating_radiative_HI	    = heating_radiative_HI();
  Cte_heating_radiative_HeI	    = heating_radiative_HeI();
  Cte_heating_radiative_HeII	    = heating_radiative_HeII();
  */

  /* Theuns */
  /*
  Cte_G_gHI			    = G_gHI_t(J0);
  Cte_G_gHeI			    = G_gHeI_t(J0);
  Cte_G_gHeII			    = G_gHeII_t(J0);
  Cte_heating_radiative_HI	    = heating_radiative_HI_t(J0);
  Cte_heating_radiative_HeI	    = heating_radiative_HeI_t(J0);
  Cte_heating_radiative_HeII	    = heating_radiative_HeII_t(J0);
  */

  /* Weinberg */
  Cte_G_gHI = G_gHI_w();
  Cte_G_gHeI = G_gHeI_w();
  Cte_G_gHeII = G_gHeII_w();
  Cte_heating_radiative_HI = heating_radiative_HI_w();
  Cte_heating_radiative_HeI = heating_radiative_HeI_w();
  Cte_heating_radiative_HeII = heating_radiative_HeII_w();
}

/*
 * J0
 */

double J_0(void) {
  double Fz;

  if (z > 6)
    Fz = 0;
  else {
    if (z > 3)
      Fz = 4 / (z + 1);
    else {
      if (z > 2)
        Fz = 1;
      else
        Fz = pow(((1 + z) / 3.), 3);
    }
  }

  return 1.0e-22 * Fz;
}

/*
 * UV background intensity
 */

double J_nu(double e) {
  double e_L;
  e_L = 13.598 * eV;
  return (e_L / e) * J_0();
}

/*
 * sigma_rad
 */

double sigma_rad_HI(double e) {
  double xxx, alph, e_i;

  e_i = 13.598 * eV;
  xxx = e / e_i;
  alph = sqrt(xxx - 1.0);
  return 6.30e-18 / pow(xxx, 4) * exp(4.0 - 4.0 * atan(alph) / alph) /
         (1.0 - exp(-TWOPI / alph));
}

double sigma_rad_HeI(double e) {
  double xxx, e_i;

  e_i = 24.587 * eV;
  xxx = e / e_i;
  return 7.42e-18 * (1.660 / pow(xxx, 2.050) - 0.660 / pow(xxx, 3.050));
}

double sigma_rad_HeII(double e) {
  double xxx, alph, e_i;

  e_i = 54.416 * eV;
  xxx = e / e_i;
  alph = sqrt(xxx - 1.0);
  return 1.58e-18 / pow(xxx, 4) * exp(4.0 - 4.0 * atan(alph) / alph) /
         (1.0 - exp(-TWOPI / alph));
}

/*
 * cooling rates
 */

/* Bremstrahlung */
double cooling_bremstrahlung_HI(double T) {
  return 1.42e-27 * sqrt(T) *
         (1.10 + 0.340 * exp(-pow((5.50 - log10(T)), 2) / 3.0));
}

double cooling_bremstrahlung_HeI(double T) {
  return 1.42e-27 * sqrt(T) *
         (1.10 + 0.340 * exp(-pow((5.50 - log10(T)), 2) / 3.0));
}

double cooling_bremstrahlung_HeII(double T) {
  return 5.68e-27 * sqrt(T) *
         (1.10 + 0.340 * exp(-pow((5.50 - log10(T)), 2) / 3.0));
}

/* Ionization */
double cooling_ionization_HI(double T) {
  double T5;
  T5 = T / 1e5;
  return 2.54e-21 * sqrt(T) * exp(-157809.1 / T) / (1 + sqrt(T5));
}

double cooling_ionization_HeI(double T) {
  double T5;
  T5 = T / 1e5;
  return 1.88e-21 * sqrt(T) * exp(-285335.4 / T) / (1 + sqrt(T5));
}

double cooling_ionization_HeII(double T) {
  double T5;
  T5 = T / 1e5;
  return 9.90e-22 * sqrt(T) * exp(-631515.0 / T) / (1 + sqrt(T5));
}

/* Recombination */
double cooling_recombination_HI(double T) {
  double T3, T6;
  T3 = T / 1e3;
  T6 = T / 1e6;
  return 8.70e-27 * sqrt(T) / pow(T3, 0.2) / (1.0 + pow(T6, 0.7));
}

double cooling_recombination_HeI(double T) { return 1.55e-26 * pow(T, 0.3647); }

double cooling_recombination_HeII(double T) {
  double T3, T6;
  T3 = T / 1e3;
  T6 = T / 1e6;
  return 3.48e-26 * sqrt(T) / pow(T3, 0.2) / (1.0 + pow(T6, 0.7));
}

/* Dielectric Recombination */
double cooling_dielectric_recombination(double T) {
  return 1.24e-13 * pow(T, -1.5) * exp(-470000.0 / T) *
         (1.0 + 0.3 * exp(-94000.0 / T));
}

/* Ecitation cooling (line cooling) */
double cooling_excitation_HI(double T) {
  double T5;
  T5 = T / 1e5;
  return 7.50e-19 * exp(-118348.0 / T) / (1 + sqrt(T5));
}

double cooling_excitation_HII(double T) {
  double T5;
  T5 = T / 1e5;
  return 5.54e-17 / pow(T, 0.397) * exp(-473638.0 / T) / (1 + sqrt(T5));
}

/* Compton cooling */
double cooling_compton(double T) {
  return 5.406e-36 * (T - 2.7 * (1 + z)) * pow((1 + z), 4);
}

/*
 * recombination rates  (taux_rec)
 */

double A_HII(double T) {
  double T3, T6;
  T3 = T / 1e3;
  T6 = T / 1e6;
  return 6.30e-11 / sqrt(T) / pow(T3, 0.2) / (1 + pow(T6, 0.7));
}

double A_HeIId(double T) {
  return 1.9e-3 / pow(T, 1.50) * exp(-470000.0 / T) *
         (1.0 + 0.30 * exp(-94000.0 / T));
}

double A_HeII(double T) { return 1.5e-10 / pow(T, 0.6353) + A_HeIId(T); }

double A_HeIII(double T) {
  double T3, T6;
  T3 = T / 1e3;
  T6 = T / 1e6;
  return 3.36e-10 / sqrt(T) / pow(T3, 0.2) / (1.0 + pow(T6, 0.7));
}

/*
 * collisional rates  (taux_ion)
 */

double G_HI(double T) {
  double T5;
  T5 = T / 1e5;
  return 1.17e-10 * sqrt(T) * exp(-157809.1 / T) / (1.0 + sqrt(T5));
}

double G_HeI(double T) {
  double T5;
  T5 = T / 1e5;
  return 2.38e-11 * sqrt(T) * exp(-285335.4 / T) / (1.0 + sqrt(T5));
}

double G_HeII(double T) {
  double T5;
  T5 = T / 1e5;
  return 5.68e-12 * sqrt(T) * exp(-631515.0 / T) / (1.0 + sqrt(T5));
}

/*
 * photoionisation rates (depend only on z)
 */

double G_gHI(void) {
  double e_i, integ, e, de, error;

  e_i = 13.598 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;
  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error = 2 * TWOPI * J_nu(e) * sigma_rad_HI(e) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }

  return integ / PLANCK;
}

double G_gHeI(void) {
  double e_i, integ, e, de, error;

  e_i = 24.587 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;
  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error = 2 * TWOPI * J_nu(e) * sigma_rad_HeI(e) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }

  return integ / PLANCK;
}

double G_gHeII(void) {
  double e_i, integ, e, de, error;

  e_i = 54.416 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;
  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error = 2 * TWOPI * J_nu(e) * sigma_rad_HeII(e) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }

  return integ / PLANCK;
}

double G_gHI_t(double J0) { return 1.26e10 * J0 / (3.0 + alpha); }

double G_gHeI_t(double J0) {
  return 1.48e10 * J0 * pow(0.5530, alpha) *
         (1.660 / (alpha + 2.050) - 0.660 / (alpha + 3.050));
}

double G_gHeII_t(double J0) {
  return 3.34e9 * J0 * pow(0.2490, alpha) / (3.0 + alpha);
}

double G_gHI_w(void) {
  double taux_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][0] * pow(zz, i);
    taux_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    taux_rad_weinbergint = 0.0;

  tt = G_gHI_t(J0min);
  if (taux_rad_weinbergint < tt) taux_rad_weinbergint = tt;

  return taux_rad_weinbergint;
}

double G_gHeI_w(void) {
  double taux_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][1] * pow(zz, i);
    taux_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    taux_rad_weinbergint = 0.0;

  tt = G_gHeI_t(J0min);
  if (taux_rad_weinbergint < tt) taux_rad_weinbergint = tt;

  return taux_rad_weinbergint;
}

double G_gHeII_w(void) {
  double taux_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][2] * pow(zz, i);
    taux_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    taux_rad_weinbergint = 0.0;

  tt = G_gHeII_t(J0min);
  if (taux_rad_weinbergint < tt) taux_rad_weinbergint = tt;

  return taux_rad_weinbergint;
}

/*
 * heating rates (depend only on z)
 */

double heating_radiative_HI(void) /* use J_nu */
{
  double e_i, integ, e, de, error;

  e_i = 13.598 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;

  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error = 2.0 * TWOPI * J_nu(e) * sigma_rad_HI(e) * (e / e_i - 1.0) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }
  return integ / PLANCK * e_i;
}

double heating_radiative_HeI(void) /* use J_nu */
{
  double e_i, integ, e, de, error;

  e_i = 24.587 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;

  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error = 2.0 * TWOPI * J_nu(e) * sigma_rad_HeI(e) * (e / e_i - 1.0) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }
  return integ / PLANCK * e_i;
}

double heating_radiative_HeII(void) /* use J_nu */
{
  double e_i, integ, e, de, error;

  e_i = 54.416 * eV;
  integ = 0.0;
  e = e_i;
  de = e / 100.0;
  error = 1.0;

  while (error > 1.e-6) {
    e = e + de;
    de = e / 100.0;
    error =
        2.0 * TWOPI * J_nu(e) * sigma_rad_HeII(e) * (e / e_i - 1.0) * de / e;
    integ = integ + error;
    error = error / fabs(integ);
  }
  return integ / PLANCK * e_i;
}

double heating_radiative_HI_t(double J0) /* use Theuns */
{
  return (2.91e-1 * J0 / (2.0 + alpha)) / (3.0 + alpha);
}

double heating_radiative_HeI_t(double J0) /* use Theuns */
{
  return 5.84e-1 * J0 * pow(0.5530, alpha) *
         (1.660 / (alpha + 1.050) - 2.320 / (alpha + 2.050) +
          0.660 / (alpha + 3.050));
}

double heating_radiative_HeII_t(double J0) /* use Theuns */
{
  return (2.92e-1 * J0 * pow(0.2490, alpha) / (2.0 + alpha)) / (3.0 + alpha);
}

double heating_radiative_HI_w(void) /* use weinberg coeff */
{
  double heat_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][3] * pow(zz, i);
    heat_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    heat_rad_weinbergint = 0.0;

  tt = heating_radiative_HI_t(J0min);
  if (heat_rad_weinbergint < tt) heat_rad_weinbergint = tt;

  return heat_rad_weinbergint;
}

double heating_radiative_HeI_w(void) /* use weinberg coeff */
{
  double heat_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][4] * pow(zz, i);
    heat_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    heat_rad_weinbergint = 0.0;

  tt = heating_radiative_HeI_t(J0min);
  if (heat_rad_weinbergint < tt) heat_rad_weinbergint = tt;

  return heat_rad_weinbergint;
}

double heating_radiative_HeII_w(void) /* use weinberg coeff */
{
  double heat_rad_weinbergint;
  double hh, tt, zz;
  int i;

  if (z < 8.50) {
    hh = 0.0;
    zz = dmax(z, 1.0e-15);
    for (i = 0; i < Norderweinberg; i++)
      hh = hh + coefweinberg[i][5] * pow(zz, i);
    heat_rad_weinbergint = normfacJ0 * exp(hh);
  } else
    heat_rad_weinbergint = 0.0;

  tt = heating_radiative_HeII_t(J0min);
  if (heat_rad_weinbergint < tt) heat_rad_weinbergint = tt;

  return heat_rad_weinbergint;
}

double heating_compton(void) { return 5.406e-36 * 2.726 * pow((1 + z), 5); }

void compute_densities(double T, double X, double *pn_H, double *pn_HI,
                       double *pn_HII, double *pn_HEI, double *pn_HEII,
                       double *pn_HEIII, double *pn_E, double *pmu) {

  double Y, yy, x1;
  double t_rad_HI, t_rec_HI, t_ion_HI;
  double t_rad_HEI, t_rec_HEI, t_ion_HEI;
  double t_rad_HEII, t_rec_HEII, t_ion_HEII;
  double t_ion2_HI, t_ion2_HEI, t_ion2_HEII;
  double err_nE;
  double n_T=0;
  double n_H=0, n_HI=0, n_HII=0, n_HEI=0, n_HEII=0, n_HEIII=0, n_E=0, mu;

  Y = 1 - X;
  yy = Y / (4 - 4 * Y);

  t_rad_HI = Cte_G_gHI;
  t_rec_HI = A_HII(T);
  t_ion_HI = G_HI(T);

  t_rad_HEI = Cte_G_gHeI;
  t_rec_HEI = A_HeII(T);
  t_ion_HEI = G_HeI(T);

  t_rad_HEII = Cte_G_gHeII;
  t_rec_HEII = A_HeIII(T);
  t_ion_HEII = G_HeII(T);

  n_H = *pn_H;

  n_E = n_H;
  err_nE = 1.;

  while (err_nE > 1.e-8) {

    /* compute densities (Ramses implementation) */
    t_ion2_HI = t_ion_HI + t_rad_HI / dmax(n_E, 1e-15 * n_H);
    t_ion2_HEI = t_ion_HEI + t_rad_HEI / dmax(n_E, 1e-15 * n_H);
    t_ion2_HEII = t_ion_HEII + t_rad_HEII / dmax(n_E, 1e-15 * n_H);

    n_HI = t_rec_HI / (t_ion2_HI + t_rec_HI) * n_H;
    n_HII = t_ion2_HI / (t_ion2_HI + t_rec_HI) * n_H;

    x1 = (t_rec_HEII * t_rec_HEI + t_ion2_HEI * t_rec_HEII +
          t_ion2_HEII * t_ion2_HEI);

    n_HEIII = yy * t_ion2_HEII * t_ion2_HEI / x1 * n_H;
    n_HEII = yy * t_ion2_HEI * t_rec_HEII / x1 * n_H;
    n_HEI = yy * t_rec_HEII * t_rec_HEI / x1 * n_H;

    err_nE = fabs((n_E - (n_HII + n_HEII + 2. * n_HEIII)) / n_H);
    n_E = 0.5 * n_E + 0.5 * (n_HII + n_HEII + 2. * n_HEIII);
  }

  n_T = n_HI + n_HII + n_HEI + n_HEII + n_HEIII + n_E;
  mu = n_H / X / n_T;

  *pn_H = n_H;
  *pn_HI = n_HI;
  *pn_HII = n_HII;
  *pn_HEI = n_HEI;
  *pn_HEII = n_HEII;
  *pn_HEIII = n_HEIII;
  *pn_E = n_E;
  *pmu = mu;
}

void print_cooling(double T, double c1, double c2, double c3, double c4,
                   double c5, double c6, double c7, double c8, double c9,
                   double c10, double c11, double c12, double c13, double h1,
                   double h2, double h3, double h4) {

  double ctot, htot, chtot;

  ctot = c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12 + c13;
  htot = h1 + h2 + h3 + h4;
  chtot = ctot - htot;

  printf("%g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g %g\n", T,
         c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, h1, h2, h3, h4,
         ctot, htot, chtot);
}

void compute_cooling_from_T_and_Nh(double T, double X, double n_H, double *c1,
                                   double *c2, double *c3, double *c4,
                                   double *c5, double *c6, double *c7,
                                   double *c8, double *c9, double *c10,
                                   double *c11, double *c12, double *c13,
                                   double *h1, double *h2, double *h3,
                                   double *h4) {

  double n_HI, n_HII, n_HEI, n_HEII, n_HEIII, n_E, mu;
  double nH2;
  // double c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13;
  // double h1,h2,h3,h4;

  compute_densities(T, X, &n_H, &n_HI, &n_HII, &n_HEI, &n_HEII, &n_HEIII, &n_E,
                    &mu);

  nH2 = n_H * n_H;

  /*
   * compute cooling
   */

  /* Bremstrahlung (cool_bre) */
  *c1 = cooling_bremstrahlung_HI(T) * n_E * n_HII / nH2;
  *c2 = cooling_bremstrahlung_HeI(T) * n_E * n_HEII / nH2;
  *c3 = cooling_bremstrahlung_HeII(T) * n_E * n_HEIII / nH2;

  /* Ionization cooling (cool_ion) */
  *c4 = cooling_ionization_HI(T) * n_E * n_HI / nH2;
  *c5 = cooling_ionization_HeI(T) * n_E * n_HEI / nH2;
  *c6 = cooling_ionization_HeII(T) * n_E * n_HEII / nH2;

  /* Recombination cooling (cool_rec) */
  *c7 = cooling_recombination_HI(T) * n_E * n_HII / nH2;
  *c8 = cooling_recombination_HeI(T) * n_E * n_HEII / nH2;
  *c9 = cooling_recombination_HeII(T) * n_E * n_HEIII / nH2;

  /* Dielectric recombination cooling (cool_die) */
  *c10 = cooling_dielectric_recombination(T) * n_E * n_HEII / nH2;

  /* Line cooling (cool_exc) */
  *c11 = cooling_excitation_HI(T) * n_E * n_HI / nH2;
  *c12 = cooling_excitation_HII(T) * n_E * n_HEII / nH2;

  /* Compton cooling (cool_com) */
  *c13 = cooling_compton(T) * n_E / nH2; /* !! dep on z */

  /*
   * compute heating
   */

  /* Radiative heating (h_rad_spec) */
  *h1 = Cte_heating_radiative_HI * n_HI / nH2;
  *h2 = Cte_heating_radiative_HeI * n_HEI / nH2;
  *h3 = Cte_heating_radiative_HeII * n_HEII / nH2;

  /* Compton heating (heat_com) */
  *h4 = heating_compton() * n_E / nH2; /* !! dep on z */
}

double compute_cooling_from_Egyspec_and_Density(double Egyspec, double Density,
                                                double hydrogen_massfrac,
                                                double *MeanWeight) {

  double T=0, mu, n_H;
  double n_HI, n_HII, n_HEI, n_HEII, n_HEIII, n_E;

  double err_mu, mu_left, mu_right, mu_old;
  int niter;

  double c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13;
  double h1, h2, h3, h4;

  double nH2;

  /* Hydrogen density (cgs) */
  n_H = hydrogen_massfrac * Density / PROTONMASS;

  /* itterate to find the right mu and T */

  err_mu = 1.;
  mu_left = 0.5;
  mu_right = 1.3;
  niter = 0;

  while ((err_mu > 1.e-4) && (niter <= 50)) {

    mu_old = 0.5 * (mu_left + mu_right);

    /* compute temperature */
    T = GAMMA_MINUS1 * mu_old * PROTONMASS / BOLTZMANN * Egyspec;

    /* compute all */
    compute_densities(T, hydrogen_massfrac, &n_H, &n_HI, &n_HII, &n_HEI,
                      &n_HEII, &n_HEIII, &n_E, &mu);

    err_mu = (mu - mu_old) / mu_old;

    if (err_mu > 0.) {
      mu_left = 0.5 * (mu_left + mu_right);
      //mu_right = mu_right;
    } else {
      //mu_left = mu_left;
      mu_right = 0.5 * (mu_left + mu_right);
    }

    err_mu = fabs(err_mu);
    niter = niter + 1;
  }

  if (niter > 50) printf("ERROR : too many iterations.");

  *MeanWeight = 0.5 * (mu_left + mu_right);

  /* now, compute cooling */

  nH2 = n_H * n_H;

  /*
   * compute cooling
   */

  /* Bremstrahlung (cool_bre) */
  c1 = cooling_bremstrahlung_HI(T) * n_E * n_HII / nH2;
  c2 = cooling_bremstrahlung_HeI(T) * n_E * n_HEII / nH2;
  c3 = cooling_bremstrahlung_HeII(T) * n_E * n_HEIII / nH2;

  /* Ionization cooling (cool_ion) */
  c4 = cooling_ionization_HI(T) * n_E * n_HI / nH2;
  c5 = cooling_ionization_HeI(T) * n_E * n_HEI / nH2;
  c6 = cooling_ionization_HeII(T) * n_E * n_HEII / nH2;

  /* Recombination cooling (cool_rec) */
  c7 = cooling_recombination_HI(T) * n_E * n_HII / nH2;
  c8 = cooling_recombination_HeI(T) * n_E * n_HEII / nH2;
  c9 = cooling_recombination_HeII(T) * n_E * n_HEIII / nH2;

  /* Dielectric recombination cooling (cool_die) */
  c10 = cooling_dielectric_recombination(T) * n_E * n_HEII / nH2;

  /* Line cooling (cool_exc) */
  c11 = cooling_excitation_HI(T) * n_E * n_HI / nH2;
  c12 = cooling_excitation_HII(T) * n_E * n_HEII / nH2;

  /* Compton cooling (cool_com) */
  c13 = cooling_compton(T) * n_E / nH2; /* !! dep on z */

  /*
   * compute heating
   */

  /* Radiative heating (h_rad_spec) */
  h1 = Cte_heating_radiative_HI * n_HI / nH2;
  h2 = Cte_heating_radiative_HeI * n_HEI / nH2;
  h3 = Cte_heating_radiative_HeII * n_HEII / nH2;

  /* Compton heating (heat_com) */
  h4 = heating_compton() * n_E / nH2; /* !! dep on z */

  /* output info */
  // print_cooling(T,c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,h1,h2,h3,h4);

  return (c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12 + c13) -
         (h1 + h2 + h3 + h4);
}

double compute_cooling_from_Temperature_and_HydrogenDensity(
    double Temperature, double HydrogenDensity, double hydrogen_massfrac,
    double *MeanWeight, double *ElectronDensity) {

  double T, mu, n_H;
  double n_HI, n_HII, n_HEI, n_HEII, n_HEIII, n_E;

  //  double err_mu,mu_left,mu_right,mu_old;
  //  int    niter;

  double c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13;
  double h1, h2, h3, h4;

  double nH2;

  /* Hydrogen density (cgs) */
  n_H = HydrogenDensity;

  /* Temperature */
  T = Temperature;

  /* compute all */
  compute_densities(T, hydrogen_massfrac, &n_H, &n_HI, &n_HII, &n_HEI, &n_HEII,
                    &n_HEIII, &n_E, &mu);

  *MeanWeight = mu;
  *ElectronDensity = n_E;

  /* now, compute cooling */

  nH2 = n_H * n_H;

  /*
   * compute cooling
   */

  /* Bremstrahlung (cool_bre) */
  c1 = cooling_bremstrahlung_HI(T) * n_E * n_HII / nH2;
  c2 = cooling_bremstrahlung_HeI(T) * n_E * n_HEII / nH2;
  c3 = cooling_bremstrahlung_HeII(T) * n_E * n_HEIII / nH2;

  /* Ionization cooling (cool_ion) */
  c4 = cooling_ionization_HI(T) * n_E * n_HI / nH2;
  c5 = cooling_ionization_HeI(T) * n_E * n_HEI / nH2;
  c6 = cooling_ionization_HeII(T) * n_E * n_HEII / nH2;

  /* Recombination cooling (cool_rec) */
  c7 = cooling_recombination_HI(T) * n_E * n_HII / nH2;
  c8 = cooling_recombination_HeI(T) * n_E * n_HEII / nH2;
  c9 = cooling_recombination_HeII(T) * n_E * n_HEIII / nH2;

  /* Dielectric recombination cooling (cool_die) */
  c10 = cooling_dielectric_recombination(T) * n_E * n_HEII / nH2;

  /* Line cooling (cool_exc) */
  c11 = cooling_excitation_HI(T) * n_E * n_HI / nH2;
  c12 = cooling_excitation_HII(T) * n_E * n_HEII / nH2;

  /* Compton cooling (cool_com) */
  c13 = cooling_compton(T) * n_E / nH2; /* !! dep on z */

  /*
   * compute heating
   */

  /* Radiative heating (h_rad_spec) */
  h1 = Cte_heating_radiative_HI * n_HI / nH2;
  h2 = Cte_heating_radiative_HeI * n_HEI / nH2;
  h3 = Cte_heating_radiative_HeII * n_HEII / nH2;

  /* Compton heating (heat_com) */
  h4 = heating_compton() * n_E / nH2; /* !! dep on z */

  /* output info */
  // print_cooling(T,c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,h1,h2,h3,h4);

  return (c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12 + c13) -
         (h1 + h2 + h3 + h4);
}

/*********************************/
/* Cooling function              */
/*********************************/

static PyObject *coolinglib_cooling(PyObject *self, PyObject *args) {

  PyArrayObject *EgySpec;
  PyArrayObject *Density;

  PyArrayObject *Mu;
  PyArrayObject *Lambda;

  float Redshift, hydrogen_massfrac;
  int i;
  double l, MeanWeight;
  double e, d;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOff", &EgySpec, &Density, &hydrogen_massfrac,
                        &Redshift))
    return NULL;

  if (PyArray_TYPE(EgySpec) != NPY_DOUBLE) {
    error("EgySpec is not in double");
    return NULL;
  }

  if (PyArray_TYPE(Density) != NPY_DOUBLE) {
    error("Density is not in double");
    return NULL;
  }

  /* create output */
  Mu = (PyArrayObject *)PyArray_SimpleNew(
      PyArray_NDIM(EgySpec), PyArray_DIMS(EgySpec), PyArray_TYPE(EgySpec));
  Lambda = (PyArrayObject *)PyArray_SimpleNew(
      PyArray_NDIM(EgySpec), PyArray_DIMS(EgySpec), PyArray_TYPE(EgySpec));

  init_from_new_redshift((double)Redshift);

  for (i = 0; i < PyArray_DIM(EgySpec, 0); i++) {

    e = *(double *)PyArray_GETPTR1(EgySpec, i);
    d = *(double *)PyArray_GETPTR1(Density, i);

    /* compute cooling from EnergySpec and Density */
    l = compute_cooling_from_Egyspec_and_Density(e, d, hydrogen_massfrac,
                                                 &MeanWeight);

    *(double *)PyArray_GETPTR1(Mu, i) = MeanWeight;
    *(double *)PyArray_GETPTR1(Lambda, i) = l;
  }

  return Py_BuildValue("OO", Mu, Lambda);
}

static PyObject *coolinglib_cooling_from_nH_and_T(PyObject *self,
                                                  PyObject *args) {

  PyArrayObject *Temperature;
  PyArrayObject *HydrogenDensity;

  PyArrayObject *Mu;
  PyArrayObject *Ne;
  PyArrayObject *Lambda;

  float Redshift, hydrogen_massfrac;
  int i;
  double l, MeanWeight, ElectronDensity;
  double T, nH;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "OOff", &Temperature, &HydrogenDensity,
                        &hydrogen_massfrac, &Redshift))
    return NULL;

  if (PyArray_TYPE(Temperature) != NPY_DOUBLE) {
    error("Temperature is not in double");
    return NULL;
  }

  if (PyArray_TYPE(HydrogenDensity) != NPY_DOUBLE) {
    error("HydrogenDensity is not in double");
    return NULL;
  }

  /* create output */
  Mu = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(Temperature),
                                          PyArray_DIMS(Temperature),
                                          PyArray_TYPE(Temperature));
  Ne = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(Temperature),
                                          PyArray_DIMS(Temperature),
                                          PyArray_TYPE(Temperature));
  Lambda = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(Temperature),
                                              PyArray_DIMS(Temperature),
                                              PyArray_TYPE(Temperature));

  init_from_new_redshift((double)Redshift);

  for (i = 0; i < PyArray_DIM(Temperature, 0); i++) {

    T = *(double *)PyArray_GETPTR1(Temperature, i);
    nH = *(double *)PyArray_GETPTR1(HydrogenDensity, i);

    /* compute cooling from EnergySpec and Density */
    l = compute_cooling_from_Temperature_and_HydrogenDensity(
        T, nH, hydrogen_massfrac, &MeanWeight, &ElectronDensity);

    *(double *)PyArray_GETPTR1(Mu, i) = MeanWeight;
    *(double *)PyArray_GETPTR1(Ne, i) = ElectronDensity;
    *(double *)PyArray_GETPTR1(Lambda, i) = l;
  }

  return Py_BuildValue("OOO", Mu, Ne, Lambda);
}

/* definition of the method table */

static PyMethodDef coolinglibMethods[] = {

    {"cooling", coolinglib_cooling, METH_VARARGS,
     "Return Mu and Lambda. Energy spec and Density must be in cgs."},

    {"cooling_from_nH_and_T", coolinglib_cooling_from_nH_and_T, METH_VARARGS,
     "Return Mu and Lambda. Temperature and Hydrogen Density must be in cgs."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef coolinglibmodule = {
    PyModuleDef_HEAD_INIT,
    "coolinglib",
    "Defines some cooling methods",
    -1,
    coolinglibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_coolinglib(void) {
  PyObject *m;
  m = PyModule_Create(&coolinglibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
