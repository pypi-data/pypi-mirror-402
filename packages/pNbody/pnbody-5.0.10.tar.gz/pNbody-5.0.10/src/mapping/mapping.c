#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#include "kernels.h"

#define kxmax1d 1024

#define kxmax2d 1024
#define kymax2d 1024

#define kxmax3d 64
#define kymax3d 64
#define kzmax3d 64

#define PI 3.14159265358979

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

/*! Single precision fast exponential function from StackOverflow
  https://stackoverflow.com/a/10792321

  Abridged description by user njuffa:

  For inputs in [-87,88] the results have relative error <= 1.73e-3.

  A classic algorithm is being used in which the computation of exp() is mapped
  to computation of exp2(). After argument conversion via multiplication by
  log2(e), exponentation by the fractional part is handled using a minimax
  polynomial of degree 2, while exponentation by the integral part of the
  argument is performed by direct manipulation of the exponent part of the
  IEEE-754 single-precision number.

  The volatile union facilitates re-interpretation of a bit pattern as either
  an integer or a single-precision floating-point number, needed for the exponent
  manipulation.

  APC: quick tests confirm this is indeed accurate to ~1e-3 over the (small)
  range of exponents we deal with. We might improve the accuracy with a more
  tighly tuned lookup table.
  */
float fast_exp (float x)
{
  volatile union {
    float f;
    unsigned int i;
  } cvt;

  /* exp(x) = 2^i * 2^f; i = floor (log2(e) * x), 0 <= f <= 1 */
  float t = x * 1.442695041f;
  float fi = floorf (t);
  float f = t - fi;
  int i = (int)fi;
  cvt.f = (0.3371894346f * f + 0.657636276f) * f + 1.00172476f; /* compute 2^f  */
  cvt.i += (i << 23);                                           /* scale by 2^i */
  return cvt.f;
}

/*********************************/
/* mkmap1d */
/*********************************/

static PyObject *mapping_mkmap1d(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i;
  int ix;
  int kx;
  npy_intp ld[1];

  float dseo[kxmax1d];
  float x, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(i)", &pos, &gmm, &amp, &kx)) return NULL;

  /* check max size of matrix */
  if (kx > kxmax1d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  mat = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be one dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    dseo[ix] = 0.;
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);

    if (ix >= 0 && x < kx) dseo[ix] = dseo[ix] + gm * am;
  }

  /* create the subimage */
  for (i = 0; i < kx; i++) {
    *(float *)PyArray_GETPTR1(mat, i) = (float)dseo[i];
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap1dn */
/*********************************/

static PyObject *mapping_mkmap1dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i;
  int ix;
  int kx;
  npy_intp ld[1];

  float *dseo;
  float x, gm, am;
  size_t bytes;

  if (!PyArg_ParseTuple(args, "OOO(i)", &pos, &gmm, &amp, &kx)) return NULL;

  if (!(dseo = malloc(bytes = kx * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  mat = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be one dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    dseo[ix] = 0.;
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);

    if (ix >= 0 && x < kx) dseo[ix] = dseo[ix] + gm * am;
  }

  /* create the subimage */
  for (i = 0; i < kx; i++) {
    *(float *)PyArray_GETPTR1(mat, i) = (float)dseo[i];
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkcic1dn */
/*********************************/

static PyObject *mapping_mkcic1dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;

  int    nx;   /* size   in x,y */
  double lx;   /* length in x,y */
  double cx;   /* center in x,y */
  
  PyArrayObject *mat;
  
  npy_intp ld[1];
  size_t bytes;
  
  int p, n;
  int i;
  double x;
  double dx;
  double tx;
  float value;
    
    
  if (!PyArg_ParseTuple(args, "OO(d)(d)(i)", &pos, &gmm, &cx, &lx, &nx))
    return NULL;
    

  /* check the size and type of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type float32");
    return NULL;
   }

  /* check the size and type of gmm */
  if (PyArray_NDIM(gmm) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 2 must be one dimentionnal and of type float32");
    return NULL;
   }
   
    
  if (!(mat = malloc(bytes = nx * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* create the output */
  ld[0] = nx;
  
  mat = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  
  /* initialize */
  for (i=0;i<nx;i++)
    *(float *)PyArray_GETPTR1(mat, i) = 0;
  
  
  /* scale the center */
  cx = cx/lx;


  for (p = 0; p < n; p++) {
    x = *(float *)PyArray_GETPTR2(pos, p, 0);
    
    /* Scale between 0 and nx */
    x = (x/lx - cx + 0.5)* nx;
        
    /* Workout the CIC coefficients */
    i = (int)floor(x);
    if ((i<0) || (i>=nx)) continue;
    const double dx = x - i;
    const double tx = 1. - dx;
    
    value = *(float *)PyArray_GETPTR1(gmm, p);
    
    *(float *)PyArray_GETPTR1(mat, i + 0) += value * tx;
    *(float *)PyArray_GETPTR1(mat, i + 1) += value * dx;
     
  } 
     
  return PyArray_Return(mat);
  
}



/*********************************/
/* mkcic2dn */
/*********************************/


static PyObject *mapping_mkcic2dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;

  int    nx, ny;   /* size   in x,y */
  double lx, ly;   /* length in x,y */
  double cx, cy;   /* center in x,y */
  
  PyArrayObject *mat;
  
  npy_intp ld[2];
  size_t bytes;
  
  int p, n;
  int i, j;
  double x, y;
  double dx, dy;
  double tx, ty;
  float value;
    
    
  if (!PyArg_ParseTuple(args, "OO(dd)(dd)(ii)", &pos, &gmm, &cx, &cy, &lx, &ly, &nx, &ny))
    return NULL;
    

  /* check the size and type of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type float32");
    return NULL;
   }

  /* check the size and type of gmm */
  if (PyArray_NDIM(gmm) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 2 must be one dimentionnal and of type float32");
    return NULL;
   }
   
    
  if (!(mat = malloc(bytes = nx * ny * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* create the output */
  ld[0] = nx;
  ld[1] = ny;
  
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);
  
  /* initialize */
  for (i=0;i<nx;i++)
    for (j=0;j<ny;j++)
      *(float *)PyArray_GETPTR2(mat, i, j) = 0;
  
  
  /* scale the center */
  cx = cx/lx;
  cy = cy/ly;


  for (p = 0; p < n; p++) {
    x = *(float *)PyArray_GETPTR2(pos, p, 0);
    y = *(float *)PyArray_GETPTR2(pos, p, 1);
    
    /* Scale between 0 and nx */
    x = (x/lx - cx + 0.5)* nx;
    y = (y/ly - cy + 0.5)* ny;
        
    /* Workout the CIC coefficients */
    i = (int)floor(x);
    if ((i<0) || (i>=nx)) continue;
    const double dx = x - i;
    const double tx = 1. - dx;
    
    j = (int)floor(y);
    if ((j<0) || (j>=ny)) continue;
    const double dy = y - j;
    const double ty = 1. - dy;
    
    value = *(float *)PyArray_GETPTR1(gmm, p);
    
    *(float *)PyArray_GETPTR2(mat, i + 0, j + 0) += value * tx * ty;
    *(float *)PyArray_GETPTR2(mat, i + 0, j + 1) += value * tx * dy;
    *(float *)PyArray_GETPTR2(mat, i + 1, j + 0) += value * dx * ty;
    *(float *)PyArray_GETPTR2(mat, i + 1, j + 1) += value * dx * dy;
     
  } 
     
  return PyArray_Return(mat);
  
}




/*********************************/
/* mkcic3dn */
/*********************************/


static PyObject *mapping_mkcic3dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;

  int    nx, ny, nz;   /* size   in x,y,z */
  double lx, ly, lz;   /* length in x,y,z */
  double cx, cy, cz;   /* center in x,y,z */
  
  PyArrayObject *mat;
  
  npy_intp ld[3];
  size_t bytes;
  
  int p, n;
  int i, j, k;
  double x, y, z;
  double dx, dy, dz;
  double tx, ty, tz;
  float value;
    
    
  if (!PyArg_ParseTuple(args, "OO(ddd)(ddd)(iii)", &pos, &gmm, &cx, &cy, &cz, &lx, &ly, &lz, &nx, &ny, &nz))
    return NULL;
    

  /* check the size and type of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type float32");
    return NULL;
   }

  /* check the size and type of gmm */
  if (PyArray_NDIM(gmm) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 2 must be one dimentionnal and of type float32");
    return NULL;
   }
   
    
  if (!(mat = malloc(bytes = nx * ny * nz * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* create the output */
  ld[0] = nx;
  ld[1] = ny;
  ld[2] = ny;
  
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);
  
  /* initialize */
  for (i=0;i<nx;i++)
    for (j=0;j<ny;j++)
      for (k=0;k<nz;k++)
        *(float *)PyArray_GETPTR3(mat, i, j, k) = 0;
  
  
  /* scale the center */
  cx = cx/lx;
  cy = cy/ly;
  cz = cz/lz;


  for (p = 0; p < n; p++) {
    x = *(float *)PyArray_GETPTR2(pos, p, 0);
    y = *(float *)PyArray_GETPTR2(pos, p, 1);
    z = *(float *)PyArray_GETPTR2(pos, p, 2);
    
    /* Scale between 0 and nx */
    x = (x/lx - cx + 0.5)* nx;
    y = (y/ly - cy + 0.5)* ny;
    z = (z/lz - cz + 0.5)* nz;
        
    /* Workout the CIC coefficients */
    i = (int)floor(x);
    if ((i<0) || (i>=nx)) continue;
    const double dx = x - i;
    const double tx = 1. - dx;
    
    j = (int)floor(y);
    if ((j<0) || (j>=ny)) continue;
    const double dy = y - j;
    const double ty = 1. - dy;

    k = (int)floor(z);
    if ((k<0) || (k>=nz)) continue;
    const double dz = z - k;
    const double tz = 1. - dz;
    
    value = *(float *)PyArray_GETPTR1(gmm, p);
    
    *(float *)PyArray_GETPTR3(mat, i + 0, j + 0, k + 0) += value * tx * ty * tz;
    *(float *)PyArray_GETPTR3(mat, i + 0, j + 0, k + 1) += value * tx * ty * dz;
    *(float *)PyArray_GETPTR3(mat, i + 0, j + 1, k + 0) += value * tx * dy * tz;
    *(float *)PyArray_GETPTR3(mat, i + 0, j + 1, k + 1) += value * tx * dy * dz;
    *(float *)PyArray_GETPTR3(mat, i + 1, j + 0, k + 0) += value * dx * ty * tz;
    *(float *)PyArray_GETPTR3(mat, i + 1, j + 0, k + 1) += value * dx * ty * dz;
    *(float *)PyArray_GETPTR3(mat, i + 1, j + 1, k + 0) += value * dx * dy * tz;
    *(float *)PyArray_GETPTR3(mat, i + 1, j + 1, k + 1) += value * dx * dy * dz;
     
  } 
     
  return PyArray_Return(mat);
  
}








/*********************************/
/* mkmap2d */
/*********************************/

static PyObject *mapping_mkmap2d(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float dseo[kxmax2d][kymax2d];
  float x, y, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(ii)", &pos, &gmm, &amp, &kx, &ky))
    return NULL;

  /* check max size of matrix */
  if (kx > kxmax2d || ky > kymax2d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix][iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);
    iy = (int)(y);

    if (ix >= 0 && ix < kx)
      if (iy >= 0 && iy < ky) dseo[ix][iy] = dseo[ix][iy] + gm * am;
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i][j];
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap2dn */
/*********************************/

static PyObject *mapping_mkmap2dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float *dseo;
  float x, y, gm, am;
  size_t bytes;

  if (!PyArg_ParseTuple(args, "OOO(ii)", &pos, &gmm, &amp, &kx, &ky))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[iy + ix * ky] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);
    iy = (int)(y);

    if (ix >= 0 && ix < kx)
      if (iy >= 0 && iy < ky) {
        dseo[iy + ix * ky] = dseo[iy + ix * ky] + gm * am;
      }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[j + i * ky];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3d */
/*********************************/

static PyObject *mapping_mkmap3d(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j, k;
  int ix, iy, iz;
  int kx, ky, kz;
  npy_intp ld[3];

  float dseo[kxmax3d][kymax3d][kzmax3d];
  float x, y, z, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(iii)", &pos, &gmm, &amp, &kx, &ky, &kz))
    return NULL;

  /* check max size of matrix */
  if (kx > kxmax3d || ky > kymax3d || kz > kzmax3d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  ld[2] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      for (iz = 0; iz < kz; iz++) {
        dseo[ix][iy][iz] = 0.;
      }
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    z = *(float *)PyArray_GETPTR2(pos, i, 2) * kz;

    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);
    iy = (int)(y);
    iz = (int)(z);

    if (ix >= 0 && ix < kx)
      if (iy >= 0 && iy < ky)
        if (iz >= 0 && iz < kz) dseo[ix][iy][iz] = dseo[ix][iy][iz] + gm * am;
  }

  /* create the subimage */
  for (k = 0; k < kz; k++) {
    for (j = 0; j < ky; j++) {
      for (i = 0; i < kx; i++) {
        *(float *)PyArray_GETPTR3(mat, i, j, k) = (float)dseo[i][j][k];
      }
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3dn */
/*********************************/

static PyObject *mapping_mkmap3dn(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j, k;
  int ix, iy, iz;
  int kx, ky, kz;
  npy_intp ld[3];

  float *dseo;
  float x, y, z, gm, am;
  size_t bytes;

  if (!PyArg_ParseTuple(args, "OOO(iii)", &pos, &gmm, &amp, &kx, &ky, &kz))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * kz * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  ld[2] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      for (iz = 0; iz < kz; iz++) {
        dseo[ix * (kz * ky) + iy * (kz) + iz] = 0.;
      }
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    z = *(float *)PyArray_GETPTR2(pos, i, 2) * kz;

    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    ix = (int)(x);
    iy = (int)(y);
    iz = (int)(z);

    if (ix >= 0 && ix < kx)
      if (iy >= 0 && iy < ky)
        if (iz >= 0 && iz < kz)
          dseo[ix * (kz * ky) + iy * (kz) + iz] =
              dseo[ix * (kz * ky) + iy * (kz) + iz] + gm * am;
  }

  /* create the subimage */
  for (k = 0; k < kz; k++) {
    for (j = 0; j < ky; j++) {
      for (i = 0; i < kx; i++) {
        *(float *)PyArray_GETPTR3(mat, i, j, k) =
            (float)dseo[i * (kz * ky) + j * (kz) + k];
      }
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap1dw */
/*********************************/

static PyObject *mapping_mkmap1dw(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i;
  int ix1, ix2;
  float wx1, wx2;
  int kx;
  npy_intp ld[1];

  float dseo[kxmax1d];
  float x, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(i)", &pos, &gmm, &amp, &kx)) return NULL;

  /* check max size of matrix */
  if (kx > kxmax1d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  mat = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 1 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be one dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix1 = 0; ix1 < kx; ix1++) {
    dseo[ix1] = 0.;
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    if (x >= 0 && x <= 1) {

      x = x * (kx - 1);

      ix1 = (int)(x);
      ix2 = ix1 + 1;

      wx1 = 1 - (x - ix1);
      wx2 = 1 - (ix2 - x);

      if (wx1 > 0) dseo[ix1] = dseo[ix1] + gm * am * wx1;
      if (wx2 > 0) dseo[ix2] = dseo[ix2] + gm * am * wx2;
    }
  }

  /* create the subimage */
  for (i = 0; i < kx; i++) {
    *(float *)PyArray_GETPTR1(mat, i) = (float)dseo[i];
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap2dw */
/*********************************/

static PyObject *mapping_mkmap2dw(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix1, ix2, iy1, iy2;
  float wx1, wx2, wy1, wy2;
  int kx, ky;
  npy_intp ld[2];

  float dseo[kxmax2d][kymax2d];
  float x, y, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(ii)", &pos, &gmm, &amp, &kx, &ky))
    return NULL;

  /* check max size of matrix */
  if (kx > kxmax2d || ky > kymax2d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix1 = 0; ix1 < kx; ix1++) {
    for (iy1 = 0; iy1 < ky; iy1++) {
      dseo[ix1][iy1] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    if ((x >= 0 && x <= 1) && (y >= 0 && y <= 1)) {

      x = x * (kx - 1);
      ix1 = (int)(x);
      ix2 = ix1 + 1;
      wx1 = 1 - (x - ix1);
      wx2 = 1 - (ix2 - x);

      y = y * (ky - 1);
      iy1 = (int)(y);
      iy2 = iy1 + 1;
      wy1 = 1 - (y - iy1);
      wy2 = 1 - (iy2 - y);

      if (wx1 * wy1 > 0) dseo[ix1][iy1] = dseo[ix1][iy1] + gm * am * wx1 * wy1;
      if (wx2 * wy1 > 0) dseo[ix2][iy1] = dseo[ix2][iy1] + gm * am * wx2 * wy1;
      if (wx1 * wy2 > 0) dseo[ix1][iy2] = dseo[ix1][iy2] + gm * am * wx1 * wy2;
      if (wx2 * wy2 > 0) dseo[ix2][iy2] = dseo[ix2][iy2] + gm * am * wx2 * wy2;
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i][j];
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3dw */
/*********************************/

static PyObject *mapping_mkmap3dw(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;

  PyArrayObject *mat;

  int n, i, j, k;
  int ix1, ix2, iy1, iy2, iz1, iz2;
  float wx1, wx2, wy1, wy2, wz1, wz2;
  int kx, ky, kz;
  npy_intp ld[3];

  float dseo[kxmax3d][kymax3d][kzmax3d];
  float x, y, z, gm, am;

  if (!PyArg_ParseTuple(args, "OOO(iii)", &pos, &gmm, &amp, &kx, &ky, &kz))
    return NULL;

  /* check max size of matrix */
  if (kx > kxmax3d || ky > kymax3d || kz > kzmax3d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  ld[2] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix1 = 0; ix1 < kx; ix1++) {
    for (iy1 = 0; iy1 < ky; iy1++) {
      for (iz1 = 0; iz1 < kz; iz1++) {
        dseo[ix1][iy1][iz1] = 0.;
      }
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    z = *(float *)PyArray_GETPTR2(pos, i, 2);

    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    if ((x >= 0 && x <= 1) && (y >= 0 && y <= 1) && (z >= 0 && z <= 1)) {

      x = x * (kx - 1);
      ix1 = (int)(x);
      ix2 = ix1 + 1;
      wx1 = 1 - (x - ix1);
      wx2 = 1 - (ix2 - x);

      y = y * (ky - 1);
      iy1 = (int)(y);
      iy2 = iy1 + 1;
      wy1 = 1 - (y - iy1);
      wy2 = 1 - (iy2 - y);

      z = z * (kz - 1);
      iz1 = (int)(z);
      iz2 = iz1 + 1;
      wz1 = 1 - (z - iz1);
      wz2 = 1 - (iz2 - z);

      if (wx1 * wy1 * wz1 > 0)
        dseo[ix1][iy1][iz1] = dseo[ix1][iy1][iz1] + gm * am * wx1 * wy1 * wz1;
      if (wx1 * wy1 * wz2 > 0)
        dseo[ix1][iy1][iz2] = dseo[ix1][iy1][iz2] + gm * am * wx1 * wy1 * wz2;
      if (wx1 * wy2 * wz1 > 0)
        dseo[ix1][iy2][iz1] = dseo[ix1][iy2][iz1] + gm * am * wx1 * wy2 * wz1;
      if (wx1 * wy2 * wz2 > 0)
        dseo[ix1][iy2][iz2] = dseo[ix1][iy2][iz2] + gm * am * wx1 * wy2 * wz2;
      if (wx2 * wy1 * wz1 > 0)
        dseo[ix2][iy1][iz1] = dseo[ix2][iy1][iz1] + gm * am * wx2 * wy1 * wz1;
      if (wx2 * wy1 * wz2 > 0)
        dseo[ix2][iy1][iz2] = dseo[ix2][iy1][iz2] + gm * am * wx2 * wy1 * wz2;
      if (wx2 * wy2 * wz1 > 0)
        dseo[ix2][iy2][iz1] = dseo[ix2][iy2][iz1] + gm * am * wx2 * wy2 * wz1;
      if (wx2 * wy2 * wz2 > 0)
        dseo[ix2][iy2][iz2] = dseo[ix2][iy2][iz2] + gm * am * wx2 * wy2 * wz2;
    }
  }

  /* create the subimage */
  for (k = 0; k < kz; k++) {
    for (j = 0; j < ky; j++) {
      for (i = 0; i < kx; i++) {
        *(float *)PyArray_GETPTR3(mat, i, j, k) = (float)dseo[i][j][k];
      }
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap2dsph */
/*********************************/

static PyObject *mapping_mkmap2dsph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float dseo[kxmax2d][kymax2d];

  float x, y, gm, am, sigma, sigma2, pisig, gaus, sum;
  int xin, xfi, yin, yfi, ixx, iyy;
  int dkx2, dky2, dkx, dky;

  if (!PyArg_ParseTuple(args, "OOOO(ii)", &pos, &gmm, &amp, &rsp, &kx, &ky))
    return NULL;

  /* check max size of matrix */
  if (kx > kxmax2d || ky > kymax2d) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix][iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);
    sigma = *(float *)PyArray_GETPTR1(rsp, i);

    /* the size of the subgrid */

    dkx2 = (int)(3. * sigma); /* 3 sigma -> 98% volume */
    dky2 = (int)(3. * sigma);

    dkx = 2. * dkx2 + 1;
    dky = 2. * dky2 + 1;

    if (dkx == 1 && dky == 1) { /* the size is 1 */

      ix = (int)(x);
      iy = (int)(y);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky) dseo[ix][iy] = dseo[ix][iy] + gm * am;

    } else {

      ix = (int)x; /* center of the sub grid */
      iy = (int)y;

      sigma2 = sigma * sigma;
      pisig = 1. / (2. * PI * sigma2);

      sum = 0;

      /* bornes */

      xin = ix - dkx2;
      yin = iy - dky2;
      xfi = ix + dkx2 + 1;
      yfi = iy + dky2 + 1;

      if (xin < 0) {
        xin = 0;
      }
      if (yin < 0) {
        yin = 0;
      }
      if (xfi > kx - 1) {
        xfi = kx - 1;
      }
      if (yfi > ky - 1) {
        yfi = ky - 1;
      }

      if (xfi > xin && yfi > yin) {

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
          for (iyy = yin; iyy < yfi; iyy++) {

            gaus = pisig * exp(0.5 * (-((float)(ix - ixx) / (sigma)) *
                                          ((float)(ix - ixx) / (sigma)) -
                                      ((float)(iy - iyy) / (sigma)) *
                                          ((float)(iy - iyy) / (sigma))));
            sum = sum + gaus;

            dseo[ixx][iyy] = dseo[ixx][iyy] + gm * am * gaus;
          }
        }
      }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i][j];
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap2dnsph */
/*********************************/

static PyObject *mapping_mkmap2dnsph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float *dseo;
  size_t bytes;

  float x, y, gm, am, sigma, sigma2, pisig, gaus;
  //float sum;
  int xin, xfi, yin, yfi, ixx, iyy;
  int dkx2, dky2, dkx, dky;

  /* Inner loop variables (individual particle kernels) */
  float particle_amp, inv_2sigma2, dx2, dr2, gauss_exponent;
  int ixoff;

  /* Sigma clipping parameter: default is 3 sigma (98%) */
  const float sigma_clip  = 3.0;

  if (!PyArg_ParseTuple(args, "OOOO(ii)", &pos, &gmm, &amp, &rsp, &kx, &ky))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);
    sigma = *(float *)PyArray_GETPTR1(rsp, i);

    sigma2 = sigma * sigma;
    pisig = 1. / (2. * PI * sigma2);

    /* the size of the subgrid */

    dkx2 = (int)(sigma_clip * sigma); /* 3 sigma -> 98% volume */
    dky2 = (int)(sigma_clip * sigma);

    dkx = 2. * dkx2 + 1;
    dky = 2. * dky2 + 1;

    if (dkx == 1 && dky == 1) { /* the size is 1 */

      ix = (int)(x);
      iy = (int)(y);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky)
          dseo[ix * ky + iy] = dseo[ix * ky + iy] + gm * am;

    } else {

      ix = (int)x; /* center of the sub grid */
      iy = (int)y;

      // sum = 0;

      // printf("%f %d %d %d %d\n",sigma,dkx,dky,kx,ky);

      /* bornes */

      xin = ix - dkx2;
      yin = iy - dky2;
      xfi = ix + dkx2 + 1;
      yfi = iy + dky2 + 1;

      if (xin < 0) {
        xin = 0;
      }
      if (yin < 0) {
        yin = 0;
      }
      if (xfi > kx - 1) {
        xfi = kx - 1;
      }
      if (yfi > ky - 1) {
        yfi = ky - 1;
      }

      if (xfi > xin && yfi > yin) {

	/* These factors are the same for all gridpoints, for a given particle */
	particle_amp = pisig*gm*am;  // Kernel amplitude
        inv_2sigma2 = -0.5/sigma2; // -1/(2*sigma^2) factor in gaussian exp.

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
	  ixoff = ixx * ky; // Starting offset in parent grid
	  dx2 = (float)(ix - ixx) * (float)(ix - ixx);
          for (iyy = yin; iyy < yfi; iyy++) {
	    dr2 = dx2 + ((float)(iy - iyy) * (float)(iy - iyy));

	    /* Strictly enforce sigma clipping, map to a circle
	       For 3-sigma clipping, skip if dr^2/sigma^2 > 9.0,
	       equivalent to -0.5*dr^2/sigma^2 < -4.5 */
	    gauss_exponent = inv_2sigma2*dr2;
	    if (gauss_exponent < -sigma_clip*sigma_clip/2.0) continue;

	    /* Compute exp(-0.5 * (dx^2 + dy^2)/sigma^2) */
            gaus = fast_exp(gauss_exponent);
	    // sum = sum + gaus;

            dseo[ixoff + iyy] = dseo[ixoff + iyy] + particle_amp * gaus;
          }
        }
      }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i * ky + j];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}


/*********************************/
/* mkmap2dn_IDs */
/*********************************/

static PyObject *mapping_mkmap2dn_IDs(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *num = NULL;

  int n, i;
  int ix, iy;
  int id;

  float x, y;
  int kx,ky;


  if (!PyArg_ParseTuple(args, "OO(ii)", &pos, &num, &kx, &ky))
    return NULL;


  // Allocate memory for n pointers to integers
  int **ptrList = (int **)calloc(kx*ky , sizeof(int *));
  int *ptrCnt = calloc(kx * ky , sizeof(int));

    
 
  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);



  /* loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    id = *(int *)PyArray_GETPTR1(num,i);

    ix = (int)x; 
    iy = (int)y;

    if (ix >= 0 && ix < kx) {
      if (iy >= 0 && iy < ky) {

        // index in ptrList
        int idx = ix * ky + iy;

        //printf("x=%f y=%f ix=%d iy=%d id=%d idx=%d\n",x,y,ix,iy,id,idx);

        
        // if no elements is attached for the moment
        // allocate one element
        if (ptrCnt[idx]==0) { 
          ptrList[idx] = (int *)calloc(1,sizeof(int));
        }
        else {          
          // the slot is not empty, add a new element           
          ptrList[idx] = (int *)realloc(ptrList[idx],(ptrCnt[idx]+1)*sizeof(int));
        }   

        // add the id of the particle
        ptrList[idx][ptrCnt[idx]] = id;          
        ptrCnt[idx]+=1;

        if (ptrList[idx] == NULL) {
          printf("Memory allocation failed!\n");
          return NULL;
        }

      }
    }

  }

  // now, its time to fill the numpy array
 
    
  // Import NumPy API
  import_array();

  // Create a 2D NumPy array with dtype=object
  npy_intp dims[2] = {kx, ky};
  PyObject *matrix = PyArray_SimpleNew(2, dims, NPY_OBJECT);

  if (!matrix) {
        return NULL;
  }

  
  int vec_size;
  npy_intp vec_dims[1];
  PyObject *vector;
  int *data;
        


  // loop over the matrix and check for non empty slots
  for (ix=0;ix<kx;ix++){
    for (iy=0;iy<ky;iy++){
      // index in the matrix
      int idx = ix * ky + iy;

      // continue if the slot is empty 
      if (ptrCnt[idx]==0)
        continue;


      //printf("idx=%d  size=%d\n",idx,ptrCnt[idx]);
      
      vec_size = ptrCnt[idx];
      vec_dims[0] = vec_size;

      // Create a NumPy array for the vector
      vector = PyArray_SimpleNew(1, vec_dims, NPY_INT);
      if (!vector) {
        Py_DECREF(matrix);
        return NULL;
      }


      // Fill the vector with some values
      data = (int *)PyArray_DATA((PyArrayObject *)vector);
      for (int k = 0; k < vec_size; k++) {
        data[k] = ptrList[idx][k];
        //printf("  %d\n",data[k]);
      }

      // Insert the vector into the object array
      PyArray_SETITEM((PyArrayObject *) matrix, PyArray_GETPTR2((PyArrayObject *)matrix, ix, iy), vector);
      Py_DECREF(vector);  // Decrease reference since SETITEM increases it           
       
    }    
  }  


  return matrix;

  
}

/*********************************/
/* mkmap2dksph */
/*********************************/

/*

  here, we use the spline kernel to convolve the particule attribute

*/

double WK2D(double r, double h) {

  double u;
  const double K1 = 1.818913635335714;
  const double K2 = 10.913481812015714;
  const double K5 = 3.637827270672143;

  u = r / h;

  if (u > 1) return 0.;

  if (u > 0.5) return (1 / (h * h)) * K5 * pow((1 - u), 3);

  return (1 / (h * h)) * (K1 + K2 * (u - 1) * u * u);
}

static PyObject *mapping_mkmap2dksph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j, p;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float *dseo;
  size_t bytes;

  double x, y, gm, am, h, h2, hx, hy;
  double xi, yi, xi0, yi0, r, r2;
  int Nix, Niy;

  if (!PyArg_ParseTuple(args, "OOOO(ii)", &pos, &gmm, &amp, &rsp, &kx, &ky))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (p = 0; p < n; p++) {
    x = *(float *)PyArray_GETPTR2(pos, p, 0) * kx; /* scale x between [0,kx] */
    y = *(float *)PyArray_GETPTR2(pos, p, 1) * ky; /* scale x between [0,ky] */
    gm = *(float *)PyArray_GETPTR1(gmm, p);
    am = *(float *)PyArray_GETPTR1(amp, p);
    h = *(float *)PyArray_GETPTR1(rsp, p);

    hx = h * kx;
    hy = h * ky;
    h = hx; /* break the anisothropy */

    h = dmin(h, 0.25 * kx); /* limit h to a fraction of the boxsize */

    xi0 = (x - hx); /* bottom left pixel */
    yi0 = (y - hy); /* bottom left pixel */
    xi0 = dmax(xi0, 0.0);
    yi0 = dmax(yi0, 0.0);

    Nix = (int)(2 * hx + 1);
    Niy = (int)(2 * hy + 1);
    Nix = dmin(Nix, kx - (int)(xi0));
    Niy = dmin(Niy, ky - (int)(yi0));

    h2 = h * h;

    if (h < 1) {
      ix = (int)(x);
      iy = (int)(y);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky)
          dseo[ix * ky + iy] = dseo[ix * ky + iy] + gm * am;
    } else {
      for (i = 0; i < Nix; i++)
        for (j = 0; j < Niy; j++) {

          xi = xi0 + i;
          yi = yi0 + j;

          r2 = (xi - x) * (xi - x) + (yi - y) * (yi - y);

          if (r2 < h2) {

            r = sqrt(r2);

            ix = (int)(xi);
            iy = (int)(yi);

            dseo[ix * ky + iy] = dseo[ix * ky + iy] + WK2D(r, h) * gm * am;
          }
        }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i * ky + j];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3dksph */
/*********************************/

/*

  here, we use the spline kernel to convolve the particule attribute

*/

double WK3D(double r, double h) {

  double u;

  const double K1 = 2.546479089470;
  const double K2 = 15.278874536822;
  const double K5 = 5.092958178941;

  u = r / h;

  if (u > 1) return 0.;

  if (u > 0.5) return (1 / (h * h * h)) * K5 * pow((1 - u), 3);

  return (1 / (h * h * h)) * (K1 + K2 * (u - 1) * u * u);
}



static PyObject *mapping_mkmap3dksph(PyObject *self, PyObject *args, PyObject *kwds) {  

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j, k, p;
  int ix, iy, iz;
  int kx, ky, kz;
  int verbose=0;
  npy_intp ld[3];

  float *dseo;
  size_t bytes;

  double x, y, z, gm, am, h, h2, hx, hy, hz;
  double xi, yi, zi, xi0, yi0, zi0, r, r2;
  int Nix, Niy, Niz;
  
  static char *kwlist[] = {"pos","gmm","amp","rsp","shape","verbose",NULL};

  if (!PyArg_ParseTupleAndKeywords(args,kwds,"OOOO(iii)|i",kwlist, &pos, &gmm, &amp, &rsp, &kx, &ky, &kz, &verbose))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * kz * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  ld[2] = kz;
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      for (iz = 0; iz < kz; iz++) {
        dseo[ix * (kz * ky) + iy * (kz) + iz] = 0.;
      }
    }
  }

  /* full dseo : loop over all points in pos*/
  for (p = 0; p < n; p++) {
    
    if (verbose){
      if(fmod(p,(int)(100000))==0)
        printf("%d/%d\n",p,n);
    }
    
    
    x = *(float *)PyArray_GETPTR2(pos, p, 0) * kx; /* scale x between [0,kx] */
    y = *(float *)PyArray_GETPTR2(pos, p, 1) * ky; /* scale x between [0,ky] */
    z = *(float *)PyArray_GETPTR2(pos, p, 2) * kz; /* scale x between [0,kz] */
    gm = *(float *)PyArray_GETPTR1(gmm, p);
    am = *(float *)PyArray_GETPTR1(amp, p);
    h = *(float *)PyArray_GETPTR1(rsp, p);

    hx = h * kx;
    hy = h * ky;
    hz = h * kz;
    h = hx; /* break the anisothropy */

    h = dmin(h, 0.25 * kx); /* limit h to a fraction of the boxsize */

    xi0 = (x - hx); /* bottom left pixel */
    yi0 = (y - hy); /* bottom left pixel */
    zi0 = (z - hz); /* bottom left pixel */
    xi0 = dmax(xi0, 0.0);
    yi0 = dmax(yi0, 0.0);
    zi0 = dmax(zi0, 0.0);

    Nix = (int)(2 * hx + 1);
    Niy = (int)(2 * hy + 1);
    Niz = (int)(2 * hz + 1);
    Nix = dmin(Nix, kx - (int)(xi0));
    Niy = dmin(Niy, ky - (int)(yi0));
    Niz = dmin(Niz, kz - (int)(zi0));

    h2 = h * h;

    if (h < 1) {
      ix = (int)(x);
      iy = (int)(y);
      iz = (int)(z);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky)
          if (iz >= 0 && iz < kz)
            dseo[ix * (kz * ky) + iy * (kz) + iz] =
                dseo[ix * (kz * ky) + iy * (kz) + iz] + gm * am;
    } else {
      for (i = 0; i < Nix; i++)
        for (j = 0; j < Niy; j++)
          for (k = 0; k < Niz; k++) {

            xi = xi0 + i;
            yi = yi0 + j;
            zi = zi0 + k;

            r2 =
                (xi - x) * (xi - x) + (yi - y) * (yi - y) + (zi - z) * (zi - z);

            if (r2 < h2) {

              r = sqrt(r2);

              ix = (int)(xi);
              iy = (int)(yi);
              iz = (int)(zi);

              dseo[ix * (kz * ky) + iy * (kz) + iz] =
                  dseo[ix * (kz * ky) + iy * (kz) + iz] + WK3D(r, h) * gm * am;
            }
          }
    }
  }

  /* create the subimage */
  for (k = 0; k < kz; k++) {
    for (j = 0; j < ky; j++) {
      for (i = 0; i < kx; i++) {
        *(float *)PyArray_GETPTR3(mat, i, j, k) =
            (float)dseo[i * (kz * ky) + j * (kz) + k];
      }
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3dnsph */
/*********************************/

static PyObject *mapping_mkmap3dnsph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j, k;
  int ix, iy, iz;
  int kx, ky, kz;
  npy_intp ld[3];

  float *dseo;
  size_t bytes;

  float x, y, z, gm, am, sigma, sigma3, pisig, gaus, sum;
  int xin, xfi, yin, yfi, zin, zfi, ixx, iyy, izz;
  int dkx2, dky2, dkz2, dkx, dky, dkz;

  if (!PyArg_ParseTuple(args, "OOOO(iii)", &pos, &gmm, &amp, &rsp, &kx, &ky,
                        &kz))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * kz * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  ld[2] = kz;
  mat = (PyArrayObject *)PyArray_SimpleNew(3, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      for (iz = 0; iz < kz; iz++) {
        dseo[ix * (kz * ky) + iy * (kz) + iz] = 0.;
      }
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    z = *(float *)PyArray_GETPTR2(pos, i, 2) * kz;

    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);
    sigma = *(float *)PyArray_GETPTR1(rsp, i);

    sigma3 = sigma * sigma * sigma;
    pisig = 1. / (pow(2. * PI, 1.5) * sigma3);

    /* the size of the subgrid */

    dkx2 = (int)(3. * sigma); /* 3 sigma -> 98% volume */
    dky2 = (int)(3. * sigma);
    dkz2 = (int)(3. * sigma);

    dkx = 2. * dkx2 + 1;
    dky = 2. * dky2 + 1;
    dkz = 2. * dkz2 + 1;

    if (dkx == 1 && dky == 1 && dkz == 1) { /* the size is 1 */

      ix = (int)(x);
      iy = (int)(y);
      iz = (int)(z);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky)
          if (iz >= 0 && iz < kz)
            dseo[ix * (kz * ky) + iy * (kz) + iz] =
                dseo[ix * (kz * ky) + iy * (kz) + iz] + gm * am;

    } else {

      ix = (int)x; /* center of the sub grid */
      iy = (int)y;
      iz = (int)z;

      sum = 0;

      // printf("%f %d %d %d %d\n",sigma,dkx,dky,kx,ky);

      /* bornes */

      xin = ix - dkx2;
      yin = iy - dky2;
      zin = iz - dkz2;
      xfi = ix + dkx2 + 1;
      yfi = iy + dky2 + 1;
      zfi = iz + dkz2 + 1;

      if (xin < 0) {
        xin = 0;
      }
      if (yin < 0) {
        yin = 0;
      }
      if (zin < 0) {
        zin = 0;
      }
      if (xfi > kx - 1) {
        xfi = kx - 1;
      }
      if (yfi > ky - 1) {
        yfi = ky - 1;
      }
      if (zfi > kz - 1) {
        zfi = kz - 1;
      }

      if (xfi > xin && yfi > yin && zfi > zin) {

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
          for (iyy = yin; iyy < yfi; iyy++) {
            for (izz = zin; izz < zfi; izz++) {

              gaus = pisig * exp(0.5 * (-((float)(ix - ixx) / (sigma)) *
                                            ((float)(ix - ixx) / (sigma)) -
                                        ((float)(iy - iyy) / (sigma)) *
                                            ((float)(iy - iyy) / (sigma)) -
                                        ((float)(iz - izz) / (sigma)) *
                                            ((float)(iz - izz) / (sigma))));
              sum = sum + gaus;

              dseo[ixx * (kz * ky) + iyy * (kz) + izz] =
                  dseo[ixx * (kz * ky) + iyy * (kz) + izz] + gm * am * gaus;
            }
          }
        }
      }
    }
  }

  /* create the subimage */
  for (k = 0; k < kz; k++) {
    for (j = 0; j < ky; j++) {
      for (i = 0; i < kx; i++) {
        *(float *)PyArray_GETPTR3(mat, i, j, k) =
            (float)dseo[i * (kz * ky) + j * (kz) + k];
      }
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap2dncub */
/*********************************/

static PyObject *mapping_mkmap2dncub(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float *dseo;
  size_t bytes;

  float x, y, gm, am, flux, size;
  int xin, xfi, yin, yfi, ixx, iyy;
  int dkx2, dky2, dkx, dky;

  if (!PyArg_ParseTuple(args, "OOOO(ii)", &pos, &gmm, &amp, &rsp, &kx, &ky))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0) * kx;
    y = *(float *)PyArray_GETPTR2(pos, i, 1) * ky;
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);
    size = *(float *)PyArray_GETPTR1(rsp, i);

    /* the size of the subgrid */

    dkx2 = (int)(size);
    dky2 = (int)(size);

    dkx = 2 * dkx2 + 1; /* ??? */
    dky = 2 * dky2 + 1;

    flux = gm * am / (dkx * dky);

    if (dkx == 1 && dky == 1) { /* the size is 1 */

      ix = (int)(x);
      iy = (int)(y);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky) dseo[ix * ky + iy] = dseo[ix * ky + iy] + flux;

    } else {

      ix = (int)x; /* center of the sub grid */
      iy = (int)y;

      /* bornes */

      xin = ix - dkx2;
      yin = iy - dky2;
      xfi = ix + dkx2 + 1;
      yfi = iy + dky2 + 1;

      if (xin < 0) {
        xin = 0;
      }
      if (yin < 0) {
        yin = 0;
      }
      if (xfi > kx - 1) {
        xfi = kx - 1;
      }
      if (yfi > ky - 1) {
        yfi = ky - 1;
      }

      if (xfi > xin && yfi > yin) {

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
          for (iyy = yin; iyy < yfi; iyy++) {

            dseo[ixx * ky + iyy] = dseo[ixx * ky + iyy] + flux;
          }
        }
      }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i * ky + j];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* mkmap3dnsph */
/*********************************/

#define KERNEL_COEFF_1 2.546479089470
#define KERNEL_COEFF_2 15.278874536822
#define KERNEL_COEFF_5 5.092958178941

static PyObject *mapping_mkmap3dslicesph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int kx, ky, kz;
  float xmin, xmax, ymin, ymax, zmin, zmax;

  int n, i, j;
  int ix, iy;
  npy_intp ld[2];
  int izz;

  float *dseo;
  float x, y, z, gm, am, r;
  float xx, yy, zz;
  float fx, fy, fz;

  size_t bytes;

  if (!PyArg_ParseTuple(args, "OOOO(iii)(ff)(ff)(ff)i", &pos, &gmm, &amp, &rsp,
                        &kx, &ky, &kz, &xmin, &xmax, &ymin, &ymax, &zmin, &zmax,
                        &izz))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  n = PyArray_DIM(pos, 0);

  /* some constants */
  fx = (kx - 1) / (xmax - xmin);
  fy = (ky - 1) / (ymax - ymin);
  fz = (kz - 1) / (zmax - zmin);

  /* set xmin,ymin,zmin for each particles */

  /* first slice */
  int ixx, iyy;
  float wk;
  float h, u;
  float hinv3;

  int ixmin, ixmax;
  int iymin, iymax;
  int izmin, izmax;

  /* loop over all particles */
  for (i = 0; i < n; i++) {

    z = *(float *)PyArray_GETPTR2(pos, i, 2);
    h = *(float *)PyArray_GETPTR1(rsp, i);

    izmin = (int)(((z - h) - zmin) * fz);
    izmax = (int)(((z + h) - zmin) * fz);

    izmin = imax(izmin, 0);
    izmax = imin(izmax, kz - 1);

    if ((izz >= izmin) && (izz <= izmax)) {

      x = *(float *)PyArray_GETPTR2(pos, i, 0);
      y = *(float *)PyArray_GETPTR2(pos, i, 1);

      gm = *(float *)PyArray_GETPTR1(gmm, i);
      am = *(float *)PyArray_GETPTR1(amp, i);

      ixmin = (int)(((x - h) - xmin) * fx);
      ixmax = (int)(((x + h) - xmin) * fx);

      ixmin = imax(ixmin, 0);
      ixmax = imin(ixmax, kx - 1);

      iymin = (int)(((y - h) - ymin) * fy);
      iymax = (int)(((y + h) - ymin) * fy);

      iymin = imax(iymin, 0);
      iymax = imin(iymax, ky - 1);

      hinv3 = 1.0 / (h * h * h) * (xmax - xmin) / kx * (ymax - ymin) / ky *
              (zmax - zmin) / kz;

      if ((ixmin == ixmax) && (iymin == iymax) && (izmin == izmax)) {
        dseo[ixmin * ky + iymin] = dseo[ixmin * ky + iymin] + gm * am;
        continue;
      }

      /* loop over the grid */
      for (ixx = ixmin; ixx <= ixmax; ixx++) {
        for (iyy = iymin; iyy <= iymax; iyy++) {

          xx = (ixx / fx) + xmin; /* physical coordinate */
          yy = (iyy / fy) + ymin;
          zz = (izz / fz) + zmin;

          r = sqrt((x - xx) * (x - xx) + (y - yy) * (y - yy) +
                   (z - zz) * (z - zz));

          u = r / h;

          if (u < 1) {
            if (u < 0.5)
              wk = hinv3 * (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
            else
              wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) * (1.0 - u);

            dseo[ixx * ky + iyy] = dseo[ixx * ky + iyy] + gm * am * wk;
          }
        }
      }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[j + i * ky];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

struct points {
  int index;
  float h;
  float z;
  float izmin;
  float izmax;
  int next;
  int prev;
};

static PyObject *mapping_mkmap3dsortedsph(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int kx, ky, kz;
  float xmin, xmax, ymin, ymax, zmin, zmax;

  int n, i, j;
  int ix, iy;
  npy_intp ld[2];
  int izz;

  float *dseo;
  float x, y, z, gm, am, r;
  float xx, yy, zz;
  float fx, fy, fz;

  struct points *P;
  int nP;

  size_t bytes;

  if (!PyArg_ParseTuple(args, "OOOO(iii)(ff)(ff)(ff)", &pos, &gmm, &amp, &rsp,
                        &kx, &ky, &kz, &xmin, &xmax, &ymin, &ymax, &zmin,
                        &zmax))
    return NULL;

  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  n = PyArray_DIM(pos, 0);

  /* allocate memory for P */
  if (!(P = malloc(bytes = n * sizeof(struct points)))) {
    printf("failed to allocate memory for `P' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  /* some constants */
  fx = (kx - 1) / (xmax - xmin);
  fy = (ky - 1) / (ymax - ymin);
  fz = (kz - 1) / (zmax - zmin);

  /* set xmin,ymin,zmin for each particles */

  /* first slice */
  int ixx, iyy;
  float wk;
  float h, u;
  float hinv3;

  int ixmin, ixmax;
  int iymin, iymax;
  int izmin, izmax;

  int istart;
  int nAdded;

  nP = 0;
  nAdded = 0;
  istart = 0;

  for (izz = 0; izz < kz; izz++) {

    i = nAdded; /* index of first particle not added */

    do {

      if (i == n) /* no particles left to add */
        break;

      z = *(float *)PyArray_GETPTR2(pos, i, 2);
      h = *(float *)PyArray_GETPTR1(rsp, i);
      izmin = imax((int)(((z - h) - zmin) * fz), 0);
      izmax = imin((int)(((z + h) - zmin) * fz), kz - 1);

      if (izmin > izz) /* the next particle is not in the slice, do nothing */
        break;

      /* the particle enter the slice, add it */

      P[i].index = i;
      P[i].z = z;
      P[i].h = h;
      P[i].izmin = izmin;
      P[i].izmax = izmax;

      /********************************/
      /* set its position in the list */
      /********************************/

      /* default, first one */

      if (nP == 0) {
        P[i].next = -1;
      } else {
        P[i].next = istart;
        P[istart].prev = i;
      }

      P[i].prev = -1;
      istart = i;

      nAdded++;
      nP++;
      i++; /* move to next particle */

    } while (1);

    /***************************************/
    /* loop over all particles in the list */
    /***************************************/

    i = istart;

    // printf("(%d) nP=%d\n",izz,nP);

    if (nP > 0) do {

        z = P[i].z;
        izmin = P[i].izmin;
        izmax = P[i].izmax;
        h = P[i].h;

        /* do the particle */

        if (izmax < izz) /* the part leaves the slice */
        {

          if (nP == 1) {
            /* do nothing */
          } else {

            /* remove it from the list */
            if (P[i].prev == -1) /* first one */
            {
              istart = P[i].next;
              P[istart].prev = -1;
            } else {
              if (P[i].next == -1) /* last one */
              {
                P[P[i].prev].next = -1;
              } else /* one in the middle */
              {
                P[P[i].prev].next = P[i].next;
                P[P[i].next].prev = P[i].prev;
              }
            }
          }

          nP--;

        } else {

          x = *(float *)PyArray_GETPTR2(pos, P[i].index, 0);
          y = *(float *)PyArray_GETPTR2(pos, P[i].index, 1);

          gm = *(float *)PyArray_GETPTR1(gmm, P[i].index);
          am = *(float *)PyArray_GETPTR1(amp, P[i].index);

          ixmin = (int)(((x - h) - xmin) * fx);
          ixmax = (int)(((x + h) - xmin) * fx);

          ixmin = imax(ixmin, 0);
          ixmax = imin(ixmax, kx - 1);

          iymin = (int)(((y - h) - ymin) * fy);
          iymax = (int)(((y + h) - ymin) * fy);

          iymin = imax(iymin, 0);
          iymax = imin(iymax, ky - 1);

          hinv3 = 1.0 / (h * h * h) * (xmax - xmin) / kx * (ymax - ymin) / ky *
                  (zmax - zmin) / kz;

          /* loop over the grid */
          for (ixx = ixmin; ixx <= ixmax; ixx++) {
            for (iyy = iymin; iyy <= iymax; iyy++) {

              xx = (ixx / fx) + xmin; /* physical coordinate */
              yy = (iyy / fy) + ymin;
              zz = (izz / fz) + zmin;

              r = sqrt((x - xx) * (x - xx) + (y - yy) * (y - yy) +
                       (z - zz) * (z - zz));

              u = r / h;

              if (u < 1) {
                if (u < 0.5)
                  wk = hinv3 *
                       (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
                else
                  wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) *
                       (1.0 - u);

                dseo[ixx * ky + iyy] = dseo[ixx * ky + iyy] + gm * am * wk;
              }
            }
          }
        }

        i = P[i].next;

      } while (i != -1);
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[j + i * ky];
    }
  }

  free(dseo);

  return PyArray_Return(mat);
}

/*********************************/
/* create_line */
/*********************************/
/* http://graphics.lcs.mit.edu/~mcmillan/comp136/Lecture6/Lines.html */

static PyObject *mapping_create_line(PyObject *self, PyObject *args) {

  PyArrayObject *mat = NULL;
  int x0, y0, x1, y1, color, width;
  int dy, dx;
  int stepx, stepy;

  if (!PyArg_ParseTuple(args, "Oiiiii", &mat, &x0, &y0, &x1, &y1, &color))
    return NULL;

  /* create the output */

  dy = y1 - y0;
  dx = x1 - x0;

  width = 1;

  if (dy < 0) {
    dy = -dy;
    stepy = -width;
  } else {
    stepy = width;
  }
  if (dx < 0) {
    dx = -dx;
    stepx = -1;
  } else {
    stepx = 1;
  }
  dy <<= 1;
  dx <<= 1;

  y0 *= width;
  y1 *= width;
  *(float *)PyArray_GETPTR2(mat, x0, y0) = (float)color;
  if (dx > dy) {
    int fraction = dy - (dx >> 1);
    while (x0 != x1) {
      if (fraction >= 0) {
        y0 += stepy;
        fraction -= dx;
      }
      x0 += stepx;
      fraction += dy;
      *(float *)PyArray_GETPTR2(mat, x0, y0) = (float)color;
    }
  } else {
    int fraction = dx - (dy >> 1);
    while (y0 != y1) {
      if (fraction >= 0) {
        x0 += stepx;
        fraction -= dy;
      }
      y0 += stepy;
      fraction += dx;
      *(float *)PyArray_GETPTR2(mat, x0, y0) = (float)color;
    }
  }

  return Py_BuildValue("i", 1);
}

/*********************************/
/* create_line */
/*********************************/

static PyObject *mapping_create_line2(PyObject *self, PyObject *args) {

  PyArrayObject *mat;
  npy_intp ld[2];
  int kx, ky, x1, y1, x2, y2, color;

  int i;             // loop counter
  int ystep, xstep;  // the step on y and x axis
  int error;         // the error accumulated during the increment
  int errorprev;     // *vision the previous value of the error variable
  int x, y;          // the line points
  int ddy, ddx;      // compulsory variables: the double values of dy and dx
  int dx;
  int dy;

  if (!PyArg_ParseTuple(args, "iiiiiii", &kx, &ky, &x1, &y1, &x2, &y2, &color))
    return NULL;

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  y = y1;
  x = x1;
  dx = x2 - x1;
  dy = y2 - y1;

  *(short *)PyArray_GETPTR2(mat, x1, y1) = color;
  // NB the last point can't be here, because of its previous point (which has
  // to be verified)
  if (dy < 0) {
    ystep = -1;
    dy = -dy;
  } else
    ystep = 1;
  if (dx < 0) {
    xstep = -1;
    dx = -dx;
  } else
    xstep = 1;
  ddy = 2 * dy;  // work with double values for full precision
  ddx = 2 * dx;
  if (ddx >= ddy) {  // first octant (0 <= slope <= 1)
    // compulsory initialization (even for errorprev, needed when dx==dy)
    errorprev = error = dx;     // start in the middle of the square
    for (i = 0; i < dx; i++) {  // do not use the first point (already done)
      x += xstep;
      error += ddy;
      if (error > ddx) {  // increment y if AFTER the middle ( > )
        y += ystep;
        error -= ddx;
        // three cases (octant == right->right-top for directions below):
        if (error + errorprev < ddx)  // bottom square also
          *(float *)PyArray_GETPTR2(mat, x, y - ystep) = (float)color;
        else if (error + errorprev > ddx)  // left square also
          *(float *)PyArray_GETPTR2(mat, x - xstep, y) = (float)color;
        else {  // corner: bottom and left squares also
          *(short *)PyArray_GETPTR2(mat, x, y - ystep) = (float)color;
          *(short *)PyArray_GETPTR2(mat, x - xstep, y) = (float)color;
        }
      }
      *(float *)PyArray_GETPTR2(mat, x, y) = (float)color;
      errorprev = error;
    }
  } else {  // the same as above
    errorprev = error = dy;
    for (i = 0; i < dy; i++) {
      y += ystep;
      error += ddx;
      if (error > ddy) {
        x += xstep;
        error -= ddy;
        if (error + errorprev < ddy)
          *(float *)PyArray_GETPTR2(mat, x - xstep, y) = (float)color;
        else if (error + errorprev > ddy)
          *(float *)PyArray_GETPTR2(mat, x, y - ystep) = (float)color;
        else {
          *(float *)PyArray_GETPTR2(mat, x - xstep, y) = (float)color;
          *(float *)PyArray_GETPTR2(mat, x, y - ystep) = (float)color;
        }
      }
      *(float *)PyArray_GETPTR2(mat, x, y) = (float)color;
      errorprev = error;
    }
  }

  return PyArray_Return(mat);
}

/*********************************/
/* create_line */
/*********************************/

static PyObject *mapping_create_line3(PyObject *self, PyObject *args) {

  int kx, ky, x0, y0, x1, y1, color;

  PyArrayObject *mat;
  float a, b;
  int x, y, dx;
  int lx, ly, s0, s1, inv;
  npy_intp ld[2];

  if (!PyArg_ParseTuple(args, "iiiiiii", &kx, &ky, &x0, &y0, &x1, &y1, &color))
    return NULL;

  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  if (x0 == x1 && y0 == y1) {
    *(float *)PyArray_GETPTR2(mat, x0, y0) = (float)color;
    return Py_BuildValue("i", 0);
  }

  lx = abs(x1 - x0);
  ly = abs(y1 - y0);

  inv = 0;

  if (lx < ly) {
    /* swap x,y */
    s0 = x0;
    s1 = x1;
    x0 = y0;
    x1 = y1;
    y0 = s0;
    y1 = s1;
    inv = 1;
  }

  a = (float)(y0 - y1) / (float)(x0 - x1);
  b = (float)(x0 * y1 - y0 * x1) / (float)(x0 - x1);

  /* dx */
  if (x1 > x0) {
    dx = 1;
  } else {
    dx = -1;
  }

  /* main loop */
  x = x0;
  while (x != x1) {
    y = (int)(a * (float)x + b);
    if (inv) {
      *(float *)PyArray_GETPTR2(mat, y, x) = (float)color;
    } else {
      *(float *)PyArray_GETPTR2(mat, x, y) = (float)color;
    }
    x = x + dx;
  }

  /* last point */
  if (inv) {
    *(float *)PyArray_GETPTR2(mat, y1, x1) = (float)color;
  } else {
    *(float *)PyArray_GETPTR2(mat, x1, y1) = (float)color;
  }

  *(float *)PyArray_GETPTR2(mat, 96, 73) = (float)color;
  *(float *)PyArray_GETPTR2(mat, 94, 76) = (float)color;
  *(float *)PyArray_GETPTR2(mat, 92, 79) = (float)color;

  return PyArray_Return(mat);
}




/*********************************/
/* create kernel based mappings  */
/*********************************/

#define C_cub_spline_2D  3.6378272706718935
#define Hh_cub_spline_2D 1.778002


/*! Normalized 2D cubic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wcub_2D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_cub_spline_2D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(dmax(1-r,0.0),3);
  w = w -4*pow(dmax(0.5-r,0.0),3);
  w = w *C_cub_spline_2D/(h*h);
  
  return w;
}


static PyObject *mapping_mkmap2d_splcub(PyObject *self, PyObject *args) {
  
  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *rsp = NULL;

  PyArrayObject *mat;

  int n, i, j;
  int ix, iy;
  int kx, ky;
  npy_intp ld[2];

  float *dseo;
  size_t bytes;

  float x, y, gm, h, r;
  int xin, xfi, yin, yfi, ixx, iyy;
  int dkx2, dky2, dkx, dky;
  

  if (!PyArg_ParseTuple(args, "OOO(ii)", &pos, &gmm, &rsp, &kx, &ky))
    return NULL;


  if (!(dseo = malloc(bytes = kx * ky * sizeof(float)))) {
    printf("failed to allocate memory for `dseo' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    return NULL;
  }


  /* create the output */
  ld[0] = kx;
  ld[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* check the size of pos */
  if (PyArray_NDIM(pos) != 2 || PyArray_TYPE(pos) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float32");
    return NULL;
  }

  /* number of particules */
  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */
  for (ix = 0; ix < kx; ix++) {
    for (iy = 0; iy < ky; iy++) {
      dseo[ix * ky + iy] = 0.;
    }
  }

  /* full dseo : loop over all points in pos*/
  for (i = 0; i < n; i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
        
    
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    h = *(float *)PyArray_GETPTR1(rsp, i);    
    h = 2*h; /* we multiply by to be in line with eg. mkmap2dsph where rsp=sigma (here, h = 2*sigma) */

    /* set the size of the subgrid */
    dkx2 = (int)(h*Hh_cub_spline_2D);  /* compute the maximal extention */
    dky2 = dkx2;
    
    dkx = 2. * dkx2 + 1;
    dky = 2. * dky2 + 1;
        
    if (dkx == 1 && dky == 1) { /* the size is 1 */

      ix = (int)(x);
      iy = (int)(y);

      if (ix >= 0 && ix < kx)
        if (iy >= 0 && iy < ky) dseo[ix * ky + iy] = dseo[ix * ky + iy] + gm;

      } 
    else {

      ix = (int)x; /* center of the sub grid */
      iy = (int)y;

      /* bornes */
      xin = ix - dkx2;
      yin = iy - dky2;
      xfi = ix + dkx2 + 1;
      yfi = iy + dky2 + 1;

      if (xin < 0) xin = 0;
      if (yin < 0) yin = 0;
      if (xfi > kx - 1) xfi = kx - 1;
      if (yfi > ky - 1) yfi = ky - 1;

      if (xfi > xin && yfi > yin) {

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
          for (iyy = yin; iyy < yfi; iyy++) {
            r = sqrt((ix-ixx)*(ix-ixx) + (iy-iyy)*(iy-iyy)); 
            dseo[ixx * ky + iyy] = dseo[ixx * ky + iyy] + gm * Wcub_2D(r,h);
          }
        }
      }
    }
  }

  /* create the subimage */
  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {
      *(float *)PyArray_GETPTR2(mat, i, j) = (float)dseo[i * ky + j];
    }
  }

  return PyArray_Return(mat);
}




/* definition of the method table */

static PyMethodDef mappingMethods[] = {

    {"mkmap1d", mapping_mkmap1d, METH_VARARGS, "Return a 1d mapping."},

    {"mkmap1dn", mapping_mkmap1dn, METH_VARARGS,
     "Return a 1d mapping (no limit on the matrix size)."},

    {"mkcic1dn", mapping_mkcic1dn, METH_VARARGS,
     "Return a 1d cic mapping (no limit on the matrix size)."},

    {"mkcic2dn", mapping_mkcic2dn, METH_VARARGS,
     "Return a 2d cic mapping (no limit on the matrix size)."},
     
    {"mkcic3dn", mapping_mkcic3dn, METH_VARARGS,
     "Return a 3d cic mapping (no limit on the matrix size)."},

    {"mkmap2d", mapping_mkmap2d, METH_VARARGS, "Return a 2d mapping."},

    {"mkmap2dn", mapping_mkmap2dn, METH_VARARGS,
     "Return a 2d mapping (no limit on the matrix size)."},

    {"mkmap3d", mapping_mkmap3d, METH_VARARGS, "Return a 3d mapping."},

    {"mkmap3dn", mapping_mkmap3dn, METH_VARARGS,
     "Return a 3d mapping (no limit on the matrix size)."},

    {"mkmap3dslicesph", mapping_mkmap3dslicesph, METH_VARARGS,
     "Return a 3d slice (sph)."},

    {"mkmap3dsortedsph", mapping_mkmap3dsortedsph, METH_VARARGS,
     "Return a 3d mapping (sph)."},

    {"mkmap1dw", mapping_mkmap1dw, METH_VARARGS,
     "Return a 1d mapping (a particle is distributed over 2 nodes)."},

    {"mkmap2dw", mapping_mkmap2dw, METH_VARARGS,
     "Return a 2d mapping (a particle is distributed over 4 nodes)."},

    {"mkmap3dw", mapping_mkmap3dw, METH_VARARGS,
     "Return a 3d mapping (a particle is distributed over 8 nodes)."},

    {"mkmap2dsph", mapping_mkmap2dsph, METH_VARARGS,
     "Return a 2d smoothed maping."},

    {"mkmap2dksph", mapping_mkmap2dksph, METH_VARARGS,
     "Return a 2d smoothed maping (use the spline kernel)."},

    {"mkmap3dksph", (PyCFunction)mapping_mkmap3dksph, METH_VARARGS| METH_KEYWORDS,
     "Return a 3d smoothed maping (use the spline kernel)."},

    {"mkmap3dsph", mapping_mkmap3dnsph, METH_VARARGS,
     "Return a 3d smoothed maping."},

    {"mkmap2dnsph", mapping_mkmap2dnsph, METH_VARARGS,
     "Return a 2d smoothed maping (no limit on the matrix size)."},

    {"mkmap2dn_IDs", mapping_mkmap2dn_IDs, METH_VARARGS,
     "Return the list of IDs per pixels for mkmap2dn."},
    
    {"mkmap2dncub", mapping_mkmap2dncub, METH_VARARGS,
     "Return a 2d smoothed maping (each part. is projected into a cube instead "
     "of a sphere)."},

    {"create_line", mapping_create_line, METH_VARARGS,
     "Add a line in the given matrice using the Bresenham algorithm."},

    {"create_line2", mapping_create_line2, METH_VARARGS,
     "Add a line in the given matrice using the Bresenham algorithm."},

    {"create_line3", mapping_create_line3, METH_VARARGS,
     "Add a line in the given matrice using a personal algorithm."},


    {"mkmap2d_splcub", mapping_mkmap2d_splcub, METH_VARARGS,
     "Return a 2d smoothed mapping using a cubic spline kernel."},



    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef mappingmodule = {
    PyModuleDef_HEAD_INIT,
    "mapping",
    "Defines some mapping functions",
    -1,
    mappingMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_mapping(void) {
  PyObject *m;
  m = PyModule_Create(&mappingmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
