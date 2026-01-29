#include <Python.h>
#include <math.h>
#include <mpi.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "allvars.h"
#include "proto.h"
#include "endrun.h"
#include "ptreelib.h"

void domain_allocate(Tree *self) {
  self->TopNodes = malloc(MAXTOPNODES * sizeof(struct topnode_data));
  self->DomainWork = malloc(MAXTOPNODES * sizeof(double));
  self->DomainCount = malloc(MAXTOPNODES * sizeof(int));
  self->DomainCountSph = malloc(MAXTOPNODES * sizeof(int));
  self->DomainTask = malloc(MAXTOPNODES * sizeof(int));
  self->DomainNodeIndex = malloc(MAXTOPNODES * sizeof(int));
  self->DomainTreeNodeLen = malloc(MAXTOPNODES * sizeof(FLOAT));
  self->DomainHmax = malloc(MAXTOPNODES * sizeof(FLOAT));
  self->DomainMoment = malloc(MAXTOPNODES * sizeof(struct DomainNODE));

  self->DomainStartList = malloc(self->NTask * sizeof(int));
  self->DomainEndList = malloc(self->NTask * sizeof(int));

  self->DomainPartBuf = (struct particle_data *)self->CommBuffer;
  self->DomainSphBuf = (struct sph_particle_data *)(self->DomainPartBuf +
                                                    self->All.BunchSizeDomain);
  self->DomainKeyBuf =
      (peanokey *)(self->DomainSphBuf + self->All.BunchSizeDomain);

  /* yr */
  self->DomainIdProc =
      malloc(self->All.MaxPart * sizeof(struct particle_IdProc));
}

void domain_deallocate(Tree *self) {
  free(self->TopNodes);
  free(self->DomainWork);
  free(self->DomainCount);
  free(self->DomainCountSph);
  free(self->DomainTask);
  free(self->DomainNodeIndex);
  free(self->DomainTreeNodeLen);
  free(self->DomainHmax);
  free(self->DomainMoment);

  free(self->DomainStartList);
  free(self->DomainEndList);

  // free(self->DomainKeyBuf);			/* Here, I do not know how do
  // deallocate
  // */ free(self->DomainSphBuf); free(self->DomainPartBuf);

  free(self->DomainIdProc);
}

/*! This is the main routine for the domain decomposition.  It acts as a
 *  driver routine that allocates various temporary buffers, maps the
 *  particles back onto the periodic box if needed, and then does the
 *  domain decomposition, and a final Peano-Hilbert order of all particles
 *  as a tuning measure.
 */
void domain_Decomposition(Tree *self) {
  double t0, t1;

#ifdef PMGRID
//  if(All.PM_Ti_endstep == All.Ti_Current)
//    {
//      All.NumForcesSinceLastDomainDecomp = 1 + All.TotNumPart *
//      All.TreeDomainUpdateFrequency;
//      /* to make sure that we do a domain decomposition before the PM-force is
//      evaluated.
//         this is needed to make sure that the particles are wrapped into the
//         box */
//    }
#endif

  //  /* Check whether it is really time for a new domain decomposition */
  //  if(All.NumForcesSinceLastDomainDecomp > All.TotNumPart *
  //  All.TreeDomainUpdateFrequency)
  //    {
  //      t0 = second();

  //#ifdef PERIODIC
  if (self->All.PeriodicBoundariesOn)
    do_box_wrapping(self); /* map the particles back onto the box */
                           //#endif
                           //      All.NumForcesSinceLastDomainDecomp = 0;
  //      TreeReconstructFlag = 1;	/* ensures that new tree will be
  //      constructed */

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("domain decomposition... \n");
    fflush(stdout);
  }

  self->Key = malloc(sizeof(peanokey) * self->All.MaxPart);
  self->KeySorted = malloc(sizeof(peanokey) * self->All.MaxPart);

  self->toGo = malloc(sizeof(int) * self->NTask * self->NTask);
  self->toGoSph = malloc(sizeof(int) * self->NTask * self->NTask);
  self->local_toGo = malloc(sizeof(int) * self->NTask);
  self->local_toGoSph = malloc(sizeof(int) * self->NTask);
  self->list_NumPart = malloc(sizeof(int) * self->NTask);
  self->list_N_gas = malloc(sizeof(int) * self->NTask);
  self->list_load = malloc(sizeof(int) * self->NTask);
  self->list_loadsph = malloc(sizeof(int) * self->NTask);
  self->list_work = malloc(sizeof(double) * self->NTask);

  MPI_Allgather(&self->NumPart, 1, MPI_INT, self->list_NumPart, 1, MPI_INT,
                MPI_COMM_WORLD);
  MPI_Allgather(&self->N_gas, 1, MPI_INT, self->list_N_gas, 1, MPI_INT,
                MPI_COMM_WORLD);

  self->maxload = self->All.MaxPart * REDUC_FAC;
  self->maxloadsph = self->All.MaxPartSph * REDUC_FAC;

  /* yr */
  self->NSend = 0;
  self->NRecv = 0;

  domain_decompose(self);

  free(self->list_work);
  free(self->list_loadsph);
  free(self->list_load);
  free(self->list_N_gas);
  free(self->list_NumPart);
  free(self->local_toGoSph);
  free(self->local_toGo);
  free(self->toGoSph);
  free(self->toGo);

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("domain decomposition done. \n");
    fflush(stdout);
  }

  // t1 = second();
  // All.CPU_Domain += timediff(t0, t1);

  //#ifdef PEANOHILBERT
  // t0 = second();
  if (self->All.PeanoHilbertOrder) peano_hilbert_order(self);
  // t1 = second();
  // All.CPU_Peano += timediff(t0, t1);
  //#endif

  free(self->KeySorted);
  free(self->Key);
  //    }
}

/*! This function carries out the actual domain decomposition for all
 *  particle types. It will try to balance the work-load for each domain,
 *  as estimated based on the P[i]-GravCost values.  The decomposition will
 *  respect the maximum allowed memory-imbalance given by the value of
 *  PartAllocFactor.
 */
void domain_decompose(Tree *self) {
  int i, j, status;
  int ngrp, task, partner, sendcount, recvcount;
  long long sumtogo, sumload;
  int maxload, *temp;
  double sumwork, maxwork;

  for (i = 0; i < 6; i++) self->NtypeLocal[i] = 0;

  for (i = 0; i < self->NumPart; i++) self->NtypeLocal[self->P[i].Type]++;

  /* because Ntype[] is of type `long long', we cannot do a simple
   * MPI_Allreduce() to sum the total particle numbers
   */
  temp = malloc(self->NTask * 6 * sizeof(int));
  MPI_Allgather(self->NtypeLocal, 6, MPI_INT, temp, 6, MPI_INT, MPI_COMM_WORLD);
  for (i = 0; i < 6; i++) {
    self->Ntype[i] = 0;
    for (j = 0; j < self->NTask; j++) self->Ntype[i] += temp[j * 6 + i];
  }
  free(temp);

#ifndef UNEQUALSOFTENINGS
  for (i = 0; i < 6; i++)
    if (self->Ntype[i] > 0) break;

  for (ngrp = i + 1; ngrp < 6; ngrp++) {
    if (self->Ntype[ngrp] > 0)
      if (self->All.SofteningTable[ngrp] != self->All.SofteningTable[i]) {
        if (self->ThisTask == 0) {
          fprintf(stdout,
                  "Code was not compiled with UNEQUALSOFTENINGS, but some of "
                  "the\n");
          fprintf(stdout, "softening lengths are unequal nevertheless.\n");
          fprintf(stdout, "This is not allowed.\n");
        }
        endrun(self, 0);
      }
  }
#endif

  /* determine global dimensions of domain grid */
  domain_findExtent(self);

  domain_determineTopTree(self);

  /* determine cost distribution in domain grid */
  domain_sumCost(self);

  /* find the split of the domain grid recursively */
  status = domain_findSplit(self, 0, self->NTask, 0, self->NTopleaves - 1);
  if (status != 0) {
    if (self->ThisTask == 0)
      printf(
          "\nNo domain decomposition that stays within memory bounds is "
          "possible.\n");
    endrun(self, 0);
  }

  /* now try to improve the work-load balance of the split */
  domain_shiftSplit(self);

  self->DomainMyStart = self->DomainStartList[self->ThisTask];
  self->DomainMyLast = self->DomainEndList[self->ThisTask];

  if (self->ThisTask == 0) {
    sumload = maxload = 0;
    sumwork = maxwork = 0;
    for (i = 0; i < self->NTask; i++) {
      sumload += self->list_load[i];
      sumwork += self->list_work[i];

      if (self->list_load[i] > maxload) maxload = self->list_load[i];

      if (self->list_work[i] > maxwork) maxwork = self->list_work[i];
    }

    // printf("work-load balance=%g   memory-balance=%g\n",
    //	     maxwork / (sumwork / self->NTask), maxload / (((double) sumload) /
    // self->NTask));
  }

  /* determine for each cpu how many particles have to be shifted to other cpus
   */
  domain_countToGo(self);

  for (i = 0, sumtogo = 0; i < self->NTask * self->NTask; i++)
    sumtogo += self->toGo[i];

  while (sumtogo > 0) {
    if (self->ThisTask == 0 && self->All.OutputInfo) {
      printf("exchange of %d%09d particles\n", (int)(sumtogo / 1000000000),
             (int)(sumtogo % 1000000000));
      fflush(stdout);
    }

    for (ngrp = 1; ngrp < (1 << self->PTask); ngrp++) {
      for (task = 0; task < self->NTask; task++) {
        partner = task ^ ngrp;

        if (partner < self->NTask && task < partner) {
          /* treat SPH separately */
          if (self->All.TotN_gas > 0) {

            domain_findExchangeNumbers(self, task, partner, 1, &sendcount,
                                       &recvcount);

            self->list_NumPart[task] += recvcount - sendcount;
            self->list_NumPart[partner] -= recvcount - sendcount;
            self->list_N_gas[task] += recvcount - sendcount;
            self->list_N_gas[partner] -= recvcount - sendcount;

            self->toGo[task * self->NTask + partner] -= sendcount;
            self->toGo[partner * self->NTask + task] -= recvcount;
            self->toGoSph[task * self->NTask + partner] -= sendcount;
            self->toGoSph[partner * self->NTask + task] -= recvcount;

            if (task == self->ThisTask) /* actually carry out the exchange */
              domain_exchangeParticles(self, partner, 1, sendcount, recvcount);
            if (partner == self->ThisTask)
              domain_exchangeParticles(self, task, 1, recvcount, sendcount);
          }

          domain_findExchangeNumbers(self, task, partner, 0, &sendcount,
                                     &recvcount);

          self->list_NumPart[task] += recvcount - sendcount;
          self->list_NumPart[partner] -= recvcount - sendcount;

          self->toGo[task * self->NTask + partner] -= sendcount;
          self->toGo[partner * self->NTask + task] -= recvcount;

          if (task == self->ThisTask) /* actually carry out the exchange */
            domain_exchangeParticles(self, partner, 0, sendcount, recvcount);
          if (partner == self->ThisTask)
            domain_exchangeParticles(self, task, 0, recvcount, sendcount);
        }
      }
    }

    for (i = 0, sumtogo = 0; i < self->NTask * self->NTask; i++)
      sumtogo += self->toGo[i];
  }
}

/*! This function tries to find a split point in a range of cells in the
 *  domain-grid.  The range of cells starts at 'first', and ends at 'last'
 *  (inclusively). The number of cpus that holds the range is 'ncpu', with
 *  the first cpu given by 'cpustart'. If more than 2 cpus are to be split,
 *  the function calls itself recursively. The division tries to achieve a
 *  best particle-load balance under the constraint that 'maxload' and
 *  'maxloadsph' may not be exceeded, and that each cpu holds at least one
 *  cell from the domaingrid. If such a decomposition cannot be achieved, a
 *  non-zero error code is returned.
 *
 *  After successful completion, DomainMyStart[] and DomainMyLast[] contain
 *  the first and last cell of the domaingrid assigned to the local task
 *  for the given type. Also, DomainTask[] contains for each cell the task
 *  it was assigned to.
 */
int domain_findSplit(Tree *self, int cpustart, int ncpu, int first, int last) {
  int i, split, ok_left, ok_right;
  long long load, sphload, load_leftOfSplit, sphload_leftOfSplit;
  int ncpu_leftOfSplit;
  double maxAvgLoad_CurrentSplit, maxAvgLoad_NewSplit;

  ncpu_leftOfSplit = ncpu / 2;

  for (i = first, load = 0, sphload = 0; i <= last; i++) {
    load += self->DomainCount[i];
    sphload += self->DomainCountSph[i];
  }

  split = first + ncpu_leftOfSplit;

  for (i = first, load_leftOfSplit = sphload_leftOfSplit = 0; i < split; i++) {
    load_leftOfSplit += self->DomainCount[i];
    sphload_leftOfSplit += self->DomainCountSph[i];
  }

  /* find the best split point in terms of work-load balance */

  while (split < last - (ncpu - ncpu_leftOfSplit - 1) && split > 0) {
    maxAvgLoad_CurrentSplit =
        dmax(load_leftOfSplit / ncpu_leftOfSplit,
             (load - load_leftOfSplit) / (ncpu - ncpu_leftOfSplit));

    maxAvgLoad_NewSplit =
        dmax((load_leftOfSplit + self->DomainCount[split]) / ncpu_leftOfSplit,
             (load - load_leftOfSplit - self->DomainCount[split]) /
                 (ncpu - ncpu_leftOfSplit));

    if (maxAvgLoad_NewSplit <= maxAvgLoad_CurrentSplit) {
      load_leftOfSplit += self->DomainCount[split];
      sphload_leftOfSplit += self->DomainCountSph[split];
      split++;
    } else
      break;
  }

  /* we will now have to check whether this solution is possible given the
   * restrictions on the maximum load */

  for (i = first, load_leftOfSplit = 0, sphload_leftOfSplit = 0; i < split;
       i++) {
    load_leftOfSplit += self->DomainCount[i];
    sphload_leftOfSplit += self->DomainCountSph[i];
  }

  if (load_leftOfSplit > self->maxload * ncpu_leftOfSplit ||
      (load - load_leftOfSplit) > self->maxload * (ncpu - ncpu_leftOfSplit)) {
    /* we did not find a viable split */
    return -1;
  }

  if (sphload_leftOfSplit > self->maxloadsph * ncpu_leftOfSplit ||
      (sphload - sphload_leftOfSplit) >
          self->maxloadsph * (ncpu - ncpu_leftOfSplit)) {
    /* we did not find a viable split */
    return -1;
  }

  if (ncpu_leftOfSplit >= 2)
    ok_left =
        domain_findSplit(self, cpustart, ncpu_leftOfSplit, first, split - 1);
  else
    ok_left = 0;

  if ((ncpu - ncpu_leftOfSplit) >= 2)
    ok_right = domain_findSplit(self, cpustart + ncpu_leftOfSplit,
                                ncpu - ncpu_leftOfSplit, split, last);
  else
    ok_right = 0;

  if (ok_left == 0 && ok_right == 0) {
    /* found a viable split */

    if (ncpu_leftOfSplit == 1) {
      for (i = first; i < split; i++) self->DomainTask[i] = cpustart;

      self->list_load[cpustart] = load_leftOfSplit;
      self->list_loadsph[cpustart] = sphload_leftOfSplit;
      self->DomainStartList[cpustart] = first;
      self->DomainEndList[cpustart] = split - 1;
    }

    if ((ncpu - ncpu_leftOfSplit) == 1) {
      for (i = split; i <= last; i++)
        self->DomainTask[i] = cpustart + ncpu_leftOfSplit;

      self->list_load[cpustart + ncpu_leftOfSplit] = load - load_leftOfSplit;
      self->list_loadsph[cpustart + ncpu_leftOfSplit] =
          sphload - sphload_leftOfSplit;
      self->DomainStartList[cpustart + ncpu_leftOfSplit] = split;
      self->DomainEndList[cpustart + ncpu_leftOfSplit] = last;
    }

    return 0;
  }

  /* we did not find a viable split */
  return -1;
}

/*! This function tries to improve the domain decomposition found by
 *  domain_findSplit() with respect to work-load balance.  To this end, the
 *  boundaries in the existing domain-split solution (which was found by
 *  trying to balance the particle load) are shifted as long as this leads
 *  to better work-load while still remaining within the allowed
 *  memory-imbalance constraints.
 */
void domain_shiftSplit(Tree *self) {
  int i, task, iter = 0, moved;
  double maxw, newmaxw;

  for (task = 0; task < self->NTask; task++) self->list_work[task] = 0;

  for (i = 0; i < self->NTopleaves; i++)
    self->list_work[self->DomainTask[i]] += self->DomainWork[i];

  do {
    for (task = 0, moved = 0; task < self->NTask - 1; task++) {
      maxw = dmax(self->list_work[task], self->list_work[task + 1]);

      if (self->list_work[task] < self->list_work[task + 1]) {
        newmaxw = dmax(self->list_work[task] +
                           self->DomainWork[self->DomainStartList[task + 1]],
                       self->list_work[task + 1] -
                           self->DomainWork[self->DomainStartList[task + 1]]);
        if (newmaxw <= maxw) {
          if (self->list_load[task] +
                  self->DomainCount[self->DomainStartList[task + 1]] <=
              self->maxload) {
            if (self->list_loadsph[task] +
                    self->DomainCountSph[self->DomainStartList[task + 1]] >
                self->maxloadsph)
              continue;

            /* ok, we can move one domain cell from right to left */
            self->list_work[task] +=
                self->DomainWork[self->DomainStartList[task + 1]];
            self->list_load[task] +=
                self->DomainCount[self->DomainStartList[task + 1]];
            self->list_loadsph[task] +=
                self->DomainCountSph[self->DomainStartList[task + 1]];
            self->list_work[task + 1] -=
                self->DomainWork[self->DomainStartList[task + 1]];
            self->list_load[task + 1] -=
                self->DomainCount[self->DomainStartList[task + 1]];
            self->list_loadsph[task + 1] -=
                self->DomainCountSph[self->DomainStartList[task + 1]];

            self->DomainTask[self->DomainStartList[task + 1]] = task;
            self->DomainStartList[task + 1] += 1;
            self->DomainEndList[task] += 1;

            moved++;
          }
        }
      } else {
        newmaxw = dmax(
            self->list_work[task] - self->DomainWork[self->DomainEndList[task]],
            self->list_work[task + 1] +
                self->DomainWork[self->DomainEndList[task]]);
        if (newmaxw <= maxw) {
          if (self->list_load[task + 1] +
                  self->DomainCount[self->DomainEndList[task]] <=
              self->maxload) {
            if (self->list_loadsph[task + 1] +
                    self->DomainCountSph[self->DomainEndList[task]] >
                self->maxloadsph)
              continue;

            /* ok, we can move one domain cell from left to right */
            self->list_work[task] -=
                self->DomainWork[self->DomainEndList[task]];
            self->list_load[task] -=
                self->DomainCount[self->DomainEndList[task]];
            self->list_loadsph[task] -=
                self->DomainCountSph[self->DomainEndList[task]];
            self->list_work[task + 1] +=
                self->DomainWork[self->DomainEndList[task]];
            self->list_load[task + 1] +=
                self->DomainCount[self->DomainEndList[task]];
            self->list_loadsph[task + 1] +=
                self->DomainCountSph[self->DomainEndList[task]];

            self->DomainTask[self->DomainEndList[task]] = task + 1;
            self->DomainEndList[task] -= 1;
            self->DomainStartList[task + 1] -= 1;

            moved++;
          }
        }
      }
    }

    iter++;
  } while (moved > 0 && iter < 10 * self->NTopleaves);
}

/*! This function counts how many particles have to be exchanged between
 *  two CPUs according to the domain split. If the CPUs are already quite
 *  full and hold data from other CPUs as well, not all the particles may
 *  be exchanged at once. In this case the communication phase has to be
 *  repeated, until enough of the third-party particles have been moved
 *  away such that the decomposition can be completed.
 */
void domain_findExchangeNumbers(Tree *self, int task, int partner, int sphflag,
                                int *send, int *recv) {
  int numpartA, numpartsphA, ntobesentA, maxsendA, maxsendA_old;
  int numpartB, numpartsphB, ntobesentB, maxsendB, maxsendB_old;

  numpartA = self->list_NumPart[task];
  numpartsphA = self->list_N_gas[task];

  numpartB = self->list_NumPart[partner];
  numpartsphB = self->list_N_gas[partner];

  if (sphflag == 1) {
    ntobesentA = self->toGoSph[task * self->NTask + partner];
    ntobesentB = self->toGoSph[partner * self->NTask + task];
  } else {
    ntobesentA = self->toGo[task * self->NTask + partner] -
                 self->toGoSph[task * self->NTask + partner];
    ntobesentB = self->toGo[partner * self->NTask + task] -
                 self->toGoSph[partner * self->NTask + task];
  }

  maxsendA = imin(ntobesentA, self->All.BunchSizeDomain);
  maxsendB = imin(ntobesentB, self->All.BunchSizeDomain);

  do {
    maxsendA_old = maxsendA;
    maxsendB_old = maxsendB;

    maxsendA = imin(self->All.MaxPart - numpartB + maxsendB, maxsendA);
    maxsendB = imin(self->All.MaxPart - numpartA + maxsendA, maxsendB);
  } while ((maxsendA != maxsendA_old) || (maxsendB != maxsendB_old));

  /* now make also sure that there is enough space for SPH particeles */
  if (sphflag == 1) {
    do {
      maxsendA_old = maxsendA;
      maxsendB_old = maxsendB;

      maxsendA = imin(self->All.MaxPartSph - numpartsphB + maxsendB, maxsendA);
      maxsendB = imin(self->All.MaxPartSph - numpartsphA + maxsendA, maxsendB);
    } while ((maxsendA != maxsendA_old) || (maxsendB != maxsendB_old));
  }

  *send = maxsendA;
  *recv = maxsendB;
}

/*! This function exchanges particles between two CPUs according to the
 *  domain split. In doing this, the memory boundaries which may restrict
 *  the exhange process are observed.
 */
void domain_exchangeParticles(Tree *self, int partner, int sphflag,
                              int send_count, int recv_count) {
  int i, no, n, count, rep;
  MPI_Status status;

  for (n = 0, count = 0; count < send_count && n < self->NumPart; n++) {
    if (sphflag) {
      if (self->P[n].Type != 0) continue;
    } else {
      if (self->P[n].Type == 0) continue;
    }

    no = 0;

    while (self->TopNodes[no].Daughter >= 0)
      no = self->TopNodes[no].Daughter +
           (self->Key[n] - self->TopNodes[no].StartKey) /
               (self->TopNodes[no].Size / 8);

    no = self->TopNodes[no].Leaf;

    if (self->DomainTask[no] == partner) {
      if (sphflag) /* special reorder routine for SPH particles (need to stay at
                      beginning) */
      {
        self->DomainPartBuf[count] =
            self->P[n]; /* copy particle and collect in contiguous memory */
        self->DomainKeyBuf[count] = self->Key[n];
        self->DomainSphBuf[count] = self->SphP[n];

        /* yr */
        self->DomainIdProc[self->NSend].ID = self->P[n].ID;
        self->DomainIdProc[self->NSend].Proc = partner;
        self->NSend++;

        self->P[n] = self->P[self->N_gas - 1];
        self->P[self->N_gas - 1] = self->P[self->NumPart - 1];

        self->Key[n] = self->Key[self->N_gas - 1];
        self->Key[self->N_gas - 1] = self->Key[self->NumPart - 1];

        self->SphP[n] = self->SphP[self->N_gas - 1];

        self->N_gas--;
      } else {
        self->DomainPartBuf[count] =
            self->P[n]; /* copy particle and collect in contiguous memory */
        self->DomainKeyBuf[count] = self->Key[n];

        /* yr */
        self->DomainIdProc[self->NSend].ID = self->P[n].ID;
        self->DomainIdProc[self->NSend].Proc = partner;
        self->NSend++;

        self->P[n] = self->P[self->NumPart - 1];
        self->Key[n] = self->Key[self->NumPart - 1];
      }

      count++;
      self->NumPart--;
      n--;
    }
  }

  if (count != send_count) {
    printf("Houston, we got a problem...\n");
    printf("ThisTask=%d count=%d send_count=%d\n", self->ThisTask, count,
           send_count);
    endrun(self, 88);
  }

  /* transmit */

  for (rep = 0; rep < 2; rep++) {
    if ((rep == 0 && self->ThisTask < partner) ||
        (rep == 1 && self->ThisTask > partner)) {
      if (send_count > 0) {
        MPI_Ssend(&self->DomainPartBuf[0],
                  send_count * sizeof(struct particle_data), MPI_BYTE, partner,
                  TAG_PDATA, MPI_COMM_WORLD);

        MPI_Ssend(&self->DomainKeyBuf[0], send_count * sizeof(peanokey),
                  MPI_BYTE, partner, TAG_KEY, MPI_COMM_WORLD);

        if (sphflag)
          MPI_Ssend(&self->DomainSphBuf[0],
                    send_count * sizeof(struct sph_particle_data), MPI_BYTE,
                    partner, TAG_SPHDATA, MPI_COMM_WORLD);
      }
    }

    if ((rep == 1 && self->ThisTask < partner) ||
        (rep == 0 && self->ThisTask > partner)) {
      if (recv_count > 0) {
        if (sphflag) {
          if ((self->NumPart - self->N_gas) > recv_count) {
            for (i = 0; i < recv_count; i++) {
              self->P[self->NumPart + i] = self->P[self->N_gas + i];
              self->Key[self->NumPart + i] = self->Key[self->N_gas + i];
            }
          } else {
            for (i = self->NumPart - 1; i >= self->N_gas; i--) {
              self->P[i + recv_count] = self->P[i];
              self->Key[i + recv_count] = self->Key[i];
            }
          }

          MPI_Recv(&self->P[self->N_gas],
                   recv_count * sizeof(struct particle_data), MPI_BYTE, partner,
                   TAG_PDATA, MPI_COMM_WORLD, &status);
          MPI_Recv(&self->Key[self->N_gas], recv_count * sizeof(peanokey),
                   MPI_BYTE, partner, TAG_KEY, MPI_COMM_WORLD, &status);
          MPI_Recv(&self->SphP[self->N_gas],
                   recv_count * sizeof(struct sph_particle_data), MPI_BYTE,
                   partner, TAG_SPHDATA, MPI_COMM_WORLD, &status);

          self->N_gas += recv_count;
        } else {
          MPI_Recv(&self->P[self->NumPart],
                   recv_count * sizeof(struct particle_data), MPI_BYTE, partner,
                   TAG_PDATA, MPI_COMM_WORLD, &status);
          MPI_Recv(&self->Key[self->NumPart], recv_count * sizeof(peanokey),
                   MPI_BYTE, partner, TAG_KEY, MPI_COMM_WORLD, &status);
        }

        self->NumPart += recv_count;
      }
    }
  }
}

/*! This function determines how many particles that are currently stored
 *  on the local CPU have to be moved off according to the domain
 *  decomposition.
 */
void domain_countToGo(Tree *self) {
  int n, no;

  for (n = 0; n < self->NTask; n++) {
    self->local_toGo[n] = 0;
    self->local_toGoSph[n] = 0;
  }

  for (n = 0; n < self->NumPart; n++) {
    no = 0;

    while (self->TopNodes[no].Daughter >= 0)
      no = self->TopNodes[no].Daughter +
           (self->Key[n] - self->TopNodes[no].StartKey) /
               (self->TopNodes[no].Size / 8);

    no = self->TopNodes[no].Leaf;

    if (self->DomainTask[no] != self->ThisTask) {
      self->local_toGo[self->DomainTask[no]] += 1;
      if (self->P[n].Type == 0) self->local_toGoSph[self->DomainTask[no]] += 1;
    }
  }

  MPI_Allgather(self->local_toGo, self->NTask, MPI_INT, self->toGo, self->NTask,
                MPI_INT, MPI_COMM_WORLD);
  MPI_Allgather(self->local_toGoSph, self->NTask, MPI_INT, self->toGoSph,
                self->NTask, MPI_INT, MPI_COMM_WORLD);
}

/*! This routine finds the extent of the global domain grid.
 */
void domain_findExtent(Tree *self) {
  int i, j;
  double len, xmin[3], xmax[3], xmin_glob[3], xmax_glob[3];

  /* determine local extension */
  for (j = 0; j < 3; j++) {
    xmin[j] = MAX_REAL_NUMBER;
    xmax[j] = -MAX_REAL_NUMBER;
  }

  for (i = 0; i < self->NumPart; i++) {
    for (j = 0; j < 3; j++) {
      if (xmin[j] > self->P[i].Pos[j]) xmin[j] = self->P[i].Pos[j];

      if (xmax[j] < self->P[i].Pos[j]) xmax[j] = self->P[i].Pos[j];
    }
  }

  MPI_Allreduce(xmin, xmin_glob, 3, MPI_DOUBLE, MPI_MIN, MPI_COMM_WORLD);
  MPI_Allreduce(xmax, xmax_glob, 3, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);

  len = 0;
  for (j = 0; j < 3; j++)
    if (xmax_glob[j] - xmin_glob[j] > len) len = xmax_glob[j] - xmin_glob[j];

  len *= 1.001;

  for (j = 0; j < 3; j++) {
    self->DomainCenter[j] = 0.5 * (xmin_glob[j] + xmax_glob[j]);
    self->DomainCorner[j] = 0.5 * (xmin_glob[j] + xmax_glob[j]) - 0.5 * len;
  }

  self->DomainLen = len;
  self->DomainFac = 1.0 / len * (((peanokey)1) << (BITS_PER_DIMENSION));
}

/*! This function constructs the global top-level tree node that is used
 *  for the domain decomposition. This is done by considering the string of
 *  Peano-Hilbert keys for all particles, which is recursively chopped off
 *  in pieces of eight segments until each segment holds at most a certain
 *  number of particles.
 */
void domain_determineTopTree(Tree *self) {
  int i, ntop_local, ntop;
  int *ntopnodelist, *ntopoffset;

  for (i = 0; i < self->NumPart; i++) {
    self->KeySorted[i] = self->Key[i] = peano_hilbert_key(
        (self->P[i].Pos[0] - self->DomainCorner[0]) * self->DomainFac,
        (self->P[i].Pos[1] - self->DomainCorner[1]) * self->DomainFac,
        (self->P[i].Pos[2] - self->DomainCorner[2]) * self->DomainFac,
        BITS_PER_DIMENSION);
  }

  qsort(self->KeySorted, self->NumPart, sizeof(peanokey), domain_compare_key);

  self->NTopnodes = 1;
  self->TopNodes[0].Daughter = -1;
  self->TopNodes[0].Size = PEANOCELLS;
  self->TopNodes[0].StartKey = 0;
  self->TopNodes[0].Count = self->NumPart;
  self->TopNodes[0].Pstart = 0;

  domain_topsplit_local(self, 0, 0);

  self->toplist_local =
      malloc(self->NTopnodes * sizeof(struct topnode_exchange));

  for (i = 0, ntop_local = 0; i < self->NTopnodes; i++) {
    if (self->TopNodes[i].Daughter == -1) /* only use leaves */
    {
      self->toplist_local[ntop_local].Startkey = self->TopNodes[i].StartKey;
      self->toplist_local[ntop_local].Count = self->TopNodes[i].Count;
      ntop_local++;
    }
  }

  ntopnodelist = malloc(sizeof(int) * self->NTask);
  ntopoffset = malloc(sizeof(int) * self->NTask);

  MPI_Allgather(&ntop_local, 1, MPI_INT, ntopnodelist, 1, MPI_INT,
                MPI_COMM_WORLD);

  for (i = 0, ntop = 0, ntopoffset[0] = 0; i < self->NTask; i++) {
    ntop += ntopnodelist[i];
    if (i > 0) ntopoffset[i] = ntopoffset[i - 1] + ntopnodelist[i - 1];
  }

  self->toplist = malloc(ntop * sizeof(struct topnode_exchange));

  for (i = 0; i < self->NTask; i++) {
    ntopnodelist[i] *= sizeof(struct topnode_exchange);
    ntopoffset[i] *= sizeof(struct topnode_exchange);
  }

  MPI_Allgatherv(self->toplist_local,
                 ntop_local * sizeof(struct topnode_exchange), MPI_BYTE,
                 self->toplist, ntopnodelist, ntopoffset, MPI_BYTE,
                 MPI_COMM_WORLD);

  qsort(self->toplist, ntop, sizeof(struct topnode_exchange),
        domain_compare_toplist);

  self->NTopnodes = 1;
  self->TopNodes[0].Daughter = -1;
  self->TopNodes[0].Size = PEANOCELLS;
  self->TopNodes[0].StartKey = 0;
  self->TopNodes[0].Count = self->All.TotNumPart;
  self->TopNodes[0].Pstart = 0;
  self->TopNodes[0].Blocks = ntop;

  domain_topsplit(self, 0, 0);

  free(self->toplist);
  free(ntopoffset);
  free(ntopnodelist);
  free(self->toplist_local);
}

/*! This function is responsible for constructing the local top-level
 *  Peano-Hilbert segments. A segment is cut into 8 pieces recursively
 *  until the number of particles in the segment has fallen below
 *  All.TotNumPart / (TOPNODEFACTOR * NTask * NTask).
 */
void domain_topsplit_local(Tree *self, int node, peanokey startkey) {
  int i, p, sub, bin;

  if (self->TopNodes[node].Size >= 8) {
    self->TopNodes[node].Daughter = self->NTopnodes;

    for (i = 0; i < 8; i++) {
      if (self->NTopnodes < MAXTOPNODES) {
        sub = self->TopNodes[node].Daughter + i;
        self->TopNodes[sub].Size = self->TopNodes[node].Size / 8;
        self->TopNodes[sub].Count = 0;
        self->TopNodes[sub].Daughter = -1;
        self->TopNodes[sub].StartKey = startkey + i * self->TopNodes[sub].Size;
        self->TopNodes[sub].Pstart = self->TopNodes[node].Pstart;

        self->NTopnodes++;
      } else {
        printf(
            "task=%d: We are out of Topnodes. Increasing the constant "
            "MAXTOPNODES might help.\n",
            self->ThisTask);
        fflush(stdout);
        endrun(self, 13213);
      }
    }

    for (p = self->TopNodes[node].Pstart;
         p < self->TopNodes[node].Pstart + self->TopNodes[node].Count; p++) {
      bin = (self->KeySorted[p] - startkey) / (self->TopNodes[node].Size / 8);

      if (bin < 0 || bin > 7) {
        printf("task=%d: something odd has happened here. bin=%d\n",
               self->ThisTask, bin);
        fflush(stdout);
        endrun(self, 13123123);
      }

      sub = self->TopNodes[node].Daughter + bin;

      if (self->TopNodes[sub].Count == 0) self->TopNodes[sub].Pstart = p;

      self->TopNodes[sub].Count++;
    }

    for (i = 0; i < 8; i++) {
      sub = self->TopNodes[node].Daughter + i;
      if (self->TopNodes[sub].Count >
          self->All.TotNumPart / (TOPNODEFACTOR * self->NTask * self->NTask))
        domain_topsplit_local(self, sub, self->TopNodes[sub].StartKey);
    }
  }
}

/*! This function is responsible for constructing the global top-level tree
 *  segments. Starting from a joint list of all local top-level segments,
 *  in which mulitple occurences of the same spatial segment have been
 *  combined, a segment is subdivided into 8 pieces recursively until the
 *  number of particles in each segment has fallen below All.TotNumPart /
 *  (TOPNODEFACTOR * NTask).
 */
void domain_topsplit(Tree *self, int node, peanokey startkey) {
  int i, p, sub, bin;

  if (self->TopNodes[node].Size >= 8) {
    self->TopNodes[node].Daughter = self->NTopnodes;

    for (i = 0; i < 8; i++) {
      if (self->NTopnodes < MAXTOPNODES) {
        sub = self->TopNodes[node].Daughter + i;
        self->TopNodes[sub].Size = self->TopNodes[node].Size / 8;
        self->TopNodes[sub].Count = 0;
        self->TopNodes[sub].Blocks = 0;
        self->TopNodes[sub].Daughter = -1;
        self->TopNodes[sub].StartKey = startkey + i * self->TopNodes[sub].Size;
        self->TopNodes[sub].Pstart = self->TopNodes[node].Pstart;
        self->NTopnodes++;
      } else {
        printf(
            "Task=%d: We are out of Topnodes. Increasing the constant "
            "MAXTOPNODES might help.\n",
            self->ThisTask);
        fflush(stdout);
        endrun(self, 137213);
      }
    }

    for (p = self->TopNodes[node].Pstart;
         p < self->TopNodes[node].Pstart + self->TopNodes[node].Blocks; p++) {
      bin = (self->toplist[p].Startkey - startkey) /
            (self->TopNodes[node].Size / 8);
      sub = self->TopNodes[node].Daughter + bin;

      if (bin < 0 || bin > 7) endrun(self, 77);

      if (self->TopNodes[sub].Blocks == 0) self->TopNodes[sub].Pstart = p;

      self->TopNodes[sub].Count += self->toplist[p].Count;
      self->TopNodes[sub].Blocks++;
    }

    for (i = 0; i < 8; i++) {
      sub = self->TopNodes[node].Daughter + i;
      if (self->TopNodes[sub].Count >
          self->All.TotNumPart / (TOPNODEFACTOR * self->NTask))
        domain_topsplit(self, sub, self->TopNodes[sub].StartKey);
    }
  }
}

/*! This function walks the global top tree in order to establish the
 *  number of leaves it has. These leaves are distributed to different
 *  processors.
 */
void domain_walktoptree(Tree *self, int no) {
  int i;

  if (self->TopNodes[no].Daughter == -1) {
    self->TopNodes[no].Leaf = self->NTopleaves;
    self->NTopleaves++;
  } else {
    for (i = 0; i < 8; i++)
      domain_walktoptree(self, self->TopNodes[no].Daughter + i);
  }
}

/*! This routine bins the particles onto the domain-grid, i.e. it sums up the
 *  total number of particles and the total amount of work in each of the
 *  domain-cells. This information forms the basis for the actual decision on
 *  the adopted domain decomposition.
 */
void domain_sumCost(Tree *self) {
  int i, n, no;
  double *local_DomainWork;
  int *local_DomainCount;
  int *local_DomainCountSph;

  local_DomainWork = malloc(self->NTopnodes * sizeof(double));
  local_DomainCount = malloc(self->NTopnodes * sizeof(int));
  local_DomainCountSph = malloc(self->NTopnodes * sizeof(int));

  self->NTopleaves = 0;

  domain_walktoptree(self, 0);

  for (i = 0; i < self->NTopleaves; i++) {
    local_DomainWork[i] = 0;
    local_DomainCount[i] = 0;
    local_DomainCountSph[i] = 0;
  }

  if (self->ThisTask == 0 && self->All.OutputInfo)
    printf("NTopleaves= %d\n", self->NTopleaves);

  for (n = 0; n < self->NumPart; n++) {
    no = 0;

    while (self->TopNodes[no].Daughter >= 0)
      no = self->TopNodes[no].Daughter +
           (self->Key[n] - self->TopNodes[no].StartKey) /
               (self->TopNodes[no].Size / 8);

    no = self->TopNodes[no].Leaf;

    //      if(self->P[n].Ti_endstep > self->P[n].Ti_begstep)
    //	local_DomainWork[no] += (1.0 + self->P[n].GravCost) /
    //(self->P[n].Ti_endstep - self->P[n].Ti_begstep);
    //      else
    //	local_DomainWork[no] += (1.0 + self->P[n].GravCost);

    local_DomainWork[no] += (1.0 + 1.0); /* yr : avoid using P[n].GravCost */

    local_DomainCount[no] += 1;
    if (self->P[n].Type == 0) local_DomainCountSph[no] += 1;
  }

  MPI_Allreduce(local_DomainWork, self->DomainWork, self->NTopleaves,
                MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
  MPI_Allreduce(local_DomainCount, self->DomainCount, self->NTopleaves, MPI_INT,
                MPI_SUM, MPI_COMM_WORLD);
  MPI_Allreduce(local_DomainCountSph, self->DomainCountSph, self->NTopleaves,
                MPI_INT, MPI_SUM, MPI_COMM_WORLD);

  free(local_DomainCountSph);
  free(local_DomainCount);
  free(local_DomainWork);
}

/*! This is a comparison kernel used in a sort routine.
 */
int domain_compare_toplist(const void *a, const void *b) {
  if (((struct topnode_exchange *)a)->Startkey <
      (((struct topnode_exchange *)b)->Startkey))
    return -1;

  if (((struct topnode_exchange *)a)->Startkey >
      (((struct topnode_exchange *)b)->Startkey))
    return +1;

  return 0;
}

/*! This is a comparison kernel used in a sort routine.
 */
int domain_compare_key(const void *a, const void *b) {
  if (*(peanokey *)a < *(peanokey *)b) return -1;

  if (*(peanokey *)a > *(peanokey *)b) return +1;

  return 0;
}

/*! This function makes sure that all particle coordinates (Pos) are
 *  periodically mapped onto the interval [0, BoxSize].  After this function
 *  has been called, a new domain decomposition should be done, which will
 *  also force a new tree construction.
 */
void do_box_wrapping(Tree *self) {
  int i, j;
  double boxsize[3];

  for (j = 0; j < 3; j++) boxsize[j] = self->All.BoxSize;

  //#ifdef LONG_X
  //  boxsize[0] *= LONG_X;
  //#endif
  //#ifdef LONG_Y
  //  boxsize[1] *= LONG_Y;
  //#endif
  //#ifdef LONG_Z
  //  boxsize[2] *= LONG_Z;
  //#endif

  for (i = 0; i < self->NumPart; i++)
    for (j = 0; j < 3; j++) {
      while (self->P[i].Pos[j] < 0) self->P[i].Pos[j] += boxsize[j];

      while (self->P[i].Pos[j] >= boxsize[j]) self->P[i].Pos[j] -= boxsize[j];
    }
}
