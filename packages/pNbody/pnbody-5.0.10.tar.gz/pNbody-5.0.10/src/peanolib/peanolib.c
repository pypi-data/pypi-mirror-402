#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

/*!< Bits per dimension available for Peano-Hilbert order.
     Note: If peanokey is defined as type int, the allowed maximum is 10.
     If 64-bit integers are used, the maximum is 21 */

#define FLOAT float
typedef int peanokey; /* originaly long long */

#define MAXTOPNODES 200000
#define MAX_REAL_NUMBER 1e37
#define BITS_PER_DIMENSION 10 /* originaly 18 */
#define PEANOCELLS (((peanokey)1) << (3 * BITS_PER_DIMENSION))

/*

int -> 32
long -> 32
long long -> 64

x = 18014398509481984

n = 64
xint1 = (x >> n)
xint2 = x - xint1
x = (xint1 << n ) + xint2


*/

/******************************************************************************

PEANO THINGS

*******************************************************************************/

static int quadrants[24][2][2][2] = {
    /* rotx=0, roty=0-3 */
    {{{0, 7}, {1, 6}}, {{3, 4}, {2, 5}}},
    {{{7, 4}, {6, 5}}, {{0, 3}, {1, 2}}},
    {{{4, 3}, {5, 2}}, {{7, 0}, {6, 1}}},
    {{{3, 0}, {2, 1}}, {{4, 7}, {5, 6}}},
    /* rotx=1, roty=0-3 */
    {{{1, 0}, {6, 7}}, {{2, 3}, {5, 4}}},
    {{{0, 3}, {7, 4}}, {{1, 2}, {6, 5}}},
    {{{3, 2}, {4, 5}}, {{0, 1}, {7, 6}}},
    {{{2, 1}, {5, 6}}, {{3, 0}, {4, 7}}},
    /* rotx=2, roty=0-3 */
    {{{6, 1}, {7, 0}}, {{5, 2}, {4, 3}}},
    {{{1, 2}, {0, 3}}, {{6, 5}, {7, 4}}},
    {{{2, 5}, {3, 4}}, {{1, 6}, {0, 7}}},
    {{{5, 6}, {4, 7}}, {{2, 1}, {3, 0}}},
    /* rotx=3, roty=0-3 */
    {{{7, 6}, {0, 1}}, {{4, 5}, {3, 2}}},
    {{{6, 5}, {1, 2}}, {{7, 4}, {0, 3}}},
    {{{5, 4}, {2, 3}}, {{6, 7}, {1, 0}}},
    {{{4, 7}, {3, 0}}, {{5, 6}, {2, 1}}},
    /* rotx=4, roty=0-3 */
    {{{6, 7}, {5, 4}}, {{1, 0}, {2, 3}}},
    {{{7, 0}, {4, 3}}, {{6, 1}, {5, 2}}},
    {{{0, 1}, {3, 2}}, {{7, 6}, {4, 5}}},
    {{{1, 6}, {2, 5}}, {{0, 7}, {3, 4}}},
    /* rotx=5, roty=0-3 */
    {{{2, 3}, {1, 0}}, {{5, 4}, {6, 7}}},
    {{{3, 4}, {0, 7}}, {{2, 5}, {1, 6}}},
    {{{4, 5}, {7, 6}}, {{3, 2}, {0, 1}}},
    {{{5, 2}, {6, 1}}, {{4, 3}, {7, 0}}}};

static int rotxmap_table[24] = {4, 5, 6, 7, 8,  9,  10, 11, 12, 13, 14, 15,
                                0, 1, 2, 3, 17, 18, 19, 16, 23, 20, 21, 22};

static int rotymap_table[24] = {1,  2,  3,  0,  16, 17, 18, 19, 11, 8, 9, 10,
                                22, 23, 20, 21, 14, 15, 12, 13, 4,  5, 6, 7};

static int rotx_table[8] = {3, 0, 0, 2, 2, 0, 0, 1};
static int roty_table[8] = {0, 1, 1, 2, 2, 3, 3, 0};

static int sense_table[8] = {-1, -1, -1, +1, +1, -1, -1, -1};

static int flag_quadrants_inverse = 1;
static char quadrants_inverse_x[24][8];
static char quadrants_inverse_y[24][8];
static char quadrants_inverse_z[24][8];

/*! This function computes a Peano-Hilbert key for an integer triplet (x,y,z),
 *  with x,y,z in the range between 0 and 2^bits-1.
 */
peanokey peano_hilbert_key(int x, int y, int z, int bits) {
  int i, quad, bitx, bity, bitz;
  int mask, rotation, rotx, roty, sense;
  peanokey key;

  mask = 1 << (bits - 1);
  key = 0;
  rotation = 0;
  sense = 1;

  for (i = 0; i < bits; i++, mask >>= 1) {
    bitx = (x & mask) ? 1 : 0;
    bity = (y & mask) ? 1 : 0;
    bitz = (z & mask) ? 1 : 0;

    quad = quadrants[rotation][bitx][bity][bitz];

    key <<= 3;
    key += (sense == 1) ? (quad) : (7 - quad);

    rotx = rotx_table[quad];
    roty = roty_table[quad];
    sense *= sense_table[quad];

    while (rotx > 0) {
      rotation = rotxmap_table[rotation];
      rotx--;
    }

    while (roty > 0) {
      rotation = rotymap_table[rotation];
      roty--;
    }
  }

  return key;
}

/*! This function computes for a given Peano-Hilbert key, the inverse,
 *  i.e. the integer triplet (x,y,z) with a Peano-Hilbert key equal to the
 *  input key. (This functionality is actually not needed in the present
 *  code.)
 */
void peano_hilbert_key_inverse(peanokey key, int bits, int *x, int *y, int *z) {
  int i, keypart, bitx, bity, bitz, mask, quad, rotation, shift;
  char sense, rotx, roty;

  if (flag_quadrants_inverse) {
    flag_quadrants_inverse = 0;
    for (rotation = 0; rotation < 24; rotation++)
      for (bitx = 0; bitx < 2; bitx++)
        for (bity = 0; bity < 2; bity++)
          for (bitz = 0; bitz < 2; bitz++) {
            quad = quadrants[rotation][bitx][bity][bitz];
            quadrants_inverse_x[rotation][quad] = bitx;
            quadrants_inverse_y[rotation][quad] = bity;
            quadrants_inverse_z[rotation][quad] = bitz;
          }
  }

  shift = 3 * (bits - 1);
  mask = 7 << shift;

  rotation = 0;
  sense = 1;

  *x = *y = *z = 0;

  for (i = 0; i < bits; i++, mask >>= 3, shift -= 3) {
    keypart = (key & mask) >> shift;

    quad = (sense == 1) ? (keypart) : (7 - keypart);

    *x = (*x << 1) + quadrants_inverse_x[rotation][quad];
    *y = (*y << 1) + quadrants_inverse_y[rotation][quad];
    *z = (*z << 1) + quadrants_inverse_z[rotation][quad];

    rotx = rotx_table[quad];
    roty = roty_table[quad];
    sense *= sense_table[quad];

    while (rotx > 0) {
      rotation = rotxmap_table[rotation];
      rotx--;
    }

    while (roty > 0) {
      rotation = rotymap_table[rotation];
      roty--;
    }
  }
}

/*********************************/
/* get peano key from x,y,z      */
/*********************************/

static PyObject *peano_xyz2peano(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *DomainCorner;
  PyArrayObject *DomainLen;
  // PyArrayObject *key1,*key2;
  PyArrayObject *key;

  int i;
  float x, y, z;
  float xDomainCorner, yDomainCorner, zDomainCorner;
  float xDomainLen, yDomainLen, zDomainLen;
  float xDomainFac, yDomainFac, zDomainFac;
  int ix, iy, iz, bits;
  // peanokey mkey;
  // int mkey1,mkey2;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &pos, &DomainCorner, &DomainLen))
    return NULL;

  /* create a NumPy object of similar size than the input */
  key = (PyArrayObject *)PyArray_SimpleNew(1, PyArray_DIMS(pos), NPY_LONG);

  bits = BITS_PER_DIMENSION;
  xDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 0);
  yDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 1);
  zDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 2);

  xDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 0);
  yDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 1);
  zDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 2);

  xDomainFac = 1.0 / xDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));
  yDomainFac = 1.0 / yDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));
  zDomainFac = 1.0 / zDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    z = *(float *)PyArray_GETPTR2(pos, i, 2);

    ix = (int)(x - xDomainCorner) * xDomainFac;
    iy = (int)(y - yDomainCorner) * yDomainFac;
    iz = (int)(z - zDomainCorner) * zDomainFac;

    *(long *)PyArray_GETPTR1(key, i) = peano_hilbert_key(ix, iy, iz, bits);
  }

  return PyArray_Return(key);
}

/*********************************/
/* get x,y,z, from peano key     */
/*********************************/

static PyObject *peano_peano2xyz(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *DomainCorner;
  PyArrayObject *DomainLen;
  PyArrayObject *key;

  int i;
  float x, y, z;
  float xDomainCorner, yDomainCorner, zDomainCorner;
  float xDomainLen, yDomainLen, zDomainLen;
  float xDomainFac, yDomainFac, zDomainFac;
  int ix, iy, iz, bits;

  npy_intp ld[2];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &key, &DomainCorner, &DomainLen))
    return NULL;

  /* create a NumPy object of similar size than the input */
  ld[0] = PyArray_DIM(key, 0);
  ld[1] = 3;
  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  bits = BITS_PER_DIMENSION;
  xDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 0);
  yDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 1);
  zDomainCorner = *(float *)PyArray_GETPTR1(DomainCorner, 2);

  xDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 0);
  yDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 1);
  zDomainLen = *(float *)PyArray_GETPTR1(DomainLen, 2);

  xDomainFac = 1.0 / xDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));
  yDomainFac = 1.0 / yDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));
  zDomainFac = 1.0 / zDomainLen * (((peanokey)1) << (BITS_PER_DIMENSION));

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    peano_hilbert_key_inverse(*(peanokey *)PyArray_GETPTR1(key, i), bits, &ix,
                              &iy, &iz);

    x = (float)(ix / xDomainFac + xDomainCorner);
    y = (float)(iy / yDomainFac + yDomainCorner);
    z = (float)(iz / zDomainFac + zDomainCorner);

    *(float *)PyArray_GETPTR2(pos, i, 0) = x;
    *(float *)PyArray_GETPTR2(pos, i, 1) = y;
    *(float *)PyArray_GETPTR2(pos, i, 2) = z;
  }

  return PyArray_Return(pos);
}

/* definition of the method table */

static PyMethodDef peanoMethods[] = {

    {"xyz2peano", peano_xyz2peano, METH_VARARGS,
     "From a triplet xyz return a peano key."},

    {"peano2xyz", peano_peano2xyz, METH_VARARGS,
     "From a peano key return a triplet xyz."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef peanolibmodule = {
    PyModuleDef_HEAD_INIT,
    "peanolib",
    "Defines some function to get the peano hilbert key",
    -1,
    peanoMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_peanolib(void) {
  PyObject *m;
  m = PyModule_Create(&peanolibmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
