#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "endrun.h"
#include "proto.h"
#include "ptreelib.h"

/*! \file potential.c
 *  \brief Computation of the gravitational potential of particles
 */

/*! This function computes the gravitational potential for ALL the particles.
 *  First, the (short-range) tree potential is computed, and then, if needed,
 *  the long range PM potential is added.
 */
void compute_potential(Tree *self) {
  int i;

#ifndef NOGRAVITY
  long long ntot, ntotleft;
  int j, k, level, sendTask, recvTask;
  int ndone;
  int maxfill, ngrp, place, nexport;
  int *nsend, *noffset, *nsend_local, *nbuffer, *ndonelist, *numlist;
  double fac;
  double t0, t1, tstart, tend;
  MPI_Status status;
  double r2;

  if (self->All.ComovingIntegrationOn) set_softenings(self);

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("Start computation of potential for all particles...\n");
    fflush(stdout);
  }

  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  MPI_Allgather(&self->NumPart, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  i = 0;           /* beginn with this index */
  ntotleft = ntot; /* particles left for all tasks together */

  while (ntotleft > 0) {
    for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

    /* do local particles and prepare export list */
    for (nexport = 0, ndone = 0;
         i < self->NumPart && nexport < self->All.BunchSizeForce - self->NTask;
         i++) {
      ndone++;

      for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;

#ifndef PMGRID
      force_treeevaluate_potential(self, i, 0);
#else
      force_treeevaluate_potential_shortrange(self, i, 0);
#endif

      for (j = 0; j < self->NTask; j++) {
        if (self->Exportflag[j]) {
          for (k = 0; k < 3; k++)
            self->GravDataGet[nexport].u.Pos[k] = self->P[i].Pos[k];
#ifdef UNEQUALSOFTENINGS
          self->GravDataGet[nexport].Type = P[i].Type;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
          if (P[i].Type == 0) self->GravDataGet[nexport].Soft = SphP[i].Hsml;
#endif
#endif
          self->GravDataGet[nexport].w.OldAcc = self->P[i].OldAcc;

          self->GravDataIndexTable[nexport].Task = j;
          self->GravDataIndexTable[nexport].Index = i;
          self->GravDataIndexTable[nexport].SortIndex = nexport;

          nexport++;
          nsend_local[j]++;
        }
      }
    }

    qsort(self->GravDataIndexTable, nexport, sizeof(struct gravdata_index),
          grav_tree_compare_key);

    for (j = 0; j < nexport; j++)
      self->GravDataIn[j] =
          self->GravDataGet[self->GravDataIndexTable[j].SortIndex];

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
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* get the particles */
            MPI_Sendrecv(&self->GravDataIn[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_A,
                         &self->GravDataGet[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_A, MPI_COMM_WORLD,
                         &status);
          }
        }

        for (j = 0; j < self->NTask; j++)
          if ((j ^ ngrp) < self->NTask)
            nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
      }

      for (j = 0; j < nbuffer[self->ThisTask]; j++) {
#ifndef PMGRID
        force_treeevaluate_potential(self, j, 1);
#else
        force_treeevaluate_potential_shortrange(self, j, 1);
#endif
      }

      /* get the result */
      for (j = 0; j < self->NTask; j++) nbuffer[j] = 0;
      for (ngrp = level; ngrp < (1 << self->PTask); ngrp++) {
        maxfill = 0;
        for (j = 0; j < self->NTask; j++) {
          if ((j ^ ngrp) < self->NTask)
            if (maxfill < nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j])
              maxfill = nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j];
        }
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* send the results */
            MPI_Sendrecv(&self->GravDataResult[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_B,
                         &self->GravDataOut[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_B, MPI_COMM_WORLD,
                         &status);

            /* add the result to the particles */
            for (j = 0; j < nsend_local[recvTask]; j++) {
              place = self->GravDataIndexTable[noffset[recvTask] + j].Index;

              self->P[place].Potential +=
                  self->GravDataOut[j + noffset[recvTask]].u.Potential;
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

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* add correction to exclude self-potential */

  for (i = 0; i < self->NumPart; i++) {
    /* remove self-potential */
    self->P[i].Potential +=
        self->P[i].Mass / self->All.SofteningTable[self->P[i].Type];

    if (self->All.ComovingIntegrationOn)
      if (self->All.PeriodicBoundariesOn)
        self->P[i].Potential -=
            2.8372975 * pow(self->P[i].Mass, 2.0 / 3) *
            pow(self->All.Omega0 * 3 * self->All.Hubble * self->All.Hubble /
                    (8 * M_PI * self->All.G),
                1.0 / 3);
  }

  /* multiply with the gravitational constant */

  for (i = 0; i < self->NumPart; i++) self->P[i].Potential *= self->All.G;

#ifdef PMGRID

#ifdef PERIODIC
  pmpotential_periodic();
#ifdef PLACEHIGHRESREGION
  i = pmpotential_nonperiodic(1);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();
    pm_setup_nonperiodic_kernel();
    i = pmpotential_nonperiodic(1); /* try again */
  }
  if (i == 1) endrun(self, 88686);
#endif
#else
  i = pmpotential_nonperiodic(0);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();
    pm_setup_nonperiodic_kernel();
    i = pmpotential_nonperiodic(0); /* try again */
  }
  if (i == 1) endrun(88687);
#ifdef PLACEHIGHRESREGION
  i = pmpotential_nonperiodic(1);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();

    i = pmpotential_nonperiodic(1);
  }
  if (i != 0) endrun(88688);
#endif
#endif

#endif

  if (self->All.ComovingIntegrationOn) {
    //#ifndef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      fac = -0.5 * self->All.Omega0 * self->All.Hubble * self->All.Hubble;

      for (i = 0; i < self->NumPart; i++) {
        for (k = 0, r2 = 0; k < 3; k++)
          r2 += self->P[i].Pos[k] * self->P[i].Pos[k];

        self->P[i].Potential += fac * r2;
      }
      //#endif
    }
  } else {
    fac = -0.5 * self->All.OmegaLambda * self->All.Hubble * self->All.Hubble;
    if (fac != 0) {
      for (i = 0; i < self->NumPart; i++) {
        for (k = 0, r2 = 0; k < 3; k++)
          r2 += self->P[i].Pos[k] * self->P[i].Pos[k];

        self->P[i].Potential += fac * r2;
      }
    }
  }

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("potential done.\n");
    fflush(stdout);
  }

#else
  for (i = 0; i < self->NumPart; i++) self->P[i].Potential = 0;
#endif
}

/*! This function computes the gravitational potential for ALL the particles.
 *  First, the (short-range) tree potential is computed, and then, if needed,
 *  the long range PM potential is added.
 */
void compute_potential_sub(Tree *self) {
  int i;

#ifndef NOGRAVITY
  long long ntot, ntotleft;
  int j, k, level, sendTask, recvTask;
  int ndone;
  int maxfill, ngrp, place, nexport;
  int *nsend, *noffset, *nsend_local, *nbuffer, *ndonelist, *numlist;
  double fac;
  double t0, t1, tstart, tend;
  MPI_Status status;
  double r2;

  //  if(self->All.ComovingIntegrationOn)
  //    set_softenings();

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("Start computation of potential for all particles...\n");
    fflush(stdout);
  }

  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  MPI_Allgather(&self->NumPartQ, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  i = 0;           /* beginn with this index */
  ntotleft = ntot; /* particles left for all tasks together */

  while (ntotleft > 0) {
    for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

    /* do local particles and prepare export list */
    for (nexport = 0, ndone = 0;
         i < self->NumPartQ && nexport < self->All.BunchSizeForce - self->NTask;
         i++) {
      ndone++;

      for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;

#ifndef PMGRID
      force_treeevaluate_potential_sub(self, i, 0);
#else
      force_treeevaluate_potential_shortrange_sub(self, i, 0);
#endif

      for (j = 0; j < self->NTask; j++) {
        if (self->Exportflag[j]) {
          for (k = 0; k < 3; k++)
            self->GravDataGet[nexport].u.Pos[k] = self->Q[i].Pos[k];
#ifdef UNEQUALSOFTENINGS
          self->GravDataGet[nexport].Type = self->Q[i].Type;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
          if (P[i].Type == 0) self->GravDataGet[nexport].Soft = SphP[i].Hsml;
#endif
#endif
          self->GravDataGet[nexport].w.OldAcc = self->Q[i].OldAcc;

          self->GravDataIndexTable[nexport].Task = j;
          self->GravDataIndexTable[nexport].Index = i;
          self->GravDataIndexTable[nexport].SortIndex = nexport;

          nexport++;
          nsend_local[j]++;
        }
      }
    }

    qsort(self->GravDataIndexTable, nexport, sizeof(struct gravdata_index),
          grav_tree_compare_key);

    for (j = 0; j < nexport; j++)
      self->GravDataIn[j] =
          self->GravDataGet[self->GravDataIndexTable[j].SortIndex];

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
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* get the particles */
            MPI_Sendrecv(&self->GravDataIn[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_A,
                         &self->GravDataGet[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_A, MPI_COMM_WORLD,
                         &status);
          }
        }

        for (j = 0; j < self->NTask; j++)
          if ((j ^ ngrp) < self->NTask)
            nbuffer[j] += nsend[(j ^ ngrp) * self->NTask + j];
      }

      for (j = 0; j < nbuffer[self->ThisTask]; j++) {
#ifndef PMGRID
        force_treeevaluate_potential_sub(self, j, 1);
#else
        force_treeevaluate_potential_shortrange_sub(self, j, 1);
#endif
      }

      /* get the result */
      for (j = 0; j < self->NTask; j++) nbuffer[j] = 0;
      for (ngrp = level; ngrp < (1 << self->PTask); ngrp++) {
        maxfill = 0;
        for (j = 0; j < self->NTask; j++) {
          if ((j ^ ngrp) < self->NTask)
            if (maxfill < nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j])
              maxfill = nbuffer[j] + nsend[(j ^ ngrp) * self->NTask + j];
        }
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* send the results */
            MPI_Sendrecv(&self->GravDataResult[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_B,
                         &self->GravDataOut[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_POTENTIAL_B, MPI_COMM_WORLD,
                         &status);

            /* add the result to the particles */
            for (j = 0; j < nsend_local[recvTask]; j++) {
              place = self->GravDataIndexTable[noffset[recvTask] + j].Index;

              self->Q[place].Potential +=
                  self->GravDataOut[j + noffset[recvTask]].u.Potential;
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

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* add correction to exclude self-potential */

  // for(i = 0; i < self->NumPartQ; i++)
  //  {
  //    /* remove self-potential */
  //    self->Q[i].Potential += self->Q[i].Mass /
  //    self->All.SofteningTable[self->Q[i].Type];
  //
  //    if(self->All.ComovingIntegrationOn)
  //	if(self->All.PeriodicBoundariesOn)
  //	  self->Q[i].Potential -= 2.8372975 * pow(self->Q[i].Mass, 2.0 / 3) *
  //	    pow(self->All.Omega0 * 3 * self->All.Hubble * self->All.Hubble / (8
  //* M_PI * self->All.G), 1.0 / 3);
  //  }

  /* multiply with the gravitational constant */

  for (i = 0; i < self->NumPartQ; i++) self->Q[i].Potential *= self->All.G;

#ifdef PMGRID

#ifdef PERIODIC
  pmpotential_periodic();
#ifdef PLACEHIGHRESREGION
  i = pmpotential_nonperiodic(1);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();
    pm_setup_nonperiodic_kernel();
    i = pmpotential_nonperiodic(1); /* try again */
  }
  if (i == 1) endrun(self, 88686);
#endif
#else
  i = pmpotential_nonperiodic(0);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();
    pm_setup_nonperiodic_kernel();
    i = pmpotential_nonperiodic(0); /* try again */
  }
  if (i == 1) endrun(88687);
#ifdef PLACEHIGHRESREGION
  i = pmpotential_nonperiodic(1);
  if (i == 1) /* this is returned if a particle lied outside allowed range */
  {
    pm_init_regionsize();

    i = pmpotential_nonperiodic(1);
  }
  if (i != 0) endrun(self, 88688);
#endif
#endif

#endif

  if (self->All.ComovingIntegrationOn) {
    //#ifndef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      fac = -0.5 * self->All.Omega0 * self->All.Hubble * self->All.Hubble;

      for (i = 0; i < self->NumPartQ; i++) {
        for (k = 0, r2 = 0; k < 3; k++)
          r2 += self->Q[i].Pos[k] * self->Q[i].Pos[k];

        self->Q[i].Potential += fac * r2;
      }
      //#endif
    }
  } else {
    fac = -0.5 * self->All.OmegaLambda * self->All.Hubble * self->All.Hubble;
    if (fac != 0) {
      for (i = 0; i < self->NumPartQ; i++) {
        for (k = 0, r2 = 0; k < 3; k++)
          r2 += self->Q[i].Pos[k] * self->Q[i].Pos[k];

        self->Q[i].Potential += fac * r2;
      }
    }
  }

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("potential done.\n");
    fflush(stdout);
  }

#else
  for (i = 0; i < self->NumPartQ; i++) self->Q[i].Potential = 0;
#endif
}
