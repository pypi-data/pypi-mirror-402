#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "proto.h"
#include "ptreelib.h"

/*! \file gravtree.c
 *  \brief main driver routines for gravitational (short-range) force
 * computation
 *
 *  This file contains the code for the gravitational force computation by
 *  means of the tree algorithm. To this end, a tree force is computed for
 *  all active local particles, and particles are exported to other
 *  processors if needed, where they can receive additional force
 *  contributions. If the TreePM algorithm is enabled, the force computed
 *  will only be the short-range part.
 */

/*! This function computes the gravitational forces for all active
 *  particles.  If needed, a new tree is constructed, otherwise the
 *  dynamically updated tree is used.  Particles are only exported to other
 *  processors when really needed, thereby allowing a good use of the
 *  communication buffer.
 */
void gravity_tree(Tree *self) {
  long long ntot;
  int numnodes, nexportsum = 0;
  int i, j, iter = 0;
  int *numnodeslist, maxnumnodes, nexport, *numlist, *nrecv, *ndonelist;
  double tstart, tend, timetree = 0, timecommsumm = 0, timeimbalance = 0,
                       sumimbalance;
  double ewaldcount;
  double costtotal, ewaldtot, *costtreelist, *ewaldlist;
  double maxt, sumt, *timetreelist, *timecommlist;
  double fac, plb, plb_max, sumcomm;

#ifndef NOGRAVITY
  int *noffset, *nbuffer, *nsend, *nsend_local;
  long long ntotleft;
  int ndone, maxfill, ngrp;
  int k, place;
  int level, sendTask, recvTask;
  double ax, ay, az;
  MPI_Status status;
#endif

  /* set new softening lengths */
  if (self->All.ComovingIntegrationOn) set_softenings(self);

  /* contruct tree if needed */
  // tstart = second();
  // if(TreeReconstructFlag)
  //  {
  //    if(ThisTask == 0)
  //	 printf("Tree construction.\n");
  //
  //    force_treebuild(NumPart);
  //
  //    TreeReconstructFlag = 0;
  //
  //    if(ThisTask == 0)
  //	 printf("Tree construction done.\n");
  //  }
  // tend = second();
  // All.CPU_TreeConstruction += timediff(tstart, tend);

  costtotal = ewaldcount = 0;

  /* Note: 'NumForceUpdate' has already been determined in
   * find_next_sync_point_and_drift() */
  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  // MPI_Allgather(&self->NumForceUpdate, 1, MPI_INT, numlist, 1, MPI_INT,
  // MPI_COMM_WORLD);
  MPI_Allgather(&self->NumPart, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

#ifndef NOGRAVITY
  if (self->ThisTask == 0 && self->All.OutputInfo)
    printf("Begin tree force.\n");

#ifdef SELECTIVE_NO_GRAVITY
  for (i = 0; i < self->NumPart; i++)
    if (((1 << self->P[i].Type) & (SELECTIVE_NO_GRAVITY)))
      self->P[i].Ti_endstep = -self->P[i].Ti_endstep - 1;
#endif

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  i = 0;           /* beginn with this index */
  ntotleft = ntot; /* particles left for all tasks together */

  while (ntotleft > 0) {
    iter++;

    for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

    /* do local particles and prepare export list */
    // tstart = second();
    for (nexport = 0, ndone = 0;
         i < self->NumPart && nexport < self->All.BunchSizeForce - self->NTask;
         i++)
    // if(P[i].Ti_endstep == All.Ti_Current)
    {
      ndone++;

      for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;
#ifndef PMGRID
      costtotal += force_treeevaluate(self, i, 0, &ewaldcount);
#else
      costtotal += force_treeevaluate_shortrange(self, i, 0);
#endif
      for (j = 0; j < self->NTask; j++) {
        if (self->Exportflag[j]) {
          for (k = 0; k < 3; k++)
            self->GravDataGet[nexport].u.Pos[k] = self->P[i].Pos[k];
#ifdef UNEQUALSOFTENINGS
          self->GravDataGet[nexport].Type = self->P[i].Type;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
          if (P[i].Type == 0)
            self->GravDataGet[nexport].Soft = self->SphP[i].Hsml;
#endif
#endif
          self->GravDataGet[nexport].w.OldAcc = self->P[i].OldAcc;
          self->GravDataIndexTable[nexport].Task = j;
          self->GravDataIndexTable[nexport].Index = i;
          self->GravDataIndexTable[nexport].SortIndex = nexport;
          nexport++;
          nexportsum++;
          nsend_local[j]++;
        }
      }
    }
    // tend = second();
    // timetree += timediff(tstart, tend);

    qsort(self->GravDataIndexTable, nexport, sizeof(struct gravdata_index),
          grav_tree_compare_key);

    for (j = 0; j < nexport; j++)
      self->GravDataIn[j] =
          self->GravDataGet[self->GravDataIndexTable[j].SortIndex];

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
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* get the particles */
            MPI_Sendrecv(&self->GravDataIn[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_A,
                         &self->GravDataGet[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_A, MPI_COMM_WORLD,
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
      for (j = 0; j < nbuffer[self->ThisTask]; j++) {
#ifndef PMGRID
        costtotal += force_treeevaluate(self, j, 1, &ewaldcount);
#else
        costtotal += force_treeevaluate_shortrange(self, j, 1);
#endif
      }
      // tend = second();
      // timetree += timediff(tstart, tend);

      // tstart = second();
      MPI_Barrier(MPI_COMM_WORLD);
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
                         MPI_BYTE, recvTask, TAG_GRAV_B,
                         &self->GravDataOut[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_B, MPI_COMM_WORLD,
                         &status);

            /* add the result to the particles */
            for (j = 0; j < nsend_local[recvTask]; j++) {
              place = self->GravDataIndexTable[noffset[recvTask] + j].Index;

              for (k = 0; k < 3; k++)
                self->P[place].GravAccel[k] +=
                    self->GravDataOut[j + noffset[recvTask]].u.Acc[k];

              // self->P[place].GravCost += self->GravDataOut[j +
              // noffset[recvTask]].w.Ninteractions;
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

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* now add things for comoving integration */

  //#ifndef PERIODIC
  if (self->All.PeriodicBoundariesOn == 0) {
#ifndef PMGRID
    if (self->All.ComovingIntegrationOn) {
      fac = 0.5 * self->All.Hubble * self->All.Hubble * self->All.Omega0 /
            self->All.G;

      for (i = 0; i < self->NumPart; i++)
        // if(self->P[i].Ti_endstep == self->All.Ti_Current)
        for (j = 0; j < 3; j++)
          self->P[i].GravAccel[j] += fac * self->P[i].Pos[j];
    }
#endif
  }
  //#endif

  for (i = 0; i < self->NumPart; i++)
  // if(self->P[i].Ti_endstep == self->All.Ti_Current)
  {
#ifdef PMGRID
    ax = self->P[i].GravAccel[0] + self->P[i].GravPM[0] / self->All.G;
    ay = self->P[i].GravAccel[1] + self->P[i].GravPM[1] / self->All.G;
    az = self->P[i].GravAccel[2] + self->P[i].GravPM[2] / self->All.G;
#else
    ax = self->P[i].GravAccel[0];
    ay = self->P[i].GravAccel[1];
    az = self->P[i].GravAccel[2];
#endif
    // P[i].OldAcc = sqrt(ax * ax + ay * ay + az * az);
  }

  if (self->All.TypeOfOpeningCriterion == 1)
    self->All.ErrTolTheta =
        0; /* This will switch to the relative opening criterion for the
              following force computations */

  /*  muliply by G */
  for (i = 0; i < self->NumPart; i++)
    // if(P[i].Ti_endstep == All.Ti_Current)
    for (j = 0; j < 3; j++) self->P[i].GravAccel[j] *= self->All.G;

  /* Finally, the following factor allows a computation of a cosmological
     simulation with vacuum energy in physical coordinates */
  //#ifndef PERIODIC
  if (self->All.PeriodicBoundariesOn == 0) {
#ifndef PMGRID
    if (self->All.ComovingIntegrationOn == 0) {
      fac = self->All.OmegaLambda * self->All.Hubble * self->All.Hubble;

      for (i = 0; i < self->NumPart; i++)
        // if(self->P[i].Ti_endstep == self->All.Ti_Current)
        for (j = 0; j < 3; j++)
          self->P[i].GravAccel[j] += fac * self->P[i].Pos[j];
    }
#endif
  }
  //#endif

#ifdef SELECTIVE_NO_GRAVITY
  for (i = 0; i < self->NumPart; i++)
    if (self->P[i].Ti_endstep < 0)
      self->P[i].Ti_endstep = -self->P[i].Ti_endstep - 1;
#endif

  if (self->ThisTask == 0 && self->All.OutputInfo) printf("tree is done.\n");

#else /* gravity is switched off */

  for (i = 0; i < self->NumPart; i++)
    // if(self->P[i].Ti_endstep == self->All.Ti_Current)
    for (j = 0; j < 3; j++) self->P[i].GravAccel[j] = 0;

#endif

  /* Now the force computation is finished */

  /*  gather some diagnostic information */

  timetreelist = malloc(sizeof(double) * self->NTask);
  timecommlist = malloc(sizeof(double) * self->NTask);
  costtreelist = malloc(sizeof(double) * self->NTask);
  numnodeslist = malloc(sizeof(int) * self->NTask);
  ewaldlist = malloc(sizeof(double) * self->NTask);
  nrecv = malloc(sizeof(int) * self->NTask);

  numnodes = self->Numnodestree;

  MPI_Gather(&costtotal, 1, MPI_DOUBLE, costtreelist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&numnodes, 1, MPI_INT, numnodeslist, 1, MPI_INT, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&timetree, 1, MPI_DOUBLE, timetreelist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&timecommsumm, 1, MPI_DOUBLE, timecommlist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&self->NumPart, 1, MPI_INT, nrecv, 1, MPI_INT, 0, MPI_COMM_WORLD);
  MPI_Gather(&ewaldcount, 1, MPI_DOUBLE, ewaldlist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Reduce(&nexportsum, &nexport, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&timeimbalance, &sumimbalance, 1, MPI_DOUBLE, MPI_SUM, 0,
             MPI_COMM_WORLD);

  //  if(ThisTask == 0)
  //    {
  //      All.TotNumOfForces += ntot;
  //
  //      fprintf(FdTimings, "Step= %d  t= %g  dt= %g \n", All.NumCurrentTiStep,
  //      All.Time, All.TimeStep); fprintf(FdTimings, "Nf= %d%09d  total-Nf=
  //      %d%09d  ex-frac= %g  iter= %d\n",
  //	      (int) (ntot / 1000000000), (int) (ntot % 1000000000),
  //	      (int) (All.TotNumOfForces / 1000000000), (int) (All.TotNumOfForces
  //% 1000000000), 	      nexport / ((double) ntot), iter);
  //      /* note: on Linux, the 8-byte integer could be printed with the format
  //      identifier "%qd", but doesn't work on AIX */
  //
  //      fac = NTask / ((double) All.TotNumPart);
  //
  //      for(i = 0, maxt = timetreelist[0], sumt = 0, plb_max = 0,
  //	  maxnumnodes = 0, costtotal = 0, sumcomm = 0, ewaldtot = 0; i < NTask;
  // i++)
  //	{
  //	  costtotal += costtreelist[i];
  //
  //	  sumcomm += timecommlist[i];
  //
  //	  if(maxt < timetreelist[i])
  //	    maxt = timetreelist[i];
  //	  sumt += timetreelist[i];
  //
  //	  plb = nrecv[i] * fac;
  //
  //	  if(plb > plb_max)
  //	    plb_max = plb;
  //
  //	  if(numnodeslist[i] > maxnumnodes)
  //	    maxnumnodes = numnodeslist[i];
  //
  //	  ewaldtot += ewaldlist[i];
  //	}
  //      fprintf(FdTimings, "work-load balance: %g  max=%g avg=%g PE0=%g\n",
  //	      maxt / (sumt / NTask), maxt, sumt / NTask, timetreelist[0]);
  //      fprintf(FdTimings, "particle-load balance: %g\n", plb_max);
  //      fprintf(FdTimings, "max. nodes: %d, filled: %g\n", maxnumnodes,
  //	      maxnumnodes / (All.TreeAllocFactor * All.MaxPart));
  //      fprintf(FdTimings, "part/sec=%g | %g  ia/part=%g (%g)\n", ntot / (sumt
  //      + 1.0e-20),
  //	      ntot / (maxt * NTask), ((double) (costtotal)) / ntot, ((double)
  // ewaldtot) / ntot);
  //      fprintf(FdTimings, "\n");
  //
  //      fflush(FdTimings);
  //
  //      All.CPU_TreeWalk += sumt / NTask;
  //      All.CPU_Imbalance += sumimbalance / NTask;
  //      All.CPU_CommSum += sumcomm / NTask;
  //    }

  free(nrecv);
  free(ewaldlist);
  free(numnodeslist);
  free(costtreelist);
  free(timecommlist);
  free(timetreelist);
}

/*! This function computes the gravitational forces for all active
 *  particles.  If needed, a new tree is constructed, otherwise the
 *  dynamically updated tree is used.  Particles are only exported to other
 *  processors when really needed, thereby allowing a good use of the
 *  communication buffer.
 */
void gravity_tree_sub(Tree *self) {
  long long ntot;
  int numnodes, nexportsum = 0;
  int i, j, iter = 0;
  int *numnodeslist, maxnumnodes, nexport, *numlist, *nrecv, *ndonelist;
  double tstart, tend, timetree = 0, timecommsumm = 0, timeimbalance = 0,
                       sumimbalance;
  double ewaldcount;
  double costtotal, ewaldtot, *costtreelist, *ewaldlist;
  double maxt, sumt, *timetreelist, *timecommlist;
  double fac, plb, plb_max, sumcomm;

#ifndef NOGRAVITY
  int *noffset, *nbuffer, *nsend, *nsend_local;
  long long ntotleft;
  int ndone, maxfill, ngrp;
  int k, place;
  int level, sendTask, recvTask;
  double ax, ay, az;
  MPI_Status status;
#endif

  /* set new softening lengths */
  if (self->All.ComovingIntegrationOn) set_softenings(self);

  /* contruct tree if needed */
  // tstart = second();
  // if(TreeReconstructFlag)
  //  {
  //    if(ThisTask == 0)
  //	 printf("Tree construction.\n");
  //
  //    force_treebuild(NumPart);
  //
  //    TreeReconstructFlag = 0;
  //
  //    if(ThisTask == 0)
  //	 printf("Tree construction done.\n");
  //  }
  // tend = second();
  // All.CPU_TreeConstruction += timediff(tstart, tend);

  costtotal = ewaldcount = 0;

  /* Note: 'NumForceUpdate' has already been determined in
   * find_next_sync_point_and_drift() */
  numlist = malloc(self->NTask * sizeof(int) * self->NTask);
  // MPI_Allgather(&self->NumForceUpdate, 1, MPI_INT, numlist, 1, MPI_INT,
  // MPI_COMM_WORLD);
  MPI_Allgather(&self->NumPartQ, 1, MPI_INT, numlist, 1, MPI_INT,
                MPI_COMM_WORLD);
  for (i = 0, ntot = 0; i < self->NTask; i++) ntot += numlist[i];
  free(numlist);

#ifndef NOGRAVITY
  if (self->ThisTask == 0 && self->All.OutputInfo)
    printf("Begin tree force.\n");

#ifdef SELECTIVE_NO_GRAVITY
  for (i = 0; i < self->NumPart; i++)
    if (((1 << self->Q[i].Type) & (SELECTIVE_NO_GRAVITY)))
      self->Q[i].Ti_endstep = -self->Q[i].Ti_endstep - 1;
#endif

  noffset =
      malloc(sizeof(int) * self->NTask); /* offsets of bunches in common list */
  nbuffer = malloc(sizeof(int) * self->NTask);
  nsend_local = malloc(sizeof(int) * self->NTask);
  nsend = malloc(sizeof(int) * self->NTask * self->NTask);
  ndonelist = malloc(sizeof(int) * self->NTask);

  i = 0;           /* beginn with this index */
  ntotleft = ntot; /* particles left for all tasks together */

  while (ntotleft > 0) {
    iter++;

    for (j = 0; j < self->NTask; j++) nsend_local[j] = 0;

    /* do local particles and prepare export list */
    // tstart = second();
    for (nexport = 0, ndone = 0;
         i < self->NumPartQ && nexport < self->All.BunchSizeForce - self->NTask;
         i++)
    // if(P[i].Ti_endstep == All.Ti_Current)
    {
      ndone++;

      for (j = 0; j < self->NTask; j++) self->Exportflag[j] = 0;
#ifndef PMGRID
      costtotal += force_treeevaluate_sub(self, i, 0, &ewaldcount);
#else
      costtotal += force_treeevaluate_shortrange_sub(self, i, 0);
#endif
      for (j = 0; j < self->NTask; j++) {
        if (self->Exportflag[j]) {
          for (k = 0; k < 3; k++)
            self->GravDataGet[nexport].u.Pos[k] = self->Q[i].Pos[k];
#ifdef UNEQUALSOFTENINGS
          self->GravDataGet[nexport].Type = self->Q[i].Type;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
          if (P[i].Type == 0)
            self->GravDataGet[nexport].Soft = self->SphP[i].Hsml;
#endif
#endif
          self->GravDataGet[nexport].w.OldAcc = self->Q[i].OldAcc;
          self->GravDataIndexTable[nexport].Task = j;
          self->GravDataIndexTable[nexport].Index = i;
          self->GravDataIndexTable[nexport].SortIndex = nexport;
          nexport++;
          nexportsum++;
          nsend_local[j]++;
        }
      }
    }
    // tend = second();
    // timetree += timediff(tstart, tend);

    qsort(self->GravDataIndexTable, nexport, sizeof(struct gravdata_index),
          grav_tree_compare_key);

    for (j = 0; j < nexport; j++)
      self->GravDataIn[j] =
          self->GravDataGet[self->GravDataIndexTable[j].SortIndex];

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
        if (maxfill >= self->All.BunchSizeForce) break;

        sendTask = self->ThisTask;
        recvTask = self->ThisTask ^ ngrp;

        if (recvTask < self->NTask) {
          if (nsend[self->ThisTask * self->NTask + recvTask] > 0 ||
              nsend[recvTask * self->NTask + self->ThisTask] > 0) {
            /* get the particles */
            MPI_Sendrecv(&self->GravDataIn[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_A,
                         &self->GravDataGet[nbuffer[self->ThisTask]],
                         nsend[recvTask * self->NTask + self->ThisTask] *
                             sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_A, MPI_COMM_WORLD,
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
      for (j = 0; j < nbuffer[self->ThisTask]; j++) {
#ifndef PMGRID
        costtotal += force_treeevaluate_sub(self, j, 1, &ewaldcount);
#else
        costtotal += force_treeevaluate_shortrange_sub(self, j, 1);
#endif
      }
      // tend = second();
      // timetree += timediff(tstart, tend);

      // tstart = second();
      MPI_Barrier(MPI_COMM_WORLD);
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
                         MPI_BYTE, recvTask, TAG_GRAV_B,
                         &self->GravDataOut[noffset[recvTask]],
                         nsend_local[recvTask] * sizeof(struct gravdata_in),
                         MPI_BYTE, recvTask, TAG_GRAV_B, MPI_COMM_WORLD,
                         &status);

            /* add the result to the particles */
            for (j = 0; j < nsend_local[recvTask]; j++) {
              place = self->GravDataIndexTable[noffset[recvTask] + j].Index;

              for (k = 0; k < 3; k++)
                self->Q[place].GravAccel[k] +=
                    self->GravDataOut[j + noffset[recvTask]].u.Acc[k];

              // self->Q[place].GravCost += self->GravDataOut[j +
              // noffset[recvTask]].w.Ninteractions;
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

  free(ndonelist);
  free(nsend);
  free(nsend_local);
  free(nbuffer);
  free(noffset);

  /* now add things for comoving integration */

  //#ifndef PERIODIC
  if (self->All.PeriodicBoundariesOn == 0) {
#ifndef PMGRID
    if (self->All.ComovingIntegrationOn) {
      fac = 0.5 * self->All.Hubble * self->All.Hubble * self->All.Omega0 /
            self->All.G;

      for (i = 0; i < self->NumPartQ; i++)
        // if(self->Q[i].Ti_endstep == self->All.Ti_Current)
        for (j = 0; j < 3; j++)
          self->Q[i].GravAccel[j] += fac * self->Q[i].Pos[j];
    }
#endif
  }
  //#endif

  for (i = 0; i < self->NumPartQ; i++)
  // if(self->Q[i].Ti_endstep == self->All.Ti_Current)
  {
#ifdef PMGRID
    ax = self->Q[i].GravAccel[0] + self->Q[i].GravPM[0] / self->All.G;
    ay = self->Q[i].GravAccel[1] + self->Q[i].GravPM[1] / self->All.G;
    az = self->Q[i].GravAccel[2] + self->Q[i].GravPM[2] / self->All.G;
#else
    ax = self->Q[i].GravAccel[0];
    ay = self->Q[i].GravAccel[1];
    az = self->Q[i].GravAccel[2];
#endif
    // P[i].OldAcc = sqrt(ax * ax + ay * ay + az * az);
  }

  if (self->All.TypeOfOpeningCriterion == 1)
    self->All.ErrTolTheta =
        0; /* This will switch to the relative opening criterion for the
              following force computations */

  /*  muliply by G */
  for (i = 0; i < self->NumPartQ; i++)
    // if(P[i].Ti_endstep == All.Ti_Current)
    for (j = 0; j < 3; j++) self->Q[i].GravAccel[j] *= self->All.G;

  /* Finally, the following factor allows a computation of a cosmological
     simulation with vacuum energy in physical coordinates */
  //#ifndef PERIODIC
  if (self->All.PeriodicBoundariesOn == 0) {
#ifndef PMGRID
    if (self->All.ComovingIntegrationOn == 0) {
      fac = self->All.OmegaLambda * self->All.Hubble * self->All.Hubble;

      for (i = 0; i < self->NumPartQ; i++)
        // if(self->Q[i].Ti_endstep == self->All.Ti_Current)
        for (j = 0; j < 3; j++)
          self->Q[i].GravAccel[j] += fac * self->Q[i].Pos[j];
    }
#endif
  }
  //#endif

#ifdef SELECTIVE_NO_GRAVITY
  for (i = 0; i < self->NumPartQ; i++)
    if (self->Q[i].Ti_endstep < 0)
      self->Q[i].Ti_endstep = -self->Q[i].Ti_endstep - 1;
#endif

  if (self->ThisTask == 0 && self->All.OutputInfo) printf("tree is done.\n");

#else /* gravity is switched off */

  for (i = 0; i < self->NumPartQ; i++)
    // if(self->Q[i].Ti_endstep == self->All.Ti_Current)
    for (j = 0; j < 3; j++) self->Q[i].GravAccel[j] = 0;

#endif

  /* Now the force computation is finished */

  /*  gather some diagnostic information */

  timetreelist = malloc(sizeof(double) * self->NTask);
  timecommlist = malloc(sizeof(double) * self->NTask);
  costtreelist = malloc(sizeof(double) * self->NTask);
  numnodeslist = malloc(sizeof(int) * self->NTask);
  ewaldlist = malloc(sizeof(double) * self->NTask);
  nrecv = malloc(sizeof(int) * self->NTask);

  numnodes = self->Numnodestree;

  MPI_Gather(&costtotal, 1, MPI_DOUBLE, costtreelist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&numnodes, 1, MPI_INT, numnodeslist, 1, MPI_INT, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&timetree, 1, MPI_DOUBLE, timetreelist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&timecommsumm, 1, MPI_DOUBLE, timecommlist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Gather(&self->NumPartQ, 1, MPI_INT, nrecv, 1, MPI_INT, 0, MPI_COMM_WORLD);
  MPI_Gather(&ewaldcount, 1, MPI_DOUBLE, ewaldlist, 1, MPI_DOUBLE, 0,
             MPI_COMM_WORLD);
  MPI_Reduce(&nexportsum, &nexport, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&timeimbalance, &sumimbalance, 1, MPI_DOUBLE, MPI_SUM, 0,
             MPI_COMM_WORLD);

  //  if(ThisTask == 0)
  //    {
  //      All.TotNumOfForces += ntot;
  //
  //      fprintf(FdTimings, "Step= %d  t= %g  dt= %g \n", All.NumCurrentTiStep,
  //      All.Time, All.TimeStep); fprintf(FdTimings, "Nf= %d%09d  total-Nf=
  //      %d%09d  ex-frac= %g  iter= %d\n",
  //	      (int) (ntot / 1000000000), (int) (ntot % 1000000000),
  //	      (int) (All.TotNumOfForces / 1000000000), (int) (All.TotNumOfForces
  //% 1000000000), 	      nexport / ((double) ntot), iter);
  //      /* note: on Linux, the 8-byte integer could be printed with the format
  //      identifier "%qd", but doesn't work on AIX */
  //
  //      fac = NTask / ((double) All.TotNumPart);
  //
  //      for(i = 0, maxt = timetreelist[0], sumt = 0, plb_max = 0,
  //	  maxnumnodes = 0, costtotal = 0, sumcomm = 0, ewaldtot = 0; i < NTask;
  // i++)
  //	{
  //	  costtotal += costtreelist[i];
  //
  //	  sumcomm += timecommlist[i];
  //
  //	  if(maxt < timetreelist[i])
  //	    maxt = timetreelist[i];
  //	  sumt += timetreelist[i];
  //
  //	  plb = nrecv[i] * fac;
  //
  //	  if(plb > plb_max)
  //	    plb_max = plb;
  //
  //	  if(numnodeslist[i] > maxnumnodes)
  //	    maxnumnodes = numnodeslist[i];
  //
  //	  ewaldtot += ewaldlist[i];
  //	}
  //      fprintf(FdTimings, "work-load balance: %g  max=%g avg=%g PE0=%g\n",
  //	      maxt / (sumt / NTask), maxt, sumt / NTask, timetreelist[0]);
  //      fprintf(FdTimings, "particle-load balance: %g\n", plb_max);
  //      fprintf(FdTimings, "max. nodes: %d, filled: %g\n", maxnumnodes,
  //	      maxnumnodes / (All.TreeAllocFactor * All.MaxPart));
  //      fprintf(FdTimings, "part/sec=%g | %g  ia/part=%g (%g)\n", ntot / (sumt
  //      + 1.0e-20),
  //	      ntot / (maxt * NTask), ((double) (costtotal)) / ntot, ((double)
  // ewaldtot) / ntot);
  //      fprintf(FdTimings, "\n");
  //
  //      fflush(FdTimings);
  //
  //      All.CPU_TreeWalk += sumt / NTask;
  //      All.CPU_Imbalance += sumimbalance / NTask;
  //      All.CPU_CommSum += sumcomm / NTask;
  //    }

  free(nrecv);
  free(ewaldlist);
  free(numnodeslist);
  free(costtreelist);
  free(timecommlist);
  free(timetreelist);
}

/*! This function sets the (comoving) softening length of all particle
 *  types in the table All.SofteningTable[...].  We check that the physical
 *  softening length is bounded by the Softening-MaxPhys values.
 */
void set_softenings(Tree *self) {
  int i;

  //  if(self->All.ComovingIntegrationOn)
  //    {
  //      if(self->All.SofteningGas * self->All.Time >
  //      self->All.SofteningGasMaxPhys)
  //        self->All.SofteningTable[0] = self->All.SofteningGasMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[0] = self->All.SofteningGas;
  //
  //      if(self->All.SofteningHalo * self->All.Time >
  //      self->All.SofteningHaloMaxPhys)
  //        self->All.SofteningTable[1] = self->All.SofteningHaloMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[1] = self->All.SofteningHalo;
  //
  //      if(self->All.SofteningDisk * self->All.Time >
  //      self->All.SofteningDiskMaxPhys)
  //        self->All.SofteningTable[2] = self->All.SofteningDiskMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[2] = self->All.SofteningDisk;
  //
  //      if(self->All.SofteningBulge * self->All.Time >
  //      self->All.SofteningBulgeMaxPhys)
  //        self->All.SofteningTable[3] = self->All.SofteningBulgeMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[3] = self->All.SofteningBulge;
  //
  //      if(self->All.SofteningStars * self->All.Time >
  //      self->All.SofteningStarsMaxPhys)
  //        self->All.SofteningTable[4] = self->All.SofteningStarsMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[4] = self->All.SofteningStars;
  //
  //      if(self->All.SofteningBndry * self->All.Time >
  //      self->All.SofteningBndryMaxPhys)
  //        self->All.SofteningTable[5] = self->All.SofteningBndryMaxPhys /
  //        self->All.Time;
  //      else
  //        self->All.SofteningTable[5] = self->All.SofteningBndry;
  //    }
  //  else
  //    {
  //      self->All.SofteningTable[0] = self->All.SofteningGas;
  //      self->All.SofteningTable[1] = self->All.SofteningHalo;
  //      self->All.SofteningTable[2] = self->All.SofteningDisk;
  //      self->All.SofteningTable[3] = self->All.SofteningBulge;
  //      self->All.SofteningTable[4] = self->All.SofteningStars;
  //      self->All.SofteningTable[5] = self->All.SofteningBndry;
  //    }
  //
  //  for(i = 0; i < 6; i++)
  //    self->All.ForceSoftening[i] = 2.8 * self->All.SofteningTable[i];
  //
  //  self->All.MinGasHsml = self->All.MinGasHsmlFractional *
  //  self->All.ForceSoftening[0];
}

/*! This function is used as a comparison kernel in a sort routine. It is
 *  used to group particles in the communication buffer that are going to
 *  be sent to the same CPU.
 */
int grav_tree_compare_key(const void *a, const void *b) {
  if (((struct gravdata_index *)a)->Task < (((struct gravdata_index *)b)->Task))
    return -1;

  if (((struct gravdata_index *)a)->Task > (((struct gravdata_index *)b)->Task))
    return +1;

  return 0;
}
