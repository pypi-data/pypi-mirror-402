#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "numpy/ndarraytypes.h"
#include "numpy/npy_3kcompat.h"
#include "numpy/ufuncobject.h"

#define MAX_REAL_NUMBER 1e+37
#define MIN_REAL_NUMBER 1e-37

#define TO_DOUBLE(a) \
  ((PyArrayObject *)PyArray_CastToType(a, PyArray_DescrFromType(NPY_DOUBLE), 0))

#define MAXNUMTRIANGLES 100000

#define PI 3.1415926535897931

struct global_data_all_processes {
  int MaxPart; /*!< This gives the maxmimum number of particles that can be
                  stored on one processor. */
} All;

/*! This structure holds all the information that is
 * stored for each particle of the simulation.
 */

struct Point /* struct particle_data */
{
  double Pos[3]; /*!< particle position at its current time */
  double Mass;
  int IsDone;
  int ivPoint;  /* index of first voronoi point */
  int nvPoints; /* number of voronoi points */
  int iMedian;
  int nMedians;
  double Volume;
  double Density;
} * P; /*!< holds particle data on local processor */

struct Face /* a list of edges (only for 3d tesselation) */
{};

struct Triangle {
  struct Point Pt1[3];
  struct Point Pt2[3];
  struct Point Pt3[3];
};

struct TriangleInList {
  int idx;                     /* index of current triangle (used for checks) */
  struct Point *P[3];          /* pointers towards the 3  point */
  struct TriangleInList *T[3]; /* pointers towards the 3  triangles */
  int idxe[3]; /* index of point in the first  triangle, opposite to the common
                  edge */
  struct Median *Med[3]; /* pointers towards 3 medians */
};

struct Median {
  double a;           /* params for the equation of the segemnt */
  double b;           /* params for the equation of the segemnt */
  double c;           /* params for the equation of the segemnt */
  struct vPoint *vPs; /* pointer towards starting vPoint of the segment */
  struct vPoint *vPe; /* pointer towards stoping  vPoint of the segment */
  struct Point *Pa;   /* pointer towards point A*/
  struct Point *Pb;   /* pointer towards point B*/
};

/* a voronoi point */
struct vPoint {
  double Pos[3];
  int next;
};

/* some global varables */

int nT = 0, numTinStack = 0; /* number of triangles in the list */
struct TriangleInList Triangles[MAXNUMTRIANGLES]; /* list of triangles */
struct TriangleInList
    *TStack[MAXNUMTRIANGLES]; /* index of triangles to check	   */
struct Median MediansList[3 * MAXNUMTRIANGLES][3];
int nvPoints = 0; /* number of Voronoi Points */
int nMedians = 0; /* number of Medians */
struct vPoint vPoints[5 * MAXNUMTRIANGLES];
struct Median Medians[5 * MAXNUMTRIANGLES];

int NumPart;
double domainRadius, domainCenter[3];

struct Point Pe[3]; /* edges */

void endrun(int ierr) {

  int ThisTask = 0;

  if (ierr) {
    printf("task %d: endrun called with an error level of %d\n\n\n", ThisTask,
           ierr);
    fflush(stdout);
    exit(0);
  }

  exit(0);
}

/*! This routine allocates memory for particle storage, both the
 *  collisionless and the SPH particles.
 */
void allocate_memory(void) {
  size_t bytes;
  double bytes_tot = 0;

  if (All.MaxPart > 0) {
    if (!(P = malloc(bytes = All.MaxPart * sizeof(struct Point)))) {
      printf("failed to allocate memory for `P' (%g MB).\n",
             bytes / (1024.0 * 1024.0));
      endrun(1);
    }
    bytes_tot += bytes;

    printf("\nAllocated %g MByte for particle storage. %lu\n\n",
           bytes_tot / (1024.0 * 1024.0), sizeof(struct Point));
  }
}

void lines_intersections(double a0, double b0, double c0, double a1, double b1,
                         double c1, double *x, double *y) {

  *x = (c1 * b0 - c0 * b1) / (a0 * b1 - a1 * b0);
  *y = (c1 * a0 - c0 * a1) / (a1 * b0 - a0 * b1);
}

/*!
 */

struct Triangle TriangleInList2Triangle(struct TriangleInList Tl) {
  struct Triangle T;

  T.Pt1->Pos[0] = Tl.P[0]->Pos[0];
  T.Pt1->Pos[1] = Tl.P[0]->Pos[1];

  T.Pt2->Pos[0] = Tl.P[1]->Pos[0];
  T.Pt2->Pos[1] = Tl.P[1]->Pos[1];

  T.Pt3->Pos[0] = Tl.P[2]->Pos[0];
  T.Pt3->Pos[1] = Tl.P[2]->Pos[1];

  return T;
}

/*! For a set of three points, construct a triangle
 */

struct Triangle MakeTriangleFromPoints(struct Point Pt1, struct Point Pt2,
                                       struct Point Pt3) {
  struct Triangle T;
  T.Pt1->Pos[0] = Pt1.Pos[0];
  T.Pt1->Pos[1] = Pt1.Pos[1];

  T.Pt2->Pos[0] = Pt2.Pos[0];
  T.Pt2->Pos[1] = Pt2.Pos[1];

  T.Pt3->Pos[0] = Pt3.Pos[0];
  T.Pt3->Pos[1] = Pt3.Pos[1];

  return T;
}

/*! For a set of three points, this function computes the 3 medians.
 */

void TriangleMedians(struct Point Pt1, struct Point Pt2, struct Point Pt3,
                     struct Point *Pmm1, struct Point *Pmm2, struct Point *Pmm3,
                     struct Point *Pme1, struct Point *Pme2,
                     struct Point *Pme3) {

  double ma1, mb1, mc1;
  double ma2, mb2, mc2;

  /* median 0-1 */
  ma1 = 2 * (Pt2.Pos[0] - Pt1.Pos[0]);
  mb1 = 2 * (Pt2.Pos[1] - Pt1.Pos[1]);
  mc1 = (Pt1.Pos[0] * Pt1.Pos[0]) - (Pt2.Pos[0] * Pt2.Pos[0]) +
        (Pt1.Pos[1] * Pt1.Pos[1]) - (Pt2.Pos[1] * Pt2.Pos[1]);

  /* median 1-2 */
  ma2 = 2 * (Pt3.Pos[0] - Pt2.Pos[0]);
  mb2 = 2 * (Pt3.Pos[1] - Pt2.Pos[1]);
  mc2 = (Pt2.Pos[0] * Pt2.Pos[0]) - (Pt3.Pos[0] * Pt3.Pos[0]) +
        (Pt2.Pos[1] * Pt2.Pos[1]) - (Pt3.Pos[1] * Pt3.Pos[1]);

  /* intersection m0-1 -- m1-2 */
  Pmm1->Pos[0] = (mc2 * mb1 - mc1 * mb2) / (ma1 * mb2 - ma2 * mb1);
  Pmm1->Pos[1] = (mc2 * ma1 - mc1 * ma2) / (ma2 * mb1 - ma1 * mb2);

  /* intersection m1-2 -- m2-0 */
  Pmm2->Pos[0] = (mc2 * mb1 - mc1 * mb2) / (ma1 * mb2 - ma2 * mb1);
  Pmm2->Pos[1] = (mc2 * ma1 - mc1 * ma2) / (ma2 * mb1 - ma1 * mb2);

  /* intersection m2-0 -- m0-1 */
  Pmm3->Pos[0] = (mc2 * mb1 - mc1 * mb2) / (ma1 * mb2 - ma2 * mb1);
  Pmm3->Pos[1] = (mc2 * ma1 - mc1 * ma2) / (ma2 * mb1 - ma1 * mb2);

  /* intersection m1-2 -- e1-2 */
  Pme1->Pos[0] = 0.5 * (Pt1.Pos[0] + Pt2.Pos[0]);
  Pme1->Pos[1] = 0.5 * (Pt1.Pos[1] + Pt2.Pos[1]);

  /* intersection m2-3 -- e3-1 */
  Pme2->Pos[0] = 0.5 * (Pt2.Pos[0] + Pt3.Pos[0]);
  Pme2->Pos[1] = 0.5 * (Pt2.Pos[1] + Pt3.Pos[1]);

  /* intersection m3-1 -- e1-2 */
  Pme3->Pos[0] = 0.5 * (Pt3.Pos[0] + Pt1.Pos[0]);
  Pme3->Pos[1] = 0.5 * (Pt3.Pos[1] + Pt1.Pos[1]);
}

/*! For a set of three points, this function computes their cirum-circle.
 *  Its radius is return, while the center is return using pointers.
 */

double CircumCircleProperties(struct Point Pt1, struct Point Pt2,
                              struct Point Pt3, double *xc, double *yc) {

  double r;
  double x21, x32, y21, y32;
  double x12mx22, y12my22, x22mx32, y22my32;
  double c1, c2;

  x21 = Pt2.Pos[0] - Pt1.Pos[0];
  x32 = Pt3.Pos[0] - Pt2.Pos[0];

  y21 = Pt2.Pos[1] - Pt1.Pos[1];
  y32 = Pt3.Pos[1] - Pt2.Pos[1];

  x12mx22 = (Pt1.Pos[0] * Pt1.Pos[0]) - (Pt2.Pos[0] * Pt2.Pos[0]);
  y12my22 = (Pt1.Pos[1] * Pt1.Pos[1]) - (Pt2.Pos[1] * Pt2.Pos[1]);
  x22mx32 = (Pt2.Pos[0] * Pt2.Pos[0]) - (Pt3.Pos[0] * Pt3.Pos[0]);
  y22my32 = (Pt2.Pos[1] * Pt2.Pos[1]) - (Pt3.Pos[1] * Pt3.Pos[1]);

  c1 = x12mx22 + y12my22;
  c2 = x22mx32 + y22my32;

  *xc = (y32 * c1 - y21 * c2) / 2.0 / (x32 * y21 - x21 * y32);
  *yc = (x32 * c1 - x21 * c2) / 2.0 / (x21 * y32 - x32 * y21);

  r = sqrt((Pt1.Pos[0] - *xc) * (Pt1.Pos[0] - *xc) +
           (Pt1.Pos[1] - *yc) * (Pt1.Pos[1] - *yc));

  return r;
}

/*! For a given triangle T, the routine tells if the point P4
    is in the circum circle of the triangle or not.
 */

int InCircumCircle(struct Triangle T, struct Point Pt4) {

  double a, b, c;
  double d, e, f;
  double g, h, i;
  double det;

  /*
  a = T.Pt1->Pos[0] - Pt4.Pos[0];
  b = T.Pt1->Pos[1] - Pt4.Pos[1];
  c = (T.Pt1->Pos[0]*T.Pt1->Pos[0] - Pt4.Pos[0]*Pt4.Pos[0]) +
  (T.Pt1->Pos[1]*T.Pt1->Pos[1] - Pt4.Pos[1]*Pt4.Pos[1]);

  d = T.Pt2->Pos[0] - Pt4.Pos[0];
  e = T.Pt2->Pos[1] - Pt4.Pos[1];
  f = (T.Pt2->Pos[0]*T.Pt2->Pos[0] - Pt4.Pos[0]*Pt4.Pos[0]) +
  (T.Pt2->Pos[1]*T.Pt2->Pos[1] - Pt4.Pos[1]*Pt4.Pos[1]);

  g = T.Pt3->Pos[0] - Pt4.Pos[0];
  h = T.Pt3->Pos[1] - Pt4.Pos[1];
  i = (T.Pt3->Pos[0]*T.Pt3->Pos[0] - Pt4.Pos[0]*Pt4.Pos[0]) +
  (T.Pt3->Pos[1]*T.Pt3->Pos[1] - Pt4.Pos[1]*Pt4.Pos[1]);
  */

  /*
  Volker Formula
  */
  a = T.Pt2->Pos[0] - T.Pt1->Pos[0];
  b = T.Pt2->Pos[1] - T.Pt1->Pos[1];
  c = a * a + b * b;

  d = T.Pt3->Pos[0] - T.Pt1->Pos[0];
  e = T.Pt3->Pos[1] - T.Pt1->Pos[1];
  f = d * d + e * e;

  g = Pt4.Pos[0] - T.Pt1->Pos[0];
  h = Pt4.Pos[1] - T.Pt1->Pos[1];
  i = g * g + h * h;

  det = a * e * i - a * f * h - b * d * i + b * f * g + c * d * h - c * e * g;

  if (det < 0)
    return 1; /* inside */
  else
    return 0; /* outside */
}

/*! For a given triangle T, the routine tells if the point P4
    lie inside the triangle or not.
 */

int InTriangle(struct Triangle T, struct Point Pt4) {

  double c1, c2, c3;

  /* here, we use the cross product */
  c1 = (T.Pt2->Pos[0] - T.Pt1->Pos[0]) * (Pt4.Pos[1] - T.Pt1->Pos[1]) -
       (T.Pt2->Pos[1] - T.Pt1->Pos[1]) * (Pt4.Pos[0] - T.Pt1->Pos[0]);
  c2 = (T.Pt3->Pos[0] - T.Pt2->Pos[0]) * (Pt4.Pos[1] - T.Pt2->Pos[1]) -
       (T.Pt3->Pos[1] - T.Pt2->Pos[1]) * (Pt4.Pos[0] - T.Pt2->Pos[0]);
  c3 = (T.Pt1->Pos[0] - T.Pt3->Pos[0]) * (Pt4.Pos[1] - T.Pt3->Pos[1]) -
       (T.Pt1->Pos[1] - T.Pt3->Pos[1]) * (Pt4.Pos[0] - T.Pt3->Pos[0]);

  if ((c1 > 0) && (c2 > 0) && (c3 > 0)) /* inside */
    return 1;
  else
    return 0;
}

int InTriangleOrOutside(struct Triangle T, struct Point Pt4) {

  double c1, c2, c3;

  c1 = (T.Pt2->Pos[0] - T.Pt1->Pos[0]) * (Pt4.Pos[1] - T.Pt1->Pos[1]) -
       (T.Pt2->Pos[1] - T.Pt1->Pos[1]) * (Pt4.Pos[0] - T.Pt1->Pos[0]);
  if (c1 < 0) return 2; /* to triangle T[2] */

  c2 = (T.Pt3->Pos[0] - T.Pt2->Pos[0]) * (Pt4.Pos[1] - T.Pt2->Pos[1]) -
       (T.Pt3->Pos[1] - T.Pt2->Pos[1]) * (Pt4.Pos[0] - T.Pt2->Pos[0]);
  if (c2 < 0) return 0; /* to triangle T[1] */

  c3 = (T.Pt1->Pos[0] - T.Pt3->Pos[0]) * (Pt4.Pos[1] - T.Pt3->Pos[1]) -
       (T.Pt1->Pos[1] - T.Pt3->Pos[1]) * (Pt4.Pos[0] - T.Pt3->Pos[0]);
  if (c3 < 0) return 1; /* to triangle T[0] */

  return -1; /* the point is inside */
}

/*! For a given triangle, orient it positively.
 */

struct Triangle OrientTriangle(struct Triangle T) {
  double a, b, c, d;
  double det;
  struct Point Ptsto;

  a = T.Pt2->Pos[0] - T.Pt1->Pos[0];
  b = T.Pt2->Pos[1] - T.Pt1->Pos[1];
  c = T.Pt3->Pos[0] - T.Pt1->Pos[0];
  d = T.Pt3->Pos[1] - T.Pt1->Pos[1];

  det = (a * d) - (b * c);

  if (det < 0) {
    Ptsto.Pos[0] = T.Pt1->Pos[0];
    Ptsto.Pos[1] = T.Pt1->Pos[1];

    T.Pt1->Pos[0] = T.Pt3->Pos[0];
    T.Pt1->Pos[1] = T.Pt3->Pos[1];

    T.Pt3->Pos[0] = Ptsto.Pos[0];
    T.Pt3->Pos[1] = Ptsto.Pos[1];

    T = OrientTriangle(T);
  }

  return T;
}

/*! For a given triangle, orient it positively.
 */

struct TriangleInList OrientTriangleInList(struct TriangleInList T) {
  double a, b, c, d;
  double det;
  struct Point Ptsto;

  a = T.P[1]->Pos[0] - T.P[0]->Pos[0];
  b = T.P[1]->Pos[1] - T.P[0]->Pos[1];
  c = T.P[2]->Pos[0] - T.P[0]->Pos[0];
  d = T.P[2]->Pos[1] - T.P[0]->Pos[1];

  det = (a * d) - (b * c);

  if (det < 0) {
    Ptsto.Pos[0] = T.P[0]->Pos[0];
    Ptsto.Pos[1] = T.P[0]->Pos[1];

    T.P[0]->Pos[0] = T.P[2]->Pos[0];
    T.P[0]->Pos[1] = T.P[2]->Pos[1];

    T.P[2]->Pos[0] = Ptsto.Pos[0];
    T.P[2]->Pos[1] = Ptsto.Pos[1];

    T = OrientTriangleInList(T);
  }

  return T;
}

/*! This function computes the extension of the domain.
 *  It computes:
 *    len           : max-min
 *    domainCenter  : min + 0.5*len
 *    domainRadius = len*1.5;
 */

void FindExtent(void) {

  int i, j;
  double xmin[3], xmax[3], len;

  /* determine local extension */
  for (j = 0; j < 3; j++) {
    xmin[j] = MAX_REAL_NUMBER;
    xmax[j] = -MAX_REAL_NUMBER;
  }

  for (i = 0; i < NumPart; i++) {
    for (j = 0; j < 3; j++) {
      if (xmin[j] > P[i].Pos[j]) xmin[j] = P[i].Pos[j];

      if (xmax[j] < P[i].Pos[j]) xmax[j] = P[i].Pos[j];
    }
  }

  len = 0;
  for (j = 0; j < 3; j++) {
    if (xmax[j] - xmin[j] > len) len = xmax[j] - xmin[j];
  }

  for (j = 0; j < 3; j++) domainCenter[j] = xmin[j] + len / 2.;

  domainRadius = len * 1.5;

  printf("domainRadius = %g\n", domainRadius);
  printf("domainCenter = (%g %g)\n", domainCenter[0], domainCenter[1]);
}

int FindSegmentInTriangle(struct TriangleInList *T, double v,
                          struct Point P[3]) {

  double v0, v1, v2;
  double x0, x1;
  double y0, y1;
  double f;
  int iP;

  /* if the triangle as an edge point, do nothing */
  if ((T->P[0] == &Pe[0]) || (T->P[1] == &Pe[0]) || (T->P[2] == &Pe[0]))
    return 0;
  /* if the triangle as an edge point, do nothing */
  if ((T->P[0] == &Pe[1]) || (T->P[1] == &Pe[1]) || (T->P[2] == &Pe[1]))
    return 0;
  /* if the triangle as an edge point, do nothing */
  if ((T->P[0] == &Pe[2]) || (T->P[1] == &Pe[2]) || (T->P[2] == &Pe[2]))
    return 0;

  iP = 0;
  v0 = T->P[0]->Mass;
  v1 = T->P[1]->Mass;
  v2 = T->P[2]->Mass;

  // printf("Triangle %d : %g %g %g\n",T->idx,v0,v1,v2);

  /* we could also use the sign v-v0 * v-v1 ??? */

  if ((((v > v0) && (v < v1)) || ((v > v1) && (v < v0))) &&
      (v0 != v1)) /* in 0-1 */
  {
    x0 = T->P[0]->Pos[0];
    y0 = T->P[0]->Pos[1];
    x1 = T->P[1]->Pos[0];
    y1 = T->P[1]->Pos[1];

    f = (v - v0) / (v1 - v0);
    P[iP].Pos[0] = f * (x1 - x0) + x0;
    P[iP].Pos[1] = f * (y1 - y0) + y0;
    iP++;
  }

  if ((((v > v1) && (v < v2)) || ((v > v2) && (v < v1))) &&
      (v1 != v2)) /* in 1-2 */
  {
    x0 = T->P[1]->Pos[0];
    y0 = T->P[1]->Pos[1];
    x1 = T->P[2]->Pos[0];
    y1 = T->P[2]->Pos[1];

    f = (v - v1) / (v2 - v1);
    P[iP].Pos[0] = f * (x1 - x0) + x0;
    P[iP].Pos[1] = f * (y1 - y0) + y0;
    iP++;
  }

  if ((((v > v2) && (v < v0)) || ((v > v0) && (v < v2))) &&
      (v2 != v0)) /* in 2-0 */
  {
    x0 = T->P[2]->Pos[0];
    y0 = T->P[2]->Pos[1];
    x1 = T->P[0]->Pos[0];
    y1 = T->P[0]->Pos[1];

    f = (v - v2) / (v0 - v2);
    P[iP].Pos[0] = f * (x1 - x0) + x0;
    P[iP].Pos[1] = f * (y1 - y0) + y0;
    iP++;
  }

  return iP;
}

void CheckTriangles(void) {
  int iT;
  struct TriangleInList *T, *Te;

  for (iT = 0; iT < nT; iT++) {
    T = &Triangles[iT];

    Te = T->T[0];
    if (Te != NULL) {
      if ((Te->T[0] != NULL) && (Te->T[0] == T)) {
      } else if ((Te->T[1] != NULL) && (Te->T[1] == T)) {
      } else if ((Te->T[2] != NULL) && (Te->T[2] == T)) {
      } else {
        printf("Triangle %d does not point towards %d, while T->T2=%d\n",
               Te->idx, T->idx, T->T[0]->idx);
        exit(-1);
      }
    }

    Te = T->T[1];
    if (Te != NULL) {
      if ((Te->T[0] != NULL) && (Te->T[0] == T)) {
      } else if ((Te->T[1] != NULL) && (Te->T[1] == T)) {
      } else if ((Te->T[2] != NULL) && (Te->T[2] == T)) {
      } else {
        printf("Triangle %d does not point towards %d, while T->T2=%d\n",
               Te->idx, T->idx, T->T[1]->idx);
        exit(-1);
      }
    }

    Te = T->T[2];
    if (Te != NULL) {
      if ((Te->T[0] != NULL) && (Te->T[0] == T)) {
      } else if ((Te->T[1] != NULL) && (Te->T[1] == T)) {
      } else if ((Te->T[2] != NULL) && (Te->T[2] == T)) {
      } else {
        printf("Triangle %d does not point towards %d, while T->T2=%d\n",
               Te->idx, T->idx, T->T[2]->idx);
        exit(-1);
      }
    }
  }
}

/*! Flip two triangles.
    Te = T.T[i]
 */

void FlipTriangle(int i, struct TriangleInList *T, struct TriangleInList *Te,
                  struct TriangleInList *T1, struct TriangleInList *T2) {
  struct TriangleInList Ts1, Ts2;
  int i0, i1, i2;
  int j0, j1, j2;
  int j;

  Ts1 = *T;  /* save the content of the pointed triangle */
  Ts2 = *Te; /* save the content of the pointed triangle */

  j = T->idxe[i]; /* index of point opposite to i */

  i0 = i;
  i1 = (i + 1) % 3;
  i2 = (i + 2) % 3;

  j0 = j;
  j1 = (j + 1) % 3;
  j2 = (j + 2) % 3;

  /* triangle 1 */

  T1->P[0] = Ts1.P[i0];
  T1->P[1] = Ts1.P[i1];
  T1->P[2] = Ts2.P[j0];

  T1->T[0] = Ts2.T[j1];
  T1->T[1] = T2;
  T1->T[2] = Ts1.T[i2];

  T1->idxe[0] = Ts2.idxe[j1];
  T1->idxe[1] = 1;
  T1->idxe[2] = Ts1.idxe[i2];

  /* triangle 2 */

  T2->P[0] = Ts2.P[j0];
  T2->P[1] = Ts2.P[j1];
  T2->P[2] = Ts1.P[i0];

  T2->T[0] = Ts1.T[i1];
  T2->T[1] = T1;
  T2->T[2] = Ts2.T[j2];

  T2->idxe[0] = Ts1.idxe[i1];
  T2->idxe[1] = 1;
  T2->idxe[2] = Ts2.idxe[j2];

  /* restore links with adjacents triangles */
  if (Ts1.T[i1] != NULL) {
    Ts1.T[i1]->T[Ts1.idxe[i1]] = T2;
    Ts1.T[i1]->idxe[Ts1.idxe[i1]] = 0;
  }

  if (Ts1.T[i2] != NULL) {
    Ts1.T[i2]->T[Ts1.idxe[i2]] = T1;
    Ts1.T[i2]->idxe[Ts1.idxe[i2]] = 2;
  }

  if (Ts2.T[j1] != NULL) {
    Ts2.T[j1]->T[Ts2.idxe[j1]] = T1;
    Ts2.T[j1]->idxe[Ts2.idxe[j1]] = 0;
  }

  if (Ts2.T[j2] != NULL) {
    Ts2.T[j2]->T[Ts2.idxe[j2]] = T2;
    Ts2.T[j2]->idxe[Ts2.idxe[j2]] = 2;
  }
}

void DoTrianglesInStack(void) {

  struct TriangleInList *T, *Te, *T1, *T2;
  struct Point P;
  int istack;
  int idx1, idx2;
  int i;

  istack = 0;
  while (numTinStack > 0) {
    int insphere = 0;

    T = TStack[istack];

    // printf(" DoInStack T=%d  (istack=%d,
    // numTinStack=%d)\n",T->idx,istack,numTinStack);

    /* find the opposite point of the 3 adjacent triangles */

    /*******************/
    /* triangle 1      */
    /*******************/
    i = 0;
    Te = T->T[i];
    if (Te != NULL) {
      /* index of opposite point */
      P = *Te->P[T->idxe[i]];

      insphere = InCircumCircle(TriangleInList2Triangle(*T), P);
      if (insphere) {
        // printf("insphere (1)... %g %g %g in
        // T=%d\n",P.Pos[0],P.Pos[1],P.Pos[2],T->idx);
        /* index of the new triangles */
        idx1 = T->idx;
        idx2 = Te->idx;

        T1 = &Triangles[idx1];
        T2 = &Triangles[idx2];

        FlipTriangle(i, T, Te, T1, T2);

        /* add triangles in stack */
        if (numTinStack + 1 > MAXNUMTRIANGLES) {
          printf("\nNo more memory !\n");
          printf("numTinStack+1=%d > MAXNUMTRIANGLES=%d\n", numTinStack + 1,
                 MAXNUMTRIANGLES);
          printf("You should increase MAXNUMTRIANGLES\n\n");
          exit(-1);
        }
        TStack[istack] = T1;
        TStack[istack + numTinStack] = T2;
        numTinStack++;
        continue;
      }
    }

    /*******************/
    /* triangle 2      */
    /*******************/
    i = 1;
    Te = T->T[i];
    if (Te != NULL) {
      /* index of opposite point */
      P = *Te->P[T->idxe[i]];

      insphere = InCircumCircle(TriangleInList2Triangle(*T), P);
      if (insphere) {
        // printf("insphere (2)... %g %g %g in
        // T=%d\n",P.Pos[0],P.Pos[1],P.Pos[2],T->idx);
        /* index of the new triangles */
        idx1 = T->idx;
        idx2 = Te->idx;

        T1 = &Triangles[idx1];
        T2 = &Triangles[idx2];

        FlipTriangle(i, T, Te, T1, T2);

        /* add triangles in stack */
        if (numTinStack + 1 > MAXNUMTRIANGLES) {
          printf("\nNo more memory !\n");
          printf("numTinStack+1=%d > MAXNUMTRIANGLES=%d\n", numTinStack + 1,
                 MAXNUMTRIANGLES);
          printf("You should increase MAXNUMTRIANGLES\n\n");
          exit(-1);
        }
        TStack[istack] = T1;
        TStack[istack + numTinStack] = T2;
        numTinStack++;
        continue;
      }
    }

    /*******************/
    /* triangle 3      */
    /*******************/
    i = 2;
    Te = T->T[i];
    if (Te != NULL) {
      /* index of opposite point */
      P = *Te->P[T->idxe[i]];

      insphere = InCircumCircle(TriangleInList2Triangle(*T), P);
      if (insphere) {
        // printf("insphere (3)... %g %g %g in
        // T=%d\n",P.Pos[0],P.Pos[1],P.Pos[2],T->idx);
        /* index of the new triangles */
        idx1 = T->idx;
        idx2 = Te->idx;

        T1 = &Triangles[idx1];
        T2 = &Triangles[idx2];

        FlipTriangle(i, T, Te, T1, T2);

        /* add triangles in stack */
        if (numTinStack + 1 > MAXNUMTRIANGLES) {
          printf("\nNo more memory !\n");
          printf("numTinStack+1=%d > MAXNUMTRIANGLES=%d\n", numTinStack + 1,
                 MAXNUMTRIANGLES);
          printf("You should increase MAXNUMTRIANGLES\n\n");
          exit(-1);
        }
        TStack[istack] = T1;
        TStack[istack + numTinStack] = T2;
        numTinStack++;
        continue;
      }
    }

    numTinStack--;
    istack++;

    // printf("one triangle less...(istack=%d
    // numTinStack=%d)\n",istack,numTinStack);
  }
}

void Check(void) {

  int iT;

  printf("===========================\n");

  for (iT = 0; iT < nT; iT++) {
    printf("* T %d\n", Triangles[iT].idx);
    printf("pt1    %g %g %g\n", Triangles[iT].P[0]->Pos[0],
           Triangles[iT].P[0]->Pos[1], Triangles[iT].P[0]->Pos[2]);
    printf("pt2    %g %g %g\n", Triangles[iT].P[1]->Pos[0],
           Triangles[iT].P[1]->Pos[1], Triangles[iT].P[1]->Pos[2]);
    printf("pt3    %g %g %g\n", Triangles[iT].P[2]->Pos[0],
           Triangles[iT].P[2]->Pos[1], Triangles[iT].P[2]->Pos[2]);
    if (Triangles[iT].T[0] != NULL)
      printf("T1     %d\n", Triangles[iT].T[0]->idx);
    else
      printf("T1     x\n");

    if (Triangles[iT].T[1] != NULL)
      printf("T2     %d\n", Triangles[iT].T[1]->idx);
    else
      printf("T2     x\n");

    if (Triangles[iT].T[2] != NULL)
      printf("T3     %d\n", Triangles[iT].T[2]->idx);
    else
      printf("T3     x\n");
  }

  printf("===========================\n");
}

/*! Split a triangle in 3, using the point P inside it.
    Update the global list.
 */

void SplitTriangle(struct TriangleInList *pT, struct Point *Pt) {

  struct TriangleInList T, *T0, *T1, *T2, *Te;
  int idx, idx0, idx1, idx2;

  T = *pT; /* save the content of the pointed triangle */

  idx = T.idx;

  /* index of the new triangles */
  idx0 = idx;
  idx1 = nT;
  idx2 = nT + 1;

  /* increment counter */
  nT = nT + 2;

  /* check memory */
  if (nT > MAXNUMTRIANGLES) {
    printf("\nNo more memory !\n");
    printf("nT=%d > MAXNUMTRIANGLES=%d\n", nT, MAXNUMTRIANGLES);
    printf("You should increase MAXNUMTRIANGLES\n\n");
    exit(-1);
  }

  /* create pointers towards the triangles */
  T0 = &Triangles[idx0];
  T1 = &Triangles[idx1];
  T2 = &Triangles[idx2];

  /* first */
  T0->idx = idx0;

  T0->P[0] = T.P[0];
  T0->P[1] = T.P[1];
  T0->P[2] = Pt;

  /* second */
  T1->idx = idx1;

  T1->P[0] = T.P[1];
  T1->P[1] = T.P[2];
  T1->P[2] = Pt;

  /* third */
  T2->idx = idx2;

  T2->P[0] = T.P[2];
  T2->P[1] = T.P[0];
  T2->P[2] = Pt;

  /* add adjacents */
  T0->T[0] = T1;
  T0->T[1] = T2;
  T0->T[2] = T.T[2];

  T1->T[0] = T2;
  T1->T[1] = T0;
  T1->T[2] = T.T[0];

  T2->T[0] = T0;
  T2->T[1] = T1;
  T2->T[2] = T.T[1];

  /* add ext point */
  T0->idxe[0] = 1;
  T0->idxe[1] = 0;
  T0->idxe[2] = T.idxe[2];

  T1->idxe[0] = 1;
  T1->idxe[1] = 0;
  T1->idxe[2] = T.idxe[0];

  T2->idxe[0] = 1;
  T2->idxe[1] = 0;
  T2->idxe[2] = T.idxe[1];

  /* restore links with adgacents triangles */
  Te = T0->T[2];
  if (Te != NULL) {
    Te->T[T0->idxe[2]] = T0;
    Te->idxe[T0->idxe[2]] = 2;
  }

  Te = T1->T[2];
  if (Te != NULL) {
    Te->T[T1->idxe[2]] = T1;
    Te->idxe[T1->idxe[2]] = 2;
  }

  Te = T2->T[2];
  if (Te != NULL) {
    Te->T[T2->idxe[2]] = T2;
    Te->idxe[T2->idxe[2]] = 2;
  }

  /* add the new triangles in the stack */
  TStack[numTinStack] = T0;
  numTinStack++;

  TStack[numTinStack] = T1;
  numTinStack++;

  TStack[numTinStack] = T2;
  numTinStack++;

  // printf("--> add in stack %d %d %d\n",T0->idx,T1->idx,T2->idx);
}

int FindTriangle(struct Point *Pt) {
  int iT;

  /* find triangle containing the point */
  for (iT = 0; iT < nT; iT++) /* loop over all triangles */
  {
    if (InTriangle(TriangleInList2Triangle(Triangles[iT]), *Pt)) break;
  }

  return iT;
}

int NewFindTriangle(struct Point *Pt) {
  int iT;
  struct TriangleInList *T;
  int e;

  iT = 0; /* star with first triangle */
  T = &Triangles[iT];

  while (1) {
    /* test position of the point relative to the triangle */
    e = InTriangleOrOutside(TriangleInList2Triangle(*T), *Pt);

    // printf("T=%d e=%d Te=%d\n",T->idx,e,T->T[e]->idx);

    if (e == -1) /* the point is inside */
      break;

    T = T->T[e];

    if (T == NULL) {
      printf("point lie outside the limits.\n");
      exit(-1);
    }
  }

  // printf("done with find triangle (T=%d)\n",T->idx);

  return T->idx;
}

/*! Add a new point in the tesselation
 */

void AddPoint(struct Point *Pt) {

  int iT;

  /* find the triangle that contains the point P */
  // iT= FindTriangle(Pt);
  iT = NewFindTriangle(Pt);

  /* create the new triangles */
  SplitTriangle(&Triangles[iT], Pt);

  /* test the new triangles and divide and modify if necessary */
  DoTrianglesInStack();

  /* check */
  // CheckTriangles();
}

/*! Compute all medians properties (a,b,c)
 *  For each triangle, for each edge, the function computes the
 *  median properties which is stored in MediansList
 */

void ComputeMediansProperties(void) {
  int iT;

  /* loop over all triangles */
  for (iT = 0; iT < nT; iT++) {

    struct Point Pt0, Pt1, Pt2;

    Pt0.Pos[0] = Triangles[iT].P[0]->Pos[0];
    Pt0.Pos[1] = Triangles[iT].P[0]->Pos[1];

    Pt1.Pos[0] = Triangles[iT].P[1]->Pos[0];
    Pt1.Pos[1] = Triangles[iT].P[1]->Pos[1];

    Pt2.Pos[0] = Triangles[iT].P[2]->Pos[0];
    Pt2.Pos[1] = Triangles[iT].P[2]->Pos[1];

    /* median 0-1 */
    MediansList[iT][2].a = 2 * (Pt1.Pos[0] - Pt0.Pos[0]);
    MediansList[iT][2].b = 2 * (Pt1.Pos[1] - Pt0.Pos[1]);
    MediansList[iT][2].c =
        (Pt0.Pos[0] * Pt0.Pos[0]) - (Pt1.Pos[0] * Pt1.Pos[0]) +
        (Pt0.Pos[1] * Pt0.Pos[1]) - (Pt1.Pos[1] * Pt1.Pos[1]);

    /* median 1-2 */
    MediansList[iT][0].a = 2 * (Pt2.Pos[0] - Pt1.Pos[0]);
    MediansList[iT][0].b = 2 * (Pt2.Pos[1] - Pt1.Pos[1]);
    MediansList[iT][0].c =
        (Pt1.Pos[0] * Pt1.Pos[0]) - (Pt2.Pos[0] * Pt2.Pos[0]) +
        (Pt1.Pos[1] * Pt1.Pos[1]) - (Pt2.Pos[1] * Pt2.Pos[1]);

    /* median 2-0 */
    MediansList[iT][1].a = 2 * (Pt0.Pos[0] - Pt2.Pos[0]);
    MediansList[iT][1].b = 2 * (Pt0.Pos[1] - Pt2.Pos[1]);
    MediansList[iT][1].c =
        (Pt2.Pos[0] * Pt2.Pos[0]) - (Pt0.Pos[0] * Pt0.Pos[0]) +
        (Pt2.Pos[1] * Pt2.Pos[1]) - (Pt0.Pos[1] * Pt0.Pos[1]);

    /* link The triangle with the MediansList */
    Triangles[iT].Med[0] = &MediansList[iT][0]; /* median 1-2 */
    Triangles[iT].Med[1] = &MediansList[iT][1]; /* median 2-0 */
    Triangles[iT].Med[2] = &MediansList[iT][2]; /* median 0-1 */
  }
}

/*! Compute the intersetions of medians around a point of index p (index of the
 * point in the triangle T)
 *
 */

void ComputeMediansAroundPoint(struct TriangleInList *Tstart, int iPstart) {

  /*

     Tstart  : pointer to first triangle
     iPstart : index of master point relative to triangle Tstart


     if p = 0:
       T1 = T0->T[iTn];	pn=1

     if p = 1:
       T1 = T0->T[iTn];	pn=2

     if p = 0:
       T1 = T0->T[iTn];	pn=3

      iTn = (p+1) % 3;

  */

  double x, y;
  struct TriangleInList *T0, *T1;
  int iP0, iP1;
  int iT1;
  struct Point *initialPoint;
  int iM0, iM1;
  int next_vPoint = -1; /* index towards next voronoi point */
  int number_of_vPoints = 0;

  T0 = Tstart;
  iP0 = iPstart;

  initialPoint = T0->P[iP0];

  // printf("\n--> rotating around T=%d p=%d\n",T0->idx,iP0);

  /* rotate around the point */
  while (1) {

    /* next triangle */
    iT1 = (iP0 + 1) % 3;
    T1 = T0->T[iT1];

    if (T1 == NULL) {
      // printf("reach an edge\n");
      T0->P[iP0]->IsDone = 2;
      // printf("%g %g\n",T0->P[iP0]->Pos[0],T0->P[iP0]->Pos[1]);
      return;
    }

    // printf("    next triangle = %d\n",T1->idx);

    /* index of point in the triangle */
    iP1 = T0->idxe[iT1]; /* index of point opposite to iTn */
    iP1 = (iP1 + 1) % 3; /* next index of point opposite to iTn */

    // printf("    initial point=%g %g current point =%g %g
    // iP1=%d\n",initialPoint->Pos[0],initialPoint->Pos[1],T1->P[iP1]->Pos[0],T1->P[iP1]->Pos[1],iP1);

    /* check */
    if (initialPoint != T1->P[iP1]) {
      printf("    problem : initial point=%g %g current point =%g %g  iP1=%d\n",
             initialPoint->Pos[0], initialPoint->Pos[1], T1->P[iP1]->Pos[0],
             T1->P[iP1]->Pos[1], iP1);
      exit(-1);
    }

    /* compute the intersection of the two medians */

    iM0 = (iP0 + 1) % 3;
    iM1 = (iP1 + 1) % 3;
    lines_intersections(T0->Med[iM0]->a, T0->Med[iM0]->b, T0->Med[iM0]->c,
                        T1->Med[iM1]->a, T1->Med[iM1]->b, T1->Med[iM1]->c, &x,
                        &y);

    /* create a new vPoint and put it to the vPoints list  */
    vPoints[nvPoints].Pos[0] = x;
    vPoints[nvPoints].Pos[1] = y;
    vPoints[nvPoints].next = next_vPoint;

    /* end point for T0 */
    T0->Med[iM0]->vPe = &vPoints[nvPoints];

    /* here, we could add the point to T0->Med[(iM0+2) % 3] as Ps */

    /* start point for T0 */
    T1->Med[iM1]->vPs = &vPoints[nvPoints];

    /* here, we could add the point to T1->Med[(iM1+2) % 3] as Ps */

    /* increment vPoints */
    next_vPoint = nvPoints;
    nvPoints++;
    number_of_vPoints++;

    if (T1 == Tstart) /* end of loop */
    {
      // printf("    end of loop\n");

      initialPoint->ivPoint = next_vPoint;
      initialPoint->nvPoints = number_of_vPoints;

      /* create the median list  */
      /* first vPoint */
      //              next = initialPoint->ivPoint;
      //
      //              for (j = 0; j < initialPoint->nvPoints; j++)
      //                {
      //                  Medians[nMedians].vPe = vPoints[prev];
      //                  Medians[nMedians].vPs = vPoints[next];
      //                  next = vPoints[next].next;
      //                }

      break;
    }

    T0 = T1;
    iP0 = iP1;
  }
}

/*! Compute all medians intersections and define Ps and Pe
 *  For each triangle, compute the medians
 */

void ComputeMediansIntersections(void) {
  int i, p, iT;

  for (i = 0; i < NumPart; i++) P[i].IsDone = 0;

  /* loop over all triangles */
  for (iT = 0; iT < nT; iT++) {
    /* loop over points in triangle */
    for (p = 0; p < 3; p++) {
      if (!(Triangles[iT].P[p]->IsDone)) {
        // printf("in Triangle T %d do point %d\n",iT,p);
        Triangles[iT].P[p]->IsDone = 1;
        ComputeMediansAroundPoint(&Triangles[iT], p);
      }
    }
  }
}

/*! Compute the density for all particles
 */

int ComputeDensity(void) {

  int i, j;
  int next; /* next voronoi point */
  int np;
  double x0, y0, x1, y1;
  double area;

  for (i = 0; i < NumPart; i++) {

    next = P[i].ivPoint;
    np = P[i].nvPoints;

    x0 = 0; /* this ensure the first loop to give 0 */
    y0 = 0; /* this ensure the first loop to give 0 */
    area = 0;

    for (j = 0; j < np; j++) {
      x1 = vPoints[next].Pos[0];
      y1 = vPoints[next].Pos[1];

      area = area + (x0 * y1 - x1 * y0);

      x0 = x1;
      y0 = y1;

      next = vPoints[next].next;
    }

    /* connect the last with the first */
    next = P[i].ivPoint;
    x1 = vPoints[next].Pos[0];
    y1 = vPoints[next].Pos[1];
    area = area + (x0 * y1 - x1 * y0);

    /*  */
    area = 0.5 * fabs(area);

    P[i].Volume = area;
    P[i].Density = P[i].Mass / area;
  }

  return 0;
}

/************************************************************/
/*  PYTHON INTERFACE                                        */
/************************************************************/

static PyObject *tessel_TriangleMedians(PyObject *self, PyObject *args) {

  PyArrayObject *p1 = NULL;
  PyArrayObject *p2 = NULL;
  PyArrayObject *p3 = NULL;

  struct Point Pt1, Pt2, Pt3;
  struct Point Pmm1, Pmm2, Pmm3, Pme1, Pme2, Pme3;

  if (!PyArg_ParseTuple(args, "OOO", &p1, &p2, &p3)) return NULL;

  /* check type */
  if (!(PyArray_Check(p1) && PyArray_Check(p2) && PyArray_Check(p3))) {
    PyErr_SetString(PyExc_ValueError, "aruments are not all arrays.");
    return NULL;
  }

  /* check dimension */
  if ((PyArray_NDIM(p1) != 1) || (PyArray_NDIM(p2) != 1) ||
      (PyArray_NDIM(p3) != 1)) {
    PyErr_SetString(PyExc_ValueError, "Dimension of arguments must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(p1, 0) != 3) || (PyArray_DIM(p2, 0) != 3) ||
      (PyArray_DIM(p3, 0) != 3)) {
    PyErr_SetString(PyExc_ValueError, "Size of arguments must be 3.");
    return NULL;
  }

  /* ensure double */
  p1 = TO_DOUBLE(p1);
  p2 = TO_DOUBLE(p2);
  p3 = TO_DOUBLE(p3);

  Pt1.Pos[0] = *(double *)PyArray_GETPTR1(p1, 0);
  Pt1.Pos[1] = *(double *)PyArray_GETPTR1(p1, 1);

  Pt2.Pos[0] = *(double *)PyArray_GETPTR1(p2, 0);
  Pt2.Pos[1] = *(double *)PyArray_GETPTR1(p2, 1);

  Pt3.Pos[0] = *(double *)PyArray_GETPTR1(p3, 0);
  Pt3.Pos[1] = *(double *)PyArray_GETPTR1(p3, 1);

  TriangleMedians(Pt1, Pt2, Pt3, &Pmm1, &Pmm2, &Pmm3, &Pme1, &Pme2, &Pme3);

  /* create the outputs */
  PyArrayObject *aPmm1, *aPmm2, *aPmm3, *aPme1, *aPme2, *aPme3;
  npy_intp ld[1];
  ld[0] = 3;

  aPmm1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
  aPmm2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
  aPmm3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
  aPme1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
  aPme2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
  aPme3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

  *(double *)PyArray_GETPTR1(aPmm1, 0) = Pmm1.Pos[0];
  *(double *)PyArray_GETPTR1(aPmm1, 1) = Pmm1.Pos[1];
  *(double *)PyArray_GETPTR1(aPmm1, 2) = 0;

  *(double *)PyArray_GETPTR1(aPmm2, 0) = Pmm2.Pos[0];
  *(double *)PyArray_GETPTR1(aPmm2, 1) = Pmm2.Pos[1];
  *(double *)PyArray_GETPTR1(aPmm2, 2) = 0;

  *(double *)PyArray_GETPTR1(aPmm3, 0) = Pmm3.Pos[0];
  *(double *)PyArray_GETPTR1(aPmm3, 1) = Pmm3.Pos[1];
  *(double *)PyArray_GETPTR1(aPmm3, 2) = 0;

  *(double *)PyArray_GETPTR1(aPme1, 0) = Pme1.Pos[0];
  *(double *)PyArray_GETPTR1(aPme1, 1) = Pme1.Pos[1];
  *(double *)PyArray_GETPTR1(aPme1, 2) = 0;

  *(double *)PyArray_GETPTR1(aPme2, 0) = Pme2.Pos[0];
  *(double *)PyArray_GETPTR1(aPme2, 1) = Pme2.Pos[1];
  *(double *)PyArray_GETPTR1(aPme2, 2) = 0;

  *(double *)PyArray_GETPTR1(aPme3, 0) = Pme3.Pos[0];
  *(double *)PyArray_GETPTR1(aPme3, 1) = Pme3.Pos[1];
  *(double *)PyArray_GETPTR1(aPme3, 2) = 0;

  return Py_BuildValue("(OOOOOO)", aPmm1, aPmm2, aPmm3, aPme1, aPme2, aPme3);
}

static PyObject *tessel_get_vPoints(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  npy_intp ld[2];
  int i;

  ld[0] = nvPoints;
  ld[1] = 3;

  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    *(float *)PyArray_GETPTR2(pos, i, 0) = vPoints[i].Pos[0];
    *(float *)PyArray_GETPTR2(pos, i, 1) = vPoints[i].Pos[1];
    *(float *)PyArray_GETPTR2(pos, i, 2) = 0;
  }

  return PyArray_Return(pos);
}

static PyObject *tessel_get_vPointsForOnePoint(PyObject *self, PyObject *args) {

  PyArrayObject *pos;
  npy_intp ld[2];
  int i;
  int np = 0;

  if (!PyArg_ParseTuple(args, "i", &i)) return NULL;

  int next;
  next = P[i].ivPoint;
  np = P[i].nvPoints;

  ld[0] = np;
  ld[1] = 3;

  pos = (PyArrayObject *)PyArray_SimpleNew(2, ld, NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    *(float *)PyArray_GETPTR2(pos, i, 0) = vPoints[next].Pos[0];
    *(float *)PyArray_GETPTR2(pos, i, 1) = vPoints[next].Pos[1];
    *(float *)PyArray_GETPTR2(pos, i, 2) = 0;
    next = vPoints[next].next;
  }

  next = vPoints[next].next;
  if (next != 0) {
    printf("error in tessel_get_vPointsForOnePoint\n");
    return NULL;
  }

  return PyArray_Return(pos);
}

static PyObject *tessel_get_AllDensities(PyObject *self,
                                         PyObject *Py_UNUSED(ignored)) {

  PyArrayObject *rho;
  npy_intp ld[1];
  int i;

  ld[0] = NumPart;

  rho = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

  for (i = 0; i < PyArray_DIM(rho, 0); i++) {
    *(double *)PyArray_GETPTR1(rho, i) = P[i].Density;
  }

  return PyArray_Return(rho);
}

static PyObject *tessel_get_AllVolumes(PyObject *self,
                                       PyObject *Py_UNUSED(ignored)) {

  PyArrayObject *volume;
  npy_intp ld[1];
  int i;

  ld[0] = NumPart;

  volume = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

  for (i = 0; i < PyArray_DIM(volume, 0); i++) {
    *(double *)PyArray_GETPTR1(volume, i) = P[i].Volume;
  }

  return PyArray_Return(volume);
}

static PyObject *tessel_CircumCircleProperties(PyObject *self, PyObject *args) {

  PyArrayObject *p1 = NULL;
  PyArrayObject *p2 = NULL;
  PyArrayObject *p3 = NULL;

  struct Point Pt1, Pt2, Pt3;
  double xc, yc, r;

  if (!PyArg_ParseTuple(args, "OOO", &p1, &p2, &p3)) return NULL;

  /* check type */
  if (!(PyArray_Check(p1) && PyArray_Check(p2) && PyArray_Check(p3))) {
    PyErr_SetString(PyExc_ValueError, "aruments are not all arrays.");
    return NULL;
  }

  /* check dimension */
  if ((PyArray_NDIM(p1) != 1) || (PyArray_NDIM(p2) != 1) ||
      (PyArray_NDIM(p3) != 1)) {
    PyErr_SetString(PyExc_ValueError, "Dimension of arguments must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(p1, 0) != 3) || (PyArray_DIM(p2, 0) != 3) ||
      (PyArray_DIM(p3, 0) != 3)) {
    PyErr_SetString(PyExc_ValueError, "Size of arguments must be 3.");
    return NULL;
  }

  /* ensure double */
  p1 = TO_DOUBLE(p1);
  p2 = TO_DOUBLE(p2);
  p3 = TO_DOUBLE(p3);

  Pt1.Pos[0] = *(double *)PyArray_GETPTR1(p1, 0);
  Pt1.Pos[1] = *(double *)PyArray_GETPTR1(p1, 1);

  Pt2.Pos[0] = *(double *)PyArray_GETPTR1(p2, 0);
  Pt2.Pos[1] = *(double *)PyArray_GETPTR1(p2, 1);

  Pt3.Pos[0] = *(double *)PyArray_GETPTR1(p3, 0);
  Pt3.Pos[1] = *(double *)PyArray_GETPTR1(p3, 1);

  r = CircumCircleProperties(Pt1, Pt2, Pt3, &xc, &yc);

  return Py_BuildValue("(ddd)", r, xc, yc);
}

static PyObject *tessel_InTriangle(PyObject *self, PyObject *args) {

  PyArrayObject *p1 = NULL;
  PyArrayObject *p2 = NULL;
  PyArrayObject *p3 = NULL;
  PyArrayObject *p4 = NULL;

  struct Point Pt1, Pt2, Pt3, Pt4;
  struct Triangle T;
  int b;

  if (!PyArg_ParseTuple(args, "OOOO", &p1, &p2, &p3, &p4)) return NULL;

  /* check type */
  if (!(PyArray_Check(p1) && PyArray_Check(p2) && PyArray_Check(p3) &&
        PyArray_Check(p4))) {
    PyErr_SetString(PyExc_ValueError, "aruments are not all arrays.");
    return NULL;
  }

  /* check dimension */
  if ((PyArray_NDIM(p1) != 1) || (PyArray_NDIM(p2) != 1) ||
      (PyArray_NDIM(p3) != 1) || (PyArray_NDIM(p4) != 1)) {
    PyErr_SetString(PyExc_ValueError, "Dimension of arguments must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(p1, 0) != 3) || (PyArray_DIM(p2, 0) != 3) ||
      (PyArray_DIM(p3, 0) != 3) || (PyArray_DIM(p4, 0) != 3)) {
    PyErr_SetString(PyExc_ValueError, "Size of arguments must be 3.");
    return NULL;
  }

  /* ensure double */
  p1 = TO_DOUBLE(p1);
  p2 = TO_DOUBLE(p2);
  p3 = TO_DOUBLE(p3);
  p3 = TO_DOUBLE(p3);

  Pt1.Pos[0] = *(double *)PyArray_GETPTR1(p1, 0);
  Pt1.Pos[1] = *(double *)PyArray_GETPTR1(p1, 1);

  Pt2.Pos[0] = *(double *)PyArray_GETPTR1(p2, 0);
  Pt2.Pos[1] = *(double *)PyArray_GETPTR1(p2, 1);

  Pt3.Pos[0] = *(double *)PyArray_GETPTR1(p3, 0);
  Pt3.Pos[1] = *(double *)PyArray_GETPTR1(p3, 1);

  Pt4.Pos[0] = *(double *)PyArray_GETPTR1(p4, 0);
  Pt4.Pos[1] = *(double *)PyArray_GETPTR1(p4, 1);

  T = MakeTriangleFromPoints(Pt1, Pt2, Pt3);
  T = OrientTriangle(T);

  b = InTriangle(T, Pt4);

  return Py_BuildValue("i", b);
}

static PyObject *tessel_InTriangleOrOutside(PyObject *self, PyObject *args) {

  PyArrayObject *p1 = NULL;
  PyArrayObject *p2 = NULL;
  PyArrayObject *p3 = NULL;
  PyArrayObject *p4 = NULL;

  struct Point Pt1, Pt2, Pt3, Pt4;
  struct Triangle T;
  int b;

  if (!PyArg_ParseTuple(args, "OOOO", &p1, &p2, &p3, &p4)) return NULL;

  /* check type */
  if (!(PyArray_Check(p1) && PyArray_Check(p2) && PyArray_Check(p3) &&
        PyArray_Check(p4))) {
    PyErr_SetString(PyExc_ValueError, "aruments are not all arrays.");
    return NULL;
  }

  /* check dimension */
  if ((PyArray_NDIM(p1) != 1) || (PyArray_NDIM(p2) != 1) ||
      (PyArray_NDIM(p3) != 1) || (PyArray_NDIM(p4) != 1)) {
    PyErr_SetString(PyExc_ValueError, "Dimension of arguments must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(p1, 0) != 3) || (PyArray_DIM(p2, 0) != 3) ||
      (PyArray_DIM(p3, 0) != 3) || (PyArray_DIM(p4, 0) != 3)) {
    PyErr_SetString(PyExc_ValueError, "Size of arguments must be 3.");
    return NULL;
  }

  /* ensure double */
  p1 = TO_DOUBLE(p1);
  p2 = TO_DOUBLE(p2);
  p3 = TO_DOUBLE(p3);
  p3 = TO_DOUBLE(p3);

  Pt1.Pos[0] = *(double *)PyArray_GETPTR1(p1, 0);
  Pt1.Pos[1] = *(double *)PyArray_GETPTR1(p1, 1);

  Pt2.Pos[0] = *(double *)PyArray_GETPTR1(p2, 0);
  Pt2.Pos[1] = *(double *)PyArray_GETPTR1(p2, 1);

  Pt3.Pos[0] = *(double *)PyArray_GETPTR1(p3, 0);
  Pt3.Pos[1] = *(double *)PyArray_GETPTR1(p3, 1);

  Pt4.Pos[0] = *(double *)PyArray_GETPTR1(p4, 0);
  Pt4.Pos[1] = *(double *)PyArray_GETPTR1(p4, 1);

  T = MakeTriangleFromPoints(Pt1, Pt2, Pt3);
  T = OrientTriangle(T);

  b = InTriangleOrOutside(T, Pt4);

  return Py_BuildValue("i", b);
}

static PyObject *tessel_InCircumCircle(PyObject *self, PyObject *args) {

  PyArrayObject *p1 = NULL;
  PyArrayObject *p2 = NULL;
  PyArrayObject *p3 = NULL;
  PyArrayObject *p4 = NULL;

  struct Point Pt1, Pt2, Pt3, Pt4;
  struct Triangle T;
  int b;

  if (!PyArg_ParseTuple(args, "OOOO", &p1, &p2, &p3, &p4)) return NULL;

  /* check type */
  if (!(PyArray_Check(p1) && PyArray_Check(p2) && PyArray_Check(p3) &&
        PyArray_Check(p4))) {
    PyErr_SetString(PyExc_ValueError, "aruments are not all arrays.");
    return NULL;
  }

  /* check dimension */
  if ((PyArray_NDIM(p1) != 1) || (PyArray_NDIM(p2) != 1) ||
      (PyArray_NDIM(p3) != 1) || (PyArray_NDIM(p4) != 1)) {
    PyErr_SetString(PyExc_ValueError, "Dimension of arguments must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(p1, 0) != 3) || (PyArray_DIM(p2, 0) != 3) ||
      (PyArray_DIM(p3, 0) != 3) || (PyArray_DIM(p4, 0) != 3)) {
    PyErr_SetString(PyExc_ValueError, "Size of arguments must be 3.");
    return NULL;
  }

  /* ensure double */
  p1 = TO_DOUBLE(p1);
  p2 = TO_DOUBLE(p2);
  p3 = TO_DOUBLE(p3);
  p3 = TO_DOUBLE(p3);

  Pt1.Pos[0] = *(double *)PyArray_GETPTR1(p1, 0);
  Pt1.Pos[1] = *(double *)PyArray_GETPTR1(p1, 1);

  Pt2.Pos[0] = *(double *)PyArray_GETPTR1(p2, 0);
  Pt2.Pos[1] = *(double *)PyArray_GETPTR1(p2, 1);

  Pt3.Pos[0] = *(double *)PyArray_GETPTR1(p3, 0);
  Pt3.Pos[1] = *(double *)PyArray_GETPTR1(p3, 1);

  Pt4.Pos[0] = *(double *)PyArray_GETPTR1(p4, 0);
  Pt4.Pos[1] = *(double *)PyArray_GETPTR1(p4, 1);

  T = MakeTriangleFromPoints(Pt1, Pt2, Pt3);
  T = OrientTriangle(T);

  b = InCircumCircle(T, Pt4);

  return Py_BuildValue("i", b);
}

/*! This function computes the Delaunay tesselation.
 *  For given set of points P, it first find the domain extention.
 *  Then, starting for a triangle defined by Pe (edges) that contains
 *  all other points, it includes iteratively all points P and create
 *  a list of triangles (Triangles).
 */
static PyObject *tessel_ConstructDelaunay(PyObject *self, PyObject *args) {

  PyArrayObject *pos = NULL;
  PyArrayObject *mass = NULL;

  int i, j;

  if (!PyArg_ParseTuple(args, "OO", &pos, &mass)) return NULL;

  /* check type */
  if (!(PyArray_Check(pos))) {
    PyErr_SetString(PyExc_ValueError, "aruments 1 must be array.");
    return NULL;
  }

  /* check type */
  if (!(PyArray_Check(mass))) {
    PyErr_SetString(PyExc_ValueError, "aruments 2 must be array.");
    return NULL;
  }

  /* check dimension */
  if (PyArray_NDIM(pos) != 2) {
    PyErr_SetString(PyExc_ValueError, "Dimension of argument 1 must be 2.");
    return NULL;
  }

  /* check dimension */
  if (PyArray_NDIM(mass) != 1) {
    PyErr_SetString(PyExc_ValueError, "Dimension of argument 2 must be 1.");
    return NULL;
  }

  /* check size */
  if ((PyArray_DIM(pos, 1) != 3)) {
    PyErr_SetString(PyExc_ValueError, "First size of argument must be 3.");
    return NULL;
  }

  /* check size */
  if (PyArray_DIM(pos, 0) != PyArray_DIM(mass, 0)) {
    PyErr_SetString(PyExc_ValueError,
                    "Size of argument 1 must be similar to argument 2.");
    return NULL;
  }

  /* ensure double */
  pos = TO_DOUBLE(pos);
  mass = TO_DOUBLE(mass);
  NumPart = PyArray_DIM(pos, 0);

  /* add first triangle */

  /* init */
  All.MaxPart = NumPart;

  /* allocate memory */
  allocate_memory();

  /* init P */
  /* loop over all points */

  for (i = 0; i < NumPart; i++) {
    P[i].Pos[0] = *(double *)PyArray_GETPTR2(pos, i, 0);
    P[i].Pos[1] = *(double *)PyArray_GETPTR2(pos, i, 1);
    P[i].Pos[2] = *(double *)PyArray_GETPTR2(pos, i, 2);
    P[i].Mass = *(double *)PyArray_GETPTR1(mass, i);
  }

  /* find domain extent */
  FindExtent();

  /* set edges Pe, the 3 points are in an equilateral triangle around all
   * particles */
  for (j = 0; j < 3; j++) {
    Pe[j].Pos[0] = domainCenter[0] + domainRadius * cos(2. / 3. * PI * j);
    Pe[j].Pos[1] = domainCenter[1] + domainRadius * sin(2. / 3. * PI * j);
    Pe[j].Pos[2] = 0;
    Pe[j].Mass = 0;
  }

  /* Triangle list */
  Triangles[0].idx = 0;
  Triangles[0].P[0] = &Pe[0];
  Triangles[0].P[1] = &Pe[1];
  Triangles[0].P[2] = &Pe[2];
  Triangles[0].T[0] = NULL;
  Triangles[0].T[1] = NULL;
  Triangles[0].T[2] = NULL;
  Triangles[0].idxe[0] = -1;
  Triangles[0].idxe[1] = 1;
  Triangles[0].idxe[2] = -1;
  nT++;
  OrientTriangleInList(Triangles[0]);

  /* loop over all points */
  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    AddPoint(&P[i]);
  }

  /* check */
  CheckTriangles();

  return Py_BuildValue("i", 1);
}

static PyObject *tessel_GetTriangles(PyObject *self, PyObject *args) {

  PyObject *OutputList;
  PyObject *OutputDict;
  PyArrayObject *tri = NULL;
  npy_intp dim[2];
  int iT;

  /* loop over all triangles */
  OutputList = PyList_New(0);

  for (iT = 0; iT < nT; iT++) {

    /* 3x3 vector */
    dim[0] = 3;
    dim[1] = 3;

    tri = (PyArrayObject *)PyArray_SimpleNew(2, dim, NPY_DOUBLE);

    *(double *)PyArray_GETPTR2(tri, 0, 0) = Triangles[iT].P[0]->Pos[0];
    *(double *)PyArray_GETPTR2(tri, 0, 1) = Triangles[iT].P[0]->Pos[1];
    *(double *)PyArray_GETPTR2(tri, 0, 2) = 0;

    *(double *)PyArray_GETPTR2(tri, 1, 0) = Triangles[iT].P[1]->Pos[0];
    *(double *)PyArray_GETPTR2(tri, 1, 1) = Triangles[iT].P[1]->Pos[1];
    *(double *)PyArray_GETPTR2(tri, 1, 2) = 0;

    *(double *)PyArray_GETPTR2(tri, 2, 0) = Triangles[iT].P[2]->Pos[0];
    *(double *)PyArray_GETPTR2(tri, 2, 1) = Triangles[iT].P[2]->Pos[1];
    *(double *)PyArray_GETPTR2(tri, 2, 2) = 0;

    OutputDict = PyDict_New();
    PyDict_SetItem(OutputDict, PyUnicode_FromString("id"),
                   PyLong_FromLong(Triangles[iT].idx));
    PyDict_SetItem(OutputDict, PyUnicode_FromString("coord"), (PyObject *)tri);

    //(PyObject*)tri

    PyList_Append(OutputList, OutputDict);
  }

  return Py_BuildValue("O", OutputList);
}

static PyObject *tessel_ComputeIsoContours(PyObject *self, PyObject *args) {

  double val;
  int iT;

  struct Point P[3];
  int nP;

  PyObject *OutputXList;
  PyObject *OutputYList;

  if (!PyArg_ParseTuple(args, "d", &val)) return NULL;

  OutputXList = PyList_New(0);
  OutputYList = PyList_New(0);

  /* find triangle containing the point */
  for (iT = 0; iT < nT; iT++) /* loop over all triangles */
  {
    nP = FindSegmentInTriangle(&Triangles[iT], val, P);

    if (nP > 0) switch (nP) {
        case 1:
          printf("we are in trouble here (ComputeIsoContours)\n");
          exit(-1);
          break;
        case 2:
          PyList_Append(OutputXList, PyFloat_FromDouble(P[0].Pos[0]));
          PyList_Append(OutputXList, PyFloat_FromDouble(P[1].Pos[0]));

          PyList_Append(OutputYList, PyFloat_FromDouble(P[0].Pos[1]));
          PyList_Append(OutputYList, PyFloat_FromDouble(P[1].Pos[1]));
          break;
        case 3:
          PyList_Append(OutputXList, PyFloat_FromDouble(P[0].Pos[0]));
          PyList_Append(OutputXList, PyFloat_FromDouble(P[1].Pos[0]));
          PyList_Append(OutputXList, PyFloat_FromDouble(P[2].Pos[0]));
          PyList_Append(OutputXList, PyFloat_FromDouble(P[0].Pos[0]));

          PyList_Append(OutputYList, PyFloat_FromDouble(P[0].Pos[1]));
          PyList_Append(OutputYList, PyFloat_FromDouble(P[1].Pos[1]));
          PyList_Append(OutputYList, PyFloat_FromDouble(P[2].Pos[1]));
          PyList_Append(OutputYList, PyFloat_FromDouble(P[0].Pos[1]));
          break;
      }
  }

  return Py_BuildValue("(O,O)", OutputXList, OutputYList);
}

static PyObject *tessel_GetVoronoi(PyObject *self, PyObject *args) {

  int iT;
  int Tloc;

  struct Point Pt1, Pt2, Pt3;
  struct Point Pmm1, Pmm2, Pmm3, Pme1, Pme2, Pme3;

  PyArrayObject *aPmm1, *aPmm2, *aPmm3, *aPme1, *aPme2, *aPme3;
  npy_intp ld[1];

  PyObject *OutputList;
  PyObject *SegmentList;

  OutputList = PyList_New(0);

  /* create the outputs */
  ld[0] = 3;

  ComputeMediansProperties();
  ComputeMediansIntersections();

  /* loop over all triangles */
  for (iT = 0; iT < nT; iT++) {

    if (Triangles[iT].P[0]->IsDone == 2) {
      // printf("T=%d P %d (%g %g)
      // incomplete\n",Triangles[iT].idx,Triangles[iT].P[0]->Pos[0],Triangles[iT].P[0]->Pos[1]);
      continue;
    }
    if (Triangles[iT].P[1]->IsDone == 2) {
      // printf("T=%d P %d (%g %g)
      // incomplete\n",Triangles[iT].idx,Triangles[iT].P[1]->Pos[0],Triangles[iT].P[1]->Pos[1]);
      continue;
    }
    if (Triangles[iT].P[2]->IsDone == 2) {
      // printf("T=%d P %d (%g %g)
      // incomplete\n",Triangles[iT].idx,Triangles[iT].P[2]->Pos[0],Triangles[iT].P[2]->Pos[1]);
      continue;
    }

    aPmm1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPmm1, 0) = Triangles[iT].Med[0]->vPs->Pos[0];
    *(double *)PyArray_GETPTR1(aPmm1, 1) = Triangles[iT].Med[0]->vPs->Pos[1];
    *(double *)PyArray_GETPTR1(aPmm1, 2) = 0;

    aPme1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPme1, 0) = Triangles[iT].Med[0]->vPe->Pos[0];
    *(double *)PyArray_GETPTR1(aPme1, 1) = Triangles[iT].Med[0]->vPe->Pos[1];
    *(double *)PyArray_GETPTR1(aPme1, 2) = 0;

    SegmentList = PyList_New(0);
    PyList_Append(SegmentList, (PyObject *)aPmm1);
    PyList_Append(SegmentList, (PyObject *)aPme1);
    PyList_Append(OutputList, SegmentList);

    aPmm2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPmm2, 0) = Triangles[iT].Med[1]->vPs->Pos[0];
    *(double *)PyArray_GETPTR1(aPmm2, 1) = Triangles[iT].Med[1]->vPs->Pos[1];
    *(double *)PyArray_GETPTR1(aPmm2, 2) = 0;

    aPme2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPme2, 0) = Triangles[iT].Med[1]->vPe->Pos[0];
    *(double *)PyArray_GETPTR1(aPme2, 1) = Triangles[iT].Med[1]->vPe->Pos[1];
    *(double *)PyArray_GETPTR1(aPme2, 2) = 0;

    SegmentList = PyList_New(0);
    PyList_Append(SegmentList, (PyObject *)aPmm2);
    PyList_Append(SegmentList, (PyObject *)aPme2);
    PyList_Append(OutputList, SegmentList);

    aPmm3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPmm3, 0) = Triangles[iT].Med[2]->vPs->Pos[0];
    *(double *)PyArray_GETPTR1(aPmm3, 1) = Triangles[iT].Med[2]->vPs->Pos[1];
    *(double *)PyArray_GETPTR1(aPmm3, 2) = 0;

    aPme3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
    *(double *)PyArray_GETPTR1(aPme3, 0) = Triangles[iT].Med[2]->vPe->Pos[0];
    *(double *)PyArray_GETPTR1(aPme3, 1) = Triangles[iT].Med[2]->vPe->Pos[1];
    *(double *)PyArray_GETPTR1(aPme3, 2) = 0;

    SegmentList = PyList_New(0);
    PyList_Append(SegmentList, (PyObject *)aPmm3);
    PyList_Append(SegmentList, (PyObject *)aPme3);
    PyList_Append(OutputList, SegmentList);
  }

  ComputeDensity();

  int cond=0;

  if (cond==0) /* ????? */
  {

    /* find triangle containing the point */
    for (iT = 0; iT < nT; iT++) /* loop over all triangles */
    {

      Pt1.Pos[0] = Triangles[iT].P[0]->Pos[0];
      Pt1.Pos[1] = Triangles[iT].P[0]->Pos[1];

      Pt2.Pos[0] = Triangles[iT].P[1]->Pos[0];
      Pt2.Pos[1] = Triangles[iT].P[1]->Pos[1];

      Pt3.Pos[0] = Triangles[iT].P[2]->Pos[0];
      Pt3.Pos[1] = Triangles[iT].P[2]->Pos[1];

      TriangleMedians(Pt1, Pt2, Pt3, &Pmm1, &Pmm2, &Pmm3, &Pme1, &Pme2, &Pme3);

      aPmm1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
      aPmm2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
      aPmm3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
      aPme1 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
      aPme2 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);
      aPme3 = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

      *(double *)PyArray_GETPTR1(aPmm1, 0) = Pmm1.Pos[0];
      *(double *)PyArray_GETPTR1(aPmm1, 1) = Pmm1.Pos[1];
      *(double *)PyArray_GETPTR1(aPmm1, 2) = 0;

      *(double *)PyArray_GETPTR1(aPmm2, 0) = Pmm2.Pos[0];
      *(double *)PyArray_GETPTR1(aPmm2, 1) = Pmm2.Pos[1];
      *(double *)PyArray_GETPTR1(aPmm2, 2) = 0;

      *(double *)PyArray_GETPTR1(aPmm3, 0) = Pmm3.Pos[0];
      *(double *)PyArray_GETPTR1(aPmm3, 1) = Pmm3.Pos[1];
      *(double *)PyArray_GETPTR1(aPmm3, 2) = 0;

      *(double *)PyArray_GETPTR1(aPme1, 0) = Pme1.Pos[0];
      *(double *)PyArray_GETPTR1(aPme1, 1) = Pme1.Pos[1];
      *(double *)PyArray_GETPTR1(aPme1, 2) = 0;

      *(double *)PyArray_GETPTR1(aPme2, 0) = Pme2.Pos[0];
      *(double *)PyArray_GETPTR1(aPme2, 1) = Pme2.Pos[1];
      *(double *)PyArray_GETPTR1(aPme2, 2) = 0;

      *(double *)PyArray_GETPTR1(aPme3, 0) = Pme3.Pos[0];
      *(double *)PyArray_GETPTR1(aPme3, 1) = Pme3.Pos[1];
      *(double *)PyArray_GETPTR1(aPme3, 2) = 0;

      /* check if the interesection is inside the triangle */
      Tloc = InTriangleOrOutside(TriangleInList2Triangle(Triangles[iT]), Pmm1);

      /*
      return 2;	       to triangle T[2]
      return 0;	       to triangle T[1]
      return 1;	       to triangle T[0]
      return -1;         the point is inside
      */

      if (Tloc == -1) {
        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm1);
        PyList_Append(SegmentList, (PyObject *)aPme1);
        PyList_Append(OutputList, SegmentList);

        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm2);
        PyList_Append(SegmentList, (PyObject *)aPme2);
        PyList_Append(OutputList, SegmentList);

        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm3);
        PyList_Append(SegmentList, (PyObject *)aPme3);
        PyList_Append(OutputList, SegmentList);
      }

      if (Tloc == 0) {
      }

      if (Tloc == 1) {
        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm1);
        PyList_Append(SegmentList, (PyObject *)aPme1);
        PyList_Append(OutputList, SegmentList);

        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm2);
        PyList_Append(SegmentList, (PyObject *)aPme2);
        PyList_Append(OutputList, SegmentList);
      }

      if (Tloc == 2) {
        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm1);
        PyList_Append(SegmentList, (PyObject *)aPme1);
        PyList_Append(OutputList, SegmentList);

        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm2);
        PyList_Append(SegmentList, (PyObject *)aPme2);
        PyList_Append(OutputList, SegmentList);

        SegmentList = PyList_New(0);
        PyList_Append(SegmentList, (PyObject *)aPmm3);
        PyList_Append(SegmentList, (PyObject *)aPme3);
        PyList_Append(OutputList, SegmentList);
      }
    }
  }

  return Py_BuildValue("O", OutputList);
}

static PyObject *tessel_ComputeArea(PyObject *self, PyObject *args) {

  // ComputeArea();
  return NULL;
}

static PyObject *tessel_info(PyObject *self, PyObject *args) {

  int iT, iP, iTe;

  /* find triangle containing the point */
  for (iT = 0; iT < nT; iT++) /* loop over all triangles */
  {

    printf("Triangle =%d\n", Triangles[iT].idx);
    iP = 0;
    printf("  P=%d :%g %g\n", iP, Triangles[iT].P[iP]->Pos[0],
           Triangles[iT].P[iP]->Pos[1]);
    iP = 1;
    printf("  P=%d :%g %g\n", iP, Triangles[iT].P[iP]->Pos[0],
           Triangles[iT].P[iP]->Pos[1]);
    iP = 2;
    printf("  P=%d :%g %g\n", iP, Triangles[iT].P[iP]->Pos[0],
           Triangles[iT].P[iP]->Pos[1]);

    iTe = 0;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  T=%d :%d\n", iTe, Triangles[iT].T[iTe]->idx);
    else
      printf("  T=%d :-\n", iTe);
    iTe = 1;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  T=%d :%d\n", iTe, Triangles[iT].T[iTe]->idx);
    else
      printf("  T=%d :-\n", iTe);
    iTe = 2;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  T=%d :%d\n", iTe, Triangles[iT].T[iTe]->idx);
    else
      printf("  T=%d :-\n", iTe);
    ;

    iTe = 0;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  Pe=%d :%d\n", iTe, Triangles[iT].idxe[iTe]);
    else
      printf("  Pe=%d :-\n", iTe);
    iTe = 1;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  Pe=%d :%d\n", iTe, Triangles[iT].idxe[iTe]);
    else
      printf("  Pe=%d :-\n", iTe);
    iTe = 2;
    if (Triangles[iT].T[iTe] != NULL)
      printf("  Pe=%d :%d\n", iTe, Triangles[iT].idxe[iTe]);
    else
      printf("  Pe=%d :-\n", iTe);
    ;

    printf("\n");
  }

  return Py_BuildValue("i", 1);
}

/*********************************/
/* test */
/*********************************/

static PyObject *tessel_test(PyObject *self, PyObject *args) {

  return Py_BuildValue("i", 1);
}

/* definition of the method table */

static PyMethodDef tesselMethods[] = {

    {"test", tessel_test, METH_VARARGS, "Simple Test"},

    {"info", tessel_info, METH_VARARGS, "info on tesselation"},

    {"TriangleMedians", tessel_TriangleMedians, METH_VARARGS,
     "Get Triangle Medians"},

    {"get_vPoints", tessel_get_vPoints, METH_VARARGS, "Get voronoi points"},

    {"get_vPointsForOnePoint", tessel_get_vPointsForOnePoint, METH_VARARGS,
     "Get voronoi points for a given point"},

    {"get_AllDensities", tessel_get_AllDensities, METH_VARARGS,
     "get the densities for each particle"},

    {"get_AllVolumes", tessel_get_AllVolumes, METH_VARARGS,
     "get the volume for each particle"},

    {"CircumCircleProperties", tessel_CircumCircleProperties, METH_VARARGS,
     "Get Circum Circle Properties"},

    {"InTriangle", tessel_InTriangle, METH_VARARGS,
     "Return if the triangle (P1,P2,P3) contains the point P4"},

    {"InTriangleOrOutside", tessel_InTriangleOrOutside, METH_VARARGS,
     "Return if the triangle (P1,P2,P3) contains the point P4"},

    {"InCircumCircle", tessel_InCircumCircle, METH_VARARGS,
     "Return if the circum circle of the triangle (P1,P2,P3) contains the "
     "point P4"},

    {"ConstructDelaunay", tessel_ConstructDelaunay, METH_VARARGS,
     "Construct the Delaunay tesselation for a given sample of points"},

    {"GetTriangles", tessel_GetTriangles, METH_VARARGS,
     "Get the trianles in a list of 3x3 arrays."},

    {"ComputeIsoContours", tessel_ComputeIsoContours, METH_VARARGS,
     "Compute iso-contours."},

    {"GetVoronoi", tessel_GetVoronoi, METH_VARARGS,
     "Get a list of segements corresponding to the voronoi."},

    {"ComputeArea", tessel_ComputeArea, METH_VARARGS,
     "Compute the area of each cell."},

    {NULL, NULL, 0, NULL} /* Sentinel */
};

static PyModuleDef tesselmodule = {
    PyModuleDef_HEAD_INIT,
    "tessel",
    "Tesselation module",
    -1,
    tesselMethods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_tessel(void) {
  PyObject *m;
  m = PyModule_Create(&tesselmodule);
  if (m == NULL) return NULL;

  import_array();

  return m;
}
