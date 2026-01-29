#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <numpy/arrayobject.h>

#define kxmax 512
#define kymax 512
#define PI 3.14159265358979

/*********************************/
/* angular momentum              */
/*********************************/

static PyObject *nbody_am(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *vel;
  PyArrayObject *mas;
  PyArrayObject *ltot;

  int i;
  float *x, *y, *z;
  float *vx, *vy, *vz;
  float *m;

  float lx, ly, lz;
  npy_intp ld[1];

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &pos, &vel, &mas)) return NULL;

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

    m = (float *)PyArray_GETPTR1(mas, i);

    lx = lx + *m * (*y * *vz - *z * *vy);
    ly = ly + *m * (*z * *vx - *x * *vz);
    lz = lz + *m * (*x * *vy - *y * *vx);
  }

  /* create a NumPy object */
  ltot = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  *(float *)PyArray_GETPTR1(ltot, 0) = lx;
  *(float *)PyArray_GETPTR1(ltot, 1) = ly;
  *(float *)PyArray_GETPTR1(ltot, 2) = lz;

  return PyArray_Return(ltot);
}

/*********************************/
/* angular momentum  in x,y,z    */
/*********************************/

static PyObject *nbody_amxyz(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *vel;
  PyArrayObject *mas;
  PyArrayObject *lxyz;

  int i;
  float *x, *y, *z;
  float *vx, *vy, *vz;
  float *m;

  float lx, ly, lz;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &pos, &vel, &mas)) return NULL;

  /* create a NumPy object similar to the input */
  lxyz = (PyArrayObject *)PyArray_SimpleNew(
      PyArray_NDIM(pos), PyArray_DIMS(pos), PyArray_TYPE(pos));

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    vx = (float *)PyArray_GETPTR2(vel, i, 0);
    vy = (float *)PyArray_GETPTR2(vel, i, 1);
    vz = (float *)PyArray_GETPTR2(vel, i, 2);

    m = (float *)PyArray_GETPTR1(mas, i);

    lx = *m * (*y * *vz - *z * *vy);
    ly = *m * (*z * *vx - *x * *vz);
    lz = *m * (*x * *vy - *y * *vx);

    *(float *)PyArray_GETPTR2(lxyz, i, 0) = lx;
    *(float *)PyArray_GETPTR2(lxyz, i, 1) = ly;
    *(float *)PyArray_GETPTR2(lxyz, i, 2) = lz;
  }

  return PyArray_Return(lxyz);
}

/******************************************/
/* specific angular momentum  in x,y,z    */
/******************************************/

static PyObject *nbody_samxyz(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *vel;
  PyArrayObject *mas;
  PyArrayObject *lxyz;

  int i;
  float *x, *y, *z;
  float *vx, *vy, *vz;

  float lx, ly, lz;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOO", &pos, &vel, &mas)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);
  lxyz = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                            PyArray_TYPE(pos));

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    vx = (float *)PyArray_GETPTR2(vel, i, 0);
    vy = (float *)PyArray_GETPTR2(vel, i, 1);
    vz = (float *)PyArray_GETPTR2(vel, i, 2);

    lx = (*y * *vz - *z * *vy);
    ly = (*z * *vx - *x * *vz);
    lz = (*x * *vy - *y * *vx);

    *(float *)PyArray_GETPTR2(lxyz, i, 0) = lx;
    *(float *)PyArray_GETPTR2(lxyz, i, 1) = ly;
    *(float *)PyArray_GETPTR2(lxyz, i, 2) = lz;
  }

  return PyArray_Return(lxyz);
}

/*********************************/
/* potential in a specific point */
/*********************************/

static PyObject *nbody_potential(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *mas;
  PyArrayObject *xpos;
  float eps, eps2;

  int i;
  float *x, *y, *z;
  float *m;
  float *xx, *yy, *zz;
  float pot, dx;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOOf", &pos, &mas, &xpos, &eps)) return NULL;

  /* read the position */

  xx = (float *)PyArray_GETPTR1(xpos, 0);
  yy = (float *)PyArray_GETPTR1(xpos, 1);
  zz = (float *)PyArray_GETPTR1(xpos, 2);

  pot = 0.;
  eps2 = eps * eps;

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    m = (float *)PyArray_GETPTR1(mas, i);

    dx = (*x - *xx) * (*x - *xx) + (*y - *yy) * (*y - *yy) +
         (*z - *zz) * (*z - *zz);
    if (dx > 0) /* avoid self potential */
    {
      dx = sqrt(dx + eps2);
      pot = pot - *m / dx;
    }
  }

  return Py_BuildValue("f", pot);
}

/*********************************/
/* acceleration in a specific point */
/*********************************/

static PyObject *nbody_acceleration(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *mas;
  PyArrayObject *xpos;
  float eps, eps2;

  int i;
  float *x, *y, *z;
  float *m;
  float *xx, *yy, *zz;
  float ax, ay, az, dx, dy, dz, r2, fac;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOOf", &pos, &mas, &xpos, &eps)) return NULL;

  /* read the position */

  xx = (float *)PyArray_GETPTR1(xpos, 0);
  yy = (float *)PyArray_GETPTR1(xpos, 1);
  zz = (float *)PyArray_GETPTR1(xpos, 2);

  ax = 0.;
  ay = 0.;
  az = 0.;
  eps2 = eps * eps;

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = (float *)PyArray_GETPTR2(pos, i, 0);
    y = (float *)PyArray_GETPTR2(pos, i, 1);
    z = (float *)PyArray_GETPTR2(pos, i, 2);

    m = (float *)PyArray_GETPTR1(mas, i);

    dx = (*x - *xx);
    dy = (*y - *yy);
    dz = (*z - *zz);

    r2 = dx * dx + dy * dy + dz * dz;

    if (r2 > 0) /* avoid self force */
    {
      fac = *m / pow(r2 + eps2, 3.0 / 2.0);

      ax += dx * fac;
      ay += dy * fac;
      az += dz * fac;
    }
  }

  return Py_BuildValue("fff", ax, ay, az);
}

/**************************/
/* total potential energy */
/**************************/

static PyObject *nbody_epot(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  PyArrayObject *mas;
  float eps, eps2;

  int i, j;
  float *x1, *y1, *z1;
  float *x2, *y2, *z2;
  float *m1, *m2;
  float pot, potj, dx;

  /* parse arguments */

  if (!PyArg_ParseTuple(args, "OOf", &pos, &mas, &eps)) return NULL;

  pot = 0.;
  eps2 = eps * eps;

  /* loops over all elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x1 = (float *)PyArray_GETPTR2(pos, i, 0);
    y1 = (float *)PyArray_GETPTR2(pos, i, 1);
    z1 = (float *)PyArray_GETPTR2(pos, i, 2);

    m1 = (float *)PyArray_GETPTR1(mas, i);

    potj = 0.;

    for (j = 0; j < PyArray_DIM(pos, 0); j++) {

      if (i != j) {
        x2 = (float *)PyArray_GETPTR2(pos, j, 0);
        y2 = (float *)PyArray_GETPTR2(pos, j, 1);
        z2 = (float *)PyArray_GETPTR2(pos, j, 2);

        m2 = (float *)PyArray_GETPTR1(mas, j);

        dx = sqrt((*x1 - *x2) * (*x1 - *x2) + (*y1 - *y2) * (*y1 - *y2) +
                  (*z1 - *z2) * (*z1 - *z2) + eps2);
        potj = potj - *m2 / dx;
      }
    }
    pot = pot + *m1 * potj;
  }

  return Py_BuildValue("f", 0.5 * pot);
}

/*************************/
/* rotx                  */
/*************************/

static PyObject *nbody_rotx(PyObject *self, PyObject *args) {
  float theta;
  PyArrayObject *pos;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "fO", &theta, &pos)) return NULL;

  cs = cos(theta);
  ss = sin(theta);

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

static PyObject *nbody_roty(PyObject *self, PyObject *args) {
  float theta;
  PyArrayObject *pos;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "fO", &theta, &pos)) return NULL;

  cs = cos(theta);
  ss = sin(theta);

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

static PyObject *nbody_rotz(PyObject *self, PyObject *args) {
  float theta;
  PyArrayObject *pos;
  PyArrayObject *rpos;

  float cs, ss;
  float xs;
  float *x, *y, *z;
  float rx, ry, rz;
  int i;

  if (!PyArg_ParseTuple(args, "fO", &theta, &pos)) return NULL;

  cs = cos(theta);
  ss = sin(theta);

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

/*************************/
/* spin                  */
/*************************/

static PyObject *nbody_spin(PyObject *self, PyObject *args) {
  PyArrayObject *pos;
  PyArrayObject *vel;
  PyArrayObject *omega;
  PyArrayObject *nvel;

  float x, y, z;
  float vx, vy, vz;
  float ox, oy, oz;
  int i;

  if (!PyArg_ParseTuple(args, "OOO", &pos, &vel, &omega)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(vel, 0);
  ld[1] = PyArray_DIM(vel, 1);
  nvel = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(vel), ld,
                                            PyArray_TYPE(vel));

  ox = *(float *)PyArray_GETPTR1(omega, 0);
  oy = *(float *)PyArray_GETPTR1(omega, 1);
  oz = *(float *)PyArray_GETPTR1(omega, 2);

  /* loop over elements  */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    z = *(float *)PyArray_GETPTR2(pos, i, 2);

    vx = *(float *)PyArray_GETPTR2(vel, i, 0);
    vy = *(float *)PyArray_GETPTR2(vel, i, 1);
    vz = *(float *)PyArray_GETPTR2(vel, i, 2);

    vx = vx + (oy * z - oz * y);
    vy = vy + (oz * x - ox * z);
    vz = vz + (ox * y - oy * x);

    *(float *)PyArray_GETPTR2(nvel, i, 0) = vx;
    *(float *)PyArray_GETPTR2(nvel, i, 1) = vy;
    *(float *)PyArray_GETPTR2(nvel, i, 2) = vz;
  }

  return PyArray_Return(nvel);
}

/*********************************/
/* pamap */
/*********************************/

static PyObject *nbody_pamap(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  float xmx, ymx, cd;
  int view, scale; /* log : scale = 0, lin : scale = 1 */

  PyArrayObject *mat;

  int kx, ky;
  int kxx, kyy;
  int kxx2, kyy2;
  int n, i, j;
  int ix, iy, xi, yi;
  npy_intp dim[2];

  float ax, ay, bx, by;
  float dseo[kxmax][kymax];
  float gmnt, cdopt;
  float x, y, gm;
  float min, max;
  float v;

  if (!PyArg_ParseTuple(args, "OO(ii)fffii", &pos, &gmm, &kx, &ky, &xmx, &ymx,
                        &cd, &view, &scale))
    return NULL;

  /* check max size of matrix */

  if (kx > kxmax || ky > kymax) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */

  dim[0] = kx;
  dim[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_SHORT);

  /* set image dimension */

  kxx = kx;
  kyy = ky;
  kxx2 = kxx / 2;
  kyy2 = kyy / 2;

  ax = kxx2 / xmx;
  ay = kyy2 / ymx;

  bx = kxx2 + 1.;
  by = kyy2 + 1.;

  /* check the size of pos */

  if (PyArray_NDIM(pos) != 2 || !PyArray_ISFLOAT(pos)) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float0");
    return NULL;
  }

  /* number of particules */

  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      dseo[ix][iy] = 0.;
    }
  }

  gmnt = 0.;

  /* choose the view */

  if (view == 1) { /*xz*/
    xi = 0;
    yi = 2;
  }

  if (view == 2) { /*xy*/
    xi = 0;
    yi = 1;
  }

  if (view == 3) { /*yz*/
    xi = 1;
    yi = 2;
  }

  /* full dseo : loop over all points in pos*/

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, xi);
    y = *(float *)PyArray_GETPTR2(pos, i, yi);
    gm = *(float *)PyArray_GETPTR1(gmm, i);

    gmnt = gmnt + gm;

    if (x > -xmx && x < xmx) {
      if (y > -ymx && y < ymx) {

        ix = (int)(ax * x + bx) - 1;
        iy = (int)(ay * y + by) - 1;

        dseo[ix][iy] = dseo[ix][iy] + gm;
      }
    }
  }

  /* inverse of the mean weight per particule */
  gmnt = (float)n / gmnt; /*????*/

  min = 1e20;
  max = 0.;

  /* find min and max */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (dseo[ix][iy] < min) {
        min = dseo[ix][iy];
      }
      if (dseo[ix][iy] > max) {
        max = dseo[ix][iy];
      }
    }
  }

  /* optimum factor */
  if (gmnt * max == 0) {
    cdopt = 0.;
  } else {
    switch (scale) { /* dépendance de l'échelle */
      case 0:
        cdopt = 255. / log(gmnt * max + 1.);
        break;
      case 1:
        cdopt = 255. / (gmnt * max);
        break;
      default:
        printf("WARNING: Scale %i unknown, use default linear scale\n", scale);
        cdopt = 255. / (gmnt * max);
        break;
    }
  }
  if (cd == 0) {
    cd = cdopt;
  }

  /* create the subimage */

  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {

      switch (scale) { /* dépendance de l'échelle */
        case 0:
          v = cd * log(gmnt * dseo[i][j] + 1.);
          break;
        case 1:
          v = cd * (gmnt * dseo[i][j] + 1.);
          break;
        default:
          printf("WARNING: Scale %i unknown, use default linear scale\n",
                 scale);
          v = cd * (gmnt * dseo[i][j] + 1.);
          break;
      }

      if (v > 255.) {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)255.;
      } else {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)v;
      }
    }
  }

  return Py_BuildValue("(Of)", mat, cdopt);
}

/*********************************/
/* pdpmap */
/*********************************/

static PyObject *nbody_pdmap(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *amp = NULL;
  float xmx, ymx, cd, omin, omax;
  int view;

  PyArrayObject *mat;

  int kx, ky;
  int kxx, kyy;
  int kxx2, kyy2;
  int i, j;
  int ix, iy, xi, yi;
  npy_intp dim[2];

  float ax, ay, bx, by;
  float dseo[kxmax][kymax];
  float nn[kxmax][kymax];
  float cdopt = 0;
  float x, y, gm, am;
  float min, max, mean, sigm;
  float v;

  if (!PyArg_ParseTuple(args, "OOO(ii)fffffi", &pos, &gmm, &amp, &kx, &ky, &xmx,
                        &ymx, &cd, &omin, &omax, &view))
    return NULL;

  /* check max size of matrix */

  if (kx > kxmax || ky > kymax) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */

  dim[0] = kx;
  dim[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_SHORT);

  /* set image dimension */

  kxx = kx;
  kyy = ky;
  kxx2 = kxx / 2;
  kyy2 = kyy / 2;

  ax = kxx2 / xmx;
  ay = kyy2 / ymx;

  bx = kxx2 + 1.;
  by = kyy2 + 1.;

  /* check the size of pos */

  if (PyArray_NDIM(pos) != 2 || !PyArray_ISFLOAT(pos)) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float0");
    return NULL;
  }

  /* initialisation of dseo */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      dseo[ix][iy] = 0.;
      nn[ix][iy] = 0.;
    }
  }

  /* choose the view */

  if (view == 1) { /*xz*/
    xi = 0;
    yi = 2;
  }

  if (view == 2) { /*xy*/
    xi = 0;
    yi = 1;
  }

  if (view == 3) { /*yz*/
    xi = 1;
    yi = 2;
  }

  /* full dseo : loop over all points in pos*/

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, xi);
    y = *(float *)PyArray_GETPTR2(pos, i, yi);
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    am = *(float *)PyArray_GETPTR1(amp, i);

    if (x > -xmx && x < xmx) {
      if (y > -ymx && y < ymx) {

        ix = (int)(ax * x + bx) - 1;
        iy = (int)(ay * y + by) - 1;

        dseo[ix][iy] = dseo[ix][iy] + gm * am;
        nn[ix][iy] = nn[ix][iy] + gm;
      }
    }
  }

  min = 1e20;
  max = -1e20;
  mean = 0.;
  sigm = 0.;

  /* find min and max, mean and sigma */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (nn[ix][iy] != 0) {
        dseo[ix][iy] = dseo[ix][iy] / (float)nn[ix][iy];
        if (dseo[ix][iy] < min) {
          min = dseo[ix][iy];
        }
        if (dseo[ix][iy] > max) {
          max = dseo[ix][iy];
        }
        mean = mean + dseo[ix][iy];
        sigm = sigm + dseo[ix][iy] * dseo[ix][iy];
      }
    }
  }

  mean = mean / (float)(kxx * kyy);
  sigm = sqrt(sigm / (float)(kxx * kyy) - mean * mean);

  /* optimal ranges */
  if (cd == 0.) {
    cd = 1.;
  }

  min = mean - cd * sigm;
  max = mean + cd * sigm;

  /* use given ranges if values are different */
  if (omin != omax) {
    min = omin;
    max = omax;
    mean = (omin + omax) / 2.;
  }

  cd = 255. / (max - min);

  /* shift dseo whith the min */
  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (nn[ix][iy] == 0) {
        dseo[ix][iy] = min; /* on met au minimum si vide */
      }

      dseo[ix][iy] = dseo[ix][iy] - min;
    }
  }

  /* create the subimage */

  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {

      v = cd * dseo[i][j];

      if (v > 254.) {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)254. + 1.;
      } else {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)v + 1.;
      }
    }
  }

  return Py_BuildValue("(Of)", mat, cdopt);
}

/*********************************/
/* sphmap */
/*********************************/

static PyObject *nbody_sphmap(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  PyArrayObject *rsp = NULL;
  float xmx, ymx, cd, frsp;
  int view;

  PyArrayObject *mat;

  int kx, ky;
  int kxx, kyy;
  int kxx2, kyy2;
  int dkx2, dky2, dkx, dky;
  int n, i, j;
  int ix, iy, xi, yi, ixx, iyy;
  int xin, xfi, yin, yfi;
  npy_intp dim[2];

  float ax, ay, bx, by;
  float dseo[kxmax][kymax];
  float gmnt, cdopt;
  float x, y, gm, sigma, sigma2, pisig, gaus, ds, sum;
  float min, max;
  float v;

  if (!PyArg_ParseTuple(args, "OOO(ii)ffffi", &pos, &gmm, &rsp, &kx, &ky, &xmx,
                        &ymx, &cd, &frsp, &view))
    return NULL;

  /* check max size of matrix */

  if (kx > kxmax || ky > kymax) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */

  dim[0] = kx;
  dim[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_SHORT);

  /* set image dimension */

  kxx = kx;
  kyy = ky;
  kxx2 = kxx / 2;
  kyy2 = kyy / 2;

  ax = kxx2 / xmx;
  ay = kyy2 / ymx;

  bx = kxx2 + 1.;
  by = kyy2 + 1.;

  /* check the size of pos */

  if (PyArray_NDIM(pos) != 2 || !PyArray_ISFLOAT(pos)) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float0");
    return NULL;
  }

  /* number of particules */

  n = PyArray_DIM(pos, 0);

  /* initialisation of dseo */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      dseo[ix][iy] = 0.;
    }
  }

  gmnt = 0.;

  /* choose the view */

  if (view == 1) { /*xz*/
    xi = 0;
    yi = 2;
  }

  if (view == 2) { /*xy*/
    xi = 0;
    yi = 1;
  }

  if (view == 3) { /*yz*/
    xi = 1;
    yi = 2;
  }

  /* full dseo : loop over all points in pos*/

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, xi);
    y = *(float *)PyArray_GETPTR2(pos, i, yi);
    gm = *(float *)PyArray_GETPTR1(gmm, i);
    sigma = *(float *)PyArray_GETPTR1(rsp, i);

    sigma = frsp * sigma;
    gmnt = gmnt + gm;

    /* define the subgrid */

    /* the size of the subgrid */

    dkx2 = (int)(ax * 2. * sigma); /* 3 sigma -> 98% volume */
    dky2 = (int)(ay * 2. * sigma);

    dkx = 2. * dkx2 + 1;
    dky = 2. * dky2 + 1;

    if (dkx == 1 && dky == 1) { /* the size is 1 */

      if (x > -xmx && x < xmx) {
        if (y > -ymx && y < ymx) {

          ix = (int)(ax * x + bx) - 1;
          iy = (int)(ay * y + by) - 1;

          dseo[ix][iy] = dseo[ix][iy] + gm;
        }
      }

    } else {

      ix = (int)(ax * x + bx) - 1; /* center of the grid */
      iy = (int)(ay * y + by) - 1;

      sigma2 = sigma * sigma;
      pisig = 1. / (2. * PI * sigma2);

      ds = (1. / ax) * (1. / ay);
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
      if (xfi > kxx - 1) {
        xfi = kxx - 1;
      }
      if (yfi > kyy - 1) {
        yfi = kyy - 1;
      }

      if (xfi > xin && yfi > yin) {

        /* loop over the grid */
        for (ixx = xin; ixx < xfi; ixx++) {
          for (iyy = yin; iyy < yfi; iyy++) {

            gaus = ds * pisig *
                   exp(0.5 * (-((float)(ix - ixx) / (ax * sigma)) *
                                  ((float)(ix - ixx) / (ax * sigma)) -
                              ((float)(iy - iyy) / (ay * sigma)) *
                                  ((float)(iy - iyy) / (ay * sigma))));
            sum = sum + gaus;

            dseo[ixx][iyy] = dseo[ixx][iyy] + gm * gaus;
          }
        }
      }
    }
  }

  /* inverse of the mean weight per particule */
  gmnt = (float)n / gmnt; /*????*/

  min = 1e20;
  max = 0.;

  /* find min and max */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (dseo[ix][iy] < min) {
        min = dseo[ix][iy];
      }
      if (dseo[ix][iy] > max) {
        max = dseo[ix][iy];
      }
    }
  }

  /* optimum factor */
  if (gmnt * max == 0) {
    cdopt = 0.;
  } else {
    cdopt = 254. / log(gmnt * max + 1.);
  }
  if (cd == 0) {
    cd = cdopt;
  }

  /* create the subimage */

  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {

      v = cd * log(gmnt * dseo[i][j] + 1.);

      if (v > 254.) {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)254. + 1.;
      } else {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)v + 1.;
      }
    }
  }

  return Py_BuildValue("(Of)", mat, cdopt);
}

/*********************************/
/* ampmap */
/*********************************/

static PyObject *nbody_ampmap(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *gmm = NULL;
  float xmx, ymx, cd, omin, omax;
  int view;

  PyArrayObject *mat;

  int kx, ky;
  int kxx, kyy;
  int kxx2, kyy2;
  int i, j;
  int ix, iy, xi, yi, zi;
  npy_intp dim[2];

  float ax, ay, bx, by;
  float dseo[kxmax][kymax];
  float nn[kxmax][kymax];
  float cdopt = 0;
  float x, y, z, gm;
  float min, max, mean, sigm;
  float v;

  if (!PyArg_ParseTuple(args, "OO(ii)fffffi", &pos, &gmm, &kx, &ky, &xmx, &ymx,
                        &cd, &omin, &omax, &view))
    return NULL;

  /* check max size of matrix */

  if (kx > kxmax || ky > kymax) {
    PyErr_SetString(PyExc_ValueError, "dimension of argument 3 is too large.");
    return NULL;
  }

  /* create the output */

  dim[0] = kx;
  dim[1] = ky;
  mat = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_SHORT);

  /* set image dimension */

  kxx = kx;
  kyy = ky;
  kxx2 = kxx / 2;
  kyy2 = kyy / 2;

  ax = kxx2 / xmx;
  ay = kyy2 / ymx;

  bx = kxx2 + 1.;
  by = kyy2 + 1.;

  /* check the size of pos */

  if (PyArray_NDIM(pos) != 2 || !PyArray_TYPE(pos)) {
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 must be two dimentionnal and of type Float0");
    return NULL;
  }

  /* initialisation of dseo */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      dseo[ix][iy] = 0.;
      nn[ix][iy] = 0.;
    }
  }

  /* choose the view */

  if (view == 1) { /*xz*/
    xi = 0;
    yi = 2;
    zi = 1;
  }

  if (view == 2) { /*xy*/
    xi = 0;
    yi = 1;
    zi = 2;
  }

  if (view == 3) { /*yz*/
    xi = 1;
    yi = 2;
    zi = 3;
  }

  /* full dseo : loop over all points in pos*/

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, xi);
    y = *(float *)PyArray_GETPTR2(pos, i, yi);
    z = *(float *)PyArray_GETPTR2(pos, i, zi);
    gm = *(float *)PyArray_GETPTR1(gmm, i);

    if (x > -xmx && x < xmx) {
      if (y > -ymx && y < ymx) {

        ix = (int)(ax * x + bx) - 1;
        iy = (int)(ay * y + by) - 1;

        dseo[ix][iy] = dseo[ix][iy] + gm * z;
        nn[ix][iy] = nn[ix][iy] + gm;
      }
    }
  }

  min = 1e20;
  max = -1e20;
  mean = 0.;
  sigm = 0.;

  /* find min and max, mean and sigma */

  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (nn[ix][iy] != 0) {
        dseo[ix][iy] = dseo[ix][iy] / (float)nn[ix][iy];
        if (dseo[ix][iy] < min) {
          min = dseo[ix][iy];
        }
        if (dseo[ix][iy] > max) {
          max = dseo[ix][iy];
        }
        mean = mean + dseo[ix][iy];
        sigm = sigm + dseo[ix][iy] * dseo[ix][iy];
      }
    }
  }

  mean = mean / (float)(kxx * kyy);
  sigm = sqrt(sigm / (float)(kxx * kyy) - mean * mean);

  /* optimal ranges */
  if (cd == 0.) {
    cd = 1.;
  }

  min = mean - cd * sigm;
  max = mean + cd * sigm;

  if (omin != omax) {
    min = omin;
    max = omax;
    mean = (omin + omax) / 2.;
  }

  cd = 255. / (max - min);

  /* shift dseo whith the min */
  for (ix = 0; ix < kxx; ix++) {
    for (iy = 0; iy < kyy; iy++) {
      if (nn[ix][iy] == 0) {
        dseo[ix][iy] = min; /* on met au minimum si vide */
      }
      dseo[ix][iy] = dseo[ix][iy] - min;
    }
  }

  /* create the subimage */

  for (j = 0; j < ky; j++) {
    for (i = 0; i < kx; i++) {

      v = cd * dseo[i][j];

      if (v > 254.) {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)254. + 1.;
      } else {
        *(short *)PyArray_GETPTR2(mat, i, ky - j - 1) = (short)v + 1.;
      }
    }
  }

  return Py_BuildValue("(Of)", mat, cdopt);
}

/*********************************/
/* perspective */
/*********************************/

static PyObject *nbody_perspective(PyObject *self, PyObject *args) {
  float r_obs, foc;
  PyArrayObject *pos;
  PyArrayObject *npos;
  int view;

  int i;
  float r;
  float x, y, z;
  int xi, yi, zi;

  if (!PyArg_ParseTuple(args, "Offi", &pos, &r_obs, &foc, &view)) return NULL;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);
  npos = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                            PyArray_TYPE(pos));

  /* choose the view */

  if (view == 1) { /*xz*/
    xi = 0;
    yi = 1;
    zi = 2;
  }

  if (view == 2) { /*xy*/
    xi = 0;
    yi = 2;
    zi = 1;
  }

  if (view == 3) { /*yz*/
    xi = 1;
    yi = 0;
    zi = 2;
  }

  /* loop over elements */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    x = *(float *)PyArray_GETPTR2(pos, i, xi);
    y = *(float *)PyArray_GETPTR2(pos, i, yi);
    z = *(float *)PyArray_GETPTR2(pos, i, zi);

    r = fabs(y + r_obs);

    *(float *)PyArray_GETPTR2(npos, i, xi) = foc * x / r;
    *(float *)PyArray_GETPTR2(npos, i, yi) = y;
    *(float *)PyArray_GETPTR2(npos, i, zi) = foc * z / r;
  }

  return PyArray_Return(npos);
}

/*********************************/
/* convol */
/*********************************/

static PyObject *nbody_convol(PyObject *self, PyObject *args) {
  PyArrayObject *a = NULL;
  PyArrayObject *b = NULL;
  PyArrayObject *c = NULL;

  int nxd, nyd;

  int i, j, k, l;
  double *val, *aa, *bb;

  if (!PyArg_ParseTuple(args, "OO", &a, &b)) return NULL;

  nxd = (PyArray_DIM(b, 0) - 1) / 2;
  nyd = (PyArray_DIM(b, 1) - 1) / 2;

  /* create a NumPy object similar to the input */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(a, 0);
  ld[1] = PyArray_DIM(a, 1);
  c = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(a), ld, PyArray_TYPE(a));

  for (i = 0; i < PyArray_DIM(c, 0); i++) {
    for (j = 0; j < PyArray_DIM(c, 1); j++) { /* loops over the image */

      val = (double *)PyArray_GETPTR2(c, i, j);

      for (k = -nxd; k < nxd + 1; k++) {
        for (l = -nyd; l < nyd + 1; l++) { /* loops over the kernel */

          if (i + k >= 0 && i + k < PyArray_DIM(c, 0)) {
            if (j + l >= 0 &&
                j + l < PyArray_DIM(c, 1)) { /* check if we are in the window */

              aa = (double *)PyArray_GETPTR2(a, i + k, j + l);
              bb = (double *)PyArray_GETPTR2(b, k + nxd, l + nyd);

              *val = *val + *aa * *bb;
            }
          }
        }
      }
    }
  }

  return PyArray_Return(c);
}

/* definition of the method table */

static PyMethodDef nbodyMethods[] = {

    {"am", nbody_am, METH_VARARGS,
     "Calculate the angular momentum of the model."},

    {"amxyz", nbody_amxyz, METH_VARARGS,
     "Calculate the angular momentum in x,y,z for all particles."},

    {"samxyz", nbody_samxyz, METH_VARARGS,
     "Calculate the specific angular momentum in x,y,z for all particles."},

    {"potential", nbody_potential, METH_VARARGS,
     "Calculate the potential at a given position, with a given softening."},

    {"acceleration", nbody_acceleration, METH_VARARGS,
     "Calculate the acceleration at a given position, with a given softening."},

    {"epot", nbody_epot, METH_VARARGS, "Calculate the total potential energy."},

    {"rotx", nbody_rotx, METH_VARARGS, "Rotation around the x axis."},

    {"roty", nbody_roty, METH_VARARGS, "Rotation around the y axis."},

    {"rotz", nbody_rotz, METH_VARARGS, "Rotation around the z axis."},

    {"spin", nbody_spin, METH_VARARGS, "Spin the model around an axis."},

    {"pamap", nbody_pamap, METH_VARARGS, "Return a map of the given points."},

    {"pdmap", nbody_pdmap, METH_VARARGS,
     "Return a ponderated map of the given points."},

    {"sphmap", nbody_sphmap, METH_VARARGS,
     "Return a sphmap of the given points."},

    {"ampmap", nbody_ampmap, METH_VARARGS,
     "Return a map of amplitude of the given points."},

    {"perspective", nbody_perspective, METH_VARARGS,
     "Return a 3d projection of the given points."},

    {"convol", nbody_convol, METH_VARARGS,
     "Return a 2d convolution of a with kernel b."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef nbodymodule = {
    PyModuleDef_HEAD_INIT,
    "nbodymodule",
    "Defines some mathematical functions usefull in Nbody simulations",
    -1,
    nbodyMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_nbodymodule(void) {
  PyObject *m;
  m = PyModule_Create(&nbodymodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
