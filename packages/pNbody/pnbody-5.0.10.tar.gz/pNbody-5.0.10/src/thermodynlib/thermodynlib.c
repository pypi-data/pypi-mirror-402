#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#define TO_DOUBLE(a) \
  ((PyArrayObject *)PyArray_CastToType(a, PyArray_DescrFromType(NPY_DOUBLE), 0))

#define NT 10

double tt[NT] = {1.0e+01, 1.0e+02, 1.0e+03, 1.0e+04, 1.3e+04,
                 2.1e+04, 3.4e+04, 6.3e+04, 1.0e+05, 1.0e+09};
double mt[NT] = {1.18701555, 1.15484424, 1.09603514, 0.9981496, 0.96346395,
                 0.65175895, 0.6142901,  0.6056833,  0.5897776, 0.58822635};
double unr[NT];

double MeanWeightT(double T) {

  /* mean molecular weight as a function of the Temperature */

  double logt;
  double ttt;
  double slope;
  double mu;

  int j;

  logt = log(T);
  ttt = exp(logt);

  if (ttt < tt[0])
    j = 1;
  else
    for (j = 1; j < NT; j++)
      if ((ttt > tt[j - 1]) && (ttt <= tt[j])) break;

  slope = log(mt[j] / mt[j - 1]) / log(tt[j] / tt[j - 1]);
  mu = exp(slope * (logt - log(tt[j])) + log(mt[j]));

  return mu;
}

double UNt(double T) { return T / MeanWeightT(T); }

double Tun(double UN) {

  /* return T for a given normalized energy */

  double logu;
  double uuu;
  double slope;
  double T;

  int j;

  if (UN == 0)
    return 0;

  logu = log(UN);
  uuu = exp(logu);

  if (uuu < unr[0])
    j = 1;
  else
    for (j = 1; j < NT; j++)
      if ((uuu > unr[j - 1]) && (uuu <= unr[j])) break;

  if (j == NT) {
    printf("U: %g, %g, %g\n",uuu, unr[j - 2], unr[j-1]);
    printf("WARNING: Temperature too high\n");
  }

  slope = log(tt[j] / tt[j - 1]) / log(unr[j] / unr[j - 1]);
  T = exp(slope * (logu - log(unr[j])) + log(tt[j]));
  return T;
}

static PyObject *thermodynlib_MeanWeightT(PyObject *self, PyObject *args) {

  PyObject *T;
  PyArrayObject *Ta, *mus;
  double mu;

  int i;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "O", &T)) return NULL;

  /* a scalar */
  if (PyArray_IsAnyScalar(T)) {
    mu = MeanWeightT(PyFloat_AsDouble(T));
    return Py_BuildValue("d", mu);
  }

  /* an array scalar */
  if (PyArray_Check(T)) {

    /* convert into array */
    Ta = (PyArrayObject *)T;

    /* convert arrays to double */
    Ta = TO_DOUBLE(Ta);

    /* create output */
    mus = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(Ta), PyArray_DIMS(Ta),
                                             NPY_DOUBLE);

    for (i = 0; i < PyArray_DIM(Ta, 0); i++)
      *(double *)PyArray_GETPTR1(mus, i) =
          MeanWeightT(*(double *)PyArray_GETPTR1(Ta, i));

    return PyArray_Return(mus);
  }

  return Py_BuildValue("i", -1);
}

static PyObject *thermodynlib_Tun(PyObject *self, PyObject *args) {

  PyObject *UN;
  PyArrayObject *UNa, *Ts;
  double T;

  int i;

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "O", &UN)) return NULL;

  /* a scalar */
  if (PyArray_IsAnyScalar(UN)) {
    T = Tun(PyFloat_AsDouble(UN));
    return Py_BuildValue("d", T);
  }

  /* an array scalar */
  if (PyArray_Check(UN)) {

    /* convert into array */
    UNa = (PyArrayObject *)UN;

    /* convert arrays to double */
    UNa = TO_DOUBLE(UNa);

    /* create output */
    Ts = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(UNa),
                                            PyArray_DIMS(UNa), NPY_DOUBLE);

    for (i = 0; i < PyArray_DIM(UNa, 0); i++)
      *(double *)PyArray_GETPTR1(Ts, i) =
          Tun(*(double *)PyArray_GETPTR1(UNa, i));

    return PyArray_Return(Ts);
  }

  return Py_BuildValue("i", -1);
}

/* definition of the method table */

static PyMethodDef thermodynlibMethods[] = {

    {"MeanWeightT", thermodynlib_MeanWeightT, METH_VARARGS,
     "Compute the mean weight for a given temperature."},

    {"Tun", thermodynlib_Tun, METH_VARARGS,
     "Compute temperature from the normalized specific energy."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef thermodynlibmodule = {
    PyModuleDef_HEAD_INIT,
    "thermodynlib",
    "Defines some thermodynamic functions",
    -1,
    thermodynlibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_thermodynlib(void) {
  PyObject *m;
  m = PyModule_Create(&thermodynlibmodule);
  if (m == NULL) return NULL;

  import_array();

  /* Init unr */
  for(int i=0; i < NT; i++)
    unr[i] = UNt(tt[i]);

  return m;
}
