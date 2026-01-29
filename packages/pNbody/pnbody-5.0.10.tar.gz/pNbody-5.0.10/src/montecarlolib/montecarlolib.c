#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>
#define kxmax1d 1024

#define kxmax2d 1024
#define kymax2d 1024

#define kxmax3d 64
#define kymax3d 64
#define kzmax3d 64

#define PI 3.14159265358979

/*********************************/
/* mkmap1d */
/*********************************/

static PyObject *montecarlolib_mc1d(PyObject *self, PyObject *args) {

  PyArrayObject *mat = NULL;
  PyArrayObject *pos;

  int n, i;
  int nx;
  int ix;
  int irand;

  float x, p;
  npy_intp ld[1];

  if (!PyArg_ParseTuple(args, "Oii", &mat, &n, &irand)) return NULL;

  /* get the size of mat */
  if (PyArray_NDIM(mat) != 1) {
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of dimension 1.");
    return NULL;
  } else {
    nx = PyArray_DIM(mat, 0);
  }

  /* create the output */
  ld[0] = n;
  pos = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  /* now, compute */
  for (i = 0; i < n; i++) {

    do {
      x = (float)random() / (float)RAND_MAX;

      ix = (int)(x * (nx - 1));

      /* find the corresponding probability */
      p = *(float *)PyArray_GETPTR1(mat, ix);

    } while (p < (float)random() / (float)RAND_MAX);

    *(float *)PyArray_GETPTR1(pos, i) = x;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* mkmap2d */
/*********************************/

static PyObject *montecarlolib_mc2d(PyObject *self, PyObject *args) {

  PyArrayObject *mat = NULL;
  PyArrayObject *pos;

  int n, i;
  int nx, ny;
  int ix, iy;
  int irand;

  float x, y, p;
  npy_intp ld[2];

  if (!PyArg_ParseTuple(args, "Oii", &mat, &n, &irand)) return NULL;

  /* get the size of mat */
  if (PyArray_NDIM(mat) != 2) {
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of dimension 2.");
    return NULL;
  } else {
    nx = PyArray_DIM(mat, 0);
    ny = PyArray_DIM(mat, 1);
  }

  /* create the output */
  ld[0] = n;
  ld[1] = 2;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  /* now, compute */
  for (i = 0; i < n; i++) {

    do {
      x = (float)random() / (float)RAND_MAX;
      y = (float)random() / (float)RAND_MAX;

      ix = (int)(x * (nx - 1));
      iy = (int)(y * (ny - 1));

      /* find the corresponding probability */
      p = *(float *)PyArray_GETPTR2(mat, ix, iy);

      // printf("%d %d %g\n",ix,iy,p);

    } while (p < (float)random() / (float)RAND_MAX);

    *(float *)PyArray_GETPTR2(pos, i, 0) = x;
    *(float *)PyArray_GETPTR2(pos, i, 1) = y;
  }

  return PyArray_Return(pos);
}

/*********************************/
/* mkmap3d */
/*********************************/

static PyObject *montecarlolib_mc3d(PyObject *self, PyObject *args) {

  PyArrayObject *mat = NULL;
  PyArrayObject *pos;

  int n, i;
  int nx, ny, nz;
  int ix, iy, iz;
  int irand;

  float x, y, z, p;
  npy_intp ld[2];

  if (!PyArg_ParseTuple(args, "Oii", &mat, &n, &irand)) return NULL;

  /* get the size of mat */
  if (PyArray_NDIM(mat) != 2) {
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of dimension 2.");
    return NULL;
  } else {
    nx = PyArray_DIM(mat, 0);
    ny = PyArray_DIM(mat, 1);
    nz = PyArray_DIM(mat, 2);
  }

  /* create the output */
  ld[0] = n;
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  /* init random */
  srandom(irand);

  /* now, compute */
  for (i = 0; i < n; i++) {

    do {
      x = (float)random() / (float)RAND_MAX;
      y = (float)random() / (float)RAND_MAX;
      z = (float)random() / (float)RAND_MAX;

      ix = (int)(x * (nx - 1));
      iy = (int)(y * (ny - 1));
      iz = (int)(z * (nz - 1));

      /* find the corresponding probability */
      p = *(float *)PyArray_GETPTR3(mat, ix, iy, iz);

    } while (p < (float)random() / (float)RAND_MAX);

    *(float *)PyArray_GETPTR2(pos, i, 0) = x;
    *(float *)PyArray_GETPTR2(pos, i, 1) = y;
    *(float *)PyArray_GETPTR2(pos, i, 2) = z;
  }

  return PyArray_Return(pos);
}

/* definition of the method table */

static PyMethodDef montecarlolibMethods[] = {

    {"mc1d", montecarlolib_mc1d, METH_VARARGS,
     "Return a 1d monte carlo distribution."},

    {"mc2d", montecarlolib_mc2d, METH_VARARGS,
     "Return a 2d monte carlo distribution."},

    {"mc3d", montecarlolib_mc3d, METH_VARARGS,
     "Return a 3d monte carlo distribution."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef montecarlolibmodule = {
    PyModuleDef_HEAD_INIT,
    "montecarlolib",
    "Defines some monte carlo methods",
    -1,
    montecarlolibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_montecarlolib(void) {
  PyObject *m;
  m = PyModule_Create(&montecarlolibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
