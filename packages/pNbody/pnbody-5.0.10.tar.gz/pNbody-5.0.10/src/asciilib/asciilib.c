#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

static PyObject *asciilib_read(PyObject *self, PyObject *args) {

  PyArrayObject *out = NULL;

  PyObject *f;
  PyObject *Py_Line;
  PyObject *Py_List;
  PyObject *Py_Float;

  int n, m, i, j;

  npy_intp dim[2];

  /* parse arguments */
  if (!PyArg_ParseTuple(args, "O(ii)", &f, &n, &m))
    return Py_BuildValue("i", -1);

  /* check */
  int file = PyObject_AsFileDescriptor(f);
  if (file == -1) {
    return NULL;
  }

  /* create the output */
  dim[0] = n;
  dim[1] = m;
  out = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_FLOAT);

  for (i = 0; i < n; i++) {
    Py_Line = PyFile_GetLine(f, 0);

    Py_List = PyUnicode_Split(Py_Line, NULL, m);

    if (PyList_GET_SIZE(Py_List) != m)
      PyErr_SetString(PyExc_AttributeError, "something's wring here.");

    for (j = 0; j < m; j++) {
      Py_Float = PyFloat_FromString(PyList_GetItem(Py_List, j));
      *(float *)PyArray_GETPTR2(out, i, j) = (float)PyFloat_AsDouble(Py_Float);
      Py_CLEAR(Py_Float);
    }

    Py_CLEAR(Py_Line);
    Py_CLEAR(Py_List);
  }

  return PyArray_Return(out);
}

/* definition of the method table */

static PyMethodDef asciilibMethods[] = {

    {"read", asciilib_read, METH_VARARGS, "Read ascii file"},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef asciilibmodule = {
    PyModuleDef_HEAD_INIT,
    "asciilib",
    "Module for reading ascii file",
    -1,
    asciilibMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_asciilib(void) {
  PyObject *m;
  m = PyModule_Create(&asciilibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
