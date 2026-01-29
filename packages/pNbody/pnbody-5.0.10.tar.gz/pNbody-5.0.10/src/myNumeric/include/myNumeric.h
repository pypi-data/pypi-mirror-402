#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>

#define PASTE(x, y) x##_##y

#define _MYNUMERIC_DO_TURNUP(f) PASTE(myNumeric_do_turnup, f)
#define MYNUMERIC_DO_TURNUP _MYNUMERIC_DO_TURNUP(FUNCTION)

#define _MYNUMERIC_DO_EXPAND(f) PASTE(myNumeric_do_expand, f)
#define MYNUMERIC_DO_EXPAND _MYNUMERIC_DO_EXPAND(FUNCTION)

void MYNUMERIC_DO_TURNUP(PyArrayObject *vec, PyArrayObject *nvec, int axe) {

  int nx = PyArray_DIM(vec, 0);
  int ny = PyArray_DIM(vec, 1);

  if (axe == 0) {
    /* loops over all elements */
    for (int i = 0; i < PyArray_DIM(vec, 0); i++) {
      for (int j = 0; j < PyArray_DIM(vec, 1); j++) {
        *(FUNCTION *)PyArray_GETPTR2(nvec, i, ny - j - 1) =
            *(FUNCTION *)PyArray_GETPTR2(vec, i, j);
      }
    }
  }
  if (axe == 1) {
    /* loops over all elements */
    for (int i = 0; i < PyArray_DIM(vec, 0); i++) {
      for (int j = 0; j < PyArray_DIM(vec, 1); j++) {
        *(FUNCTION *)PyArray_GETPTR2(nvec, nx - i - 1, j) =
            *(FUNCTION *)PyArray_GETPTR2(vec, i, j);
      }
    }
  }
}

void MYNUMERIC_DO_EXPAND(PyArrayObject *vec, PyArrayObject *nvec, int fx,
                         int fy) {

  /* loops over all elements */
  for (int j = 0; j < PyArray_DIM(vec, 1); j++) {
    for (int i = 0; i < PyArray_DIM(vec, 0); i++) {
      for (int jj = 0; jj < fy; jj++) {
        for (int ii = 0; ii < fx; ii++) {
          *(FUNCTION *)PyArray_GETPTR2(nvec, i * fx + ii, j * fy + jj) =
              *(FUNCTION *)PyArray_GETPTR2(vec, i, j);
        }
      }
    }
  }
}
