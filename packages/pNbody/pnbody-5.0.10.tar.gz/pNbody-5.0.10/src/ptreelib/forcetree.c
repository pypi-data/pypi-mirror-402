#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "endrun.h"
#include "proto.h"
#include "ptreelib.h"

/*! This function allocates the memory used for storage of the tree and of
 *  auxiliary arrays needed for tree-walk and link-lists.  Usually,
 *  maxnodes approximately equal to 0.7*maxpart is sufficient to store the
 *  tree for up to maxpart particles.
 */
void force_treeallocate(Tree *self, int maxnodes, int maxpart) {
  int i;
  size_t bytes;
  double allbytes = 0;
  double u;

  self->MaxNodes = maxnodes;

  if (!(self->Nodes_base =
            malloc(bytes = (self->MaxNodes + 1) * sizeof(struct NODE)))) {
    printf("failed to allocate memory for %d tree-nodes (%g MB).\n",
           self->MaxNodes, bytes / (1024.0 * 1024.0));
    endrun(self, 3);
  }
  allbytes += bytes;

  if (!(self->Extnodes_base =
            malloc(bytes = (self->MaxNodes + 1) * sizeof(struct extNODE)))) {
    printf("failed to allocate memory for %d tree-extnodes (%g MB).\n",
           self->MaxNodes, bytes / (1024.0 * 1024.0));
    endrun(self, 3);
  }
  allbytes += bytes;

  self->Nodes = self->Nodes_base - self->All.MaxPart;
  self->Extnodes = self->Extnodes_base - self->All.MaxPart;

  if (!(self->Nextnode =
            malloc(bytes = (maxpart + MAXTOPNODES) * sizeof(int)))) {
    printf("Failed to allocate %d spaces for 'Nextnode' array (%g MB)\n",
           maxpart + MAXTOPNODES, bytes / (1024.0 * 1024.0));
    exit(0);
  }
  allbytes += bytes;

  if (!(self->Father = malloc(bytes = (maxpart) * sizeof(int)))) {
    printf("Failed to allocate %d spaces for 'Father' array (%g MB)\n", maxpart,
           bytes / (1024.0 * 1024.0));
    exit(0);
  }
  allbytes += bytes;

  if (self->first_flag == 0) {
    self->first_flag = 1;

    if (self->ThisTask == 0 && self->All.OutputInfo)
      printf("\nAllocated %g MByte for BH-tree. %ld\n\n",
             allbytes / (1024.0 * 1024.0),
             sizeof(struct NODE) + sizeof(struct extNODE));

    self->tabfac = NTAB / 3.0;

    for (i = 0; i < NTAB; i++) {
      u = 3.0 / NTAB * (i + 0.5);
      self->shortrange_table[i] = erfc(u) + 2.0 * u / sqrt(M_PI) * exp(-u * u);
      self->shortrange_table_potential[i] = erfc(u);
    }
  }
}

/*! This function frees the memory allocated for the tree, i.e. it frees
 *  the space allocated by the function force_treeallocate().
 */
void force_treefree(Tree *self) {
  free(self->Father);
  free(self->Nextnode);
  free(self->Extnodes_base);
  free(self->Nodes_base);
}

/*! This function is a driver routine for constructing the gravitational
 *  oct-tree, which is done by calling a small number of other functions.
 */
int force_treebuild(Tree *self, int npart) {
  self->Numnodestree = force_treebuild_single(self, npart);

  force_update_pseudoparticles(self);

  force_flag_localnodes(self);

  // TimeOfLastTreeConstruction = self->All.Time;
  self->TimeOfLastTreeConstruction = 0.0;

  return self->Numnodestree;
}

/*! Constructs the gravitational oct-tree.
 *
 *  The index convention for accessing tree nodes is the following: the
 *  indices 0...NumPart-1 reference single particles, the indices
 *  All.MaxPart.... All.MaxPart+nodes-1 reference tree nodes. `Nodes_base'
 *  points to the first tree node, while `nodes' is shifted such that
 *  nodes[All.MaxPart] gives the first tree node. Finally, node indices
 *  with values 'All.MaxPart + MaxNodes' and larger indicate "pseudo
 *  particles", i.e. multipole moments of top-level nodes that lie on
 *  different CPUs. If such a node needs to be opened, the corresponding
 *  particle must be exported to that CPU. The 'Extnodes' structure
 *  parallels that of 'Nodes'. Its information is only needed for the SPH
 *  part of the computation. (The data is split onto these two structures
 *  as a tuning measure.  If it is merged into 'Nodes' a somewhat bigger
 *  size of the nodes also for gravity would result, which would reduce
 *  cache utilization slightly.
 */
int force_treebuild_single(Tree *self, int npart) {
  int i, j, subnode = 0, parent, numnodes;
  int nfree, th, nn, no;
  struct NODE *nfreep;
  double lenhalf, epsilon;
  peanokey key;

  /* create an empty root node  */
  nfree = self->All.MaxPart;    /* index of first free node */
  nfreep = &self->Nodes[nfree]; /* select first node */

  nfreep->len = self->DomainLen;
  for (j = 0; j < 3; j++) nfreep->center[j] = self->DomainCenter[j];
  for (j = 0; j < 8; j++) nfreep->u.suns[j] = -1;

  numnodes = 1;
  nfreep++;
  nfree++;

  /* create a set of empty nodes corresponding to the top-level domain
   * grid. We need to generate these nodes first to make sure that we have a
   * complete top-level tree which allows the easy insertion of the
   * pseudo-particles at the right place
   */

  force_create_empty_nodes(self, self->All.MaxPart, 0, 1, 0, 0, 0, &numnodes,
                           &nfree);

  /* if a high-resolution region in a global tree is used, we need to generate
   * an additional set empty nodes to make sure that we have a complete
   * top-level tree for the high-resolution inset
   */

  nfreep = &self->Nodes[nfree];
  parent = -1; /* note: will not be used below before it is changed */

  /* now we insert all particles */
  for (i = 0; i < npart; i++) {

    /* the softening is only used to check whether particles are so close
     * that the tree needs not to be refined further
     */
    epsilon = self->All.ForceSoftening[self->P[i].Type];

    key = peano_hilbert_key(
        (self->P[i].Pos[0] - self->DomainCorner[0]) * self->DomainFac,
        (self->P[i].Pos[1] - self->DomainCorner[1]) * self->DomainFac,
        (self->P[i].Pos[2] - self->DomainCorner[2]) * self->DomainFac,
        BITS_PER_DIMENSION);

    no = 0;
    while (self->TopNodes[no].Daughter >= 0)
      no = self->TopNodes[no].Daughter +
           (key - self->TopNodes[no].StartKey) / (self->TopNodes[no].Size / 8);

    no = self->TopNodes[no].Leaf;
    th = self->DomainNodeIndex[no];

    while (1) {
      if (th >= self->All.MaxPart) /* we are dealing with an internal node */
      {
        subnode = 0;
        if (self->P[i].Pos[0] > self->Nodes[th].center[0]) subnode += 1;
        if (self->P[i].Pos[1] > self->Nodes[th].center[1]) subnode += 2;
        if (self->P[i].Pos[2] > self->Nodes[th].center[2]) subnode += 4;

        nn = self->Nodes[th].u.suns[subnode];

        if (nn >= 0) /* ok, something is in the daughter slot already, need to
                        continue */
        {
          parent = th;
          th = nn;
        } else {
          /* here we have found an empty slot where we can attach
           * the new particle as a leaf.
           */
          self->Nodes[th].u.suns[subnode] = i;
          break; /* done for this particle */
        }
      } else {
        /* We try to insert into a leaf with a single particle.  Need
         * to generate a new internal node at this point.
         */
        self->Nodes[parent].u.suns[subnode] = nfree;

        nfreep->len = 0.5 * self->Nodes[parent].len;
        lenhalf = 0.25 * self->Nodes[parent].len;

        if (subnode & 1)
          nfreep->center[0] = self->Nodes[parent].center[0] + lenhalf;
        else
          nfreep->center[0] = self->Nodes[parent].center[0] - lenhalf;

        if (subnode & 2)
          nfreep->center[1] = self->Nodes[parent].center[1] + lenhalf;
        else
          nfreep->center[1] = self->Nodes[parent].center[1] - lenhalf;

        if (subnode & 4)
          nfreep->center[2] = self->Nodes[parent].center[2] + lenhalf;
        else
          nfreep->center[2] = self->Nodes[parent].center[2] - lenhalf;

        nfreep->u.suns[0] = -1;
        nfreep->u.suns[1] = -1;
        nfreep->u.suns[2] = -1;
        nfreep->u.suns[3] = -1;
        nfreep->u.suns[4] = -1;
        nfreep->u.suns[5] = -1;
        nfreep->u.suns[6] = -1;
        nfreep->u.suns[7] = -1;

        subnode = 0;
        if (self->P[th].Pos[0] > nfreep->center[0]) subnode += 1;
        if (self->P[th].Pos[1] > nfreep->center[1]) subnode += 2;
        if (self->P[th].Pos[2] > nfreep->center[2]) subnode += 4;
#ifndef NOTREERND
        if (nfreep->len < 1.0e-3 * epsilon) {
          /* seems like we're dealing with particles at identical (or extremely
           * close) locations. Randomize subnode index to allow tree
           * construction. Note: Multipole moments of tree are still correct,
           * but this will only happen well below gravitational softening
           * length-scale anyway.
           */
          // subnode = (int) (8.0 * get_random_number((0xffff & self->P[i].ID) +
          // self->P[i].GravCost)); self->P[i].GravCost += 1;

          printf(
              "task %d: two particles are at identical (or extremely close).\n",
              self->ThisTask);
          endrun(self, 3212);

          if (subnode >= 8) subnode = 7;
        }
#endif
        nfreep->u.suns[subnode] = th;

        th = nfree; /* resume trying to insert the new particle at
                     * the newly created internal node
                     */

        numnodes++;
        nfree++;
        nfreep++;

        if ((numnodes) >= self->MaxNodes) {
          printf("task %d: maximum number %d of tree-nodes reached.\n",
                 self->ThisTask, self->MaxNodes);
          printf("for particle %d\n", i);
          // dump_particles();
          endrun(self, 1);
        }
      }
    }
  }

  /* insert the pseudo particles that represent the mass distribution of other
   * domains */
  force_insert_pseudo_particles(self);

  /* now compute the multipole moments recursively */
  self->last = -1;

  force_update_node_recursive(self, self->All.MaxPart, -1, -1);

  if (self->last >= self->All.MaxPart) {
    if (self->last >=
        self->All.MaxPart + self->MaxNodes) /* a pseudo-particle */
      self->Nextnode[self->last - self->MaxNodes] = -1;
    else
      self->Nodes[self->last].u.d.nextnode = -1;
  } else
    self->Nextnode[self->last] = -1;

  return numnodes;
}

/*! This function recursively creates a set of empty tree nodes which
 *  corresponds to the top-level tree for the domain grid. This is done to
 *  ensure that this top-level tree is always "complete" so that we can
 *  easily associate the pseudo-particles of other CPUs with tree-nodes at
 *  a given level in the tree, even when the particle population is so
 *  sparse that some of these nodes are actually empty.
 */
void force_create_empty_nodes(Tree *self, int no, int topnode, int bits, int x,
                              int y, int z, int *nodecount, int *nextfree) {
  int i, j, k, n, sub, count;

  if (self->TopNodes[topnode].Daughter >= 0) {
    for (i = 0; i < 2; i++)
      for (j = 0; j < 2; j++)
        for (k = 0; k < 2; k++) {
          sub = 7 & peano_hilbert_key((x << 1) + i, (y << 1) + j, (z << 1) + k,
                                      bits);

          count = i + 2 * j + 4 * k;

          self->Nodes[no].u.suns[count] = *nextfree;

          self->Nodes[*nextfree].len = 0.5 * self->Nodes[no].len;
          self->Nodes[*nextfree].center[0] =
              self->Nodes[no].center[0] +
              (2 * i - 1) * 0.25 * self->Nodes[no].len;
          self->Nodes[*nextfree].center[1] =
              self->Nodes[no].center[1] +
              (2 * j - 1) * 0.25 * self->Nodes[no].len;
          self->Nodes[*nextfree].center[2] =
              self->Nodes[no].center[2] +
              (2 * k - 1) * 0.25 * self->Nodes[no].len;

          for (n = 0; n < 8; n++) self->Nodes[*nextfree].u.suns[n] = -1;

          if (self->TopNodes[self->TopNodes[topnode].Daughter + sub].Daughter ==
              -1)
            self->DomainNodeIndex
                [self->TopNodes[self->TopNodes[topnode].Daughter + sub].Leaf] =
                *nextfree;

          *nextfree = *nextfree + 1;
          *nodecount = *nodecount + 1;

          if ((*nodecount) >= self->MaxNodes) {
            printf("task %d: maximum number %d of tree-nodes reached.\n",
                   self->ThisTask, self->MaxNodes);
            printf("in create empty nodes\n");
            // dump_particles();
            endrun(self, 11);
          }

          force_create_empty_nodes(
              self, *nextfree - 1, self->TopNodes[topnode].Daughter + sub,
              bits + 1, 2 * x + i, 2 * y + j, 2 * z + k, nodecount, nextfree);
        }
  }
}

/*! this function inserts pseudo-particles which will represent the mass
 *  distribution of the other CPUs. Initially, the mass of the
 *  pseudo-particles is set to zero, and their coordinate is set to the
 *  center of the domain-cell they correspond to. These quantities will be
 *  updated later on.
 */
void force_insert_pseudo_particles(Tree *self) {
  int i, index, subnode, nn, th;

  for (i = 0; i < self->NTopleaves; i++) {
    index = self->DomainNodeIndex[i];

    self->DomainMoment[i].mass = 0;
    self->DomainMoment[i].s[0] = self->Nodes[index].center[0];
    self->DomainMoment[i].s[1] = self->Nodes[index].center[1];
    self->DomainMoment[i].s[2] = self->Nodes[index].center[2];
  }

  for (i = 0; i < self->NTopleaves; i++) {
    if (i < self->DomainMyStart || i > self->DomainMyLast) {
      th = self->All.MaxPart; /* select index of first node in tree */

      while (1) {
        if (th >= self->All.MaxPart) /* we are dealing with an internal node */
        {
          if (th >= self->All.MaxPart + self->MaxNodes)
            endrun(self, 888); /* this can't be */

          subnode = 0;
          if (self->DomainMoment[i].s[0] > self->Nodes[th].center[0])
            subnode += 1;
          if (self->DomainMoment[i].s[1] > self->Nodes[th].center[1])
            subnode += 2;
          if (self->DomainMoment[i].s[2] > self->Nodes[th].center[2])
            subnode += 4;

          nn = self->Nodes[th].u.suns[subnode];

          if (nn >= 0) /* ok, something is in the daughter slot already, need to
                          continue */
          {
            th = nn;
          } else {
            /* here we have found an empty slot where we can
             * attach the pseudo particle as a leaf
             */
            self->Nodes[th].u.suns[subnode] =
                self->All.MaxPart + self->MaxNodes + i;

            break; /* done for this pseudo particle */
          }
        } else {
          endrun(self, 889); /* this can't be */
        }
      }
    }
  }
}

/*! this routine determines the multipole moments for a given internal node
 *  and all its subnodes using a recursive computation.  The result is
 *  stored in the Nodes[] structure in the sequence of this tree-walk.
 *
 *  Note that the bitflags-variable for each node is used to store in the
 *  lowest bits some special information: Bit 0 flags whether the node
 *  belongs to the top-level tree corresponding to the domain
 *  decomposition, while Bit 1 signals whether the top-level node is
 *  dependent on local mass.
 *
 *  If UNEQUALSOFTENINGS is set, bits 2-4 give the particle type with
 *  the maximum softening among the particles in the node, and bit 5
 *  flags whether the node contains any particles with lower softening
 *  than that.
 */
void force_update_node_recursive(Tree *self, int no, int sib, int father) {
  int j, jj, p, pp, nextsib, suns[8];
  FLOAT hmax;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
  int maxsofttype, diffsoftflag;
#else
  FLOAT maxsoft;
#endif
#endif
  struct particle_data *pa;
  double s[3], vs[3], mass;

  if (no >= self->All.MaxPart &&
      no < self->All.MaxPart + self->MaxNodes) /* internal node */
  {
    for (j = 0; j < 8; j++)
      suns[j] = self->Nodes[no]
                    .u.suns[j]; /* this "backup" is necessary because the
                           nextnode entry will overwrite one element (union!) */
    if (self->last >= 0) {
      if (self->last >= self->All.MaxPart) {
        if (self->last >=
            self->All.MaxPart + self->MaxNodes) /* a pseudo-particle */
          self->Nextnode[self->last - self->MaxNodes] = no;
        else
          self->Nodes[self->last].u.d.nextnode = no;
      } else
        self->Nextnode[self->last] = no;
    }

    self->last = no;

    mass = 0;
    s[0] = 0;
    s[1] = 0;
    s[2] = 0;
    vs[0] = 0;
    vs[1] = 0;
    vs[2] = 0;
    hmax = 0;
#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
    maxsofttype = 7;
    diffsoftflag = 0;
#else
    maxsoft = 0;
#endif
#endif

    for (j = 0; j < 8; j++) {
      if ((p = suns[j]) >= 0) {
        /* check if we have a sibling on the same level */
        for (jj = j + 1; jj < 8; jj++)
          if ((pp = suns[jj]) >= 0) break;

        if (jj < 8) /* yes, we do */
          nextsib = pp;
        else
          nextsib = sib;

        force_update_node_recursive(self, p, nextsib, no);

        if (p >= self->All.MaxPart) /* an internal node or pseudo particle */
        {
          if (p >= self->All.MaxPart + self->MaxNodes) /* a pseudo particle */
          {
            /* nothing to be done here because the mass of the
             * pseudo-particle is still zero. This will be changed
             * later.
             */
          } else {
            mass += self->Nodes[p].u.d.mass;
            s[0] += self->Nodes[p].u.d.mass * self->Nodes[p].u.d.s[0];
            s[1] += self->Nodes[p].u.d.mass * self->Nodes[p].u.d.s[1];
            s[2] += self->Nodes[p].u.d.mass * self->Nodes[p].u.d.s[2];
            vs[0] += self->Nodes[p].u.d.mass * self->Extnodes[p].vs[0];
            vs[1] += self->Nodes[p].u.d.mass * self->Extnodes[p].vs[1];
            vs[2] += self->Nodes[p].u.d.mass * self->Extnodes[p].vs[2];

            if (self->Extnodes[p].hmax > hmax) hmax = self->Extnodes[p].hmax;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
            diffsoftflag |= (self->Nodes[p].u.d.bitflags >> 5) & 1;

            if (maxsofttype == 7) {
              maxsofttype = (self->Nodes[p].u.d.bitflags >> 2) & 7;
            } else {
              if (((self->Nodes[p].u.d.bitflags >> 2) & 7) != 7) {
                if (self->All.ForceSoftening[(
                        (self->Nodes[p].u.d.bitflags >> 2) & 7)] >
                    self->All.ForceSoftening[maxsofttype]) {
                  maxsofttype = ((self->Nodes[p].u.d.bitflags >> 2) & 7);
                  diffsoftflag = 1;
                } else {
                  if (self->All.ForceSoftening[(
                          (self->Nodes[p].u.d.bitflags >> 2) & 7)] <
                      self->All.ForceSoftening[maxsofttype])
                    diffsoftflag = 1;
                }
              }
            }
#else
            if (self->Nodes[p].maxsoft > maxsoft)
              maxsoft = self->Nodes[p].maxsoft;
#endif
#endif
          }
        } else /* a particle */
        {
          pa = &self->P[p];

          mass += pa->Mass;
          s[0] += pa->Mass * pa->Pos[0];
          s[1] += pa->Mass * pa->Pos[1];
          s[2] += pa->Mass * pa->Pos[2];
          vs[0] += pa->Mass * pa->Vel[0];
          vs[1] += pa->Mass * pa->Vel[1];
          vs[2] += pa->Mass * pa->Vel[2];

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
          if (maxsofttype == 7) {
            maxsofttype = pa->Type;
          } else {
            if (self->All.ForceSoftening[pa->Type] >
                self->All.ForceSoftening[maxsofttype]) {
              maxsofttype = pa->Type;
              diffsoftflag = 1;
            } else {
              if (self->All.ForceSoftening[pa->Type] <
                  self->All.ForceSoftening[maxsofttype])
                diffsoftflag = 1;
            }
          }
#else
          if (pa->Type == 0) {
            if (self->SphP[p].Hsml > maxsoft) maxsoft = self->SphP[p].Hsml;
          } else {
            if (self->All.ForceSoftening[pa->Type] > maxsoft)
              maxsoft = self->All.ForceSoftening[pa->Type];
          }
#endif
#endif
          if (pa->Type == 0)
            if (self->SphP[p].Hsml > hmax) hmax = self->SphP[p].Hsml;
        }
      }
    }

    if (mass) {
      s[0] /= mass;
      s[1] /= mass;
      s[2] /= mass;
      vs[0] /= mass;
      vs[1] /= mass;
      vs[2] /= mass;
    } else {
      s[0] = self->Nodes[no].center[0];
      s[1] = self->Nodes[no].center[1];
      s[2] = self->Nodes[no].center[2];
    }

    self->Nodes[no].u.d.s[0] = s[0];
    self->Nodes[no].u.d.s[1] = s[1];
    self->Nodes[no].u.d.s[2] = s[2];
    self->Nodes[no].u.d.mass = mass;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
    self->Nodes[no].u.d.bitflags = 4 * maxsofttype + 32 * diffsoftflag;
#else
    self->Nodes[no].u.d.bitflags = 0;
    self->Nodes[no].maxsoft = maxsoft;
#endif
#else
    self->Nodes[no].u.d.bitflags = 0;
#endif

    self->Extnodes[no].vs[0] = vs[0];
    self->Extnodes[no].vs[1] = vs[1];
    self->Extnodes[no].vs[2] = vs[2];
    self->Extnodes[no].hmax = hmax;

    self->Nodes[no].u.d.sibling = sib;
    self->Nodes[no].u.d.father = father;
  } else /* single particle or pseudo particle */
  {
    if (self->last >= 0) {
      if (self->last >= self->All.MaxPart) {
        if (self->last >=
            self->All.MaxPart + self->MaxNodes) /* a pseudo-particle */
          self->Nextnode[self->last - self->MaxNodes] = no;
        else
          self->Nodes[self->last].u.d.nextnode = no;
      } else
        self->Nextnode[self->last] = no;
    }

    self->last = no;

    if (no < self->All.MaxPart) /* only set it for single particles */
      self->Father[no] = father;
  }
}

/*! This function updates the multipole moments of the pseudo-particles
 *  that represent the mass distribution on different CPUs. For that
 *  purpose, it first exchanges the necessary data, and then updates the
 *  top-level tree accordingly. The detailed implementation of these two
 *  tasks is done in separate functions.
 */
void force_update_pseudoparticles(Tree *self) {
  force_exchange_pseudodata(self);
  force_treeupdate_pseudos(self);
}

/*! This function communicates the values of the multipole moments of the
 *  top-level tree-nodes of the domain grid.  This data can then be used to
 *  update the pseudo-particles on each CPU accordingly.
 */
void force_exchange_pseudodata(Tree *self) {
  int i, no;
  MPI_Status status;
  int level, sendTask, recvTask;

  for (i = self->DomainMyStart; i <= self->DomainMyLast; i++) {
    no = self->DomainNodeIndex[i];

    /* read out the multipole moments from the local base cells */
    self->DomainMoment[i].s[0] = self->Nodes[no].u.d.s[0];
    self->DomainMoment[i].s[1] = self->Nodes[no].u.d.s[1];
    self->DomainMoment[i].s[2] = self->Nodes[no].u.d.s[2];
    self->DomainMoment[i].vs[0] = self->Extnodes[no].vs[0];
    self->DomainMoment[i].vs[1] = self->Extnodes[no].vs[1];
    self->DomainMoment[i].vs[2] = self->Extnodes[no].vs[2];
    self->DomainMoment[i].mass = self->Nodes[no].u.d.mass;
#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
    self->DomainMoment[i].bitflags = self->Nodes[no].u.d.bitflags;
#else
    self->DomainMoment[i].maxsoft = self->Nodes[no].maxsoft;
#endif
#endif
  }

  /* share the pseudo-particle data accross CPUs */

  for (level = 1; level < (1 << self->PTask); level++) {
    sendTask = self->ThisTask;
    recvTask = self->ThisTask ^ level;

    if (recvTask < self->NTask)
      MPI_Sendrecv(&self->DomainMoment[self->DomainStartList[sendTask]],
                   (self->DomainEndList[sendTask] -
                    self->DomainStartList[sendTask] + 1) *
                       sizeof(struct DomainNODE),
                   MPI_BYTE, recvTask, TAG_DMOM,
                   &self->DomainMoment[self->DomainStartList[recvTask]],
                   (self->DomainEndList[recvTask] -
                    self->DomainStartList[recvTask] + 1) *
                       sizeof(struct DomainNODE),
                   MPI_BYTE, recvTask, TAG_DMOM, MPI_COMM_WORLD, &status);
  }
}

/*! This function updates the top-level tree after the multipole moments of
 *  the pseudo-particles have been updated.
 */
void force_treeupdate_pseudos(Tree *self) {
  int i, k, no;
  FLOAT sold[3], vsold[3], snew[3], vsnew[3], massold, massnew, mm;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
  int maxsofttype, diffsoftflag;
#else
  FLOAT maxsoft;
#endif
#endif

  for (i = 0; i < self->NTopleaves; i++)
    if (i < self->DomainMyStart || i > self->DomainMyLast) {
      no = self->DomainNodeIndex[i];

      for (k = 0; k < 3; k++) {
        sold[k] = self->Nodes[no].u.d.s[k];
        vsold[k] = self->Extnodes[no].vs[k];
      }
      massold = self->Nodes[no].u.d.mass;

      for (k = 0; k < 3; k++) {
        snew[k] = self->DomainMoment[i].s[k];
        vsnew[k] = self->DomainMoment[i].vs[k];
      }
      massnew = self->DomainMoment[i].mass;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
      maxsofttype = (self->DomainMoment[i].bitflags >> 2) & 7;
      diffsoftflag = (self->DomainMoment[i].bitflags >> 5) & 1;
#else
      maxsoft = self->DomainMoment[i].maxsoft;
#endif
#endif
      do {
        mm = self->Nodes[no].u.d.mass + massnew - massold;
        for (k = 0; k < 3; k++) {
          if (mm > 0) {
            self->Nodes[no].u.d.s[k] =
                (self->Nodes[no].u.d.mass * self->Nodes[no].u.d.s[k] +
                 massnew * snew[k] - massold * sold[k]) /
                mm;
            self->Extnodes[no].vs[k] =
                (self->Nodes[no].u.d.mass * self->Extnodes[no].vs[k] +
                 massnew * vsnew[k] - massold * vsold[k]) /
                mm;
          }
        }
        self->Nodes[no].u.d.mass = mm;

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
        diffsoftflag |= (self->Nodes[no].u.d.bitflags >> 5) & 1;

        if (maxsofttype == 7)
          maxsofttype = (self->Nodes[no].u.d.bitflags >> 2) & 7;
        else {
          if (((self->Nodes[no].u.d.bitflags >> 2) & 7) != 7) {
            if (self->All
                    .ForceSoftening[((self->Nodes[no].u.d.bitflags >> 2) & 7)] >
                self->All.ForceSoftening[maxsofttype]) {
              maxsofttype = ((self->Nodes[no].u.d.bitflags >> 2) & 7);
              diffsoftflag = 1;
            } else {
              if (self->All.ForceSoftening[(
                      (self->Nodes[no].u.d.bitflags >> 2) & 7)] <
                  self->All.ForceSoftening[maxsofttype])
                diffsoftflag = 1;
            }
          }
        }

        self->Nodes[no].u.d.bitflags =
            (Nodes[no].u.d.bitflags & 3) + 4 * maxsofttype + 32 * diffsoftflag;
#else
        if (self->Nodes[no].maxsoft < maxsoft)
          self->Nodes[no].maxsoft = maxsoft;
        maxsoft = self->Nodes[no].maxsoft;
#endif
#endif
        no = self->Nodes[no].u.d.father;

      } while (no >= 0);
    }
}

/*! This function flags nodes in the top-level tree that are dependent on
 *  local particle data.
 */
void force_flag_localnodes(Tree *self) {
  int no, i;

  /* mark all top-level nodes */

  for (i = 0; i < self->NTopleaves; i++) {
    no = self->DomainNodeIndex[i];

    while (no >= 0) {
      if ((self->Nodes[no].u.d.bitflags & 1)) break;

      self->Nodes[no].u.d.bitflags |= 1;

      no = self->Nodes[no].u.d.father;
    }
  }

  /* mark top-level nodes that contain local particles */

  for (i = self->DomainMyStart; i <= self->DomainMyLast; i++) {
    /*
       if(DomainMoment[i].mass > 0)
     */
    {
      no = self->DomainNodeIndex[i];

      while (no >= 0) {
        if ((self->Nodes[no].u.d.bitflags & 2)) break;

        self->Nodes[no].u.d.bitflags |= 2;

        no = self->Nodes[no].u.d.father;
      }
    }
  }
}

/*! This function maps a distance to the nearest periodic neighbour
 */
double force_nearest(double x, double boxsize, double boxhalf) {
  if (x > boxhalf) return x - boxsize;

  if (x < -boxhalf) return x + boxsize;

  return x;
}

/*! This routine computes the gravitational potential by walking the
 *  tree. The same opening criteria is used as for the gravitational force
 *  walk.
 */
void force_treeevaluate_potential(Tree *self, int target, int mode) {
  struct NODE *nop = 0;
  int no, ptype;
  double r2, dx, dy, dz, mass, r, u, h, h_inv, wp;
  double pot, pos_x, pos_y, pos_z, aold;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
  double soft = 0;
#endif
  //#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;
  //#endif

  pot = 0;

  if (mode == 0) {
    pos_x = self->P[target].Pos[0];
    pos_y = self->P[target].Pos[1];
    pos_z = self->P[target].Pos[2];
    ptype = self->P[target].Type;
//      aold = All.ErrTolForceAcc * self->P[target].OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = SphP[target].Hsml;
#endif
  } else {
    pos_x = self->GravDataGet[target].u.Pos[0];
    pos_y = self->GravDataGet[target].u.Pos[1];
    pos_z = self->GravDataGet[target].u.Pos[2];
#ifdef UNEQUALSOFTENINGS
    ptype = self->GravDataGet[target].Type;
#else
    ptype = self->P[0].Type;
#endif
//      aold = All.ErrTolForceAcc * GravDataGet[target].w.OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = GravDataGet[target].Soft;
#endif
  }

#ifndef UNEQUALSOFTENINGS
  h = self->All.ForceSoftening[ptype];
  h_inv = 1.0 / h;
#endif
  no = self->All.MaxPart;

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;
      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;
      mass = nop->u.d.mass;
    }

    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      dx = force_nearest(dx, boxsize, boxhalf);
      dy = force_nearest(dy, boxsize, boxhalf);
      dz = force_nearest(dz, boxsize, boxhalf);
    }
    //#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) {
#ifdef UNEQUALSOFTENINGS
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
      if (ptype == 0)
        h = soft;
      else
        h = self->All.ForceSoftening[ptype];

      if (self->P[no].Type == 0) {
        if (h < self->SphP[no].Hsml) h = self->SphP[no].Hsml;
      } else {
        if (h < self->All.ForceSoftening[self->P[no].Type])
          h = self->All.ForceSoftening[self->P[no].Type];
      }
#else
      h = self->All.ForceSoftening[ptype];
      if (h < self->All.ForceSoftening[P[no].Type])
        h = self->All.ForceSoftening[P[no].Type];
#endif
#endif
      no = self->Nextnode[no];
    } else /* we have an internal node. Need to check opening criterion */
    {
      if (mode == 1) {
        if ((nop->u.d.bitflags & 3) == 1) /* if it's a top-level node
                                           * which does not contain
                                           * local particles we can make
                                           * a short-cut
                                           */
        {
          no = nop->u.d.sibling;
          continue;
        }
      }

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }

        if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
          if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
            if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
      h = self->All.ForceSoftening[ptype];
      maxsofttype = (nop->u.d.bitflags >> 2) & 7;
      if (maxsofttype == 7) /* may only occur for zero mass top-level nodes */
      {
        if (mass > 0) endrun(self, 988);
        no = nop->u.d.nextnode;
        continue;
      } else {
        if (h < self->All.ForceSoftening[maxsofttype]) {
          h = self->All.ForceSoftening[maxsofttype];
          if (r2 < h * h) {
            if (((nop->u.d.bitflags >> 5) &
                 1)) /* bit-5 signals that there are particles of different
                        softening in the node */
            {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#else
      if (ptype == 0)
        h = soft;
      else
        h = self->All.ForceSoftening[ptype];

      if (h < nop->maxsoft) {
        h = nop->maxsoft;
        if (r2 < h * h) {
          no = nop->u.d.nextnode;
          continue;
        }
      }
#endif
#endif

      no = nop->u.d.sibling; /* node can be used */

      if (mode == 1) {
        if (((nop->u.d.bitflags) &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    r = sqrt(r2);

    if (r >= h)
      pot -= mass / r;
    else {
#ifdef UNEQUALSOFTENINGS
      h_inv = 1.0 / h;
#endif
      u = r * h_inv;

      if (u < 0.5)
        wp = -2.8 + u * u * (5.333333333333 + u * u * (6.4 * u - 9.6));
      else
        wp = -3.2 + 0.066666666667 / u +
             u * u *
                 (10.666666666667 +
                  u * (-16.0 + u * (9.6 - 2.133333333333 * u)));

      pot += mass * h_inv * wp;
    }
    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn)
      pot += mass * ewald_pot_corr(self, dx, dy, dz);
    //#endif
  }

  /* store result at the proper place */

  if (mode == 0)
    self->P[target].Potential = pot;
  else
    self->GravDataResult[target].u.Potential = pot;
}

/*! This routine computes the gravitational force for a given local
 *  particle, or for a particle in the communication buffer. Depending on
 *  the value of TypeOfOpeningCriterion, either the geometrical BH
 *  cell-opening criterion, or the `relative' opening criterion is used.
 */
int force_treeevaluate(Tree *self, int target, int mode,
                       double *ewaldcountsum) {
  struct NODE *nop = 0;
  int no, ninteractions, ptype;
  double r2, dx, dy, dz, mass, r, fac, u, h, h_inv, h3_inv;
  double acc_x, acc_y, acc_z, pos_x, pos_y, pos_z, aold;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
  double soft = 0;
#endif
  //#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;
  //#endif

  acc_x = 0;
  acc_y = 0;
  acc_z = 0;
  ninteractions = 0;

  if (mode == 0) {
    pos_x = self->P[target].Pos[0];
    pos_y = self->P[target].Pos[1];
    pos_z = self->P[target].Pos[2];
    ptype = self->P[target].Type;
    aold = self->All.ErrTolForceAcc * self->P[target].OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = SphP[target].Hsml;
#endif
  } else {
    pos_x = self->GravDataGet[target].u.Pos[0];
    pos_y = self->GravDataGet[target].u.Pos[1];
    pos_z = self->GravDataGet[target].u.Pos[2];
#ifdef UNEQUALSOFTENINGS
    ptype = self->GravDataGet[target].Type;
#else
    ptype = self->P[0].Type;
#endif
    aold = self->All.ErrTolForceAcc * self->GravDataGet[target].w.OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = self->GravDataGet[target].Soft;
#endif
  }

#ifndef UNEQUALSOFTENINGS
  h = self->All.ForceSoftening[ptype];
  h_inv = 1.0 / h;
  h3_inv = h_inv * h_inv * h_inv;
#endif
  no = self->All.MaxPart; /* root node */

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;

      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }
      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;

      mass = nop->u.d.mass;
    }
    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      dx = force_nearest(dx, boxsize, boxhalf);
      dy = force_nearest(dy, boxsize, boxhalf);
      dz = force_nearest(dz, boxsize, boxhalf);
    }
    //#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) {
#ifdef UNEQUALSOFTENINGS
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
      if (ptype == 0)
        h = soft;
      else
        h = self->All.ForceSoftening[ptype];

      if (self->P[no].Type == 0) {
        if (h < self->SphP[no].Hsml) h = self->SphP[no].Hsml;
      } else {
        if (h < self->All.ForceSoftening[P[no].Type])
          h = self->All.ForceSoftening[P[no].Type];
      }
#else
      h = self->All.ForceSoftening[ptype];
      if (h < self->All.ForceSoftening[P[no].Type])
        h = self->All.ForceSoftening[P[no].Type];
#endif
#endif
      no = self->Nextnode[no];
    } else /* we have an  internal node. Need to check opening criterion */
    {
      if (mode == 1) {
        if ((nop->u.d.bitflags & 3) == 1) /* if it's a top-level node
                                           * which does not contain
                                           * local particles we can
                                           * continue to do a short-cut */
        {
          no = nop->u.d.sibling;
          continue;
        }
      }

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }

        /* check in addition whether we lie inside the cell */

        if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
          if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
            if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
      h = self->All.ForceSoftening[ptype];
      maxsofttype = (nop->u.d.bitflags >> 2) & 7;
      if (maxsofttype == 7) /* may only occur for zero mass top-level nodes */
      {
        if (mass > 0) endrun(self, 986);
        no = nop->u.d.nextnode;
        continue;
      } else {
        if (h < self->All.ForceSoftening[maxsofttype]) {
          h = self->All.ForceSoftening[maxsofttype];
          if (r2 < h * h) {
            if (((nop->u.d.bitflags >> 5) &
                 1)) /* bit-5 signals that there are particles of different
                        softening in the node */
            {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#else
      if (ptype == 0)
        h = soft;
      else
        h = self->All.ForceSoftening[ptype];

      if (h < nop->maxsoft) {
        h = nop->maxsoft;
        if (r2 < h * h) {
          no = nop->u.d.nextnode;
          continue;
        }
      }
#endif
#endif

      no = nop->u.d.sibling; /* ok, node can be used */

      if (mode == 1) {
        if (((nop->u.d.bitflags) &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    r = sqrt(r2);

    if (r >= h)
      fac = mass / (r2 * r);
    else {
#ifdef UNEQUALSOFTENINGS
      h_inv = 1.0 / h;
      h3_inv = h_inv * h_inv * h_inv;
#endif
      u = r * h_inv;
      if (u < 0.5)
        fac = mass * h3_inv * (10.666666666667 + u * u * (32.0 * u - 38.4));
      else
        fac = mass * h3_inv *
              (21.333333333333 - 48.0 * u + 38.4 * u * u -
               10.666666666667 * u * u * u - 0.066666666667 / (u * u * u));
    }

    acc_x += dx * fac;
    acc_y += dy * fac;
    acc_z += dz * fac;

    ninteractions++;
  }

  /* store result at the proper place */
  if (mode == 0) {
    self->P[target].GravAccel[0] = acc_x;
    self->P[target].GravAccel[1] = acc_y;
    self->P[target].GravAccel[2] = acc_z;
    // self->P[target].GravCost = ninteractions;
  } else {
    self->GravDataResult[target].u.Acc[0] = acc_x;
    self->GravDataResult[target].u.Acc[1] = acc_y;
    self->GravDataResult[target].u.Acc[2] = acc_z;
    self->GravDataResult[target].w.Ninteractions = ninteractions;
  }

  //#ifdef PERIODIC
  if (self->All.PeriodicBoundariesOn)
    *ewaldcountsum += force_treeevaluate_ewald_correction(
        self, target, mode, pos_x, pos_y, pos_z, aold);
  //#endif

  return ninteractions;
}

/*! This function computes the Ewald correction, and is needed if periodic
 *  boundary conditions together with a pure tree algorithm are used. Note
 *  that the ordinary tree walk does not carry out this correction directly
 *  as it was done in Gadget-1.1. Instead, the tree is walked a second
 *  time. This is actually faster because the "Ewald-Treewalk" can use a
 *  different opening criterion than the normal tree walk. In particular,
 *  the Ewald correction is negligible for particles that are very close,
 *  but it is large for particles that are far away (this is quite
 *  different for the normal direct force). So we can here use a different
 *  opening criterion. Sufficient accuracy is usually obtained if the node
 *  length has dropped to a certain fraction ~< 0.25 of the
 *  BoxLength. However, we may only short-cut the interaction list of the
 *  normal full Ewald tree walk if we are sure that the whole node and all
 *  daughter nodes "lie on the same side" of the periodic boundary,
 *  i.e. that the real tree walk would not find a daughter node or particle
 *  that was mapped to a different nearest neighbour position when the tree
 *  walk would be further refined.
 */
int force_treeevaluate_ewald_correction(Tree *self, int target, int mode,
                                        double pos_x, double pos_y,
                                        double pos_z, double aold) {
  struct NODE *nop = 0;
  int no, cost;
  double dx, dy, dz, mass, r2;
  int signx, signy, signz;
  int i, j, k, openflag;
  double u, v, w;
  double f1, f2, f3, f4, f5, f6, f7, f8;
  double acc_x, acc_y, acc_z;
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;

  acc_x = 0;
  acc_y = 0;
  acc_z = 0;
  cost = 0;

  no = self->All.MaxPart;

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;
      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }

        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;
      mass = nop->u.d.mass;
    }

    dx = force_nearest(dx, boxsize, boxhalf);
    dy = force_nearest(dy, boxsize, boxhalf);
    dz = force_nearest(dz, boxsize, boxhalf);

    if (no < self->All.MaxPart)
      no = self->Nextnode[no];
    else /* we have an  internal node. Need to check opening criterion */
    {
      openflag = 0;

      r2 = dx * dx + dy * dy + dz * dz;

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          openflag = 1;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          openflag = 1;
        } else {
          if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
            if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
              if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
                openflag = 1;
              }
            }
          }
        }
      }

      if (openflag) {
        /* now we check if we can avoid opening the cell */

        u = nop->center[0] - pos_x;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        u = nop->center[1] - pos_y;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        u = nop->center[2] - pos_z;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        /* if the cell is too large, we need to refine
         * it further
         */
        if (nop->len > 0.20 * boxsize) {
          /* cell is too large */
          no = nop->u.d.nextnode;
          continue;
        }
      }

      no = nop->u.d.sibling; /* ok, node can be used */

      if (mode == 1) {
        if ((nop->u.d.bitflags &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    /* compute the Ewald correction force */

    if (dx < 0) {
      dx = -dx;
      signx = +1;
    } else
      signx = -1;

    if (dy < 0) {
      dy = -dy;
      signy = +1;
    } else
      signy = -1;

    if (dz < 0) {
      dz = -dz;
      signz = +1;
    } else
      signz = -1;

    u = dx * self->fac_intp;
    i = (int)u;
    if (i >= EN) i = EN - 1;
    u -= i;
    v = dy * self->fac_intp;
    j = (int)v;
    if (j >= EN) j = EN - 1;
    v -= j;
    w = dz * self->fac_intp;
    k = (int)w;
    if (k >= EN) k = EN - 1;
    w -= k;

    /* compute factors for trilinear interpolation */

    f1 = (1 - u) * (1 - v) * (1 - w);
    f2 = (1 - u) * (1 - v) * (w);
    f3 = (1 - u) * (v) * (1 - w);
    f4 = (1 - u) * (v) * (w);
    f5 = (u) * (1 - v) * (1 - w);
    f6 = (u) * (1 - v) * (w);
    f7 = (u) * (v) * (1 - w);
    f8 = (u) * (v) * (w);

    acc_x +=
        mass * signx *
        (self->fcorrx[i][j][k] * f1 + self->fcorrx[i][j][k + 1] * f2 +
         self->fcorrx[i][j + 1][k] * f3 + self->fcorrx[i][j + 1][k + 1] * f4 +
         self->fcorrx[i + 1][j][k] * f5 + self->fcorrx[i + 1][j][k + 1] * f6 +
         self->fcorrx[i + 1][j + 1][k] * f7 +
         self->fcorrx[i + 1][j + 1][k + 1] * f8);

    acc_y +=
        mass * signy *
        (self->fcorry[i][j][k] * f1 + self->fcorry[i][j][k + 1] * f2 +
         self->fcorry[i][j + 1][k] * f3 + self->fcorry[i][j + 1][k + 1] * f4 +
         self->fcorry[i + 1][j][k] * f5 + self->fcorry[i + 1][j][k + 1] * f6 +
         self->fcorry[i + 1][j + 1][k] * f7 +
         self->fcorry[i + 1][j + 1][k + 1] * f8);

    acc_z +=
        mass * signz *
        (self->fcorrz[i][j][k] * f1 + self->fcorrz[i][j][k + 1] * f2 +
         self->fcorrz[i][j + 1][k] * f3 + self->fcorrz[i][j + 1][k + 1] * f4 +
         self->fcorrz[i + 1][j][k] * f5 + self->fcorrz[i + 1][j][k + 1] * f6 +
         self->fcorrz[i + 1][j + 1][k] * f7 +
         self->fcorrz[i + 1][j + 1][k + 1] * f8);
    cost++;
  }

  /* add the result at the proper place */

  if (mode == 0) {
    self->P[target].GravAccel[0] += acc_x;
    self->P[target].GravAccel[1] += acc_y;
    self->P[target].GravAccel[2] += acc_z;
    // self->P[target].GravCost += cost;
  } else {
    self->GravDataResult[target].u.Acc[0] += acc_x;
    self->GravDataResult[target].u.Acc[1] += acc_y;
    self->GravDataResult[target].u.Acc[2] += acc_z;
    self->GravDataResult[target].w.Ninteractions += cost;
  }

  return cost;
}

/*! This routine computes the gravitational potential by walking the
 *  tree. The same opening criteria is used as for the gravitational force
 *  walk.
 */
void force_treeevaluate_potential_sub(Tree *self, int target, int mode) {
  struct NODE *nop = 0;
  int no, ptype;
  double r2, dx, dy, dz, mass, r, u, h, h_inv, wp;
  double pot, pos_x, pos_y, pos_z, aold;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
  double soft = 0;
#endif
  //#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;
  //#endif

  pot = 0;

  if (mode == 0) {
    pos_x = self->Q[target].Pos[0];
    pos_y = self->Q[target].Pos[1];
    pos_z = self->Q[target].Pos[2];
    ptype = self->Q[target].Type;
//      aold = All.ErrTolForceAcc * self->Q[target].OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = SphP[target].Hsml;
#endif
  } else {
    pos_x = self->GravDataGet[target].u.Pos[0];
    pos_y = self->GravDataGet[target].u.Pos[1];
    pos_z = self->GravDataGet[target].u.Pos[2];
#ifdef UNEQUALSOFTENINGS
    ptype = self->GravDataGet[target].Type;
#else
    ptype = self->P[0].Type;
#endif
//      aold = All.ErrTolForceAcc * GravDataGet[target].w.OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = GravDataGet[target].Soft;
#endif
  }

#ifndef UNEQUALSOFTENINGS
  h = self->ForceSofteningQ;
  h_inv = 1.0 / h;
#endif
  no = self->All.MaxPart;

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;
      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;
      mass = nop->u.d.mass;
    }

    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      dx = force_nearest(dx, boxsize, boxhalf);
      dy = force_nearest(dy, boxsize, boxhalf);
      dz = force_nearest(dz, boxsize, boxhalf);
    }
    //#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) {
#ifdef UNEQUALSOFTENINGS
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
      if (ptype == 0)
        h = soft;
      else
        h = self->ForceSofteningQ;

      if (self->P[no].Type == 0) {
        if (h < self->SphP[no].Hsml) h = self->SphP[no].Hsml;
      } else {
        if (h < self->All.ForceSoftening[self->P[no].Type])
          h = self->All.ForceSoftening[self->P[no].Type];
      }
#else
      h = self->ForceSofteningQ;
      if (h < self->All.ForceSoftening[P[no].Type])
        h = self->All.ForceSoftening[P[no].Type];
#endif
#endif
      no = self->Nextnode[no];
    } else /* we have an internal node. Need to check opening criterion */
    {
      if (mode == 1) {
        if ((nop->u.d.bitflags & 3) == 1) /* if it's a top-level node
                                           * which does not contain
                                           * local particles we can make
                                           * a short-cut
                                           */
        {
          no = nop->u.d.sibling;
          continue;
        }
      }

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }

        if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
          if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
            if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
      h = self->ForceSofteningQ;
      maxsofttype = (nop->u.d.bitflags >> 2) & 7;
      if (maxsofttype == 7) /* may only occur for zero mass top-level nodes */
      {
        if (mass > 0) endrun(self, 988);
        no = nop->u.d.nextnode;
        continue;
      } else {
        if (h < self->All.ForceSoftening[maxsofttype]) {
          h = self->All.ForceSoftening[maxsofttype];
          if (r2 < h * h) {
            if (((nop->u.d.bitflags >> 5) &
                 1)) /* bit-5 signals that there are particles of different
                        softening in the node */
            {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#else
      if (ptype == 0)
        h = soft;
      else
        h = self->ForceSofteningQ;

      if (h < nop->maxsoft) {
        h = nop->maxsoft;
        if (r2 < h * h) {
          no = nop->u.d.nextnode;
          continue;
        }
      }
#endif
#endif

      no = nop->u.d.sibling; /* node can be used */

      if (mode == 1) {
        if (((nop->u.d.bitflags) &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    r = sqrt(r2);

    if (r >= h)
      pot -= mass / r;
    else {
#ifdef UNEQUALSOFTENINGS
      h_inv = 1.0 / h;
#endif
      u = r * h_inv;

      if (u < 0.5)
        wp = -2.8 + u * u * (5.333333333333 + u * u * (6.4 * u - 9.6));
      else
        wp = -3.2 + 0.066666666667 / u +
             u * u *
                 (10.666666666667 +
                  u * (-16.0 + u * (9.6 - 2.133333333333 * u)));

      pot += mass * h_inv * wp;
    }
    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn)
      pot += mass * ewald_pot_corr(self, dx, dy, dz);
    //#endif
  }

  /* store result at the proper place */

  if (mode == 0)
    self->Q[target].Potential = pot;
  else
    self->GravDataResult[target].u.Potential = pot;
}

/*! This routine computes the gravitational force for a given local
 *  particle, or for a particle in the communication buffer. Depending on
 *  the value of TypeOfOpeningCriterion, either the geometrical BH
 *  cell-opening criterion, or the `relative' opening criterion is used.
 */
int force_treeevaluate_sub(Tree *self, int target, int mode,
                           double *ewaldcountsum) {
  struct NODE *nop = 0;
  int no, ninteractions, ptype;
  double r2, dx, dy, dz, mass, r, fac, u, h, h_inv, h3_inv;
  double acc_x, acc_y, acc_z, pos_x, pos_y, pos_z, aold;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
  double soft = 0;
#endif
  //#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;
  //#endif

  acc_x = 0;
  acc_y = 0;
  acc_z = 0;
  ninteractions = 0;

  if (mode == 0) {
    pos_x = self->Q[target].Pos[0];
    pos_y = self->Q[target].Pos[1];
    pos_z = self->Q[target].Pos[2];
    ptype = self->Q[target].Type;
    aold = self->All.ErrTolForceAcc * self->Q[target].OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = SphP[target].Hsml;
#endif
  } else {
    pos_x = self->GravDataGet[target].u.Pos[0];
    pos_y = self->GravDataGet[target].u.Pos[1];
    pos_z = self->GravDataGet[target].u.Pos[2];
#ifdef UNEQUALSOFTENINGS
    ptype = self->GravDataGet[target].Type;
#else
    ptype = self->P[0].Type;
#endif
    aold = self->All.ErrTolForceAcc * self->GravDataGet[target].w.OldAcc;
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
    if (ptype == 0) soft = self->GravDataGet[target].Soft;
#endif
  }

#ifndef UNEQUALSOFTENINGS
  h = self->ForceSofteningQ;
  h_inv = 1.0 / h;
  h3_inv = h_inv * h_inv * h_inv;
#endif
  no = self->All.MaxPart; /* root node */

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;

      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }
      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;

      mass = nop->u.d.mass;
    }
    //#ifdef PERIODIC
    if (self->All.PeriodicBoundariesOn) {
      dx = force_nearest(dx, boxsize, boxhalf);
      dy = force_nearest(dy, boxsize, boxhalf);
      dz = force_nearest(dz, boxsize, boxhalf);
    }
    //#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) {
#ifdef UNEQUALSOFTENINGS
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
      if (ptype == 0)
        h = soft;
      else
        h = self->ForceSofteningQ;

      if (self->P[no].Type == 0) {
        if (h < self->SphP[no].Hsml) h = self->SphP[no].Hsml;
      } else {
        if (h < self->All.ForceSoftening[P[no].Type])
          h = self->All.ForceSoftening[P[no].Type];
      }
#else
      h = self->ForceSofteningQ;
      if (h < self->All.ForceSoftening[P[no].Type])
        h = self->All.ForceSoftening[P[no].Type];
#endif
#endif
      no = self->Nextnode[no];
    } else /* we have an  internal node. Need to check opening criterion */
    {
      if (mode == 1) {
        if ((nop->u.d.bitflags & 3) == 1) /* if it's a top-level node
                                           * which does not contain
                                           * local particles we can
                                           * continue to do a short-cut */
        {
          no = nop->u.d.sibling;
          continue;
        }
      }

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }

        /* check in addition whether we lie inside the cell */

        if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
          if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
            if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }

#ifdef UNEQUALSOFTENINGS
#ifndef ADAPTIVE_GRAVSOFT_FORGAS
      h = self->ForceSofteningQ;
      maxsofttype = (nop->u.d.bitflags >> 2) & 7;
      if (maxsofttype == 7) /* may only occur for zero mass top-level nodes */
      {
        if (mass > 0) endrun(self, 986);
        no = nop->u.d.nextnode;
        continue;
      } else {
        if (h < self->All.ForceSoftening[maxsofttype]) {
          h = self->All.ForceSoftening[maxsofttype];
          if (r2 < h * h) {
            if (((nop->u.d.bitflags >> 5) &
                 1)) /* bit-5 signals that there are particles of different
                        softening in the node */
            {
              no = nop->u.d.nextnode;
              continue;
            }
          }
        }
      }
#else
      if (ptype == 0)
        h = soft;
      else
        h = self->ForceSofteningQ;

      if (h < nop->maxsoft) {
        h = nop->maxsoft;
        if (r2 < h * h) {
          no = nop->u.d.nextnode;
          continue;
        }
      }
#endif
#endif

      no = nop->u.d.sibling; /* ok, node can be used */

      if (mode == 1) {
        if (((nop->u.d.bitflags) &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    r = sqrt(r2);

    if (r >= h)
      fac = mass / (r2 * r);
    else {
#ifdef UNEQUALSOFTENINGS
      h_inv = 1.0 / h;
      h3_inv = h_inv * h_inv * h_inv;
#endif
      u = r * h_inv;
      if (u < 0.5)
        fac = mass * h3_inv * (10.666666666667 + u * u * (32.0 * u - 38.4));
      else
        fac = mass * h3_inv *
              (21.333333333333 - 48.0 * u + 38.4 * u * u -
               10.666666666667 * u * u * u - 0.066666666667 / (u * u * u));
    }

    acc_x += dx * fac;
    acc_y += dy * fac;
    acc_z += dz * fac;

    ninteractions++;
  }

  /* store result at the proper place */
  if (mode == 0) {
    self->Q[target].GravAccel[0] = acc_x;
    self->Q[target].GravAccel[1] = acc_y;
    self->Q[target].GravAccel[2] = acc_z;
    // self->Q[target].GravCost = ninteractions;
  } else {
    self->GravDataResult[target].u.Acc[0] = acc_x;
    self->GravDataResult[target].u.Acc[1] = acc_y;
    self->GravDataResult[target].u.Acc[2] = acc_z;
    self->GravDataResult[target].w.Ninteractions = ninteractions;
  }

  //#ifdef PERIODIC
  if (self->All.PeriodicBoundariesOn)
    *ewaldcountsum += force_treeevaluate_ewald_correction_sub(
        self, target, mode, pos_x, pos_y, pos_z, aold);
  //#endif

  return ninteractions;
}

/*! This function computes the Ewald correction, and is needed if periodic
 *  boundary conditions together with a pure tree algorithm are used. Note
 *  that the ordinary tree walk does not carry out this correction directly
 *  as it was done in Gadget-1.1. Instead, the tree is walked a second
 *  time. This is actually faster because the "Ewald-Treewalk" can use a
 *  different opening criterion than the normal tree walk. In particular,
 *  the Ewald correction is negligible for particles that are very close,
 *  but it is large for particles that are far away (this is quite
 *  different for the normal direct force). So we can here use a different
 *  opening criterion. Sufficient accuracy is usually obtained if the node
 *  length has dropped to a certain fraction ~< 0.25 of the
 *  BoxLength. However, we may only short-cut the interaction list of the
 *  normal full Ewald tree walk if we are sure that the whole node and all
 *  daughter nodes "lie on the same side" of the periodic boundary,
 *  i.e. that the real tree walk would not find a daughter node or particle
 *  that was mapped to a different nearest neighbour position when the tree
 *  walk would be further refined.
 */
int force_treeevaluate_ewald_correction_sub(Tree *self, int target, int mode,
                                            double pos_x, double pos_y,
                                            double pos_z, double aold) {
  struct NODE *nop = 0;
  int no, cost;
  double dx, dy, dz, mass, r2;
  int signx, signy, signz;
  int i, j, k, openflag;
  double u, v, w;
  double f1, f2, f3, f4, f5, f6, f7, f8;
  double acc_x, acc_y, acc_z;
  double boxsize, boxhalf;

  boxsize = self->All.BoxSize;
  boxhalf = 0.5 * self->All.BoxSize;

  acc_x = 0;
  acc_y = 0;
  acc_z = 0;
  cost = 0;

  no = self->All.MaxPart;

  while (no >= 0) {
    if (no < self->All.MaxPart) /* single particle */
    {
      /* the index of the node is the index of the particle */
      /* observe the sign */

      dx = self->P[no].Pos[0] - pos_x;
      dy = self->P[no].Pos[1] - pos_y;
      dz = self->P[no].Pos[2] - pos_z;
      mass = self->P[no].Mass;
    } else {
      if (no >= self->All.MaxPart + self->MaxNodes) /* pseudo particle */
      {
        if (mode == 0) {
          self->Exportflag[self->DomainTask[no - (self->All.MaxPart +
                                                  self->MaxNodes)]] = 1;
        }

        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;
      mass = nop->u.d.mass;
    }

    dx = force_nearest(dx, boxsize, boxhalf);
    dy = force_nearest(dy, boxsize, boxhalf);
    dz = force_nearest(dz, boxsize, boxhalf);

    if (no < self->All.MaxPart)
      no = self->Nextnode[no];
    else /* we have an  internal node. Need to check opening criterion */
    {
      openflag = 0;

      r2 = dx * dx + dy * dy + dz * dz;

      if (self->All.ErrTolTheta) /* check Barnes-Hut opening criterion */
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          openflag = 1;
        }
      } else /* check relative opening criterion */
      {
        if (mass * nop->len * nop->len > r2 * r2 * aold) {
          openflag = 1;
        } else {
          if (fabs(nop->center[0] - pos_x) < 0.60 * nop->len) {
            if (fabs(nop->center[1] - pos_y) < 0.60 * nop->len) {
              if (fabs(nop->center[2] - pos_z) < 0.60 * nop->len) {
                openflag = 1;
              }
            }
          }
        }
      }

      if (openflag) {
        /* now we check if we can avoid opening the cell */

        u = nop->center[0] - pos_x;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        u = nop->center[1] - pos_y;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        u = nop->center[2] - pos_z;
        if (u > boxhalf) u -= boxsize;
        if (u < -boxhalf) u += boxsize;

        if (fabs(u) > 0.5 * (boxsize - nop->len)) {
          no = nop->u.d.nextnode;
          continue;
        }

        /* if the cell is too large, we need to refine
         * it further
         */
        if (nop->len > 0.20 * boxsize) {
          /* cell is too large */
          no = nop->u.d.nextnode;
          continue;
        }
      }

      no = nop->u.d.sibling; /* ok, node can be used */

      if (mode == 1) {
        if ((nop->u.d.bitflags &
             1)) /* Bit 0 signals that this node belongs to top-level tree */
          continue;
      }
    }

    /* compute the Ewald correction force */

    if (dx < 0) {
      dx = -dx;
      signx = +1;
    } else
      signx = -1;

    if (dy < 0) {
      dy = -dy;
      signy = +1;
    } else
      signy = -1;

    if (dz < 0) {
      dz = -dz;
      signz = +1;
    } else
      signz = -1;

    u = dx * self->fac_intp;
    i = (int)u;
    if (i >= EN) i = EN - 1;
    u -= i;
    v = dy * self->fac_intp;
    j = (int)v;
    if (j >= EN) j = EN - 1;
    v -= j;
    w = dz * self->fac_intp;
    k = (int)w;
    if (k >= EN) k = EN - 1;
    w -= k;

    /* compute factors for trilinear interpolation */

    f1 = (1 - u) * (1 - v) * (1 - w);
    f2 = (1 - u) * (1 - v) * (w);
    f3 = (1 - u) * (v) * (1 - w);
    f4 = (1 - u) * (v) * (w);
    f5 = (u) * (1 - v) * (1 - w);
    f6 = (u) * (1 - v) * (w);
    f7 = (u) * (v) * (1 - w);
    f8 = (u) * (v) * (w);

    acc_x +=
        mass * signx *
        (self->fcorrx[i][j][k] * f1 + self->fcorrx[i][j][k + 1] * f2 +
         self->fcorrx[i][j + 1][k] * f3 + self->fcorrx[i][j + 1][k + 1] * f4 +
         self->fcorrx[i + 1][j][k] * f5 + self->fcorrx[i + 1][j][k + 1] * f6 +
         self->fcorrx[i + 1][j + 1][k] * f7 +
         self->fcorrx[i + 1][j + 1][k + 1] * f8);

    acc_y +=
        mass * signy *
        (self->fcorry[i][j][k] * f1 + self->fcorry[i][j][k + 1] * f2 +
         self->fcorry[i][j + 1][k] * f3 + self->fcorry[i][j + 1][k + 1] * f4 +
         self->fcorry[i + 1][j][k] * f5 + self->fcorry[i + 1][j][k + 1] * f6 +
         self->fcorry[i + 1][j + 1][k] * f7 +
         self->fcorry[i + 1][j + 1][k + 1] * f8);

    acc_z +=
        mass * signz *
        (self->fcorrz[i][j][k] * f1 + self->fcorrz[i][j][k + 1] * f2 +
         self->fcorrz[i][j + 1][k] * f3 + self->fcorrz[i][j + 1][k + 1] * f4 +
         self->fcorrz[i + 1][j][k] * f5 + self->fcorrz[i + 1][j][k + 1] * f6 +
         self->fcorrz[i + 1][j + 1][k] * f7 +
         self->fcorrz[i + 1][j + 1][k + 1] * f8);
    cost++;
  }

  /* add the result at the proper place */

  if (mode == 0) {
    self->Q[target].GravAccel[0] += acc_x;
    self->Q[target].GravAccel[1] += acc_y;
    self->Q[target].GravAccel[2] += acc_z;
    // self->P[target].GravCost += cost;
  } else {
    self->GravDataResult[target].u.Acc[0] += acc_x;
    self->GravDataResult[target].u.Acc[1] += acc_y;
    self->GravDataResult[target].u.Acc[2] += acc_z;
    self->GravDataResult[target].w.Ninteractions += cost;
  }

  return cost;
}

/*! This function initializes tables with the correction force and the
 *  correction potential due to the periodic images of a point mass located
 *  at the origin. These corrections are obtained by Ewald summation. (See
 *  Hernquist, Bouchet, Suto, ApJS, 1991, 75, 231) The correction fields
 *  are used to obtain the full periodic force if periodic boundaries
 *  combined with the pure tree algorithm are used. For the TreePM
 *  algorithm, the Ewald correction is not used.
 *
 *  The correction fields are stored on disk once they are computed. If a
 *  corresponding file is found, they are loaded from disk to speed up the
 *  initialization.  The Ewald summation is done in parallel, i.e. the
 *  processors share the work to compute the tables if needed.
 */
void ewald_init(Tree *self) {
  int i, j, k, beg, len, size, n, task, count;
  double x[3], force[3];
  char buf[200];
  FILE *fd;

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("initialize Ewald correction...\n");
    fflush(stdout);
  }

#ifdef DOUBLEPRECISION
  sprintf(buf, "ewald_spc_table_%d_dbl.dat", EN);
#else
  sprintf(buf, "ewald_spc_table_%d.dat", EN);
#endif

  if ((fd = fopen(buf, "r"))) {
    if (self->ThisTask == 0 && self->All.OutputInfo) {
      printf("\nreading Ewald tables from file `%s'\n", buf);
      fflush(stdout);
    }

    my_fread(self, &self->fcorrx[0][0][0], sizeof(FLOAT),
             (EN + 1) * (EN + 1) * (EN + 1), fd);
    my_fread(self, &self->fcorry[0][0][0], sizeof(FLOAT),
             (EN + 1) * (EN + 1) * (EN + 1), fd);
    my_fread(self, &self->fcorrz[0][0][0], sizeof(FLOAT),
             (EN + 1) * (EN + 1) * (EN + 1), fd);
    my_fread(self, &self->potcorr[0][0][0], sizeof(FLOAT),
             (EN + 1) * (EN + 1) * (EN + 1), fd);
    fclose(fd);
  } else {
    if (self->ThisTask == 0 && self->All.OutputInfo) {
      printf("\nNo Ewald tables in file `%s' found.\nRecomputing them...\n",
             buf);
      fflush(stdout);
    }

    /* ok, let's recompute things. Actually, we do that in parallel. */

    size = (EN + 1) * (EN + 1) * (EN + 1) / self->NTask;

    beg = self->ThisTask * size;
    len = size;
    if (self->ThisTask == (self->NTask - 1))
      len = (EN + 1) * (EN + 1) * (EN + 1) - beg;

    for (i = 0, count = 0; i <= EN; i++)
      for (j = 0; j <= EN; j++)
        for (k = 0; k <= EN; k++) {
          n = (i * (EN + 1) + j) * (EN + 1) + k;
          if (n >= beg && n < (beg + len)) {
            if (self->ThisTask == 0 && self->All.OutputInfo) {
              if ((count % (len / 20)) == 0) {
                printf("%4.1f percent done\n", count / (len / 100.0));
                fflush(stdout);
              }
            }

            x[0] = 0.5 * ((double)i) / EN;
            x[1] = 0.5 * ((double)j) / EN;
            x[2] = 0.5 * ((double)k) / EN;

            ewald_force(i, j, k, x, force);

            self->fcorrx[i][j][k] = force[0];
            self->fcorry[i][j][k] = force[1];
            self->fcorrz[i][j][k] = force[2];

            if (i + j + k == 0)
              self->potcorr[i][j][k] = 2.8372975;
            else
              self->potcorr[i][j][k] = ewald_psi(x);

            count++;
          }
        }

    for (task = 0; task < self->NTask; task++) {
      beg = task * size;
      len = size;
      if (task == (self->NTask - 1)) len = (EN + 1) * (EN + 1) * (EN + 1) - beg;

#ifdef DOUBLEPRECISION
      MPI_Bcast(&self->fcorrx[0][0][beg], len, MPI_DOUBLE, task,
                MPI_COMM_WORLD);
      MPI_Bcast(&self->fcorry[0][0][beg], len, MPI_DOUBLE, task,
                MPI_COMM_WORLD);
      MPI_Bcast(&self->fcorrz[0][0][beg], len, MPI_DOUBLE, task,
                MPI_COMM_WORLD);
      MPI_Bcast(&self->potcorr[0][0][beg], len, MPI_DOUBLE, task,
                MPI_COMM_WORLD);
#else
      MPI_Bcast(&self->fcorrx[0][0][beg], len, MPI_FLOAT, task, MPI_COMM_WORLD);
      MPI_Bcast(&self->fcorry[0][0][beg], len, MPI_FLOAT, task, MPI_COMM_WORLD);
      MPI_Bcast(&self->fcorrz[0][0][beg], len, MPI_FLOAT, task, MPI_COMM_WORLD);
      MPI_Bcast(&self->potcorr[0][0][beg], len, MPI_FLOAT, task,
                MPI_COMM_WORLD);
#endif
    }

    if (self->ThisTask == 0 && self->All.OutputInfo) {
      printf("\nwriting Ewald tables to file `%s'\n", buf);
      fflush(stdout);

      if ((fd = fopen(buf, "w"))) {
        my_fwrite(self, &self->fcorrx[0][0][0], sizeof(FLOAT),
                  (EN + 1) * (EN + 1) * (EN + 1), fd);
        my_fwrite(self, &self->fcorry[0][0][0], sizeof(FLOAT),
                  (EN + 1) * (EN + 1) * (EN + 1), fd);
        my_fwrite(self, &self->fcorrz[0][0][0], sizeof(FLOAT),
                  (EN + 1) * (EN + 1) * (EN + 1), fd);
        my_fwrite(self, &self->potcorr[0][0][0], sizeof(FLOAT),
                  (EN + 1) * (EN + 1) * (EN + 1), fd);
        fclose(fd);
      }
    }
  }

  self->fac_intp = 2 * EN / self->All.BoxSize;

  for (i = 0; i <= EN; i++)
    for (j = 0; j <= EN; j++)
      for (k = 0; k <= EN; k++) {
        self->potcorr[i][j][k] /= self->All.BoxSize;
        self->fcorrx[i][j][k] /= self->All.BoxSize * self->All.BoxSize;
        self->fcorry[i][j][k] /= self->All.BoxSize * self->All.BoxSize;
        self->fcorrz[i][j][k] /= self->All.BoxSize * self->All.BoxSize;
      }

  if (self->ThisTask == 0 && self->All.OutputInfo) {
    printf("initialization of periodic boundaries finished.\n");
    fflush(stdout);
  }
}

/*! This function looks up the correction potential due to the infinite
 *  number of periodic particle/node images. We here use tri-linear
 *  interpolation to get it from the precomputed table, which contains
 *  one octant around the target particle at the origin. The other
 *  octants are obtained from it by exploiting symmetry properties.
 */
double ewald_pot_corr(Tree *self, double dx, double dy, double dz) {
  int i, j, k;
  double u, v, w;
  double f1, f2, f3, f4, f5, f6, f7, f8;

  if (dx < 0) dx = -dx;

  if (dy < 0) dy = -dy;

  if (dz < 0) dz = -dz;

  u = dx * self->fac_intp;
  i = (int)u;
  if (i >= EN) i = EN - 1;
  u -= i;
  v = dy * self->fac_intp;
  j = (int)v;
  if (j >= EN) j = EN - 1;
  v -= j;
  w = dz * self->fac_intp;
  k = (int)w;
  if (k >= EN) k = EN - 1;
  w -= k;

  f1 = (1 - u) * (1 - v) * (1 - w);
  f2 = (1 - u) * (1 - v) * (w);
  f3 = (1 - u) * (v) * (1 - w);
  f4 = (1 - u) * (v) * (w);
  f5 = (u) * (1 - v) * (1 - w);
  f6 = (u) * (1 - v) * (w);
  f7 = (u) * (v) * (1 - w);
  f8 = (u) * (v) * (w);

  return self->potcorr[i][j][k] * f1 + self->potcorr[i][j][k + 1] * f2 +
         self->potcorr[i][j + 1][k] * f3 + self->potcorr[i][j + 1][k + 1] * f4 +
         self->potcorr[i + 1][j][k] * f5 + self->potcorr[i + 1][j][k + 1] * f6 +
         self->potcorr[i + 1][j + 1][k] * f7 +
         self->potcorr[i + 1][j + 1][k + 1] * f8;
}

/*! This function computes the potential correction term by means of Ewald
 *  summation.
 */
double ewald_psi(double x[3]) {
  double alpha, psi;
  double r, sum1, sum2, hdotx;
  double dx[3];
  int i, n[3], h[3], h2;

  alpha = 2.0;

  for (n[0] = -4, sum1 = 0; n[0] <= 4; n[0]++)
    for (n[1] = -4; n[1] <= 4; n[1]++)
      for (n[2] = -4; n[2] <= 4; n[2]++) {
        for (i = 0; i < 3; i++) dx[i] = x[i] - n[i];

        r = sqrt(dx[0] * dx[0] + dx[1] * dx[1] + dx[2] * dx[2]);
        sum1 += erfc(alpha * r) / r;
      }

  for (h[0] = -4, sum2 = 0; h[0] <= 4; h[0]++)
    for (h[1] = -4; h[1] <= 4; h[1]++)
      for (h[2] = -4; h[2] <= 4; h[2]++) {
        hdotx = x[0] * h[0] + x[1] * h[1] + x[2] * h[2];
        h2 = h[0] * h[0] + h[1] * h[1] + h[2] * h[2];
        if (h2 > 0)
          sum2 += 1 / (M_PI * h2) * exp(-M_PI * M_PI * h2 / (alpha * alpha)) *
                  cos(2 * M_PI * hdotx);
      }

  r = sqrt(x[0] * x[0] + x[1] * x[1] + x[2] * x[2]);

  psi = M_PI / (alpha * alpha) - sum1 - sum2 + 1 / r;

  return psi;
}

/*! This function computes the force correction term (difference between full
 *  force of infinite lattice and nearest image) by Ewald summation.
 */
void ewald_force(int iii, int jjj, int kkk, double x[3], double force[3]) {
  double alpha, r2;
  double r, val, hdotx, dx[3];
  int i, h[3], n[3], h2;

  alpha = 2.0;

  for (i = 0; i < 3; i++) force[i] = 0;

  if (iii == 0 && jjj == 0 && kkk == 0) return;

  r2 = x[0] * x[0] + x[1] * x[1] + x[2] * x[2];

  for (i = 0; i < 3; i++) force[i] += x[i] / (r2 * sqrt(r2));

  for (n[0] = -4; n[0] <= 4; n[0]++)
    for (n[1] = -4; n[1] <= 4; n[1]++)
      for (n[2] = -4; n[2] <= 4; n[2]++) {
        for (i = 0; i < 3; i++) dx[i] = x[i] - n[i];

        r = sqrt(dx[0] * dx[0] + dx[1] * dx[1] + dx[2] * dx[2]);

        val = erfc(alpha * r) +
              2 * alpha * r / sqrt(M_PI) * exp(-alpha * alpha * r * r);

        for (i = 0; i < 3; i++) force[i] -= dx[i] / (r * r * r) * val;
      }

  for (h[0] = -4; h[0] <= 4; h[0]++)
    for (h[1] = -4; h[1] <= 4; h[1]++)
      for (h[2] = -4; h[2] <= 4; h[2]++) {
        hdotx = x[0] * h[0] + x[1] * h[1] + x[2] * h[2];
        h2 = h[0] * h[0] + h[1] * h[1] + h[2] * h[2];

        if (h2 > 0) {
          val = 2.0 / ((double)h2) * exp(-M_PI * M_PI * h2 / (alpha * alpha)) *
                sin(2 * M_PI * hdotx);

          for (i = 0; i < 3; i++) force[i] -= h[i] * val;
        }
      }
}
