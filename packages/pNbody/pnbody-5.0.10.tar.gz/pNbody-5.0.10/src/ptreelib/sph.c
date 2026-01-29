
#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "proto.h"
#include "ptreelib.h"

/*! \file density.c
 *  \brief SPH density computation and smoothing length determination
 *
 *  This file contains the "first SPH loop", where the SPH densities and
 *  some auxiliary quantities are computed.  If the number of neighbours
 *  obtained falls outside the target range, the correct smoothing
 *  length is determined iteratively, if needed.
 */

//#ifdef PERIODIC
// static double boxSize, boxHalf;
//
//#ifdef LONG_X
// static double boxSize_X, boxHalf_X;
//#else
//#define boxSize_X boxSize
//#define boxHalf_X boxHalf
//#endif
//#ifdef LONG_Y
// static double boxSize_Y, boxHalf_Y;
//#else
//#define boxSize_Y boxSize
//#define boxHalf_Y boxHalf
//#endif
//#ifdef LONG_Z
// static double boxSize_Z, boxHalf_Z;
//#else
//#define boxSize_Z boxSize
//#define boxHalf_Z boxHalf
//#endif
//#endif

/*! This function computes the local density for each active SPH particle,
 *  the number of neighbours in the current smoothing radius, and the
 *  divergence and curl of the velocity field.  The pressure is updated as
 *  well.  If a particle with its smoothing region is fully inside the
 *  local domain, it is not exported to the other processors. The function
 *  also detects particles that have a number of neighbours outside the
 *  allowed tolerance range. For these particles, the smoothing length is
 *  adjusted accordingly, and the density computation is executed again.
 *  Note that the smoothing length is not allowed to fall below the lower
 *  bound set by MinGasHsml.
 */
void sph_sub(Tree* self) {
  long long ntot, ntotleft;
  int *noffset, *nbuffer, *nsend, *nsend_local, *numlist, *ndonelist;
  int i, j, n, ndone, npleft, maxfill, source, iter = 0;
  int level, ngrp, sendTask, recvTask, place, nexport;
  double dt_entr, tstart, tend, tstart_ngb = 0, tend_ngb = 0;
  double sumt, sumcomm, timengb, sumtimengb;
  double timecomp = 0, timeimbalance = 0, timecommsumm = 0, sumimbalance;
  MPI_Status status;

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

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  for (n = 0, self->NumSphUpdateQ = 0; n < self->N_gasQ; n++) {
    self->SphQ[n].Left = self->SphQ[n].Right = 0;

    // if(P[n].Ti_endstep == All.Ti_Current)
    self->NumSphUpdateQ++;
  }

  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  MPI_Allgather(&self->NumSphUpdateQ, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

  i = 0;           /* beginn with this index */
  ntotleft = ntot; /* particles left for all tasks together */

  while (ntotleft > 0) {
    for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

    /* do local particles and prepare export list */
    for (nexport = 0, ndone = 0;
         i < self->N_gasQ && nexport < self->All.BunchSizeDensity - self->NTask;
         i++)
    // if(P[i].Ti_endstep == All.Ti_Current)
    {
      ndone++;

      for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;

      sph_evaluate_sub(self, i, 0);

      for (j = 0; j < self->NTask; j++) {
        if (self->Exportflag[j]) {
          self->DensDataIn[nexport].Pos[0] = self->Q[i].Pos[0];
          self->DensDataIn[nexport].Pos[1] = self->Q[i].Pos[1];
          self->DensDataIn[nexport].Pos[2] = self->Q[i].Pos[2];
          // self->DensDataIn[nexport].Vel[0] = self->SphQ[i].VelPred[0];
          // self->DensDataIn[nexport].Vel[1] = self->SphQ[i].VelPred[1];
          // self->DensDataIn[nexport].Vel[2] = self->SphQ[i].VelPred[2];
          self->DensDataIn[nexport].Vel[0] = self->Q[i].Vel[0];
          self->DensDataIn[nexport].Vel[1] = self->Q[i].Vel[1];
          self->DensDataIn[nexport].Vel[2] = self->Q[i].Vel[2];
          self->DensDataIn[nexport].Hsml = self->SphQ[i].Hsml;
          self->DensDataIn[nexport].Index = i;
          self->DensDataIn[nexport].Task = j;
          nexport++;
          nsend_local[j]++;
        }
      }
    }

    qsort(self->DensDataIn, nexport, sizeof(struct densdata_in),
          dens_compare_key);

    for (j = 1, noffset[0] = 0; j < self->NTask; j++)
      noffset[j] = noffset[j - 1] + nsend_local[j - 1];

    MPI_Allgather(nsend_local, self->NTask, MPI_INT, nsend, self->NTask,
                  MPI_INT, MPI_COMM_WORLD);

    /* now do the particles that need to be exported */

    for (level = 1; level < (1 << self->PTask); level++) {
      for (j = 0; j < self->NTask; j++) nbuffer[j] = 0;
      for (ngrp = level; ngrp < (1 << self->PTask); ngrp++) {
        maxfill = 0;
        for (j = 0; j < self->NTask; j++) {
          if ((j ^ ngrp) < self->NTask)
            if (maxfill < nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j])
              maxfill = nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j];
        }
        if (maxfill >= self->All.BunchSizeDensity) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* get the particles */
            MPI_Sendrecv(&self->DensDataIn[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct densdata_in),
                         MPI_BYTE, recvTask, TAG_DENS_A,
                         &self->DensDataGet[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct densdata_in),
                         MPI_BYTE, recvTask, TAG_DENS_A, MPI_COMM_WORLD,
                         &status);
          }
        }

        for (j = 0; j < self->NTask; j++)
          if ((j ^ ngrp) < self->NTask)
            nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
      }

      for (j = 0; j < nbuffer[self->ThisTask]; j++)
        sph_evaluate_sub(self, j, 1);

      /* get the result */
      for (j = 0; j < self->NTask; j++) nbuffer[j] = 0;
      for (ngrp = level; ngrp < (1 << self->PTask); ngrp++) {
        maxfill = 0;
        for (j = 0; j < self->NTask; j++) {
          if ((j ^ ngrp) < self->NTask)
            if (maxfill < nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j])
              maxfill = nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j];
        }
        if (maxfill >= self->All.BunchSizeDensity) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* send the results */
            MPI_Sendrecv(&self->DensDataResult[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct densdata_out),
                         MPI_BYTE, recvTask, TAG_DENS_B,
                         &self->DensDataPartialResult[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct densdata_out),
                         MPI_BYTE, recvTask, TAG_DENS_B, MPI_COMM_WORLD,
                         &status);

            /* add the result to the particles */
            for (j = 0; j < nsend_local[recvTask]; j++) {
              source = j + noffset[recvTask];
              place = self->DensDataIn[source].Index;

              self->SphQ[place].NumNgb +=
                  self->DensDataPartialResult[source].Ngb;
              self->SphQ[place].Density +=
                  self->DensDataPartialResult[source].Rho;
              self->SphQ[place].DivVel +=
                  self->DensDataPartialResult[source].Div;

              self->SphQ[place].DhsmlDensityFactor +=
                  self->DensDataPartialResult[source].DhsmlDensity;

              self->SphQ[place].Rot[0] +=
                  self->DensDataPartialResult[source].Rot[0];
              self->SphQ[place].Rot[1] +=
                  self->DensDataPartialResult[source].Rot[1];
              self->SphQ[place].Rot[2] +=
                  self->DensDataPartialResult[source].Rot[2];
              self->SphQ[place].Observable +=
                  self->DensDataPartialResult[source].Observable;
            }
          }
        }

        for (j = 0; j < self->NTask; j++)
          if ((j ^ ngrp) < self->NTask)
            nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
      }

      level = ngrp - 1;
    }

    MPI_Allgather(&ndone, 1, MPI_INT, ndonelist, 1, MPI_INT, MPI_COMM_WORLD);
    for (j = 0; j < self->NTask; j++) ntotleft -= ndonelist[j];
  }

  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  MPI_Allgather(&npleft, 1, MPI_INT, numlist, 1, MPI_INT, MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);
}

/*! This function represents the core of the SPH density computation. The
 *  target particle may either be local, or reside in the communication
 *  buffer.
 */
void sph_evaluate_sub(Tree* self, int target, int mode) {
  int j, n, startnode, numngb, numngb_inbox;
  double h, h2, fac, hinv, hinv3, hinv4;
  double rho, divv, wk, dwk;
  double dx, dy, dz, r, r2, u, mass_j;
  double dvx, dvy, dvz, rotv[3];
  double weighted_numngb, dhsmlrho;
  FLOAT *pos, *vel;
  double observable;

  if (mode == 0) {
    pos = self->Q[target].Pos;
    // vel = self->SphQ[target].VelPred;
    vel = self->Q[target].Vel;
    h = self->SphQ[target].Hsml;
  } else {
    pos = self->DensDataGet[target].Pos;
    vel = self->DensDataGet[target].Vel;
    h = self->DensDataGet[target].Hsml;
  }

  h2 = h * h;
  hinv = 1.0 / h;
#ifndef TWODIMS
  hinv3 = hinv * hinv * hinv;
#else
  hinv3 = hinv * hinv / boxSize_Z;
#endif
  hinv4 = hinv3 * hinv;

  rho = divv = rotv[0] = rotv[1] = rotv[2] = 0;
  weighted_numngb = 0;
  dhsmlrho = 0;

  startnode = self->All.MaxPart;
  numngb = 0;

  observable = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

      //#ifdef PERIODIC			/*  now find the closest image in the
      // given box size  */
      if (self->All.PeriodicBoundariesOn) {
        if (dx > self->All.BoxHalf_X) dx -= self->All.BoxSize_X;
        if (dx < -self->All.BoxHalf_X) dx += self->All.BoxSize_X;
        if (dy > self->All.BoxHalf_Y) dy -= self->All.BoxSize_Y;
        if (dy < -self->All.BoxHalf_Y) dy += self->All.BoxSize_Y;
        if (dz > self->All.BoxHalf_Z) dz -= self->All.BoxSize_Z;
        if (dz < -self->All.BoxHalf_Z) dz += self->All.BoxSize_Z;
      }
      //#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;

        r = sqrt(r2);

        u = r * hinv;

        if (u < 0.5) {
          wk = hinv3 * (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
          dwk = hinv4 * u * (KERNEL_COEFF_3 * u - KERNEL_COEFF_4);
        } else {
          wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) * (1.0 - u);
          dwk = hinv4 * KERNEL_COEFF_6 * (1.0 - u) * (1.0 - u);
        }

        observable += self->P[j].Mass * (self->SphP[j].Observable) /
                      (self->SphP[j].Density) * wk;
      }
    }
  } while (startnode >= 0);

  if (mode == 0) {
    self->SphQ[target].NumNgb = weighted_numngb;
    self->SphQ[target].Density = rho;
    self->SphQ[target].DivVel = divv;
    self->SphQ[target].DhsmlDensityFactor = dhsmlrho;
    self->SphQ[target].Rot[0] = rotv[0];
    self->SphQ[target].Rot[1] = rotv[1];
    self->SphQ[target].Rot[2] = rotv[2];
    self->SphQ[target].Observable = observable;
  } else {
    self->DensDataResult[target].Rho = rho;
    self->DensDataResult[target].Div = divv;
    self->DensDataResult[target].Ngb = weighted_numngb;
    self->DensDataResult[target].DhsmlDensity = dhsmlrho;
    self->DensDataResult[target].Rot[0] = rotv[0];
    self->DensDataResult[target].Rot[1] = rotv[1];
    self->DensDataResult[target].Rot[2] = rotv[2];
    self->DensDataResult[target].Observable = observable;
  }
}
