#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#define TWOPI 6.2831853071795862

/* Write an error message compatible with python but does not return */
#define error(s, ...)                                                \
  ({                                                                 \
    fflush(stdout);                                                  \
    char msg[400];                                                   \
    sprintf(msg, "%s:%s():%i: " s, __FILE__, __FUNCTION__, __LINE__, \
            ##__VA_ARGS__);                                          \
    PyErr_SetString(PyExc_ValueError, msg);                          \
  })

float f_fct(float r, PyArrayObject *fct, float Rmax) {

  float f, y1, y2, ix;
  int x1, x2;
  int n;

  /* interpolate */
  n = PyArray_DIM(fct, 0);
  ix = (r / Rmax * n);

  if (ix <= 0)
    f = *(float *)PyArray_GETPTR1(fct, 0);
  else {
    if (ix >= (n - 1)) {
      f = *(float *)PyArray_GETPTR1(fct, n - 1);
    } else {

      x1 = (int)ix;
      x2 = x1 + 1;

      y1 = *(float *)PyArray_GETPTR1(fct, x1);
      y2 = *(float *)PyArray_GETPTR1(fct, x2);

      f = (ix - x1) / (x2 - x1) * (y2 - y1) + y1;
    }
  }

  return f;
}

float ValFromVect(float x, PyArrayObject *xs, PyArrayObject *ys) {

  /*

  for a given x, return the interpolated corresponding y (from ys)
  x is assumed to be linear

  */

  float f, y1, y2;
  int x1, x2, nx;

  float xmin, xmax;
  float ix;

  /* interpolate */
  nx = PyArray_DIM(xs, 0);
  xmin = *(float *)PyArray_GETPTR1(xs, 0);
  xmax = *(float *)PyArray_GETPTR1(xs, nx - 1);

  ix = (x - xmin) / (xmax - xmin) * (nx - 1);

  x1 = (int)ix;
  x2 = x1 + 1;

  if ((ix < 0) || (x1 < 0)) {
    f = *(float *)PyArray_GETPTR1(ys, 0);
    return f;
  }

  if ((ix > (nx - 1)) || (x2 > (nx - 1))) {
    f = *(float *)PyArray_GETPTR1(ys, PyArray_DIM(ys, 0) - 1);
    return f;
  }

  /* here, we can interpolate */

  y1 = *(float *)PyArray_GETPTR1(ys, x1);
  y2 = *(float *)PyArray_GETPTR1(ys, x2);

  f = (ix - x1) / (x2 - x1) * (y2 - y1) + y1;

  printf("%g %g %d %g  - %g %g %d\n", x, ix, x1, y1, xmin, xmax, nx);

  return f;
}

float ValFromVect2(float x, PyArrayObject *xs, PyArrayObject *ys) {

  /*

  !!! here, xs is not linear !!!

  */

  float f = 0.;
  float y1, y2;
  float v1, v2;
  int x1, x2, nx, i;

  float xmin, xmax;

  /* interpolate */
  nx = PyArray_DIM(xs, 0);
  xmin = *(float *)PyArray_GETPTR1(xs, 0);
  xmax = *(float *)PyArray_GETPTR1(xs, nx - 1);

  if (x < xmin) {
    f = *(float *)PyArray_GETPTR1(ys, 0);
    return f;
  }

  if (x > xmax) {
    f = *(float *)PyArray_GETPTR1(ys, PyArray_DIM(ys, 0) - 1);
    return f;
  }

  /* here, we need to loop in order to find x1,x2*/

  for (i = 0; i < (nx - 1); i++) {

    x1 = i;
    x2 = i + 1;

    v1 = *(float *)PyArray_GETPTR1(xs, x1);
    v2 = *(float *)PyArray_GETPTR1(xs, x2);

    if ((v1 <= x) && (x < v2)) {

      y1 = *(float *)PyArray_GETPTR1(ys, x1);
      y2 = *(float *)PyArray_GETPTR1(ys, x2);

      f = (float)(x - v1) / (float)(v2 - v1) * (y2 - y1) + y1;
    }
  }

  return f;
}

/*********************************/
/* generic_Mx1D                 */
/*********************************/

static PyObject *iclib_generic_Mx1D(PyObject *self, PyObject *args) {

  PyArrayObject *x, *xs, *Mx;
  PyArrayObject *rand1;
  PyObject *verbose;
  float xmax;
  int n;

  int i;
  npy_intp ld[1];

  float XX;
  float MxMax;
  float rnd;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "ifOOOOOO", &n, &xmax, &xs, &Mx, &rand1,
                        &verbose))
    return NULL;

  /* create output */
  ld[0] = n;
  x = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  MxMax = ValFromVect(xmax, xs, Mx);

  for (i = 0; i < n; i++) {

    /* number between 0 and 1 */
    // rnd = (float)random()/(float)RAND_MAX;
    rnd = *(float *)PyArray_GETPTR1(rand1, i);

    /* find the corresponding radius (x may be nonlinear) */
    XX = ValFromVect2(rnd * MxMax, Mx, xs);

    if (verbose == Py_True)
      if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR1(x, i) = XX;
  }

  return PyArray_Return(x);
}

/*********************************/
/* generic_Mx                 */
/*********************************/

static PyObject *iclib_generic_Mx(PyObject *self, PyObject *args) {

  PyArrayObject *pos, *xs, *Mx;
  PyArrayObject *rand1, *rand2, *rand3;
  PyObject *verbose;
  float xmax;
  int n;

  int i;
  npy_intp ld[2];

  float XX, YY, ZZ;
  float MxMax;
  float rnd;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "ifOOOOOO", &n, &xmax, &xs, &Mx, &rand1, &rand2,
                        &rand3, &verbose))
    return NULL;

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  // srandom(irand);

  MxMax = ValFromVect(xmax, xs, Mx);

  /* normalize Mr */
  // for (i = 0; i < Mx->dimensions[0]; i++)
  //  {
  //  *(float*)(Mx->data + i*(Mx->strides[0])) = *(float*)(Mx->data +
  //  i*(Mx->strides[0]))/MxMax ;
  //  }

  for (i = 0; i < n; i++) {

    /* number between 0 and 1 */
    // rnd = (float)random()/(float)RAND_MAX;
    rnd = *(float *)PyArray_GETPTR1(rand1, i);

    /* find the corresponding radius (x may be nonlinear) */
    XX = ValFromVect2(rnd * MxMax, Mx, xs);
    YY = *(float *)PyArray_GETPTR1(rand2, i);
    ZZ = *(float *)PyArray_GETPTR1(rand3, i);

    if (verbose == Py_True)
      if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = ZZ;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* generic_alpha                 */
/*********************************/

float generic_alpha_density(float a, float e, float r) {

  return pow((r + e), a);
}

static PyObject *iclib_generic_alpha(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  float a, e, rmax;
  int n, irand;

  int i;
  npy_intp ld[2];

  float URHOD0, CTHE, STHE, PHI, RR, RHO, R;
  float XX, YY, ZZ;
  float EPS;
  float DPI;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "ifffi", &n, &a, &e, &rmax, &irand)) return NULL;

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  // pos = (PyArrayObject *) PyArray_FromDims(2,ld,PyArray_FLOAT);
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  EPS = 1e-30;
  EPS = 0;
  DPI = 8. * atan(1.);

  URHOD0 = 1. / (generic_alpha_density(a, e, 0.) + EPS);

  for (i = 0; i < n; i++) {

    do {

      RR = pow((float)random() / (float)RAND_MAX, 1.0 / 3.0);
      PHI = DPI * (float)random() / (float)RAND_MAX;
      CTHE = 1. - 2. * (float)random() / (float)RAND_MAX;
      STHE = sqrt(1. - CTHE * CTHE);

      XX = RR * cos(PHI) * STHE;
      YY = RR * sin(PHI) * STHE;
      ZZ = RR * CTHE;

      R = sqrt(XX * XX + YY * YY + ZZ * ZZ);

      RHO = URHOD0 * generic_alpha_density(a, e, rmax * R);

    } while (RHO < (float)random() / (float)RAND_MAX);

    if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = rmax * XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = rmax * YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = rmax * ZZ;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* generic_Mr                 */
/*********************************/

static PyObject *iclib_generic_Mr(PyObject *self, PyObject *args) {

  PyArrayObject *pos, *rs, *Mr;
  PyArrayObject *rand1, *rand2, *rand3;
  PyObject *verbose;
  float rmax;
  int n;

  int i;
  npy_intp ld[2];

  float CTHE, STHE, PHI, RR;
  float XX, YY, ZZ;
  float DPI, MrMax;
  float rnd;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "ifOOOOOO", &n, &rmax, &rs, &Mr, &rand1, &rand2,
                        &rand3, &verbose))
    return NULL;

  if (!PyArray_Check(rand1) || !PyArray_Check(rand2) || !PyArray_Check(rand3)) {
    error("Rand arguments must be numpy arrays.");
    return NULL;
  }

  if (PyArray_DIM(rand1, 0) != n || PyArray_DIM(rand2, 0) != n ||
      PyArray_DIM(rand3, 0) != n) {
    error("Rand arguments do not have the required size");
    return NULL;
  }

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  DPI = 8. * atan(1.);

  MrMax = ValFromVect(rmax, rs, Mr);

  for (i = 0; i < n; i++) {

    /* number between 0 and 1 */
    rnd = *(float *)PyArray_GETPTR1(rand1, i);

    /* find the corresponding radius (x may be nonlinear) */
    RR = ValFromVect2(rnd * MrMax, Mr, rs);

    rnd = *(float *)PyArray_GETPTR1(rand2, i);
    PHI = DPI * rnd;
    rnd = *(float *)PyArray_GETPTR1(rand3, i);
    CTHE = 1. - 2. * rnd;
    STHE = sqrt(1. - CTHE * CTHE);

    XX = RR * cos(PHI) * STHE;
    YY = RR * sin(PHI) * STHE;
    ZZ = RR * CTHE;

    if (verbose == Py_True)
      if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = ZZ;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* exponential_disk              */
/*********************************/

float RHO1(float X) {
  /* first deriv of TM1 */
  return X * exp(-X);
}

float TM1(float X) { return 1.0 - (1.0 + X) * exp(-X); }

static PyObject *iclib_exponential_disk(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  float Hr, Hz, Rmax, Zmax;
  float x, y, z;
  int n, irand;

  int i;
  npy_intp ld[2];
  int k;
  float XM, xx, D;
  float R, PHI;
  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffffi", &n, &Hr, &Hz, &Rmax, &Zmax, &irand))
    return NULL;

  /* create output */
  // pos = (PyArrayObject *)
  // PyArray_FromDims(as->nd,as->dimensions,as->descr->type_num);
  ld[0] = n;
  ld[1] = 3;
  // pos = (PyArrayObject *) PyArray_FromDims(2,ld,PyArray_FLOAT);
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  for (i = 0; i < n; i++) {

    /* radial distribution */
    R = Rmax + 1;
    while (R > Rmax) {

      k = 0;
      XM = (float)random() / (float)RAND_MAX;
      // xx = 2.*Hr*XM;			/* initial point (bad choice... Pfen ?)
      // */
      xx = 2. * XM; /* initial point */

      k = 0;
      D = 1;
      while (fabs(D) > 1E-12) {

        if (k > 32) {
          // printf("x0=%g xx=%g D=%g\n",x0,xx,D);
          break;
        }

        D = (XM - TM1(xx)) / RHO1(xx);
        xx = xx + D;
        k = k + 1;
      }

      R = xx * Hr;
    }

    /* angular distribution */
    PHI = TWOPI * (float)random() / (float)RAND_MAX;
    x = R * cos(PHI);
    y = R * sin(PHI);

    /* verticale distribution */
    z = Zmax + 1;
    while (z > Zmax) {
      z = -Hz * log((float)random() / (float)RAND_MAX);
    }

    if ((float)random() / (float)RAND_MAX < 0.5) z = -z;

    *(float *)PyArray_GETPTR2(pos, i, 0) = x;
    *(float *)PyArray_GETPTR2(pos, i, 1) = y;
    *(float *)PyArray_GETPTR2(pos, i, 2) = z;
  }

  return PyArray_Return(pos);
}






/*********************************/
/* exponential_disk_radius       */
/*********************************/


static PyObject *iclib_exponential_disk_radius(PyObject *self, PyObject *args) {

  PyArrayObject *Rs;
  float Hr, Rmax;
  int n, irand;

  int i;
  npy_intp ld[1];
  int k;
  float XM, xx, D;
  float R;
  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffi", &n, &Hr, &Rmax, &irand))
    return NULL;

  /* create output */
  // pos = (PyArrayObject *)
  // PyArray_FromDims(as->nd,as->dimensions,as->descr->type_num);
  ld[0] = n;
  // pos = (PyArrayObject *) PyArray_FromDims(2,ld,PyArray_FLOAT);
  Rs = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  for (i = 0; i < n; i++) {

    /* radial distribution */
    R = Rmax + 1;
    while (R > Rmax) {

      k = 0;
      XM = (float)random() / (float)RAND_MAX;
      // xx = 2.*Hr*XM;			/* initial point (bad choice... Pfen ?)
      // */
      xx = 2. * XM; /* initial point */

      k = 0;
      D = 1;
      while (fabs(D) > 1E-12) {

        if (k > 32) {
          // printf("x0=%g xx=%g D=%g\n",x0,xx,D);
          break;
        }

        D = (XM - TM1(xx)) / RHO1(xx);
        xx = xx + D;
        k = k + 1;
      }

      R = xx * Hr;
    }

    *(float *)PyArray_GETPTR1(Rs, i) = R;
  }

  return PyArray_Return(Rs);
}






/*********************************/
/* miyamoto_nagai                */
/*********************************/

float rhod1(float a, float b2, float r2, float z2) {

  float c, c2, d, d2;
  // float cte = 0.079577471636878186;

  c2 = b2 + z2;
  c = sqrt(c2);
  d = a + c;
  d2 = d * d;
  // return cte * b2*(a*r2 + (d+c+c)*d2) / ( c*c2*sqrt( pow((r2+d2),5) ) );
  return b2 * (a * r2 + (d + c + c) * d2) / (c * c2 * sqrt(pow((r2 + d2), 5)));
}

static PyObject *iclib_miyamoto_nagai(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  float a, b, Rmax, Zmax;
  int n, irand;

  int i;
  npy_intp ld[2];

  float URHOD0, CTHE, STHE, PHI, RR, R2, Z2, RHO;
  float XX, YY, ZZ;
  float EPS;
  float Rmax2, Zmax2, b2;
  float DPI;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffffi", &n, &a, &b, &Rmax, &Zmax, &irand))
    return NULL;

  /* create output */
  // pos = (PyArrayObject *)
  // PyArray_FromDims(as->nd,as->dimensions,as->descr->type_num);
  ld[0] = n;
  ld[1] = 3;
  // pos = (PyArrayObject *) PyArray_FromDims(2,ld,PyArray_FLOAT);
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  b2 = b * b;
  Rmax2 = Rmax * Rmax;
  Zmax2 = Zmax * Zmax;
  EPS = 1e-30;
  EPS = 0;
  DPI = 8. * atan(1.);

  URHOD0 = 1. / (rhod1(a, b2, 0., 0.) + EPS);

  for (i = 0; i < n; i++) {

    do {

      RR = pow((float)random() / (float)RAND_MAX, 1.0 / 3.0);
      PHI = DPI * (float)random() / (float)RAND_MAX;
      CTHE = 1. - 2. * (float)random() / (float)RAND_MAX;
      STHE = sqrt(1. - CTHE * CTHE);

      XX = RR * cos(PHI) * STHE;
      YY = RR * sin(PHI) * STHE;
      ZZ = RR * CTHE;

      R2 = XX * XX + YY * YY;
      Z2 = ZZ * ZZ;
      RHO = URHOD0 * rhod1(a, b2, Rmax2 * R2, Zmax2 * Z2);

    } while (RHO < (float)random() / (float)RAND_MAX);

    if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = Rmax * XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = Rmax * YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = Zmax * ZZ;
  }

  return PyArray_Return(pos);
}

static PyObject *iclib_miyamoto_nagai_f(PyObject *self, PyObject *args) {

  PyArrayObject *pos, *fct;
  float a, b, Rmax, Zmax;
  int n, irand;

  int i;
  npy_intp ld[2];

  float URHOD0, URHOD1, CTHE, STHE, PHI, RR, R2, Z2, RHO, R;
  float XX, YY, ZZ;
  float Rmax2, Zmax2, b2;
  float DPI;
  float fRmax;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffffiOf", &n, &a, &b, &Rmax, &Zmax, &irand,
                        &fct, &fRmax))
    return NULL;

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  // pos = (PyArrayObject *) PyArray_FromDims(2,ld,PyArray_FLOAT);
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  b2 = b * b;
  Rmax2 = Rmax * Rmax;
  Zmax2 = Zmax * Zmax;
  DPI = 8. * atan(1.);

  /* find the max density along the disk */
  URHOD0 = -1;

  for (i = 0; i < n; i++) {
    R = Rmax * ((float)i / (float)n);
    R2 = R * R;

    URHOD1 = rhod1(a, b2, R2, 0) / f_fct(R, fct, fRmax);

    if (URHOD1 > URHOD0) {
      URHOD0 = URHOD1;
    }
  }

  URHOD0 = 1 / URHOD0;

  for (i = 0; i < n; i++) {

    do {

      RR = pow((float)random() / (float)RAND_MAX, 1.0 / 3.0);
      PHI = DPI * (float)random() / (float)RAND_MAX;
      CTHE = 1. - 2. * (float)random() / (float)RAND_MAX;
      STHE = sqrt(1. - CTHE * CTHE);

      XX = RR * cos(PHI) * STHE;
      YY = RR * sin(PHI) * STHE;
      ZZ = RR * CTHE;

      R2 = XX * XX + YY * YY;
      Z2 = ZZ * ZZ;
      RHO = URHOD0 * rhod1(a, b2, Rmax2 * R2, Zmax2 * Z2) /
            f_fct(sqrt(Rmax2 * R2), fct, fRmax);

    } while (RHO < (float)random() / (float)RAND_MAX);

    if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = Rmax * XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = Rmax * YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = Zmax * ZZ;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* Burkert                */
/*********************************/

float burkert_density(float rs, float r) {
  return 1 / ((1 + r / rs) * (1 + pow((r / rs), 2)));
}

static PyObject *iclib_burkert(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  float rs, Rmax;
  int n, irand;

  int i;
  npy_intp ld[2];

  float URHOD0, CTHE, STHE, PHI, RR, R2, RHO;
  float XX, YY, ZZ;
  float Rmax2;
  float DPI;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffi", &n, &rs, &Rmax, &irand)) return NULL;

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  Rmax2 = Rmax * Rmax;
  DPI = 8. * atan(1.);

  URHOD0 = 1 / burkert_density(rs, 0);

  for (i = 0; i < n; i++) {

    do {

      RR = pow((float)random() / (float)RAND_MAX, 1.0 / 3.0);
      PHI = DPI * (float)random() / (float)RAND_MAX;
      CTHE = 1. - 2. * (float)random() / (float)RAND_MAX;
      STHE = sqrt(1. - CTHE * CTHE);

      XX = RR * cos(PHI) * STHE;
      YY = RR * sin(PHI) * STHE;
      ZZ = RR * CTHE;

      R2 = XX * XX + YY * YY + ZZ * ZZ;

      RHO = URHOD0 * burkert_density(rs, sqrt(Rmax2 * R2));

    } while (RHO < (float)random() / (float)RAND_MAX);

    if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = Rmax * XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = Rmax * YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = Rmax * ZZ;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* NFWg				 */
/*********************************/

float nfwg_density(float rs, float gamma, float e, float r) {
  return 1 / (pow(((r + e) / rs), gamma) *
              pow(1 + pow(r / rs, 2), 0.5 * (3 - gamma)));
  // return  1/  (     (((r+e)/rs) ) * pow(1+r/rs,2)   );
}

static PyObject *iclib_nfwg(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  float rs, gamma, e, Rmax;
  int n, irand;

  int i;
  npy_intp ld[2];

  float URHOD0, CTHE, STHE, PHI, RR, R2, RHO;
  float XX, YY, ZZ;
  float Rmax2;
  float DPI;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "iffffi", &n, &rs, &gamma, &e, &Rmax, &irand))
    return NULL;

  /* create output */
  ld[0] = n;
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  Rmax2 = Rmax * Rmax;
  DPI = 8. * atan(1.);

  URHOD0 = 1 / nfwg_density(rs, gamma, e, 0);

  for (i = 0; i < n; i++) {

    do {

      RR = pow((float)random() / (float)RAND_MAX, 1.0 / 3.0);
      PHI = DPI * (float)random() / (float)RAND_MAX;
      CTHE = 1. - 2. * (float)random() / (float)RAND_MAX;
      STHE = sqrt(1. - CTHE * CTHE);

      XX = RR * cos(PHI) * STHE;
      YY = RR * sin(PHI) * STHE;
      ZZ = RR * CTHE;

      R2 = XX * XX + YY * YY + ZZ * ZZ;

      RHO = URHOD0 * nfwg_density(rs, gamma, e, sqrt(Rmax2 * R2));

    } while (RHO < (float)random() / (float)RAND_MAX);

    if (fmod(i, 10000) == 0 && i != 0) printf("i=%8d/%d\n", i, n);

    *(float *)PyArray_GETPTR2(pos, i, 0) = Rmax * XX;
    *(float *)PyArray_GETPTR2(pos, i, 1) = Rmax * YY;
    *(float *)PyArray_GETPTR2(pos, i, 2) = Rmax * ZZ;
  }

  return PyArray_Return(pos);
}

/* definition of the method table */

static PyMethodDef iclibMethods[] = {

    {"generic_Mx1D", iclib_generic_Mx1D, METH_VARARGS,
     "Return position following the density given by M(x)=Mx. Return only x."},

    {"generic_Mx", iclib_generic_Mx, METH_VARARGS,
     "Return position following the density given by M(x)=Mx. We assume an "
     "homogeneous distribution in y and z."},

    {"generic_alpha", iclib_generic_alpha, METH_VARARGS,
     "Return position following the density (r+eps)^a."},

    {"generic_Mr", iclib_generic_Mr, METH_VARARGS,
     "Return position following the density given by M(r)=Mr."},

    {"exponential_disk", iclib_exponential_disk, METH_VARARGS,
     "Return position of an exponential disk."},
     
    {"exponential_disk_radius", iclib_exponential_disk_radius, METH_VARARGS,
     "Return radius of an exponential disk."},     

    {"miyamoto_nagai", iclib_miyamoto_nagai, METH_VARARGS,
     "Return position of a miyamoto_nagai model."},

    {"miyamoto_nagai_f", iclib_miyamoto_nagai_f, METH_VARARGS,
     "Return position of a miyamoto_nagai model divided by f(R)."},

    {"miyamoto_nagai_f", iclib_miyamoto_nagai_f, METH_VARARGS,
     "Return position of a miyamoto_nagai model divided by f(R)."},

    {"burkert", iclib_burkert, METH_VARARGS,
     "Return position of a burkert model."},

    {"nfwg", iclib_nfwg, METH_VARARGS, "Return position of a nfwg model."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef iclibmodule = {
    PyModuleDef_HEAD_INIT,
    "iclib",
    "",
    -1,
    iclibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_iclib(void) {
  PyObject *m;
  m = PyModule_Create(&iclibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
