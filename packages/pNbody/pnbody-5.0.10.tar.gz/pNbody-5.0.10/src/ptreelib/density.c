
#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "proto.h"
#include "endrun.h"
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
void density(Tree *self) {
  long long ntot, ntotleft;
  int *noffset, *nbuffer, *nsend, *nsend_local, *numlist, *ndonelist;
  int i, j, n, ndone, npleft, maxfill, source, iter = 0;
  int level, ngrp, sendTask, recvTask, place, nexport;
  double dt_entr, tstart, tend, tstart_ngb = 0, tend_ngb = 0;
  double sumt, sumcomm, timengb, sumtimengb;
  double timecomp = 0, timeimbalance = 0, timecommsumm = 0, sumimbalance;
  MPI_Status status;

  //#ifdef PERIODIC
  if (self->All.PeriodicBoundariesOn) {
    //      boxSize = self->All.BoxSize;
    //      boxHalf = 0.5 * self->All.BoxSize;
    //#ifdef LONG_X
    //      boxHalf_X = boxHalf * LONG_X;
    //      boxSize_X = boxSize * LONG_X;
    //#endif
    //#ifdef LONG_Y
    //      boxHalf_Y = boxHalf * LONG_Y;
    //      boxSize_Y = boxSize * LONG_Y;
    //#endif
    //#ifdef LONG_Z
    //      boxHalf_Z = boxHalf * LONG_Z;
    //      boxSize_Z = boxSize * LONG_Z;
    //#endif

    self->All.BoxHalf_X = self->All.BoxSize;
    self->All.BoxSize_X = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Y = self->All.BoxSize;
    self->All.BoxSize_Y = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Z = self->All.BoxSize;
    self->All.BoxSize_Z = 0.5 * self->All.BoxSize;
  }
  //#endif

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  for (n = 0, self->NumSphUpdate = 0; n < self->N_gas; n++) {
    self->SphP[n].Left = self->SphP[n].Right = 0;

    // if(P[n].Ti_endstep == All.Ti_Current)
    self->NumSphUpdate++;
  }

  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  MPI_Allgather(&self->NumSphUpdate, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

  /* we will repeat the whole thing for those particles where we didn't
   * find enough neighbours
   */
  do {
    i = 0;           /* beginn with this index */
    ntotleft = ntot; /* particles left for all tasks together */

    while (ntotleft > 0) {
      for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

      /* do local particles and prepare export list */
      // tstart = second();
      for (nexport = 0, ndone = 0;
           i < self->N_gas &&
           nexport < self->All.BunchSizeDensity - self->NTask;
           i++)
      // if(P[i].Ti_endstep == All.Ti_Current)
      {
        ndone++;

        for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;

        density_evaluate(self, i, 0);

        for (j = 0; j < self->NTask; j++) {
          if (self->Exportflag[j]) {
            self->DensDataIn[nexport].Pos[0] = self->P[i].Pos[0];
            self->DensDataIn[nexport].Pos[1] = self->P[i].Pos[1];
            self->DensDataIn[nexport].Pos[2] = self->P[i].Pos[2];
            // self->DensDataIn[nexport].Vel[0] = self->SphP[i].VelPred[0];
            // self->DensDataIn[nexport].Vel[1] = self->SphP[i].VelPred[1];
            // self->DensDataIn[nexport].Vel[2] = self->SphP[i].VelPred[2];
            self->DensDataIn[nexport].Vel[0] = self->P[i].Vel[0];
            self->DensDataIn[nexport].Vel[1] = self->P[i].Vel[1];
            self->DensDataIn[nexport].Vel[2] = self->P[i].Vel[2];
            self->DensDataIn[nexport].Hsml = self->SphP[i].Hsml;
            self->DensDataIn[nexport].Index = i;
            self->DensDataIn[nexport].Task = j;
            nexport++;
            nsend_local[j]++;
          }
        }
      }
      // tend = second();
      // timecomp += timediff(tstart, tend);

      qsort(self->DensDataIn, nexport, sizeof(struct densdata_in),
            dens_compare_key);

      for (j = 1, noffset[0] = 0; j < self->NTask; j++)
        noffset[j] = noffset[j - 1] + nsend_local[j - 1];

      // tstart = second();

      MPI_Allgather(nsend_local, self->NTask, MPI_INT, nsend, self->NTask,
                    MPI_INT, MPI_COMM_WORLD);

      // tend = second();
      // timeimbalance += timediff(tstart, tend);

      /* now do the particles that need to be exported */

      for (level = 1; level < (1 << self->PTask); level++) {
        // tstart = second();
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
        // tend = second();
        // timecommsumm += timediff(tstart, tend);

        // tstart = second();
        for (j = 0; j < nbuffer[self->ThisTask]; j++)
          density_evaluate(self, j, 1);
        // tend = second();
        // timecomp += timediff(tstart, tend);

        /* do a block to explicitly measure imbalance */
        // tstart = second();
        // MPI_Barrier(MPI_COMM_WORLD);
        // tend = second();
        // timeimbalance += timediff(tstart, tend);

        /* get the result */
        // tstart = second();
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

                self->SphP[place].NumNgb +=
                    self->DensDataPartialResult[source].Ngb;
                self->SphP[place].Density +=
                    self->DensDataPartialResult[source].Rho;
                self->SphP[place].DivVel +=
                    self->DensDataPartialResult[source].Div;

                self->SphP[place].DhsmlDensityFactor +=
                    self->DensDataPartialResult[source].DhsmlDensity;

                self->SphP[place].Rot[0] +=
                    self->DensDataPartialResult[source].Rot[0];
                self->SphP[place].Rot[1] +=
                    self->DensDataPartialResult[source].Rot[1];
                self->SphP[place].Rot[2] +=
                    self->DensDataPartialResult[source].Rot[2];
              }
            }
          }

          for (j = 0; j < self->NTask; j++)
            if ((j ^ ngrp) < self->NTask)
              nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
        }
        // tend = second();
        // timecommsumm += timediff(tstart, tend);

        level = ngrp - 1;
      }

      MPI_Allgather(&ndone, 1, MPI_INT, ndonelist, 1, MPI_INT, MPI_COMM_WORLD);
      for (j = 0; j < self->NTask; j++) ntotleft -= ndonelist[j];
    }

    /* do final operations on results */
    // tstart = second();
    for (i = 0, npleft = 0; i < self->N_gas; i++) {
      // if(P[i].Ti_endstep == All.Ti_Current)
      if (self->P[i].Active) {
        {
          self->SphP[i].DhsmlDensityFactor =
              1 / (1 + self->SphP[i].Hsml * self->SphP[i].DhsmlDensityFactor /
                           (NUMDIMS * self->SphP[i].Density));

          self->SphP[i].CurlVel =
              sqrt(self->SphP[i].Rot[0] * self->SphP[i].Rot[0] +
                   self->SphP[i].Rot[1] * self->SphP[i].Rot[1] +
                   self->SphP[i].Rot[2] * self->SphP[i].Rot[2]) /
              self->SphP[i].Density;

          self->SphP[i].DivVel /= self->SphP[i].Density;

          // dt_entr = (All.Ti_Current - (P[i].Ti_begstep + P[i].Ti_endstep) /
          // 2) * All.Timebase_interval;
          //
          // SphP[i].Pressure =
          //  (SphP[i].Entropy + SphP[i].DtEntropy * dt_entr) *
          //  pow(SphP[i].Density, GAMMA);
        }

        /* now check whether we had enough neighbours */

        if (self->SphP[i].NumNgb <
                (self->All.DesNumNgb - self->All.MaxNumNgbDeviation) ||
            (self->SphP[i].NumNgb >
                 (self->All.DesNumNgb + self->All.MaxNumNgbDeviation) &&
             self->SphP[i].Hsml > (1.01 * self->All.MinGasHsml))) {
          /* need to redo this particle */
          npleft++;

          if (self->SphP[i].Left > 0 && self->SphP[i].Right > 0)
            if ((self->SphP[i].Right - self->SphP[i].Left) <
                1.0e-3 * self->SphP[i].Left) {
              /* this one should be ok */
              npleft--;
              // P[i].Ti_endstep = -P[i].Ti_endstep - 1;	/* Mark as
              // inactive */
              self->P[i].Active = 0;
              continue;
            }

          if (self->SphP[i].NumNgb <
              (self->All.DesNumNgb - self->All.MaxNumNgbDeviation))
            self->SphP[i].Left = dmax(self->SphP[i].Hsml, self->SphP[i].Left);
          else {
            if (self->SphP[i].Right != 0) {
              if (self->SphP[i].Hsml < self->SphP[i].Right)
                self->SphP[i].Right = self->SphP[i].Hsml;
            } else
              self->SphP[i].Right = self->SphP[i].Hsml;
          }

          if (iter >= MAXITER - 10) {
            printf(
                "i=%d task=%d ID=%d Hsml=%g Left=%g Right=%g Ngbs=%g "
                "Right-Left=%g\n   pos=(%g|%g|%g)\n",
                i, self->ThisTask, (int)self->P[i].ID, self->SphP[i].Hsml,
                self->SphP[i].Left, self->SphP[i].Right,
                (float)self->SphP[i].NumNgb,
                self->SphP[i].Right - self->SphP[i].Left, self->P[i].Pos[0],
                self->P[i].Pos[1], self->P[i].Pos[2]);
            fflush(stdout);
          }

          if (self->SphP[i].Right > 0 && self->SphP[i].Left > 0)
            self->SphP[i].Hsml = pow(0.5 * (pow(self->SphP[i].Left, 3) +
                                            pow(self->SphP[i].Right, 3)),
                                     1.0 / 3);
          else {
            if (self->SphP[i].Right == 0 && self->SphP[i].Left == 0)
              endrun(self, 8188); /* can't occur */

            if (self->SphP[i].Right == 0 && self->SphP[i].Left > 0) {
              if (self->P[i].Type == 0 &&
                  fabs(self->SphP[i].NumNgb - self->All.DesNumNgb) <
                      0.5 * self->All.DesNumNgb) {
                self->SphP[i].Hsml *=
                    1 - (self->SphP[i].NumNgb - self->All.DesNumNgb) /
                            (NUMDIMS * self->SphP[i].NumNgb) *
                            self->SphP[i].DhsmlDensityFactor;
              } else
                self->SphP[i].Hsml *= 1.26;
            }

            if (self->SphP[i].Right > 0 && self->SphP[i].Left == 0) {
              if (self->P[i].Type == 0 &&
                  fabs(self->SphP[i].NumNgb - self->All.DesNumNgb) <
                      0.5 * self->All.DesNumNgb) {
                self->SphP[i].Hsml *=
                    1 - (self->SphP[i].NumNgb - self->All.DesNumNgb) /
                            (NUMDIMS * self->SphP[i].NumNgb) *
                            self->SphP[i].DhsmlDensityFactor;
              } else
                self->SphP[i].Hsml /= 1.26;
            }
          }

          if (self->SphP[i].Hsml < self->All.MinGasHsml)
            self->SphP[i].Hsml = self->All.MinGasHsml;
        } else
          // P[i].Ti_endstep = -P[i].Ti_endstep - 1;	/* Mark as inactive */
          self->P[i].Active = 0;
      }
    }
    // tend = second();
    // timecomp += timediff(tstart, tend);

    numlist = malloc(self->NTask * sizeof(int) * self->NTask);
    MPI_Allgather(&npleft, 1, MPI_INT, numlist, 1, MPI_INT, MPI_COMM_WORLD);
    for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
    free(numlist);

    if (ntot > 0) {
      // if(iter == 0)
      //  tstart_ngb = second();

      iter++;

      if (iter > 0 && self->ThisTask == 0) {
        if (self->All.OutputInfo) {
          printf("ngb iteration %d: need to repeat for %d%09d particles.\n",
                 iter, (int)(ntot / 1000000000), (int)(ntot % 1000000000));
          fflush(stdout);
        }
      }

      if (iter > MAXITER) {
        printf("failed to converge in neighbour iteration in density()\n");
        fflush(stdout);
        endrun(self, 1155);
      }
    }
    // else
    //  tend_ngb = second();
  } while (ntot > 0);

  /* mark as active again */
  for (i = 0; i < self->NumPart; i++) self->P[i].Active = 1;
  //  if(P[i].Ti_endstep < 0)
  //    P[i].Ti_endstep = -P[i].Ti_endstep - 1;

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* collect some timing information */
  // if(iter > 0)
  //  timengb = timediff(tstart_ngb, tend_ngb);
  // else
  //  timengb = 0;

  // MPI_Reduce(&timengb, &sumtimengb, 1, MPI_DOUBLE, MPI_SUM, 0,
  // MPI_COMM_WORLD); MPI_Reduce(&timecomp, &sumt, 1, MPI_DOUBLE, MPI_SUM, 0,
  // MPI_COMM_WORLD); MPI_Reduce(&timecommsumm, &sumcomm, 1, MPI_DOUBLE,
  // MPI_SUM, 0, MPI_COMM_WORLD); MPI_Reduce(&timeimbalance, &sumimbalance, 1,
  // MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

  // if(ThisTask == 0)
  //  {
  //    All.CPU_HydCompWalk += sumt / NTask;
  //    All.CPU_HydCommSumm += sumcomm / NTask;
  //    All.CPU_HydImbalance += sumimbalance / NTask;
  //    All.CPU_EnsureNgb += sumtimengb / NTask;
  //  }
}

/*! This function represents the core of the SPH density computation. The
 *  target particle may either be local, or reside in the communication
 *  buffer.
 */
void density_evaluate(Tree *self, int target, int mode) {
  int j, n, startnode, numngb, numngb_inbox;
  double h, h2, fac, hinv, hinv3, hinv4;
  double rho, divv, wk, dwk;
  double dx, dy, dz, r, r2, u, mass_j;
  double dvx, dvy, dvz, rotv[3];
  double weighted_numngb, dhsmlrho;
  FLOAT *pos, *vel;

  if (mode == 0) {
    pos = self->P[target].Pos;
    // vel = self->SphP[target].VelPred;
    vel = self->P[target].Vel;
    h = self->SphP[target].Hsml;
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
  hinv3 = hinv * hinv / self->All.BoxSize_Z;
#endif
  hinv4 = hinv3 * hinv;

  rho = divv = rotv[0] = rotv[1] = rotv[2] = 0;
  weighted_numngb = 0;
  dhsmlrho = 0;

  startnode = self->All.MaxPart;
  numngb = 0;
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

        mass_j = self->P[j].Mass;

        rho += mass_j * wk;

        weighted_numngb += NORM_COEFF * wk / hinv3;

        dhsmlrho += -mass_j * (NUMDIMS * hinv * wk + u * dwk);

        if (r > 0) {
          fac = mass_j * dwk / r;

          // dvx = vel[0] - self->SphP[j].VelPred[0];
          // dvy = vel[1] - self->SphP[j].VelPred[1];
          // dvz = vel[2] - self->SphP[j].VelPred[2];
          dvx = vel[0] - self->P[j].Vel[0];
          dvy = vel[1] - self->P[j].Vel[1];
          dvz = vel[2] - self->P[j].Vel[2];

          divv -= fac * (dx * dvx + dy * dvy + dz * dvz);

          rotv[0] += fac * (dz * dvy - dy * dvz);
          rotv[1] += fac * (dx * dvz - dz * dvx);
          rotv[2] += fac * (dy * dvx - dx * dvy);
        }
      }
    }
  } while (startnode >= 0);

  if (mode == 0) {
    self->SphP[target].NumNgb = weighted_numngb;
    self->SphP[target].Density = rho;
    self->SphP[target].DivVel = divv;
    self->SphP[target].DhsmlDensityFactor = dhsmlrho;
    self->SphP[target].Rot[0] = rotv[0];
    self->SphP[target].Rot[1] = rotv[1];
    self->SphP[target].Rot[2] = rotv[2];
  } else {
    self->DensDataResult[target].Rho = rho;
    self->DensDataResult[target].Div = divv;
    self->DensDataResult[target].Ngb = weighted_numngb;
    self->DensDataResult[target].DhsmlDensity = dhsmlrho;
    self->DensDataResult[target].Rot[0] = rotv[0];
    self->DensDataResult[target].Rot[1] = rotv[1];
    self->DensDataResult[target].Rot[2] = rotv[2];
  }
}

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
void density_sub(Tree *self) {
  long long ntot, ntotleft;
  int *noffset, *nbuffer, *nsend, *nsend_local, *numlist, *ndonelist;
  int i, j, n, ndone, npleft, maxfill, source, iter = 0;
  int level, ngrp, sendTask, recvTask, place, nexport;
  double dt_entr, tstart, tend, tstart_ngb = 0, tend_ngb = 0;
  double sumt, sumcomm, timengb, sumtimengb;
  double timecomp = 0, timeimbalance = 0, timecommsumm = 0, sumimbalance;
  MPI_Status status;

  //#ifdef PERIODIC
  if (self->All.PeriodicBoundariesOn) {
    //      boxSize = self->All.BoxSize;
    //      boxHalf = 0.5 * self->All.BoxSize;
    //#ifdef LONG_X
    //      boxHalf_X = boxHalf * LONG_X;
    //      boxSize_X = boxSize * LONG_X;
    //#endif
    //#ifdef LONG_Y
    //      boxHalf_Y = boxHalf * LONG_Y;
    //      boxSize_Y = boxSize * LONG_Y;
    //#endif
    //#ifdef LONG_Z
    //      boxHalf_Z = boxHalf * LONG_Z;
    //      boxSize_Z = boxSize * LONG_Z;
    //#endif

    self->All.BoxHalf_X = self->All.BoxSize;
    self->All.BoxSize_X = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Y = self->All.BoxSize;
    self->All.BoxSize_Y = 0.5 * self->All.BoxSize;
    self->All.BoxHalf_Z = self->All.BoxSize;
    self->All.BoxSize_Z = 0.5 * self->All.BoxSize;
  }
  //#endif

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

  /* we will repeat the whole thing for those particles where we didn't
   * find enough neighbours
   */
  do {
    i = 0;           /* beginn with this index */
    ntotleft = ntot; /* particles left for all tasks together */

    while (ntotleft > 0) {
      for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

      /* do local particles and prepare export list */
      // tstart = second();
      for (nexport = 0, ndone = 0;
           i < self->N_gasQ &&
           nexport < self->All.BunchSizeDensity - self->NTask;
           i++)
      // if(P[i].Ti_endstep == All.Ti_Current)
      {
        ndone++;

        for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;

        density_evaluate_sub(self, i, 0);

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
      // tend = second();
      // timecomp += timediff(tstart, tend);

      qsort(self->DensDataIn, nexport, sizeof(struct densdata_in),
            dens_compare_key);

      for (j = 1, noffset[0] = 0; j < self->NTask; j++)
        noffset[j] = noffset[j - 1] + nsend_local[j - 1];

      // tstart = second();

      MPI_Allgather(nsend_local, self->NTask, MPI_INT, nsend, self->NTask,
                    MPI_INT, MPI_COMM_WORLD);

      // tend = second();
      // timeimbalance += timediff(tstart, tend);

      /* now do the particles that need to be exported */

      for (level = 1; level < (1 << self->PTask); level++) {
        // tstart = second();
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
        // tend = second();
        // timecommsumm += timediff(tstart, tend);

        // tstart = second();
        for (j = 0; j < nbuffer[self->ThisTask]; j++)
          density_evaluate_sub(self, j, 1);
        // tend = second();
        // timecomp += timediff(tstart, tend);

        /* do a block to explicitly measure imbalance */
        // tstart = second();
        // MPI_Barrier(MPI_COMM_WORLD);
        // tend = second();
        // timeimbalance += timediff(tstart, tend);

        /* get the result */
        // tstart = second();
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
              }
            }
          }

          for (j = 0; j < self->NTask; j++)
            if ((j ^ ngrp) < self->NTask)
              nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
        }
        // tend = second();
        // timecommsumm += timediff(tstart, tend);

        level = ngrp - 1;
      }

      MPI_Allgather(&ndone, 1, MPI_INT, ndonelist, 1, MPI_INT, MPI_COMM_WORLD);
      for (j = 0; j < self->NTask; j++) ntotleft -= ndonelist[j];
    }

    /* do final operations on results */
    // tstart = second();
    for (i = 0, npleft = 0; i < self->N_gasQ; i++) {
      // if(P[i].Ti_endstep == All.Ti_Current)
      if (self->Q[i].Active) {
        {
          self->SphQ[i].DhsmlDensityFactor =
              1 / (1 + self->SphQ[i].Hsml * self->SphQ[i].DhsmlDensityFactor /
                           (NUMDIMS * self->SphQ[i].Density));

          self->SphQ[i].CurlVel =
              sqrt(self->SphQ[i].Rot[0] * self->SphQ[i].Rot[0] +
                   self->SphQ[i].Rot[1] * self->SphQ[i].Rot[1] +
                   self->SphQ[i].Rot[2] * self->SphQ[i].Rot[2]) /
              self->SphQ[i].Density;

          self->SphQ[i].DivVel /= self->SphQ[i].Density;

          // dt_entr = (All.Ti_Current - (P[i].Ti_begstep + P[i].Ti_endstep) /
          // 2) * All.Timebase_interval;
          //
          // SphP[i].Pressure =
          //  (SphP[i].Entropy + SphP[i].DtEntropy * dt_entr) *
          //  pow(SphP[i].Density, GAMMA);
        }

        /* now check whether we had enough neighbours */

        if (self->SphQ[i].NumNgb <
                (self->All.DesNumNgb - self->All.MaxNumNgbDeviation) ||
            (self->SphQ[i].NumNgb >
                 (self->All.DesNumNgb + self->All.MaxNumNgbDeviation) &&
             self->SphQ[i].Hsml > (1.01 * self->All.MinGasHsml))) {
          /* need to redo this particle */
          npleft++;

          if (self->SphQ[i].Left > 0 && self->SphQ[i].Right > 0)
            if ((self->SphQ[i].Right - self->SphQ[i].Left) <
                1.0e-3 * self->SphQ[i].Left) {
              /* this one should be ok */
              npleft--;
              // P[i].Ti_endstep = -P[i].Ti_endstep - 1;	/* Mark as
              // inactive */
              self->Q[i].Active = 0;
              continue;
            }

          if (self->SphQ[i].NumNgb <
              (self->All.DesNumNgb - self->All.MaxNumNgbDeviation))
            self->SphQ[i].Left = dmax(self->SphQ[i].Hsml, self->SphQ[i].Left);
          else {
            if (self->SphQ[i].Right != 0) {
              if (self->SphQ[i].Hsml < self->SphQ[i].Right)
                self->SphQ[i].Right = self->SphQ[i].Hsml;
            } else
              self->SphQ[i].Right = self->SphQ[i].Hsml;
          }

          if (iter >= MAXITER - 10) {
            printf(
                "i=%d task=%d ID=%d Hsml=%g Left=%g Right=%g Ngbs=%g "
                "Right-Left=%g\n   pos=(%g|%g|%g)\n",
                i, self->ThisTask, (int)self->Q[i].ID, self->SphQ[i].Hsml,
                self->SphQ[i].Left, self->SphQ[i].Right,
                (float)self->SphQ[i].NumNgb,
                self->SphQ[i].Right - self->SphQ[i].Left, self->Q[i].Pos[0],
                self->Q[i].Pos[1], self->Q[i].Pos[2]);
            fflush(stdout);
          }

          if (self->SphQ[i].Right > 0 && self->SphQ[i].Left > 0)
            self->SphQ[i].Hsml = pow(0.5 * (pow(self->SphQ[i].Left, 3) +
                                            pow(self->SphQ[i].Right, 3)),
                                     1.0 / 3);
          else {
            if (self->SphQ[i].Right == 0 && self->SphQ[i].Left == 0)
              endrun(self, 8188); /* can't occur */

            if (self->SphQ[i].Right == 0 && self->SphQ[i].Left > 0) {
              if (self->Q[i].Type == 0 &&
                  fabs(self->SphQ[i].NumNgb - self->All.DesNumNgb) <
                      0.5 * self->All.DesNumNgb) {
                self->SphQ[i].Hsml *=
                    1 - (self->SphQ[i].NumNgb - self->All.DesNumNgb) /
                            (NUMDIMS * self->SphQ[i].NumNgb) *
                            self->SphQ[i].DhsmlDensityFactor;
              } else
                self->SphQ[i].Hsml *= 1.26;
            }

            if (self->SphQ[i].Right > 0 && self->SphQ[i].Left == 0) {
              if (self->Q[i].Type == 0 &&
                  fabs(self->SphQ[i].NumNgb - self->All.DesNumNgb) <
                      0.5 * self->All.DesNumNgb) {
                self->SphQ[i].Hsml *=
                    1 - (self->SphQ[i].NumNgb - self->All.DesNumNgb) /
                            (NUMDIMS * self->SphQ[i].NumNgb) *
                            self->SphQ[i].DhsmlDensityFactor;
              } else
                self->SphQ[i].Hsml /= 1.26;
            }
          }

          if (self->SphQ[i].Hsml < self->All.MinGasHsml)
            self->SphQ[i].Hsml = self->All.MinGasHsml;
        } else
          // P[i].Ti_endstep = -P[i].Ti_endstep - 1;	/* Mark as inactive */
          self->Q[i].Active = 0;
      }
    }
    // tend = second();
    // timecomp += timediff(tstart, tend);

    numlist = malloc(self->NTask * sizeof(int) * self->NTask);
    MPI_Allgather(&npleft, 1, MPI_INT, numlist, 1, MPI_INT, MPI_COMM_WORLD);
    for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
    free(numlist);

    if (ntot > 0) {
      // if(iter == 0)
      //  tstart_ngb = second();

      iter++;

      if (iter > 0 && self->ThisTask == 0) {
        if (self->All.OutputInfo) {
          printf("ngb iteration %d: need to repeat for %d%09d particles.\n",
                 iter, (int)(ntot / 1000000000), (int)(ntot % 1000000000));
          fflush(stdout);
        }
      }

      if (iter > MAXITER) {
        printf("failed to converge in neighbour iteration in density()\n");
        fflush(stdout);
        endrun(self, 1155);
      }
    }
    // else
    //  tend_ngb = second();
  } while (ntot > 0);

  /* mark as active again */
  for (i = 0; i < self->NumPartQ; i++) self->Q[i].Active = 1;
  //  if(P[i].Ti_endstep < 0)
  //    P[i].Ti_endstep = -P[i].Ti_endstep - 1;

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* collect some timing information */
  // if(iter > 0)
  //  timengb = timediff(tstart_ngb, tend_ngb);
  // else
  //  timengb = 0;

  // MPI_Reduce(&timengb, &sumtimengb, 1, MPI_DOUBLE, MPI_SUM, 0,
  // MPI_COMM_WORLD); MPI_Reduce(&timecomp, &sumt, 1, MPI_DOUBLE, MPI_SUM, 0,
  // MPI_COMM_WORLD); MPI_Reduce(&timecommsumm, &sumcomm, 1, MPI_DOUBLE,
  // MPI_SUM, 0, MPI_COMM_WORLD); MPI_Reduce(&timeimbalance, &sumimbalance, 1,
  // MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

  // if(ThisTask == 0)
  //  {
  //    All.CPU_HydCompWalk += sumt / NTask;
  //    All.CPU_HydCommSumm += sumcomm / NTask;
  //    All.CPU_HydImbalance += sumimbalance / NTask;
  //    All.CPU_EnsureNgb += sumtimengb / NTask;
  //  }
}

/*! This function represents the core of the SPH density computation. The
 *  target particle may either be local, or reside in the communication
 *  buffer.
 */
void density_evaluate_sub(Tree *self, int target, int mode) {
  int j, n, startnode, numngb, numngb_inbox;
  double h, h2, fac, hinv, hinv3, hinv4;
  double rho, divv, wk, dwk;
  double dx, dy, dz, r, r2, u, mass_j;
  double dvx, dvy, dvz, rotv[3];
  double weighted_numngb, dhsmlrho;
  FLOAT *pos, *vel;

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
  hinv3 = hinv * hinv / self->All.BoxSize_Z;
#endif
  hinv4 = hinv3 * hinv;

  rho = divv = rotv[0] = rotv[1] = rotv[2] = 0;
  weighted_numngb = 0;
  dhsmlrho = 0;

  startnode = self->All.MaxPart;
  numngb = 0;
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

        mass_j = self->P[j].Mass;

        rho += mass_j * wk;

        weighted_numngb += NORM_COEFF * wk / hinv3;

        dhsmlrho += -mass_j * (NUMDIMS * hinv * wk + u * dwk);

        if (r > 0) {
          fac = mass_j * dwk / r;

          // dvx = vel[0] - self->SphP[j].VelPred[0];
          // dvy = vel[1] - self->SphP[j].VelPred[1];
          // dvz = vel[2] - self->SphP[j].VelPred[2];
          dvx = vel[0] - self->P[j].Vel[0];
          dvy = vel[1] - self->P[j].Vel[1];
          dvz = vel[2] - self->P[j].Vel[2];

          divv -= fac * (dx * dvx + dy * dvy + dz * dvz);

          rotv[0] += fac * (dz * dvy - dy * dvz);
          rotv[1] += fac * (dx * dvz - dz * dvx);
          rotv[2] += fac * (dy * dvx - dx * dvy);
        }
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
  } else {
    self->DensDataResult[target].Rho = rho;
    self->DensDataResult[target].Div = divv;
    self->DensDataResult[target].Ngb = weighted_numngb;
    self->DensDataResult[target].DhsmlDensity = dhsmlrho;
    self->DensDataResult[target].Rot[0] = rotv[0];
    self->DensDataResult[target].Rot[1] = rotv[1];
    self->DensDataResult[target].Rot[2] = rotv[2];
  }
}

/*! This routine is a comparison kernel used in a sort routine to group
 *  particles that are exported to the same processor.
 */
int dens_compare_key(const void *a, const void *b) {
  if (((struct densdata_in *)a)->Task < (((struct densdata_in *)b)->Task))
    return -1;

  if (((struct densdata_in *)a)->Task > (((struct densdata_in *)b)->Task))
    return +1;

  return 0;
}

/*! This function is used to find an initial smoothing length for each SPH
 *  particle. It guarantees that the number of neighbours will be between
 *  desired_ngb-MAXDEV and desired_ngb+MAXDEV. For simplicity, a first guess
 *  of the smoothing length is provided to the function density(), which will
 *  then iterate if needed to find the right smoothing length.
 */
void density_init_hsml(Tree *self) {
  int i, no, p;

  // if(RestartFlag == 0)
  {

    for (i = 0; i < self->N_gas; i++) {
      no = self->Father[i];

      while (10 * self->All.DesNumNgb * self->P[i].Mass >
             self->Nodes[no].u.d.mass) {
        p = self->Nodes[no].u.d.father;

        if (p < 0) break;

        no = p;
      }
#ifndef TWODIMS
      self->SphP[i].Hsml = pow(3.0 / (4 * M_PI) * self->All.DesNumNgb *
                                   self->P[i].Mass / self->Nodes[no].u.d.mass,
                               1.0 / 3) *
                           self->Nodes[no].len;
#else
      self->SphP[i].Hsml = pow(1.0 / (M_PI)*self->All.DesNumNgb *
                                   self->P[i].Mass / self->Nodes[no].u.d.mass,
                               1.0 / 2) *
                           self->Nodes[no].len;
#endif
    }
  }

  // density();
}
