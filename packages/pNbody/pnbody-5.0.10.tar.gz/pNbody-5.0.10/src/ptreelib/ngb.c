
#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "endrun.h"
#include "proto.h"
#include "ptreelib.h"

/*! Allocates memory for the neighbour list buffer.
 */
void ngb_treeallocate(Tree *self, int npart) {
  double totbytes = 0;
  size_t bytes;

  //#ifdef PERIODIC
  //  boxSize = All.BoxSize;
  //  boxHalf = 0.5 * All.BoxSize;
  //#ifdef LONG_X
  //  boxHalf_X = boxHalf * LONG_X;
  //  boxSize_X = boxSize * LONG_X;
  //#endif
  //#ifdef LONG_Y
  //  boxHalf_Y = boxHalf * LONG_Y;
  //  boxSize_Y = boxSize * LONG_Y;
  //#endif
  //#ifdef LONG_Z
  //  boxHalf_Z = boxHalf * LONG_Z;
  //  boxSize_Z = boxSize * LONG_Z;
  //#endif
  //#endif

  if (self->All.PeriodicBoundariesOn) {
    self->All.BoxHalf_X = self->All.BoxSize;
    self->All.BoxSize_X = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Y = self->All.BoxSize;
    self->All.BoxSize_Y = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Z = self->All.BoxSize;
    self->All.BoxSize_Z = 0.5 * self->All.BoxSize;
  }

  if (self->All.PeriodicBoundariesOn)

    if (!(self->Ngblist = malloc(bytes = npart * (long)sizeof(int)))) {
      printf("Failed to allocate %g MB for ngblist array\n",
             bytes / (1024.0 * 1024.0));
      endrun(self, 78);
    }
  totbytes += bytes;

  if (self->ThisTask == 0 && self->All.OutputInfo)
    printf("allocated %g Mbyte for ngb search.\n",
           totbytes / (1024.0 * 1024.0));
}

/*! free memory allocated for neighbour list buffer.
 */
void ngb_treefree(Tree *self) { free(self->Ngblist); }

/*! these function maps a coordinate difference to the nearest periodic image
 */
double ngb_periodic(double x, double boxsize, double boxhalf) {
  if (x > boxhalf) return x - boxsize;

  if (x < -boxhalf) return x + boxsize;

  return x;
}

/*! This function returns neighbours with distance <= hsml and returns them in
 *  Ngblist. Actually, particles in a box of half side length hsml are
 *  returned, i.e. the reduction to a sphere still needs to be done in the
 *  calling routine.
 */
int ngb_treefind_variable(Tree *self, FLOAT searchcenter[3], FLOAT hsml,
                          int *startnode) {
  int k, numngb;
  int no, p;
  struct NODE *this;
  FLOAT searchmin[3], searchmax[3];

  //#ifdef PERIODIC
  double xtmp;
  //#endif

  for (k = 0; k < 3; k++) /* cube-box window */
  {
    searchmin[k] = searchcenter[k] - hsml;
    searchmax[k] = searchcenter[k] + hsml;
  }

  numngb = 0;
  no = *startnode;

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      p = no;
      no = self->Nextnode[no];

      if (self->P[p].Type > 0) continue;

      //#ifdef PERIODIC
      if (self->All.PeriodicBoundariesOn) {

        if (ngb_periodic(self->P[p].Pos[0] - searchcenter[0],
                         self->All.BoxSize_X, self->All.BoxHalf_X) < -hsml)
          continue;
        if (ngb_periodic(self->P[p].Pos[0] - searchcenter[0],
                         self->All.BoxSize_X, self->All.BoxHalf_X) > hsml)
          continue;
        if (ngb_periodic(self->P[p].Pos[1] - searchcenter[1],
                         self->All.BoxSize_Y, self->All.BoxHalf_Y) < -hsml)
          continue;
        if (ngb_periodic(self->P[p].Pos[1] - searchcenter[1],
                         self->All.BoxSize_Y, self->All.BoxHalf_Y) > hsml)
          continue;
        if (ngb_periodic(self->P[p].Pos[2] - searchcenter[2],
                         self->All.BoxSize_Z, self->All.BoxHalf_Z) < -hsml)
          continue;
        if (ngb_periodic(self->P[p].Pos[2] - searchcenter[2],
                         self->All.BoxSize_Z, self->All.BoxHalf_Z) > hsml)
          continue;

      } else {

        //#else
        if (self->P[p].Pos[0] < searchmin[0]) continue;
        if (self->P[p].Pos[0] > searchmax[0]) continue;
        if (self->P[p].Pos[1] < searchmin[1]) continue;
        if (self->P[p].Pos[1] > searchmax[1]) continue;
        if (self->P[p].Pos[2] < searchmin[2]) continue;
        if (self->P[p].Pos[2] > searchmax[2]) continue;
      }
      //#endif
      self->Ngblist[numngb++] = p;

      if (numngb == MAX_NGB) {
        numngb = ngb_clear_buf(self, searchcenter, hsml, numngb);
        if (numngb == MAX_NGB) {
          printf(
              "ThisTask=%d: Need to do a second neighbour loop for (%g|%g|%g) "
              "hsml=%g no=%d\n",
              self->ThisTask, searchcenter[0], searchcenter[1], searchcenter[2],
              hsml, no);
          *startnode = no;
          return numngb;
        }
      }
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                self->MaxNodes)]] = 1;
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      this = &self->Nodes[no];

      no = this->u.d.sibling; /* in case the node can be discarded */
                              //#ifdef PERIODIC
      if (self->All.PeriodicBoundariesOn) {
        if ((ngb_periodic(this->center[0] - searchcenter[0],
                          self->All.BoxSize_X, self->All.BoxHalf_X) +
             0.5 * this->len) < -hsml)
          continue;
        if ((ngb_periodic(this->center[0] - searchcenter[0],
                          self->All.BoxSize_X, self->All.BoxHalf_X) -
             0.5 * this->len) > hsml)
          continue;
        if ((ngb_periodic(this->center[1] - searchcenter[1],
                          self->All.BoxSize_Y, self->All.BoxHalf_Y) +
             0.5 * this->len) < -hsml)
          continue;
        if ((ngb_periodic(this->center[1] - searchcenter[1],
                          self->All.BoxSize_Y, self->All.BoxHalf_Y) -
             0.5 * this->len) > hsml)
          continue;
        if ((ngb_periodic(this->center[2] - searchcenter[2],
                          self->All.BoxSize_Z, self->All.BoxHalf_Z) +
             0.5 * this->len) < -hsml)
          continue;
        if ((ngb_periodic(this->center[2] - searchcenter[2],
                          self->All.BoxSize_Z, self->All.BoxHalf_Z) -
             0.5 * this->len) > hsml)
          continue;
      } else {
        //#else
        if ((this->center[0] + 0.5 * this->len) < (searchmin[0])) continue;
        if ((this->center[0] - 0.5 * this->len) > (searchmax[0])) continue;
        if ((this->center[1] + 0.5 * this->len) < (searchmin[1])) continue;
        if ((this->center[1] - 0.5 * this->len) > (searchmax[1])) continue;
        if ((this->center[2] + 0.5 * this->len) < (searchmin[2])) continue;
        if ((this->center[2] - 0.5 * this->len) > (searchmax[2])) continue;
      }
      //#endif
      no = this->u.d.nextnode; /* ok, we need to open the node */
    }
  }

  *startnode = -1;
  return numngb;
}

/*! The buffer for the neighbour list has a finite length MAX_NGB. For a large
 *  search region, this buffer can get full, in which case this routine can be
 *  called to eliminate some of the superfluous particles in the "corners" of
 *  the search box - only the ones in the inscribed sphere need to be kept.
 */
int ngb_clear_buf(Tree *self, FLOAT searchcenter[3], FLOAT hsml, int numngb) {
  int i, p;
  FLOAT dx, dy, dz, r2;

  //#ifdef PERIODIC
  double xtmp;
  //#endif

  for (i = 0; i < numngb; i++) {
    p = self->Ngblist[i];
    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      dx = ngb_periodic(self->P[p].Pos[0] - searchcenter[0],
                        self->All.BoxSize_X, self->All.BoxHalf_X);
      dy = ngb_periodic(self->P[p].Pos[1] - searchcenter[1],
                        self->All.BoxSize_Y, self->All.BoxHalf_Y);
      dz = ngb_periodic(self->P[p].Pos[2] - searchcenter[2],
                        self->All.BoxSize_Z, self->All.BoxHalf_Z);
    } else {
      //#else
      dx = self->P[p].Pos[0] - searchcenter[0];
      dy = self->P[p].Pos[1] - searchcenter[1];
      dz = self->P[p].Pos[2] - searchcenter[2];
    }
    //#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (r2 > hsml * hsml) {
      self->Ngblist[i] = self->Ngblist[numngb - 1];
      i--;
      numngb--;
    }
  }

  return numngb;
}
