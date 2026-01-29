#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#define FUNCTION double
#include "myNumeric.h"
#undef FUNCTION

#define FUNCTION float
#include "myNumeric.h"
#undef FUNCTION

#define FUNCTION long
#include "myNumeric.h"
#undef FUNCTION

#define FUNCTION short
#include "myNumeric.h"
#undef FUNCTION

/*********************************/
/* some nr functions             */
/*********************************/

#define FREE_ARG char *
#define NR_END 1
#define TINY 1.0e-25
#define FREERETURN            \
  {                           \
    free_vector(d, 0, n - 1); \
    free_vector(c, 0, n - 1); \
    return;                   \
  }

void nrerror(char error_text[])
/* Numerical Recipes standard error handler */
{
  fprintf(stderr, "Numerical Recipes run-time error...\n");
  fprintf(stderr, "%s\n", error_text);
  fprintf(stderr, "...now exiting to system...\n");
  exit(1);
}

float *vector(long nl, long nh)
/* allocate a float vector with subscript range v[nl..nh] */
{
  float *v;

  v = (float *)malloc((size_t)((nh - nl + 1 + NR_END) * sizeof(float)));
  if (!v) nrerror("allocation failure in vector()");
  return v - nl + NR_END;
}

void free_vector(float *v, long nl, long nh)
/* free a float vector allocated with vector() */
{
  free((FREE_ARG)(v + nl - NR_END));
}

void polint(float xa[], float ya[], int n, float x, float *y, float *dy) {
  int i, m, ns = 1;
  float den, dif, dift, ho, hp, w;
  float *c, *d;

  dif = fabs(x - xa[0]);
  c = vector(0, n - 1);
  d = vector(0, n - 1);
  for (i = 0; i < n; i++) {
    if ((dift = fabs(x - xa[i])) < dif) {
      ns = i;
      dif = dift;
    }
    c[i] = ya[i];
    d[i] = ya[i];
  }
  *y = ya[ns--];
  for (m = 1; m < n; m++) {
    for (i = 0; i <= n - m; i++) {
      ho = xa[i] - x;
      hp = xa[i + m] - x;
      w = c[i + 1] - d[i];
      if ((den = ho - hp) == 0.0) nrerror("Error in routine polint");
      den = w / den;
      d[i] = hp * den;
      c[i] = ho * den;
    }
    *y += (*dy = (2 * ns < (n - m) ? c[ns + 1] : d[ns--]));
  }
  free_vector(d, 0, n - 1);
  free_vector(c, 0, n - 1);
}

void ratint(float xa[], float ya[], int n, float x, float *y, float *dy) {
  int m, i, ns = 1;
  float w, t, hh, h, dd, *c, *d;

  c = vector(0, n - 1);
  d = vector(0, n - 1);
  hh = fabs(x - xa[0]);
  for (i = 0; i < n; i++) {
    h = fabs(x - xa[i]);
    if (h == 0.0) {
      *y = ya[i];
      *dy = 0.0;
      FREERETURN
    } else if (h < hh) {
      ns = i;
      hh = h;
    }
    c[i] = ya[i];
    d[i] = ya[i] + TINY;
  }
  *y = ya[ns--];
  for (m = 1; m < n; m++) {
    for (i = 0; i <= n - m; i++) {
      w = c[i + 1] - d[i];
      h = xa[i + m] - x;
      t = (xa[i] - x) * d[i] / h;
      dd = t - c[i + 1];
      if (dd == 0.0) nrerror("Error in routine ratint");
      dd = w / dd;
      d[i] = c[i + 1] * dd;
      c[i] = t * dd;
    }
    *y += (*dy = (2 * ns < (n - m) ? c[ns + 1] : d[ns--]));
  }
  FREERETURN
}

void spline(float x[], float y[], int n, float yp1, float ypn, float y2[]) {
  int i, k;
  float p, qn, sig, un, *u;
  u = vector(1, n - 1);
  if (yp1 > 0.99e30)
    y2[0] = u[0] = 0.0;
  else {
    y2[0] = -0.5;
    u[0] = (3.0 / (x[1] - x[0])) * ((y[1] - y[0]) / (x[1] - x[0]) - yp1);
  }
  for (i = 1; i <= n; i++) {
    sig = (x[i] - x[i - 1]) / (x[i + 1] - x[i - 1]);
    p = sig * y2[i - 1] + 2.0;
    y2[i] = (sig - 1.0) / p;
    u[i] = (y[i + 1] - y[i]) / (x[i + 1] - x[i]) -
           (y[i] - y[i - 1]) / (x[i] - x[i - 1]);
    u[i] = (6.0 * u[i] / (x[i + 1] - x[i - 1]) - sig * u[i - 1]) / p;
  }
  if (ypn > 0.99e30)
    qn = un = 0.0;
  else {
    qn = 0.5;
    un = (3.0 / (x[n - 1] - x[n - 2])) *
         (ypn - (y[n - 1] - y[n - 2]) / (x[n - 1] - x[n - 2]));
  }
  y2[n - 1] = (un - qn * u[n - 2]) / (qn * y2[n - 2] + 1.0);
  for (k = n - 2; k >= 0; k--) y2[k] = y2[k] * y2[k + 1] + u[k];
  free_vector(u, 1, n - 1);
}
void splint(float xa[], float ya[], float y2a[], int n, float x, float *y) {
  void nrerror(char error_text[]);
  int klo, khi, k;
  float h, b, a;

  klo = 0;
  khi = n - 1;
  while (khi - klo > 1) {
    k = (khi + klo) >> 1;
    if (xa[k] > x)
      khi = k;
    else
      klo = k;
  }
  h = xa[khi] - xa[klo];
  if (h == 0.0) nrerror("Bad xa input to routine splint");
  a = (xa[khi] - x) / h;
  b = (x - xa[klo]) / h;
  *y =
      a * ya[klo] + b * ya[khi] +
      ((a * a * a - a) * y2a[klo] + (b * b * b - b) * y2a[khi]) * (h * h) / 6.0;
}

/*********************************/
/* tests                         */
/*********************************/

static PyObject *myNumeric_test(PyObject *self, PyObject *args) {

  PyArrayObject *x;
  int d, i, type;
  npy_intp *ds;
  /* parse arguments */

  if (!PyArg_ParseTuple(args, "O", &x)) return NULL;

  /* look at the dimension */

  d = PyArray_NDIM(x);
  printf("dimension = %d\n", d);

  /* look at the dimension */
  ds = PyArray_DIMS(x);

  for (i = 0; i < d; i++) {
    printf("subd %d\n", (int)ds[i]);
  }

  /* look at the type */

  type = PyArray_TYPE(x);
  printf("type = %d\n", type);
  printf("\n");
  // printf("type SBYTE = %d\n",PyArray_SBYTE);			/* same than
  // Int32 in numpy */
  printf("type SHORT = %d\n", NPY_SHORT);
  printf("type INT = %d\n", NPY_INT);
  printf("type LONG = %d\n", NPY_LONG);
  printf("type FLOAT = %d\n", NPY_FLOAT);
  printf("type DOUBLE = %d\n", NPY_DOUBLE);

  return Py_BuildValue("i", 1);
}

/*********************************/
/* lininterp1d                   */
/*********************************/

static PyObject *myNumeric_lininterp1d(PyObject *self, PyObject *args) {

  PyArrayObject *x = NULL;
  PyArrayObject *y = NULL;
  PyArrayObject *xs = NULL;
  PyArrayObject *ys = NULL;
  float xx, yy;
  int i, j;
  float x1, x2, y1, y2;
  float a, b;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &x, &xs, &ys)) return NULL;

  y = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(x), PyArray_DIMS(x),
                                         NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(x, 0); i++) {

    xx = *(float *)PyArray_GETPTR1(x, i);

    if (xx < *(float *)PyArray_GETPTR1(xs, 0)) {
      j = 0;
    } else {

      for (j = 0; j < PyArray_DIM(xs, 0) - 1; j++) {

        if ((xx >= *(float *)PyArray_GETPTR1(xs, j)) &&
            (xx < *(float *)PyArray_GETPTR1(xs, j + 1)))
          break;
      }
    }

    if (j == (PyArray_DIM(xs, 0) - 1)) j = PyArray_DIM(xs, 0) - 2;

    x1 = *(float *)PyArray_GETPTR1(xs, j);
    y1 = *(float *)PyArray_GETPTR1(ys, j);
    x2 = *(float *)PyArray_GETPTR1(xs, j + 1);
    y2 = *(float *)PyArray_GETPTR1(ys, j + 1);

    a = (y1 - y2) / (x1 - x2);
    b = y1 - a * x1;

    yy = a * xx + b;

    *(float *)PyArray_GETPTR1(y, i) = yy;
  }

  return PyArray_Return(y);
}

/*********************************/
/* quadinterp1d                   */
/*********************************/

static PyObject *myNumeric_quadinterp1d(PyObject *self, PyObject *args) {

  PyArrayObject *x = NULL;
  PyArrayObject *y = NULL;
  PyArrayObject *xs = NULL;
  PyArrayObject *ys = NULL;
  float xx, yy;
  int i, j, dj;
  float x1, x2, x3, y1, y2, y3;
  float x12, x23, xs12, xs23, y12, y23;
  float a, b, c;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &x, &xs, &ys)) return NULL;

  y = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(x), PyArray_DIMS(x),
                                         NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(x, 0); i++) {

    xx = *(float *)PyArray_GETPTR1(x, i);

    if (xx < *(float *)PyArray_GETPTR1(xs, 0)) {
      j = 0;
    } else {

      for (j = 0; j < PyArray_DIM(xs, 0) - 1; j++) {

        if ((xx >= *(float *)PyArray_GETPTR1(xs, j)) &&
            (xx < *(float *)PyArray_GETPTR1(xs, j + 1)))
          break;
      }
    }

    if (fmod(j, 2) == 0)
      dj = 0;
    else
      dj = -1;

    if ((j + 2 + dj) == PyArray_DIM(xs, 0)) dj = dj - 1;

    x1 = *(float *)PyArray_GETPTR1(xs, j + dj);
    y1 = *(float *)PyArray_GETPTR1(ys, j + dj);
    x2 = *(float *)PyArray_GETPTR1(xs, j + 1 + dj);
    y2 = *(float *)PyArray_GETPTR1(ys, j + 1 + dj);
    x3 = *(float *)PyArray_GETPTR1(xs, j + 2 + dj);
    y3 = *(float *)PyArray_GETPTR1(ys, j + 2 + dj);

    x12 = x1 - x2;
    x23 = x2 - x3;

    xs12 = x1 * x1 - x2 * x2;
    xs23 = x2 * x2 - x3 * x3;

    y12 = y1 - y2;
    y23 = y2 - y3;

    a = (y12 * x23 - y23 * x12) / (xs12 * x23 - xs23 * x12);
    b = (y12 - a * xs12) / x12;
    c = y1 - a * x1 * x1 - b * x1;

    yy = a * xx * xx + b * xx + c;

    *(float *)PyArray_GETPTR1(y, i) = yy;
  }

  return PyArray_Return(y);
}

/*********************************/
/* quadinterp1d                   */
/*********************************/

static PyObject *myNumeric_quaddinterp1d(PyObject *self, PyObject *args) {

  PyArrayObject *x = NULL;
  PyArrayObject *y = NULL;
  PyArrayObject *xs = NULL;
  PyArrayObject *ys = NULL;

  float xx, yy;
  int i, j;
  float x1, x2, y1, y2;
  float *as, *bs, *cs;
  float p0, p;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOOf", &x, &xs, &ys, &p0)) return NULL;

  y = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(x), PyArray_DIMS(x),
                                         NPY_FLOAT);

  /* allocate memory */
  if (!(as = malloc(PyArray_DIM(xs, 0) * sizeof(float)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for as.");
  }

  if (!(bs = malloc(PyArray_DIM(xs, 0) * sizeof(float)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for bs.");
  }

  if (!(cs = malloc(PyArray_DIM(xs, 0) * sizeof(float)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for cs.");
  }

  /* first, compute as,bc,cs */

  p = p0;

  for (i = 0; i < PyArray_DIM(xs, 0) - 1; i++) {

    x1 = *(float *)PyArray_GETPTR1(xs, i);
    y1 = *(float *)PyArray_GETPTR1(ys, i);
    x2 = *(float *)PyArray_GETPTR1(xs, i + 1);
    y2 = *(float *)PyArray_GETPTR1(ys, i + 1);

    if ((x1 - x2) == 0) printf("warning !!! x1=x2=%g\n\n", x1);

    as[i] = -((y1 - y2) - p * (x1 - x2)) / pow((x1 - x2), 2);
    bs[i] = p - 2 * as[i] * x1;
    cs[i] = y1 - as[i] * x1 * x1 - bs[i] * x1;

    /* slope next point */
    p = 2 * as[i] * x2 + bs[i];
  }

  /* now, loop over all points */

  for (i = 0; i < PyArray_DIM(x, 0); i++) {

    xx = *(float *)PyArray_GETPTR1(x, i);

    if (xx < *(float *)PyArray_GETPTR1(xs, 0)) {
      j = 0;
    } else {

      for (j = 0; j < PyArray_DIM(xs, 0) - 1; j++) {

        if ((xx >= *(float *)PyArray_GETPTR1(xs, j)) &&
            (xx < *(float *)PyArray_GETPTR1(xs, j + 1)))
          break;
      }
    }

    if ((j) == PyArray_DIM(xs, 0) - 1) j = j - 1;

    yy = as[j] * xx * xx + bs[j] * xx + cs[j];

    *(float *)PyArray_GETPTR1(y, i) = yy;
  }

  return PyArray_Return(y);
}

/*********************************/
/* vprod             */
/*********************************/

static PyObject *myNumeric_vprod(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *vel;
  PyArrayObject *ltot;

  int i;
  float *x, *y, *z;
  float *vx, *vy, *vz;

  float lx, ly, lz;
  npy_intp ld[1];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OO", &pos, &vel)) return NULL;

  /* dimension of the output in each dimension */

  ld[0] = 3;

  lx = 0.;
  ly = 0.;
  lz = 0.;

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    vx = (float *)PyArray_GETPTR2(vel, i, 0);
    vy = (float *)PyArray_GETPTR2(vel, i, 1);
    vz = (float *)PyArray_GETPTR2(vel, i, 2);

    lx = lx + (*y * *vz - *z * *vy);
    ly = ly + (*z * *vx - *x * *vz);
    lz = lz + (*x * *vy - *y * *vx);
  }

  /* create a NumPy object */
  ltot = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  *(float *)PyArray_GETPTR1(ltot, 0) = lx;
  *(float *)PyArray_GETPTR1(ltot, 1) = ly;
  *(float *)PyArray_GETPTR1(ltot, 2) = lz;

  return PyArray_Return(ltot);
}

/*********************************/
/* getmask                       */
/*********************************/

static PyObject *myNumeric_getmask(PyObject *self, PyObject *args) {

  PyArrayObject *x;
  PyArrayObject *y;
  PyArrayObject *z;

  int i, j, k;
  long xx, yy;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OO", &x, &y)) return NULL;

  /* check the type */

  if (PyArray_TYPE(x) != NPY_LONG) {
    PyErr_SetString(PyExc_ValueError,
                    "type of first argument must be integer.");
    return NULL;
  }

  if (PyArray_TYPE(y) != NPY_LONG) {
    PyErr_SetString(PyExc_ValueError,
                    "type of second argument must be integer.");
    return NULL;
  }

  /* check the dimension */

  if (PyArray_NDIM(x) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(y) != 1) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of second argument must be 1.");
    return NULL;
  }

  /* create a NumPy object similar to the input x*/
  z = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(x), PyArray_DIMS(x),
                                         PyArray_TYPE(x));

  /* loop over elements of x */
  j = 0;
  for (i = 0; i < PyArray_DIM(x, 0); i++) {

    xx = *(long *)PyArray_GETPTR1(x, i); /* read x */
    yy = *(long *)PyArray_GETPTR1(y, j); /* read y */

    while (xx > yy) { /* here, we assume that x and y are sorted ... no ? */
      j++;

      if (j > PyArray_DIM(y, 0)) { /* if reached the end of y */
        for (k = i; k < PyArray_DIM(x, 0); k++) {
          *(long *)PyArray_GETPTR1(z, k) = 0;
        }
        return PyArray_Return(z);
      }

      yy = *(long *)PyArray_GETPTR1(y, j); /* read y */
    }

    if (yy == xx) {
      *(long *)PyArray_GETPTR1(z, i) = 1;
      j++;
      if (j > PyArray_DIM(y, 0)) { /* if reached the end of y */
        for (k = i; k < PyArray_DIM(x, 0); k++) {
          *(long *)PyArray_GETPTR1(z, k) = 0;
        }
        return PyArray_Return(z);
      }

    } else {
      *(long *)PyArray_GETPTR1(z, i) = 0;
    }
  }
  /* end of loop over elements of x */

  return PyArray_Return(z);
}

/*********************************/
/* histogram2d                   */
/*********************************/

static PyObject *myNumeric_histogram2d(PyObject *self, PyObject *args) {

  PyArrayObject *f1;
  PyArrayObject *f2;
  PyArrayObject *binx;
  PyArrayObject *biny;
  PyArrayObject *h;

  int i, j, ix, iy;
  npy_intp dim[2];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOOO", &f1, &f2, &binx, &biny)) return NULL;

  /* check the types */

  if (PyArray_TYPE(f1) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of first argument must be float.");
    return NULL;
  }

  if (PyArray_TYPE(f2) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of second argument must be float.");
    return NULL;
  }

  if (PyArray_TYPE(binx) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of third argument must be float.");
    return NULL;
  }

  if (PyArray_TYPE(biny) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of fourth argument must be float.");
    return NULL;
  }

  /* check the dimensions */

  if (PyArray_NDIM(f1) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(f2) != 1) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of second argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(binx) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of third argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(biny) != 1) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of fourth argument must be 1.");
    return NULL;
  }

  /* -- */

  if (PyArray_DIM(f1, 0) != PyArray_DIM(f2, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second argument must have the same size.");
    return NULL;
  }

  /* create the output */

  dim[0] = PyArray_DIM(binx, 0);
  dim[1] = PyArray_DIM(biny, 0);

  h = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_DOUBLE);

  /* fill the output */

  /* loop over all elements of f1 and f2 */
  for (i = 0; i < PyArray_DIM(f1, 0); i++) {

    ix = -1;
    iy = -1;

    /* find ix*/
    for (j = 0; j < PyArray_DIM(binx, 0) - 1; j++) {
      if (*(double *)PyArray_GETPTR1(f1, i) >=
              *(double *)PyArray_GETPTR1(binx, j) &&
          *(double *)PyArray_GETPTR1(f1, i) <
              *(double *)PyArray_GETPTR1(binx, j + 1)) {
        ix = j;
        break;
      }
    }

    /* find iy*/
    for (j = 0; j < PyArray_DIM(biny, 0) - 1; j++) {
      if (*(double *)PyArray_GETPTR1(f2, i) >=
              *(double *)PyArray_GETPTR1(biny, j) &&
          *(double *)PyArray_GETPTR1(f2, i) <
              *(double *)PyArray_GETPTR1(biny, j + 1)) {
        iy = j;
        break;
      }
    }

    if (ix != -1 && iy != -1) {
      *(double *)PyArray_GETPTR2(h, ix, iy) =
          *(double *)PyArray_GETPTR2(h, ix, iy) + 1.;
    }
  }

  return PyArray_Return(h);
}

/*********************************/
/* hnd                           */
/*********************************/

static PyObject *myNumeric_hnd(PyObject *self, PyObject *args) {

  PyObject *lst;
  PyObject *tpl;
  PyArrayObject *mat;
  PyArrayObject *h;

  int i, d, ii;
  int n;
  float val;

  int offset, inbox;

  int dim;
  float min, max;

  // int *ndim;
  npy_intp *ndim;
  float *nmin, *nmax;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "OO", &lst, &mat)) return NULL;

  /***************/
  /* check input */
  /***************/

  /* check if lst is a list */
  if (!PyList_Check(lst)) {
    PyErr_SetString(PyExc_ValueError, "Type of first argument must be list.");
    return NULL;
  }

  /* check size */
  dim = PyList_Size(lst);

  if (dim != PyArray_DIM(mat, 1)) {
    PyErr_SetString(
        PyExc_ValueError,
        "First argument must have the same size than the second argument.");
    return NULL;
  }

  /* check type */
  if (PyArray_TYPE(mat) != NPY_FLOAT) {
    PyErr_SetString(PyExc_ValueError, "Type of second argument must be float.");
    return NULL;
  }

  /* allocate memory */
  if (!(ndim = malloc(dim * sizeof(npy_intp)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for ndim.");
  }
  if (!(nmin = malloc(dim * sizeof(float)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for nmin.");
  }
  if (!(nmax = malloc(dim * sizeof(float)))) {
    PyErr_SetString(PyExc_ValueError, "Failed to allocate memory for nmax.");
  }

  /* gather arguments in the list */
  for (d = 0; d < dim; d++) {

    tpl = PyList_GetItem(lst, d);

    /* check that tpl is a tuple */
    if (!PyTuple_Check(tpl)) {
      PyErr_SetString(PyExc_ValueError,
                      "Elements of first argument must be tuples.");
      return NULL;
    }
    /* check the content of the tuple */
    if (!PyArg_ParseTuple(tpl, "ffi", &min, &max, &n)) {
      PyErr_SetString(PyExc_ValueError, "Elements of tuples are wrong.");
      return NULL;
    }
    ndim[d] = n;
    nmin[d] = min;
    nmax[d] = max;
  }

  /* create the output */
  // h = (PyArrayObject *) PyArray_FromDims(dim,ndim,PyArray_FLOAT);
  h = (PyArrayObject *)PyArray_SimpleNew(dim, ndim, NPY_FLOAT);

  /*************/
  /* compute h */
  /*************/

  /* loop over all elements of mat */
  for (i = 0; i < PyArray_DIM(mat, 0); i++) {

    /* loop over all dimensions */
    offset = 0;
    inbox = 1;
    for (d = 0; d < dim; d++) {

      val = *(float *)PyArray_GETPTR2(mat, i, d);

      /* compute indexes */
      ii = (int)((val - nmin[d]) / (nmax[d] - nmin[d]) * ndim[d]);

      /* compute offset */
      offset += ii;

      /* if particle is out of the box */
      if ((ii < 0) || (ii >= ndim[d])) {
        inbox = 0;
      }
    }

    /* now, put the result at the right place */
    if (inbox)
      *(float *)PyArray_GETPTR1(h, offset) =
          *(float *)PyArray_GETPTR1(h, offset) + 1.;
  }

  return PyArray_Return(h);
}

/*********************************/
/* whistogram                    */
/*********************************/

static PyObject *myNumeric_whistogram(PyObject *self, PyObject *args) {

  PyArrayObject *x;
  PyArrayObject *m;
  PyArrayObject *binx;
  PyArrayObject *h;

  int i, j, ix;
  npy_intp dim[1];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &x, &m, &binx)) return NULL;

  /* check the types */

  if (PyArray_TYPE(x) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of first argument must be float.");
    return NULL;
  }

  if (PyArray_TYPE(m) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of second argument must be float.");
    return NULL;
  }

  if (PyArray_TYPE(binx) != NPY_DOUBLE) {
    PyErr_SetString(PyExc_ValueError, "type of third argument must be float.");
    return NULL;
  }

  /* check the dimensions */

  if (PyArray_NDIM(x) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(m) != 1) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of second argument must be 1.");
    return NULL;
  }

  if (PyArray_NDIM(binx) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of third argument must be 1.");
    return NULL;
  }

  /* -- */

  if (PyArray_DIM(x, 0) != PyArray_DIM(m, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second argument must have the same size.");
    return NULL;
  }

  /* create the output */

  dim[0] = PyArray_DIM(binx, 0);
  // h = (PyArrayObject *) PyArray_FromDims(1,dim,PyArray_DOUBLE);
  h = (PyArrayObject *)PyArray_SimpleNew(1, dim, NPY_DOUBLE);

  /* fill the output */

  /* loop over all elements of f1 and f2 */
  for (i = 0; i < PyArray_DIM(x, 0); i++) {

    ix = PyArray_DIM(binx, 0) - 1;

    /* find ix, loop over elements of binx */
    for (j = 0; j < PyArray_DIM(binx, 0) - 1; j++) {

      /* smaller than the smallest */
      if (*(double *)PyArray_GETPTR1(x, i) <
          *(double *)PyArray_GETPTR1(binx, j)) {
        ix = -1;
        break;
      }

      if (*(double *)PyArray_GETPTR1(x, i) >=
              *(double *)PyArray_GETPTR1(binx, j) &&
          *(double *)PyArray_GETPTR1(x, i) <
              *(double *)PyArray_GETPTR1(binx, j + 1)) {
        ix = j;
        break;
      }
    }

    if (ix != -1) {
      *(double *)PyArray_GETPTR1(h, ix) =
          *(double *)PyArray_GETPTR1(h, ix) + *(double *)PyArray_GETPTR1(m, i);
    }
  }

  return PyArray_Return(h);
}

/*********************************/
/* spline3d                      */
/*********************************/

static PyObject *myNumeric_spline3d(PyObject *self, PyObject *args) {

  PyArrayObject *f1;
  PyArrayObject *f2;
  PyArrayObject *binx;
  PyArrayObject *biny;
  PyArrayObject *h;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOOO", &f1, &f2, &binx, &biny)) return NULL;

  printf("ERROR: this function is not implemented\n");
  exit(12141);
  return PyArray_Return(h);
}

/*********************************/
/* polint                        */
/*********************************/

static PyObject *myNumeric_polint(PyObject *self, PyObject *args) {
  PyArrayObject *vxa, *vya;
  int n;
  float x, y, dy;

  if (!PyArg_ParseTuple(args, "OOf", &vxa, &vya, &x)) return NULL;

  if (PyArray_DIM(vxa, 0) != PyArray_DIM(vya, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second arguments must have same dimension");
    return NULL;
  }

  n = PyArray_DIM(vxa, 0);

  polint((float *)PyArray_DATA(vxa), (float *)PyArray_DATA(vya), n, x, &y, &dy);

  return Py_BuildValue("f", y);
}

/*********************************/
/* ratint                        */
/*********************************/

static PyObject *myNumeric_ratint(PyObject *self, PyObject *args) {
  PyArrayObject *vxa, *vya;
  int n;
  float x, y, dy;

  if (!PyArg_ParseTuple(args, "OOf", &vxa, &vya, &x)) return NULL;

  if (PyArray_DIM(vxa, 0) != PyArray_DIM(vya, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second arguments must have same dimension");
    return NULL;
  }

  n = PyArray_DIM(vxa, 0);

  ratint((float *)PyArray_DATA(vxa), (float *)PyArray_DATA(vya), n, x, &y, &dy);

  return Py_BuildValue("f", y);
}

/*********************************/
/* spline                        */
/*********************************/

static PyObject *myNumeric_spline(PyObject *self, PyObject *args) {
  PyArrayObject *vxa, *vya;
  PyArrayObject *y2a;
  int n;
  float yp1, ypn;

  if (!PyArg_ParseTuple(args, "OOff", &vxa, &vya, &yp1, &ypn)) return NULL;

  if (PyArray_DIM(vxa, 0) != PyArray_DIM(vya, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second arguments must have same dimension");
    return NULL;
  }

  n = PyArray_DIM(vxa, 0);

  /* create output */
  printf("myNumeric_spline : warning, we may have a problem here...");
  y2a = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(vxa), PyArray_DIMS(vxa),
                                           PyArray_TYPE(vxa));

  spline((float *)PyArray_DATA(vxa), (float *)PyArray_DATA(vya), n, yp1, ypn,
         (float *)PyArray_DATA(y2a));

  return PyArray_Return(y2a);
}

/*********************************/
/* splint                        */
/*********************************/

static PyObject *myNumeric_splint(PyObject *self, PyObject *args) {
  PyArrayObject *vxa, *vya, *y2a;
  int n;
  float x, y;

  if (!PyArg_ParseTuple(args, "OOOf", &vxa, &vya, &y2a, &x)) return NULL;

  if (PyArray_DIM(vxa, 0) != PyArray_DIM(vya, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "first and second arguments must have same dimension");
    return NULL;
  }

  n = PyArray_DIM(vxa, 0);

  splint((float *)PyArray_DATA(vxa), (float *)PyArray_DATA(vya),
         (float *)PyArray_DATA(y2a), n, x, &y);

  return Py_BuildValue("f", y);
}
/*********************************/
/* turnup                        */
/*********************************/

static PyObject *myNumeric_turnup(PyObject *self, PyObject *args) {

  PyArrayObject *vec;
  PyArrayObject *nvec;

  int axe, type;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "Oi", &vec, &axe)) return NULL;

  /* check the dimensions */
  if (PyArray_NDIM(vec) != 2) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of the first argument must be 2.");
    return NULL;
  }

  /* check the value of axe */
  if (axe != 0 && axe != 1) {
    PyErr_SetString(PyExc_ValueError,
                    "value of the second argument must be 0 or 1.");
    return NULL;
  }

  /* create a NumPy object similar to vec*/
  printf("myNumeric_turnup : warning, we may have a problem here...");
  nvec = (PyArrayObject *)PyArray_SimpleNew(
      PyArray_NDIM(vec), PyArray_DIMS(vec), PyArray_TYPE(vec));

  type = PyArray_TYPE(vec);

  switch (type) {
    /*****************/
    /* astype(float) */
    /*****************/
    case NPY_DOUBLE:
      myNumeric_do_turnup_double(vec, nvec, axe);
      break;
    /*****************/
    /* astype(float0) */
    /*****************/
    case NPY_FLOAT:
      myNumeric_do_turnup_float(vec, nvec, axe);
      break;
    /*****************/
    /* astype(Int) */
    /*****************/
    case NPY_LONG:
      myNumeric_do_turnup_long(vec, nvec, axe);
      break;
    /*****************/
    /* astype(Int16) */
    /*****************/
    case NPY_SHORT:
      myNumeric_do_turnup_short(vec, nvec, axe);
      break;
  }

  return PyArray_Return(nvec);
}

/*********************************/
/* expand                        */
/*********************************/

static PyObject *myNumeric_expand(PyObject *self, PyObject *args) {

  PyArrayObject *vec;
  PyArrayObject *nvec;

  int fx, fy, type;
  npy_intp ndimensions[2];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "Oii", &vec, &fx, &fy)) return NULL;

  /* check the dimensions */
  if (PyArray_NDIM(vec) != 2) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of the first argument must be 2.");
    return NULL;
  }

  /* check the value of axe */
  if (fx <= 0 && fy <= 0) {
    PyErr_SetString(
        PyExc_ValueError,
        "value of the second and third argument must be greater or equal to 1");
    return NULL;
  }

  /* create a NumPy object similar to vec*/
  ndimensions[0] = PyArray_DIM(vec, 0) * fx;
  ndimensions[1] = PyArray_DIM(vec, 1) * fy;

  nvec = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(vec), ndimensions,
                                            PyArray_TYPE(vec));
  type = PyArray_TYPE(vec);

  switch (type) {
    /*****************/
    /* astype(float) */
    /*****************/
    case NPY_DOUBLE:
      myNumeric_do_expand_double(vec, nvec, fx, fy);
      break;
    /*****************/
    /* astype(float0) */
    /*****************/
    case NPY_FLOAT:
      myNumeric_do_expand_float(vec, nvec, fx, fy);
      break;
    /*****************/
    /* astype(int) */
    /*****************/
    case NPY_LONG:
      myNumeric_do_expand_long(vec, nvec, fx, fy);
      break;
    /*****************/
    /* astype(int16) */
    /*****************/
    case NPY_SHORT:
      myNumeric_do_expand_short(vec, nvec, fx, fy);
      break;
  }

  return PyArray_Return(nvec);
}

/*********************************/
/* Interpolate_From_1d_Array        */
/*********************************/

static PyObject *myNumeric_Interpolate_From_1d_Array(PyObject *self,
                                                     PyObject *args) {

  PyArrayObject *idx, *mat;

  int i;
  float ix;
  int x1, x2;
  float y1, y2;
  PyArrayObject *out;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "OO", &idx, &mat)) return NULL;

  /* look at the dimension */
  if (PyArray_NDIM(idx) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of arguments 1 must be 1.\n");
    return NULL;
  }

  /* look at the dimension */
  if (PyArray_NDIM(mat) != 1) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 2 must be 1.\n");
    return NULL;
  }

  /* create the output */
  out = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(idx), PyArray_DIMS(idx),
                                           NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(idx, 0); i++) {

    ix = *(float *)PyArray_GETPTR1(idx, i);

    if (ix <= 0)
      *(float *)PyArray_GETPTR1(out, i) = *(float *)PyArray_GETPTR1(mat, 0);
    else {
      if (ix >= (PyArray_DIM(mat, 0) - 1)) {
        *(float *)PyArray_GETPTR1(out, i) =
            *(float *)PyArray_GETPTR1(mat, PyArray_DIM(mat, 0) - 1);
      } else {

        x1 = (int)ix;
        x2 = x1 + 1;

        y1 = *(float *)PyArray_GETPTR1(mat, x1);
        y2 = *(float *)PyArray_GETPTR1(mat, x2);

        *(float *)PyArray_GETPTR1(out, i) =
            (ix - x1) / (x2 - x1) * (y2 - y1) + y1;
      }
    }
  }

  return PyArray_Return(out);
}

/*********************************/
/* Interpolate_From_2d_Array        */
/*********************************/

static PyObject *myNumeric_Interpolate_From_2d_Array(PyObject *self,
                                                     PyObject *args) {

  PyArrayObject *idx, *idy, *mat;

  int i;
  float ix, iy;
  int x1, x2, y1, y2;
  float f1, f2, f3, f4;
  float w1, w2, w3, w4;
  int nx, ny;
  PyArrayObject *out;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "OOO", &idx, &idy, &mat)) return NULL;

  /* look at the dimension */
  if ((PyArray_NDIM(idx) != 1) || (PyArray_NDIM(idy) != 1)) {
    PyErr_SetString(PyExc_ValueError,
                    "dimension of arguments 1 and 2 must be 1.\n");
    return NULL;
  }

  /* look at the dimension */
  if (PyArray_DIM(idx, 0) != PyArray_DIM(idy, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "Arguments 1 and 2 must have the same size.\n");
    return NULL;
  }

  nx = PyArray_DIM(mat, 0);
  ny = PyArray_DIM(mat, 1);

  /* create the output */
  // out = (PyArrayObject *)
  out = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(idx), PyArray_DIMS(idx),
                                           NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(idx, 0); i++) {

    ix = *(float *)PyArray_GETPTR1(idx, i);
    iy = *(float *)PyArray_GETPTR1(idy, i);

    /* 5 different cases */

    if (((int)ix >= 0) && ((int)ix < nx - 1) && ((int)iy >= 0) &&
        ((int)iy < ny - 1)) {

      x1 = (int)ix;
      x2 = (int)ix + 1;
      y1 = (int)iy;
      y2 = (int)iy + 1;

      w1 = (x2 - ix) * (y2 - iy);
      w2 = (x2 - ix) * (iy - y1);
      w3 = (ix - x1) * (y2 - iy);
      w4 = (ix - x1) * (iy - y1);

      f1 = *(float *)PyArray_GETPTR2(mat, x1, y1);
      f2 = *(float *)PyArray_GETPTR2(mat, x1, y2);
      f3 = *(float *)PyArray_GETPTR2(mat, x2, y1);
      f4 = *(float *)PyArray_GETPTR2(mat, x2, y2);

      *(float *)PyArray_GETPTR1(out, i) =
          (w1 * f1 + w2 * f2 + w3 * f3 + w4 * f4);

    } else {

      if (((int)ix < 0) && ((int)iy < 0)) {
        *(float *)PyArray_GETPTR1(out, i) =
            *(float *)PyArray_GETPTR2(mat, 0, 0);
      }

      if (((int)ix < 0) && ((int)iy >= ny - 1)) {
        *(float *)PyArray_GETPTR1(out, i) =
            *(float *)PyArray_GETPTR2(mat, 0, ny - 1);
      }

      if (((int)ix >= nx - 1) && ((int)iy < 0)) {
        *(float *)PyArray_GETPTR1(out, i) =
            *(float *)PyArray_GETPTR2(mat, nx - 1, 0);
      }

      if (((int)ix >= nx - 1) && ((int)iy >= ny - 1)) {
        *(float *)PyArray_GETPTR1(out, i) =
            *(float *)PyArray_GETPTR2(mat, nx - 1, ny - 1);
      }

      if (((int)ix >= 0) && ((int)ix < nx - 1) && ((int)iy < 0)) {
        x1 = (int)ix;
        x2 = x1 + 1;
        y1 = *(float *)PyArray_GETPTR2(mat, x1, 0);
        y2 = *(float *)PyArray_GETPTR2(mat, x2, 0);
        *(float *)PyArray_GETPTR1(out, i) =
            (ix - x1) / (x2 - x1) * (y2 - y1) + y1;
      }

      if (((int)ix >= 0) && ((int)ix < nx - 1) && ((int)iy >= ny - 1)) {
        x1 = (int)ix;
        x2 = x1 + 1;
        y1 = *(float *)PyArray_GETPTR2(mat, x1, ny - 1);
        y2 = *(float *)PyArray_GETPTR2(mat, x2, ny - 1);
        *(float *)PyArray_GETPTR1(out, i) =
            (ix - x1) / (x2 - x1) * (y2 - y1) + y1;
      }

      if (((int)iy >= 0) && ((int)iy < ny - 1) && ((int)ix < 0)) {
        x1 = (int)iy;
        x2 = x1 + 1;
        y1 = *(float *)PyArray_GETPTR2(mat, 0, x1);
        y2 = *(float *)PyArray_GETPTR2(mat, 0, x2);
        *(float *)PyArray_GETPTR1(out, i) =
            (iy - x1) / (x2 - x1) * (y2 - y1) + y1;
      }

      if (((int)iy >= 0) && ((int)iy < ny - 1) && ((int)ix >= nx - 1)) {
        x1 = (int)iy;
        x2 = x1 + 1;
        y1 = *(float *)PyArray_GETPTR2(mat, nx - 1, x1);
        y2 = *(float *)PyArray_GETPTR2(mat, nx - 1, x2);
        *(float *)PyArray_GETPTR1(out, i) =
            (iy - x1) / (x2 - x1) * (y2 - y1) + y1;
      }
    }
  }

  return PyArray_Return(out);
}

/*************************/
/* rotx                  */
/*************************/

static PyObject *myNumeric_rotx(PyObject *self, PyObject *args) {
  PyArrayObject *pos, *theta;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "OO", &pos, &theta)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);

  rpos = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                            PyArray_TYPE(pos));

  /* loop over elements  */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    cs = cos(*(float *)PyArray_GETPTR1(theta, i));
    ss = sin(*(float *)PyArray_GETPTR1(theta, i));

    xs = cs * *y - ss * *z;

    rx = *x;
    ry = xs;
    rz = ss * *y + cs * *z;

    *(float *)PyArray_GETPTR2(rpos, i, 0) = rx;
    *(float *)PyArray_GETPTR2(rpos, i, 1) = ry;
    *(float *)PyArray_GETPTR2(rpos, i, 2) = rz;
  }

  return PyArray_Return(rpos);
}

/*************************/
/* roty                  */
/*************************/

static PyObject *myNumeric_roty(PyObject *self, PyObject *args) {
  PyArrayObject *pos, *theta;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "OO", &pos, &theta)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);

  rpos = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                            PyArray_TYPE(pos));

  /* loop over elements  */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    cs = cos(*(float *)PyArray_GETPTR1(theta, i));
    ss = sin(*(float *)PyArray_GETPTR1(theta, i));

    xs = cs * *x + ss * *z;

    rx = xs;
    ry = *y;
    rz = -ss * *x + cs * *z;

    *(float *)PyArray_GETPTR2(rpos, i, 0) = rx;
    *(float *)PyArray_GETPTR2(rpos, i, 1) = ry;
    *(float *)PyArray_GETPTR2(rpos, i, 2) = rz;
  }

  return PyArray_Return(rpos);
}

/*************************/
/* rotz                  */
/*************************/

static PyObject *myNumeric_rotz(PyObject *self, PyObject *args) {
  PyArrayObject *pos, *theta;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "OO", &pos, &theta)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);

  rpos = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                            PyArray_TYPE(pos));

  /* loop over elements  */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    cs = cos(*(float *)PyArray_GETPTR1(theta, i));
    ss = sin(*(float *)PyArray_GETPTR1(theta, i));

    xs = cs * *x - ss * *y;

    rx = xs;
    ry = ss * *x + cs * *y;
    rz = *z;

    *(float *)PyArray_GETPTR2(rpos, i, 0) = rx;
    *(float *)PyArray_GETPTR2(rpos, i, 1) = ry;
    *(float *)PyArray_GETPTR2(rpos, i, 2) = rz;
  }

  return PyArray_Return(rpos);
}

/* definition of the method table */

static PyMethodDef myNumericMethods[] = {

    {"test", myNumeric_test, METH_VARARGS, "Some test on PyArray object."},

    {"lininterp1d", myNumeric_lininterp1d, METH_VARARGS,
     "Linear interpolation of 1d function given by two vectors."},

    {"quadinterp1d", myNumeric_quadinterp1d, METH_VARARGS,
     "Quadratic interpolation of 1d function given by two vectors."},

    {"quaddinterp1d", myNumeric_quaddinterp1d, METH_VARARGS,
     "Quadratic interpolation of 1d function given by two vectors (the slope "
     "is continuous)."},

    {"vprod", myNumeric_vprod, METH_VARARGS,
     "Calculate the vectorial product of two vectors."},

    {"getmask", myNumeric_getmask, METH_VARARGS,
     "Return a mask of the same type as x which has ones where elemets of x "
     "that have a corespondant in y and zeros instead."},

    {"histogram2d", myNumeric_histogram2d, METH_VARARGS,
     "Return a 2d matrix corresponding to the histrogram of two   vector "
     "values in given ranges."},

    {"hnd", myNumeric_hnd, METH_VARARGS,
     "Return a 3d matrix corresponding to the histrogram in n dim of a vector "
     "3xn"},

    {"whistogram", myNumeric_whistogram, METH_VARARGS,
     "Return a weighted histogram."},

    {"spline3d", myNumeric_spline3d, METH_VARARGS,
     "Return a 3d interpolation."},

    {"polint", myNumeric_polint, METH_VARARGS, "Polynomial interpolation."},

    {"ratint", myNumeric_ratint, METH_VARARGS, "Polynomial interpolation."},

    {"spline", myNumeric_spline, METH_VARARGS, "spline."},

    {"splint", myNumeric_splint, METH_VARARGS, "splint."},

    {"turnup", myNumeric_turnup, METH_VARARGS, "Turn up a matrix."},

    {"expand", myNumeric_expand, METH_VARARGS, "Expand a matrix."},

    {"Interpolate_From_1d_Array", myNumeric_Interpolate_From_1d_Array,
     METH_VARARGS, "Interpolate values from a given array."},

    {"Interpolate_From_2d_Array", myNumeric_Interpolate_From_2d_Array,
     METH_VARARGS, "Interpolate values from a given array."},

    {"rotx", myNumeric_rotx, METH_VARARGS, "Rotation around the x axis."},

    {"roty", myNumeric_roty, METH_VARARGS, "Rotation around the y axis."},

    {"rotz", myNumeric_rotz, METH_VARARGS, "Rotation around the z axis."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef myNumericmodule = {
    PyModuleDef_HEAD_INIT,
    "myNumeric",
    "Defines some mathematical functions",
    -1,
    myNumericMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_myNumeric(void) {
  PyObject *m;
  m = PyModule_Create(&myNumericmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
