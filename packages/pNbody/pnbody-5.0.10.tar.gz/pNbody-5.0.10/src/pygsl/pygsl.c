#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#include <gsl/gsl_qrng.h>
#include <stdio.h>

/*********************************/
/* tests                         */
/*********************************/

static PyObject *pygsl_sobol_sequence(PyObject *self, PyObject *args) {

  PyArrayObject *x;
  int d, n;
  npy_intp dim[2];

  int i, j;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "ii", &n, &d)) return NULL;

  if (d > 40) {
    PyErr_SetString(PyExc_ValueError,
                    "second argument must not be larger than 40.");
    return NULL;
  }

  /* allocate */
  gsl_qrng *q = gsl_qrng_alloc(gsl_qrng_sobol, d);

  /* create output */
  dim[0] = n;
  dim[1] = d;
  // x = (PyArrayObject *) PyArray_FromDims(2,dim,PyArray_DOUBLE);
  x = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_DOUBLE);

  /* compute sequence */

  for (i = 0; i < n; i++) {
    double v[d];
    gsl_qrng_get(q, v);

    for (j = 0; j < d; j++) {
      *(double *)PyArray_GETPTR2(x, i, j) = v[j];
    }
  }

  gsl_qrng_free(q);

  return PyArray_Return(x);
}

/* definition of the method table */

static PyMethodDef pygslMethods[] = {

    {"sobol_sequence", pygsl_sobol_sequence, METH_VARARGS,
     "Return a sobol sequence of len n and of dimension d."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef pygslmodule = {
    PyModuleDef_HEAD_INIT,
    "pygsl",
    "",
    -1,
    pygslMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_pygsl(void) {
  PyObject *m;
  m = PyModule_Create(&pygslmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
