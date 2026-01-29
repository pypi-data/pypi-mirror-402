#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#define FLOAT float
typedef long long peanokey;

#define MAXTOPNODES 200000
#define MAX_REAL_NUMBER 1e37
#define BITS_PER_DIMENSION 18
#define PEANOCELLS (((peanokey)1) << (3 * BITS_PER_DIMENSION))

#ifndef TWODIMS
#define NUMDIMS 3 /*!< For 3D-normalized kernel */
#define KERNEL_COEFF_1 \
  2.546479089470 /*!< Coefficients for SPH spline kernel and its derivative */
#define KERNEL_COEFF_2 15.278874536822
#define KERNEL_COEFF_3 45.836623610466
#define KERNEL_COEFF_4 30.557749073644
#define KERNEL_COEFF_5 5.092958178941
#define KERNEL_COEFF_6 (-15.278874536822)
#define NORM_COEFF                                                            \
  4.188790204786 /*!< Coefficient for kernel normalization. Note:  4.0/3 * PI \
                    = 4.188790204786 */
#else
#define NUMDIMS 2 /*!< For 2D-normalized kernel */
#define KERNEL_COEFF_1                                                       \
  (5.0 / 7 * 2.546479089470) /*!< Coefficients for SPH spline kernel and its \
                                derivative */
#define KERNEL_COEFF_2 (5.0 / 7 * 15.278874536822)
#define KERNEL_COEFF_3 (5.0 / 7 * 45.836623610466)
#define KERNEL_COEFF_4 (5.0 / 7 * 30.557749073644)
#define KERNEL_COEFF_5 (5.0 / 7 * 5.092958178941)
#define KERNEL_COEFF_6 (5.0 / 7 * (-15.278874536822))
#define NORM_COEFF M_PI /*!< Coefficient for kernel normalization. */
#endif

/******************************************************************************

SYSTEM

*******************************************************************************/

/*! returns the maximum of two double
 */
double dmax(double x, double y) {
  if (x > y)
    return x;
  else
    return y;
}

/******************************************************************************

TREE STRUCTURE

*******************************************************************************/

struct global_data_all_processes {

  long long TotNumPart;
  long long TotN_gas;

  int MaxPart;
  int MaxPartSph;
  double SofteningTable[6];
  double ForceSoftening[6];

  double PartAllocFactor;
  double TreeAllocFactor;

  double ErrTolTheta;

  double DesNumNgb;
  double MaxNumNgbDeviation;

  double MinGasHsmlFractional;
  double MinGasHsml;
};

struct particle_data {
  FLOAT Pos[3];       /*!< particle position at its current time */
  FLOAT Mass;         /*!< particle mass */
  FLOAT Vel[3];       /*!< particle velocity at its current time */
  FLOAT GravAccel[3]; /*!< particle acceleration due to gravity */
  FLOAT Potential;    /*!< gravitational potential */
  FLOAT OldAcc; /*!< magnitude of old gravitational force. Used in relative
                   opening criterion */
  int Type; /*!< flags particle type.  0=gas, 1=halo, 2=disk, 3=bulge, 4=stars,
               5=bndry */
  int Ti_endstep; /*!< marks start of current timestep of particle on integer
                     timeline */
  int Ti_begstep; /*!< marks end of current timestep of particle on integer
                     timeline */
  FLOAT Density;
  FLOAT Observable;
};

struct topnode_exchange {
  peanokey Startkey;
  int Count;
};

struct topnode_data {
  int Daughter; /*!< index of first daughter cell (out of 8) of top-level node
                 */
  int Pstart;   /*!< for the present top-level node, this gives the index of the
                   first node in the concatenated list of topnodes collected from
                   all processors */
  int Blocks;   /*!< for the present top-level node, this gives the number of
                   corresponding nodes in the concatenated list of topnodes
                   collected from all processors */
  int Leaf; /*!< if the node is a leaf, this gives its number when all leaves
               are traversed in Peano-Hilbert order */
  peanokey Size;     /*!< number of Peano-Hilbert mesh-cells represented by
                        top-level node */
  peanokey StartKey; /*!< first Peano-Hilbert key in top-level node */
  long long Count; /*!< counts the number of particles in this top-level node */
};

typedef struct {
  PyObject_HEAD PyObject *first; /* first name */
  PyObject *list;
  int number;

  /* allvars */

  int Numnodestree;
  int MaxNodes;
  int NumPart;
  int N_gas;
  long long Ntype[6];

  int ThisTask;
  int NTask;

  struct NODE *Nodes_base;
  struct NODE *Nodes;
  struct topnode_data *TopNodes;

  peanokey *Key;
  peanokey *KeySorted;

  int *DomainNodeIndex;

  struct global_data_all_processes All;
  struct particle_data *P;

  double DomainCorner[3];
  double DomainCenter[3];
  double DomainLen;
  double DomainFac;
  int NTopnodes;

  int *Nextnode;
  int *Father;
  int NTopleaves;

  /* allvars.c */
  int NtypeLocal[6];

  /* domain */
  long long maxload, maxloadsph;
  // int *list_NumPart;
  // int *list_N_gas;

  /* force */
  int last;

  /* ngb */
  int *Ngblist;

} Tree;

/******************************************************************************

ENDRUN

*******************************************************************************/

/*!  This function aborts the simulations. If a single processors wants an
 *   immediate termination, the function needs to be called with ierr>0. A
 *   bunch of MPI-error messages may also appear in this case.  For ierr=0,
 *   MPI is gracefully cleaned up, but this requires that all processors
 *   call endrun().
 */
void endrun(Tree *self, int ierr) {
  if (ierr) {
    printf("task %d: endrun called with an error level of %d\n\n\n",
           self->ThisTask, ierr);
    fflush(stdout);
    exit(0);
  }

  //  MPI_Finalize();
  exit(0);
};

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

/******************************************************************************

DOMAIN THINGS

*******************************************************************************/

#define REDUC_FAC 0.98
#define TOPNODEFACTOR 20.0

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

/*! This function constructs the global top-level tree node that is used
 *  for the domain decomposition. This is done by considering the string of
 *  Peano-Hilbert keys for all particles, which is recursively chopped off
 *  in pieces of eight segments until each segment holds at most a certain
 *  number of particles.
 */
void domain_determineTopTree(Tree *self) {
  int i;

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

  /*  the rest of the function is only used for parallelisme  */
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

  // MPI_Allreduce(xmin, xmin_glob, 3, MPI_DOUBLE, MPI_MIN, MPI_COMM_WORLD);
  // MPI_Allreduce(xmax, xmax_glob, 3, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);

  for (j = 0; j < 3; j++) {
    xmin_glob[j] = xmin[j];
    xmax_glob[j] = xmax[j];
  }

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

/*! This function carries out the actual domain decomposition for all
 *  particle types. It will try to balance the work-load for each domain,
 *  as estimated based on the P[i]-GravCost values.  The decomposition will
 *  respect the maximum allowed memory-imbalance given by the value of
 *  PartAllocFactor.
 */
void domain_decompose(Tree *self) {
  int i;
  int ngrp;

  for (i = 0; i < 6; i++) self->NtypeLocal[i] = 0;

  for (i = 0; i < self->NumPart; i++) self->NtypeLocal[self->P[i].Type]++;

  /* because Ntype[] is of type `long long', we cannot do a simple
   * MPI_Allreduce() to sum the total particle numbers
   */

  for (i = 0; i < 6; i++) self->Ntype[i] = self->NtypeLocal[i];

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

  /* determine global dimensions of domain grid */
  domain_findExtent(self);

  domain_determineTopTree(self);
}

/*! This is the main routine for the domain decomposition.  It acts as a
 *  driver routine that allocates various temporary buffers, maps the
 *  particles back onto the periodic box if needed, and then does the
 *  domain decomposition, and a final Peano-Hilbert order of all particles
 *  as a tuning measure.
 */
void domain_Decomposition(Tree *self) {

#ifdef PERIODIC
  do_box_wrapping(); /* map the particles back onto the box */
#endif

  self->Key = malloc(sizeof(peanokey) * self->All.MaxPart);
  self->KeySorted = malloc(sizeof(peanokey) * self->All.MaxPart);

  domain_decompose(self);

#ifdef PEANOHILBERT
  t0 = second();
  peano_hilbert_order();
  t1 = second();
  All.CPU_Peano += timediff(t0, t1);
#endif

  free(self->KeySorted);
  free(self->Key);
  //    }
}

void domain_domainallocate(Tree *self) {
  self->TopNodes = malloc(MAXTOPNODES * sizeof(struct topnode_data));
  self->DomainNodeIndex = malloc(MAXTOPNODES * sizeof(int));
}

/******************************************************************************

FORCE THINGS

*******************************************************************************/

struct NODE {
  FLOAT len;       /*!< sidelength of treenode */
  FLOAT center[3]; /*!< geometrical center of node */

  union {
    int suns[8]; /*!< temporary pointers to daughter nodes */
    struct {
      FLOAT s[3];   /*!< center of mass of node */
      FLOAT mass;   /*!< mass of node */
      int bitflags; /*!< a bit-field with various information on the node */
      int sibling; /*!< this gives the next node in the walk in case the current
                      node can be used */
      int nextnode; /*!< this gives the next node in case the current node needs
                       to be opened */
      int father; /*!< this gives the parent node of each node (or -1 if we have
                     the root node) */
    } d;
  } u;
};

/*! This routine computes the gravitational force for a given local
 *  particle, or for a particle in the communication buffer. Depending on
 *  the value of TypeOfOpeningCriterion, either the geometrical BH
 *  cell-opening criterion, or the `relative' opening criterion is used.
 */
int force_treeevaluate_local(Tree *self, double pos_x, double pos_y,
                             double pos_z, double h, double *acc_x,
                             double *acc_y, double *acc_z) {
  struct NODE *nop = 0;
  int no, ninteractions;
  double r2, dx, dy, dz, mass, fac;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef ADAPTIVE_GRAVSOFT_FORGAS
  double soft = 0;
#endif
#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = All.BoxSize;
  boxhalf = 0.5 * All.BoxSize;
#endif

  *acc_x = 0;
  *acc_y = 0;
  *acc_z = 0;
  ninteractions = 0;

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
      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;

      mass = nop->u.d.mass;
    }
#ifdef PERIODIC
    dx = NEAREST(dx);
    dy = NEAREST(dy);
    dz = NEAREST(dz);
#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) {
      no = self->Nextnode[no];
    } else /* we have an  internal node. Need to check opening criterion */
    {
      if (nop->len * nop->len >
          r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
        /* open cell */
        no = nop->u.d.nextnode;
        continue;
      }

      no = nop->u.d.sibling; /* ok, node can be used */
    }

    /* here we use a plummer softening */
    if (r2 > 0) {
      fac = mass / pow(r2 + h * h, 3.0 / 2.0);

      *acc_x += dx * fac;
      *acc_y += dy * fac;
      *acc_z += dz * fac;
    }

    ninteractions++;
  }

#ifdef PERIODIC
  *ewaldcountsum += force_treeevaluate_ewald_correction(target, mode, pos_x,
                                                        pos_y, pos_z, aold);
#endif

  return ninteractions;
}

/*! This routine computes the gravitational potential by walking the
 *  tree. The same opening criteria is used as for the gravitational force
 *  walk.
 */
double force_treeevaluate_local_potential(Tree *self, double pos_x,
                                          double pos_y, double pos_z,
                                          double h) {
  struct NODE *nop = 0;
  int no;
  double r2, dx, dy, dz, mass;
  double pot;
#if defined(UNEQUALSOFTENINGS) && !defined(ADAPTIVE_GRAVSOFT_FORGAS)
  int maxsofttype;
#endif
#ifdef PERIODIC
  double boxsize, boxhalf;

  boxsize = All.BoxSize;
  boxhalf = 0.5 * All.BoxSize;
#endif

  pot = 0;

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
        printf("force_treeevaluate_local_potential : pseudo particle !\n");
        endrun(self, 1234);
      }

      nop = &self->Nodes[no];
      dx = nop->u.d.s[0] - pos_x;
      dy = nop->u.d.s[1] - pos_y;
      dz = nop->u.d.s[2] - pos_z;
      mass = nop->u.d.mass;
    }

#ifdef PERIODIC
    dx = NEAREST(dx);
    dy = NEAREST(dy);
    dz = NEAREST(dz);
#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (no < self->All.MaxPart) /* single particle */
    {
      no = self->Nextnode[no];
    } else /* we have an internal node. Need to check opening criterion */
    {
      {
        if (nop->len * nop->len >
            r2 * self->All.ErrTolTheta * self->All.ErrTolTheta) {
          /* open cell */
          no = nop->u.d.nextnode;
          continue;
        }
      }

      no = nop->u.d.sibling; /* node can be used */
    }

    /* here we use a plummer softening */
    if (r2 > 0) pot += -mass / sqrt(r2 + h * h);

#ifdef PERIODIC
    pot += mass * ewald_pot_corr(dx, dy, dz);
#endif
  }

  /* return result */
  return pot;
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

  // for(i = DomainMyStart; i <= DomainMyLast; i++)					/*
  // !!! warning
  // !!! */
  for (i = 0; i < self->NTopleaves; i++) {
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

  int maxsofttype, diffsoftflag;
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
    maxsofttype = 7;
    diffsoftflag = 0;

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

    self->Nodes[no].u.d.bitflags = 4 * maxsofttype + 32 * diffsoftflag;

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
  double lenhalf;
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
          printf("for particle %d (x=%g y=%g z=%g)\n", i, self->P[i].Pos[0], self->P[i].Pos[1], self->P[i].Pos[2]);
          // dump_particles();
          endrun(self, 1);
        }
      }
    }
  }

  /* insert the pseudo particles that represent the mass distribution of other
   * domains */
  // force_insert_pseudo_particles();

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

/*! This function is a driver routine for constructing the gravitational
 *  oct-tree, which is done by calling a small number of other functions.
 */
int force_treebuild(Tree *self, int npart) {
  self->Numnodestree = force_treebuild_single(self, npart);

  force_flag_localnodes(self);

  return self->Numnodestree;
}

/*! This function allocates the memory used for storage of the tree and of
 *  auxiliary arrays needed for tree-walk and link-lists.  Usually,
 *  maxnodes approximately equal to 0.7*maxpart is sufficient to store the
 *  tree for up to maxpart particles.
 */
void force_treeallocate(Tree *self, int maxnodes, int maxpart) {
  size_t bytes;
  double allbytes = 0;

  self->MaxNodes = maxnodes;

  if (!(self->Nodes_base =
            malloc(bytes = (self->MaxNodes + 1) * sizeof(struct NODE)))) {
    printf("failed to allocate memory for %d tree-nodes (%g MB).\n",
           self->MaxNodes, bytes / (1024.0 * 1024.0));
    endrun(self, 3);
  }
  allbytes += bytes;

  self->Nodes = self->Nodes_base - self->All.MaxPart;

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
}

/******************************************************************************

NGB THINGS

*******************************************************************************/

#define MAX_NGB 20000 /*!< defines maximum length of neighbour list */

/*! Allocates memory for the neighbour list buffer.
 */
void ngb_treeallocate(Tree *self, int npart) {
  double totbytes = 0;
  size_t bytes;

#ifdef PERIODIC
  boxSize = All.BoxSize;
  boxHalf = 0.5 * All.BoxSize;
#ifdef LONG_X
  boxHalf_X = boxHalf * LONG_X;
  boxSize_X = boxSize * LONG_X;
#endif
#ifdef LONG_Y
  boxHalf_Y = boxHalf * LONG_Y;
  boxSize_Y = boxSize * LONG_Y;
#endif
#ifdef LONG_Z
  boxHalf_Z = boxHalf * LONG_Z;
  boxSize_Z = boxSize * LONG_Z;
#endif
#endif

  if (!(self->Ngblist = malloc(bytes = npart * (long)sizeof(int)))) {
    printf("Failed to allocate %g MB for ngblist array\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 78);
  }
  totbytes += bytes;
}

/*! The buffer for the neighbour list has a finite length MAX_NGB. For a large
 *  search region, this buffer can get full, in which case this routine can be
 *  called to eliminate some of the superfluous particles in the "corners" of
 *  the search box - only the ones in the inscribed sphere need to be kept.
 */
int ngb_clear_buf(Tree *self, FLOAT searchcenter[3], FLOAT hsml, int numngb) {
  int i, p;
  FLOAT dx, dy, dz, r2;

#ifdef PERIODIC
  double xtmp;
#endif

  for (i = 0; i < numngb; i++) {
    p = self->Ngblist[i];
#ifdef PERIODIC
    dx = NGB_PERIODIC_X(self->P[p].Pos[0] - searchcenter[0]);
    dy = NGB_PERIODIC_Y(self->P[p].Pos[1] - searchcenter[1]);
    dz = NGB_PERIODIC_Z(self->P[p].Pos[2] - searchcenter[2]);
#else
    dx = self->P[p].Pos[0] - searchcenter[0];
    dy = self->P[p].Pos[1] - searchcenter[1];
    dz = self->P[p].Pos[2] - searchcenter[2];
#endif
    r2 = dx * dx + dy * dy + dz * dz;

    if (r2 > hsml * hsml) {
      self->Ngblist[i] = self->Ngblist[numngb - 1];
      i--;
      numngb--;
    }
  }

  return numngb;
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

#ifdef PERIODIC
  double xtmp;
#endif


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

#ifdef PERIODIC
      if (NGB_PERIODIC_X(P[p].Pos[0] - searchcenter[0]) < -hsml) continue;
      if (NGB_PERIODIC_X(P[p].Pos[0] - searchcenter[0]) > hsml) continue;
      if (NGB_PERIODIC_Y(P[p].Pos[1] - searchcenter[1]) < -hsml) continue;
      if (NGB_PERIODIC_Y(P[p].Pos[1] - searchcenter[1]) > hsml) continue;
      if (NGB_PERIODIC_Z(P[p].Pos[2] - searchcenter[2]) < -hsml) continue;
      if (NGB_PERIODIC_Z(P[p].Pos[2] - searchcenter[2]) > hsml) continue;
#else
      if (self->P[p].Pos[0] < searchmin[0]) continue;
      if (self->P[p].Pos[0] > searchmax[0]) continue;
      if (self->P[p].Pos[1] < searchmin[1]) continue;
      if (self->P[p].Pos[1] > searchmax[1]) continue;
      if (self->P[p].Pos[2] < searchmin[2]) continue;
      if (self->P[p].Pos[2] > searchmax[2]) continue;
#endif
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
        // Exportflag[DomainTask[no - (self->MaxPart + self->MaxNodes)]] = 1;
        no = self->Nextnode[no - self->MaxNodes];
        continue;
      }

      this = &self->Nodes[no];

      no = this->u.d.sibling; /* in case the node can be discarded */
#ifdef PERIODIC
      if ((NGB_PERIODIC_X(this->center[0] - searchcenter[0]) +
           0.5 * this->len) < -hsml)
        continue;
      if ((NGB_PERIODIC_X(this->center[0] - searchcenter[0]) -
           0.5 * this->len) > hsml)
        continue;
      if ((NGB_PERIODIC_Y(this->center[1] - searchcenter[1]) +
           0.5 * this->len) < -hsml)
        continue;
      if ((NGB_PERIODIC_Y(this->center[1] - searchcenter[1]) -
           0.5 * this->len) > hsml)
        continue;
      if ((NGB_PERIODIC_Z(this->center[2] - searchcenter[2]) +
           0.5 * this->len) < -hsml)
        continue;
      if ((NGB_PERIODIC_Z(this->center[2] - searchcenter[2]) -
           0.5 * this->len) > hsml)
        continue;
#else
      if ((this->center[0] + 0.5 * this->len) < (searchmin[0])) continue;
      if ((this->center[0] - 0.5 * this->len) > (searchmax[0])) continue;
      if ((this->center[1] + 0.5 * this->len) < (searchmin[1])) continue;
      if ((this->center[1] - 0.5 * this->len) > (searchmax[1])) continue;
      if ((this->center[2] + 0.5 * this->len) < (searchmin[2])) continue;
      if ((this->center[2] - 0.5 * this->len) > (searchmax[2])) continue;
#endif
      no = this->u.d.nextnode; /* ok, we need to open the node */
    }
  }

  *startnode = -1;
  return numngb;
}

/******************************************************************************

DENSITY THINGS

*******************************************************************************/

#define MAXITER 150

/*! This function return the number of neighbors in a radius h
 *  around position Pos
 * (Yves Revaz)
 */
double density_numngb_evaluate(Tree *self, FLOAT Pos[3], FLOAT Vel[3],
                               double h) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2;
  double dx, dy, dz, r2;
  FLOAT *pos;

  pos = Pos;

  h2 = h * h;

  startnode = self->All.MaxPart;
  numngb = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;
      }
    }
  } while (startnode >= 0);

  return numngb;
}

/*! This function represents the core of the SPH density computation. The
 *  target particle may either be local, or reside in the communication
 *  buffer.
 */

double density_evaluate(Tree *self, FLOAT Pos[3], FLOAT Vel[3], double h,
                        double *Density, double *NumNgb,
                        double *DhsmlDensityFactor) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2, hinv, hinv3, hinv4;
  double rho, divv, wk, dwk;
  double dx, dy, dz, r, r2, u, mass_j;
  double rotv[3];
  double weighted_numngb, dhsmlrho;
  FLOAT *pos;

  pos = Pos;

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

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
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
      }
    }
  } while (startnode >= 0);

  *Density = rho;
  *NumNgb = weighted_numngb;
  *DhsmlDensityFactor = dhsmlrho;

  return weighted_numngb;
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
double density(Tree *self, FLOAT Pos[3], FLOAT Vel[3], double *h,
               double *numNgb) {

  double Left, Right;
  double Hsml, Density, NumNgb, DhsmlDensityFactor;

  int npleft;

#ifdef PERIODIC
  boxSize = All.BoxSize;
  boxHalf = 0.5 * All.BoxSize;
#ifdef LONG_X
  boxHalf_X = boxHalf * LONG_X;
  boxSize_X = boxSize * LONG_X;
#endif
#ifdef LONG_Y
  boxHalf_Y = boxHalf * LONG_Y;
  boxSize_Y = boxSize * LONG_Y;
#endif
#ifdef LONG_Z
  boxHalf_Z = boxHalf * LONG_Z;
  boxSize_Z = boxSize * LONG_Z;
#endif
#endif

  Left = Right = 0;
  Hsml = *h;

  /* we will repeat the whole thing for those particles where we didn't
   * find enough neighbours
   */
  do {

    density_evaluate(self, Pos, Vel, Hsml, &Density, &NumNgb,
                     &DhsmlDensityFactor);

    /* do final operations on results */
    npleft = 0;

    DhsmlDensityFactor =
        1 / (1 + Hsml * DhsmlDensityFactor / (NUMDIMS * Density));

    /* now check whether we had enough neighbours */

    if (NumNgb < (self->All.DesNumNgb - self->All.MaxNumNgbDeviation) ||
        (NumNgb > (self->All.DesNumNgb + self->All.MaxNumNgbDeviation) &&
         Hsml > (1.01 * self->All.MinGasHsml))) {
      /* need to redo this particle */
      npleft++;

      if (Left > 0 && Right > 0)
        if ((Right - Left) < 1.0e-3 * Left) {
          /* this one should be ok */
          npleft--;
          continue;
        }

      if (NumNgb < (self->All.DesNumNgb - self->All.MaxNumNgbDeviation))
        Left = dmax(Hsml, Left);
      else {
        if (Right != 0) {
          if (Hsml < Right) Right = Hsml;
        } else
          Right = Hsml;
      }

      if (Right > 0 && Left > 0)
        Hsml = pow(0.5 * (pow(Left, 3) + pow(Right, 3)), 1.0 / 3);
      else {
        if (Right == 0 && Left == 0) endrun(self, 8188); /* can't occur */

        if (Right == 0 && Left > 0) {
          if (fabs(NumNgb - self->All.DesNumNgb) < 0.5 * self->All.DesNumNgb) {
            Hsml *= 1 - (NumNgb - self->All.DesNumNgb) / (NUMDIMS * NumNgb) *
                            DhsmlDensityFactor;
          } else
            Hsml *= 1.26;
        }

        if (Right > 0 && Left == 0) {
          if (fabs(NumNgb - self->All.DesNumNgb) < 0.5 * self->All.DesNumNgb) {
            Hsml *= 1 - (NumNgb - self->All.DesNumNgb) / (NUMDIMS * NumNgb) *
                            DhsmlDensityFactor;
          } else
            Hsml /= 1.26;
        }
      }

      if (Hsml < self->All.MinGasHsml) Hsml = self->All.MinGasHsml;
    } else {
      npleft = 0;
    }

  } while (npleft > 0);

  *h = Hsml;
  *numNgb = NumNgb;
  return Density;
}

/******************************************************************************

SPH EVALUATION

*******************************************************************************/

/*! Compute div
 */

void sph_evaluate_rot(Tree *self, FLOAT Pos[3], FLOAT Vel[3], double h,
                      double *rotvx, double *rotvy, double *rotvz) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2, fac, hinv, hinv3, hinv4;
  double dwk;
  double dx, dy, dz, r, r2, u;
  double dvx, dvy, dvz;
  FLOAT *pos, *vel;

  pos = Pos;
  vel = Vel;

  h2 = h * h;
  hinv = 1.0 / h;

#ifndef TWODIMS
  hinv3 = hinv * hinv * hinv;
#else
  hinv3 = hinv * hinv / boxSize_Z;
#endif
  hinv4 = hinv3 * hinv;

  *rotvx = 0;
  *rotvy = 0;
  *rotvz = 0;

  startnode = self->All.MaxPart;
  numngb = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;

        r = sqrt(r2);

        u = r * hinv;

        if (u < 0.5) {
          dwk = hinv4 * u * (KERNEL_COEFF_3 * u - KERNEL_COEFF_4);
        } else {
          dwk = hinv4 * KERNEL_COEFF_6 * (1.0 - u) * (1.0 - u);
        }

        if (r > 0) {
          fac = self->P[j].Mass * dwk / r;

          dvx = vel[0] - self->P[j].Vel[0];
          dvy = vel[1] - self->P[j].Vel[1];
          dvz = vel[2] - self->P[j].Vel[2];

          *rotvx += fac * (dz * dvy - dy * dvz);
          *rotvy += fac * (dx * dvz - dz * dvx);
          *rotvz += fac * (dy * dvx - dx * dvy);
        }
      }
    }
  } while (startnode >= 0);
}

/*! Compute div
 */

double sph_evaluate_div(Tree *self, FLOAT Pos[3], FLOAT Vel[3], double h) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2, fac, hinv, hinv3, hinv4;
  double divv, dwk;
  double dx, dy, dz, r, r2, u;
  double dvx, dvy, dvz;
  FLOAT *pos, *vel;

  pos = Pos;
  vel = Vel;

  h2 = h * h;
  hinv = 1.0 / h;

#ifndef TWODIMS
  hinv3 = hinv * hinv * hinv;
#else
  hinv3 = hinv * hinv / boxSize_Z;
#endif
  hinv4 = hinv3 * hinv;

  divv = 0;

  startnode = self->All.MaxPart;
  numngb = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;

        r = sqrt(r2);

        u = r * hinv;

        if (u < 0.5) {
          dwk = hinv4 * u * (KERNEL_COEFF_3 * u - KERNEL_COEFF_4);
        } else {
          dwk = hinv4 * KERNEL_COEFF_6 * (1.0 - u) * (1.0 - u);
        }

        if (r > 0) {
          fac = self->P[j].Mass * dwk / r;

          dvx = vel[0] - self->P[j].Vel[0];
          dvy = vel[1] - self->P[j].Vel[1];
          dvz = vel[2] - self->P[j].Vel[2];

          divv -= fac * (dx * dvx + dy * dvy + dz * dvz);
        }
      }
    }
  } while (startnode >= 0);

  return divv;
}

/*! Compute number of real neighbours
 */

int sph_evaluate_neighbours(Tree *self, FLOAT Pos[3], double h) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2;
  double dx, dy, dz, r2;
  FLOAT *pos;

  pos = Pos;

  h2 = h * h;

  startnode = self->All.MaxPart;
  numngb = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;
      }
    }
  } while (startnode >= 0);

  return numngb;
}

/*! Compute number of real neighbours
 */

int sph_evaluate_nearest_neighbour(Tree *self, FLOAT Pos[3], double h) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2;
  double dx, dy, dz, r2;
  double r2min;
  int jmin;
  FLOAT *pos;

  pos = Pos;

  h2 = h * h;

  startnode = self->All.MaxPart;
  numngb = 0;

  r2min = 1e100;
  jmin = -1;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;

        if (r2min > r2) {
          r2min = r2;
          jmin = j;
        }
      }
    }
  } while (startnode >= 0);

  return jmin;
}

/*! Compute sph value of an observable
 */

double sph_evaluate(Tree *self, FLOAT Pos[3], double h) {

  int j, n, startnode, numngb, numngb_inbox;
  double h2, hinv, hinv3;
  double wk;
  double dx, dy, dz, r, r2, u, valA, val0;
  FLOAT *pos;

  pos = Pos;

  h2 = h * h;
  hinv = 1.0 / h;

#ifndef TWODIMS
  hinv3 = hinv * hinv * hinv;
#else
  hinv3 = hinv * hinv / boxSize_Z;
#endif

  valA = 0;
  val0 = 0;

  startnode = self->All.MaxPart;
  numngb = 0;

  do {
    numngb_inbox = ngb_treefind_variable(self, &pos[0], h, &startnode);

    for (n = 0; n < numngb_inbox; n++) {
      j = self->Ngblist[n];

      dx = pos[0] - self->P[j].Pos[0];
      dy = pos[1] - self->P[j].Pos[1];
      dz = pos[2] - self->P[j].Pos[2];

#ifdef PERIODIC /*  now find the closest image in the given box size  */
      if (dx > boxHalf_X) dx -= boxSize_X;
      if (dx < -boxHalf_X) dx += boxSize_X;
      if (dy > boxHalf_Y) dy -= boxSize_Y;
      if (dy < -boxHalf_Y) dy += boxSize_Y;
      if (dz > boxHalf_Z) dz -= boxSize_Z;
      if (dz < -boxHalf_Z) dz += boxSize_Z;
#endif
      r2 = dx * dx + dy * dy + dz * dz;

      if (r2 < h2) {
        numngb++;

        r = sqrt(r2);

        u = r * hinv;

        if (u < 0.5) {
          wk = hinv3 * (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
        } else {
          wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) * (1.0 - u);
        }

        valA += self->P[j].Mass * (self->P[j].Observable) /
                (self->P[j].Density) * wk;
        val0 += self->P[j].Mass / (self->P[j].Density) * wk;
      }
    }
  } while (startnode >= 0);

  valA = valA / val0;

  return valA;
}

/******************************************************************************

TREE OBJECT

*******************************************************************************/

static void Tree_dealloc(Tree *self) {
  free(self->P);
  free(self->TopNodes);
  free(self->DomainNodeIndex);
  free(self->Nodes_base);
  free(self->Nextnode);
  free(self->Father);
  free(self->Ngblist);

  Py_XDECREF(self->first);
  Py_XDECREF(self->list);
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *Tree_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  Tree *self;

  self = (Tree *)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->first = PyUnicode_FromString("");
    if (self->first == NULL) {
      Py_DECREF(self);
      return NULL;
    }

    self->list = PyList_New(0);
    if (self->list == NULL) {
      Py_DECREF(self);
      return NULL;
    }

    self->number = 7;
  }

  return (PyObject *)self;
}

static int Tree_init(Tree *self, PyObject *args, PyObject *kwds) {

  int i;

  PyObject *first = NULL, *tmp;
  PyArrayObject *ntype, *pos, *vel, *mass;
  double ErrTolTheta;

  static char *kwlist[] = {"first", "npart",       "pos", "vel",
                           "mass",  "ErrTolTheta", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOOd", kwlist, &first,
                                   &ntype, &pos, &vel, &mass, &ErrTolTheta))
    return -1;

  if (first) {
    tmp = self->first;
    Py_INCREF(first);
    self->first = first;
    Py_XDECREF(tmp);
  }

  /* variables related to nbody */
  /* here, we should pass direcly the pointer */
  if ((PyArray_NDIM(ntype) != 1) || (PyArray_DIM(ntype, 0) != 6)) {
    PyErr_SetString(PyExc_ValueError,
                    "Tree_init, npart must be an array of dimension 1x6.");
    return -1;
  }

  self->NtypeLocal[0] = *(int *)PyArray_GETPTR1(ntype, 0);
  self->NtypeLocal[1] = *(int *)PyArray_GETPTR1(ntype, 1);
  self->NtypeLocal[2] = *(int *)PyArray_GETPTR1(ntype, 2);
  self->NtypeLocal[3] = *(int *)PyArray_GETPTR1(ntype, 3);
  self->NtypeLocal[4] = *(int *)PyArray_GETPTR1(ntype, 4);
  self->NtypeLocal[5] = *(int *)PyArray_GETPTR1(ntype, 5);

  self->NumPart = 0;
  self->N_gas = self->NtypeLocal[0];
  for (i = 0; i < 6; i++) self->NumPart += self->NtypeLocal[i];

  self->All.TotNumPart = self->NumPart;
  self->All.TotN_gas = self->N_gas;

  /* global variables */

  self->ThisTask = 0;
  self->NTask = 1;

  /* All vars */

  for (i = 0; i < 6; i++)
    self->All.SofteningTable[i] = 0.1; /* a changer !!!! */

  for (i = 0; i < 6; i++)
    self->All.ForceSoftening[i] = 0.1; /* a changer !!!! */

  self->All.PartAllocFactor = 1.5;
  self->All.TreeAllocFactor = 10.0;
  self->All.ErrTolTheta = ErrTolTheta;

  self->All.MaxPart =
      self->All.PartAllocFactor * (self->All.TotNumPart / self->NTask);
  self->All.MaxPartSph =
      self->All.PartAllocFactor * (self->All.TotN_gas / self->NTask);

  self->All.DesNumNgb = 33;
  self->All.MaxNumNgbDeviation = 3;

  self->All.MinGasHsmlFractional = 0.25;
  self->All.MinGasHsml =
      self->All.MinGasHsmlFractional * self->All.ForceSoftening[0];

  /* create P */
  size_t bytes;
  if (!(self->P =
            malloc(bytes = self->All.MaxPart * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `P' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    self->P[i].Pos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    self->P[i].Pos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    self->P[i].Pos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    self->P[i].Vel[0] = *(float *)PyArray_GETPTR2(vel, i, 0);
    self->P[i].Vel[1] = *(float *)PyArray_GETPTR2(vel, i, 1);
    self->P[i].Vel[2] = *(float *)PyArray_GETPTR2(vel, i, 2);
    self->P[i].Mass = *(float *)PyArray_GETPTR1(mass, i);
    self->P[i].Type = 0; /* this should be changed... */
  }

  /***************************************
   * domain decomposition construction   *
   ***************************************/

  domain_domainallocate(self);
  domain_Decomposition(self);
  self->NTopleaves = 0;        /* normally in domain_sumCost */
  domain_walktoptree(self, 0); /* normally in domain_sumCost */

  /************************
   * tree construction    *
   ************************/

  force_treeallocate(self, self->All.TreeAllocFactor * self->All.MaxPart,
                     self->All.MaxPart);
  force_treebuild(self, self->NumPart);

  /************************
   * ngb                  *
   ************************/
  ngb_treeallocate(self, self->NumPart);

  return 0;
}

static PyMemberDef Tree_members[] = {
    {"first", T_OBJECT_EX, offsetof(Tree, first), 0, "first name"},
    {"list", T_OBJECT_EX, offsetof(Tree, list), 0, "list of"},
    {"number", T_INT, offsetof(Tree, number), 0, "Tree number"},

    {NULL} /* Sentinel */
};

static PyObject *Tree_name(Tree *self, PyObject *Py_UNUSED(ignored)) {
  if (self->first == NULL) {
    PyErr_SetString(PyExc_AttributeError, "first");
    return NULL;
  }
  if (self->last == 0) {
    PyErr_SetString(PyExc_AttributeError, "last");
    return NULL;
  }
  return PyUnicode_FromFormat("%S %S", self->first, self->last);
}

static PyObject *Tree_info(Tree *self, PyObject *Py_UNUSED(ignored)) {

  // static PyObject *format = NULL;
  // PyObject *args, *result;

  printf("NumPart = %d\n", self->NumPart);

  printf("N_gas   = %d\n", self->N_gas);

  printf("DomainLen      = %g\n", self->DomainLen);
  printf("DomainCenter x = %g\n", self->DomainCenter[0]);
  printf("DomainCenter y = %g\n", self->DomainCenter[1]);
  printf("DomainCenter z = %g\n", self->DomainCenter[2]);
  printf("DomainCorner x = %g\n", self->DomainCorner[0]);
  printf("DomainCorner y = %g\n", self->DomainCorner[1]);
  printf("DomainCorner z = %g\n", self->DomainCorner[2]);

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_Acceleration(Tree *self, PyObject *args) {

  PyArrayObject *pos;
  float eps;

  if (!PyArg_ParseTuple(args, "Of", &pos, &eps))
    return PyUnicode_FromString("error");

  PyArrayObject *acc;
  int i;
  double x, y, z, ax, ay, az;
  int input_dimension;

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  npy_intp ld[2];
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);
  /* there is a kind of bug here ! I cannt replace ld by pos->dimensions */
  // acc = (PyArrayObject *) PyArray_FromDims(pos->nd,ld,pos->descr->type_num);
  acc = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                           PyArray_TYPE(pos));

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    z = *(float *)PyArray_GETPTR2(pos, i, 2);

    force_treeevaluate_local(self, x, y, z, (double)eps, &ax, &ay, &az);

    *(float *)PyArray_GETPTR2(acc, i, 0) = ax;
    *(float *)PyArray_GETPTR2(acc, i, 1) = ay;
    *(float *)PyArray_GETPTR2(acc, i, 2) = az;
  }

  return PyArray_Return(acc);
}

static PyObject *Tree_Potential(Tree *self, PyObject *args) {

  PyArrayObject *pos;
  float eps;

  if (!PyArg_ParseTuple(args, "Of", &pos, &eps))
    return PyUnicode_FromString("error");

  PyArrayObject *pot;
  int i;
  double x, y, z, lpot;
  npy_intp ld[1];
  int input_dimension;

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  // pot = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  pot = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    x = *(float *)PyArray_GETPTR2(pos, i, 0);
    y = *(float *)PyArray_GETPTR2(pos, i, 1);
    z = *(float *)PyArray_GETPTR2(pos, i, 2);

    lpot = force_treeevaluate_local_potential(self, x, y, z, (double)eps);
    *(float *)PyArray_GETPTR1(pot, i) = lpot;
  }

  return PyArray_Return(pot);
}

static PyObject *Tree_Density(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;
  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "OOdd", &pos, &hsml, &DesNumNgb,
                        &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vdensity, *vhsml;
  int i;
  double ldensity, lhsml, lnumNgb;
  npy_intp ld[1];
  int input_dimension;
  FLOAT lpos[3], lvel[3];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  // vdensity = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  vdensity = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);
  // vhsml    = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  vhsml = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  self->All.DesNumNgb = DesNumNgb;
  self->All.MaxNumNgbDeviation = MaxNumNgbDeviation;

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lvel[0] = 0.0;
    lvel[1] = 0.0;
    lvel[2] = 0.0;
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    ldensity = density(self, lpos, lvel, &lhsml, &lnumNgb);
    *(float *)PyArray_GETPTR1(vdensity, i) = ldensity;
    *(float *)PyArray_GETPTR1(vhsml, i) = lhsml;
  }

  return Py_BuildValue("OO", vdensity, vhsml);
}

static PyObject *Tree_InitHsml(Tree *self, PyObject *args) {

  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "dd", &DesNumNgb, &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vhsml;
  int i, no, p;
  double lhsml;
  npy_intp ld[1];

  /* create a NumPy object */
  ld[0] = self->NumPart;
  // vhsml    = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  vhsml = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  self->All.DesNumNgb = DesNumNgb;
  self->All.MaxNumNgbDeviation = MaxNumNgbDeviation;

  for (i = 0; i < self->NumPart; i++) {

    no = self->Father[i];

    while (10 * self->All.DesNumNgb * self->P[i].Mass >
           self->Nodes[no].u.d.mass) {
      p = self->Nodes[no].u.d.father;

      if (p < 0) break;

      no = p;
    }
#ifndef TWODIMS
    lhsml = pow(3.0 / (4 * M_PI) * self->All.DesNumNgb * self->P[i].Mass /
                    self->Nodes[no].u.d.mass,
                1.0 / 3) *
            self->Nodes[no].len;
#else
    lhsml = pow(1.0 / (M_PI)*self->All.DesNumNgb * self->P[i].Mass /
                    self->Nodes[no].u.d.mass,
                1.0 / 2) *
            self->Nodes[no].len;
#endif

    *(float *)PyArray_GETPTR1(vhsml, i) = lhsml;
  }

  return PyArray_Return(vhsml);
}

static PyObject *Tree_SphEvaluate(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;
  PyArrayObject *Density, *Observable;
  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "OOOOdd", &pos, &hsml, &Density, &Observable,
                        &DesNumNgb, &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vobservable;
  int i;
  double lhsml, lobservable;
  npy_intp ld[1];
  int input_dimension;
  FLOAT lpos[3];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  if (PyArray_DIM(Density, 0) != self->NumPart)
    PyErr_SetString(PyExc_ValueError,
                    "len of third argument must equal NumPart\n");

  if (PyArray_DIM(Observable, 0) != self->NumPart)
    PyErr_SetString(PyExc_ValueError,
                    "len of fourth argument must equal NumPart\n");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  // vobservable    = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  vobservable = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  self->All.DesNumNgb = DesNumNgb;
  self->All.MaxNumNgbDeviation = MaxNumNgbDeviation;

  for (i = 0; i < self->NumPart; i++) {
    self->P[i].Density = *(float *)PyArray_GETPTR1(Density, i);
    self->P[i].Observable = *(float *)PyArray_GETPTR1(Observable, i);
  }

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    lobservable = sph_evaluate(self, lpos, lhsml);
    *(float *)PyArray_GETPTR1(vobservable, i) = lobservable;
  }

  return PyArray_Return(vobservable);
}

static PyObject *Tree_SphEvaluateDiv(Tree *self, PyObject *args) {

  PyArrayObject *pos, *vel, *hsml;
  PyArrayObject *Density;
  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "OOOOdd", &pos, &vel, &hsml, &Density, &DesNumNgb,
                        &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vobservable;
  int i;
  double lhsml, lobservable;
  npy_intp ld[1];
  int input_dimension;
  FLOAT lpos[3], lvel[3];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  if (PyArray_DIM(Density, 0) != self->NumPart)
    PyErr_SetString(PyExc_ValueError,
                    "len of third argument must equal NumPart\n");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  // vobservable    = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_FLOAT);
  vobservable = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_FLOAT);

  self->All.DesNumNgb = DesNumNgb;
  self->All.MaxNumNgbDeviation = MaxNumNgbDeviation;

  for (i = 0; i < self->NumPart; i++) {
    self->P[i].Density = *(float *)PyArray_GETPTR1(Density, i);
  }

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lvel[0] = *(float *)PyArray_GETPTR2(vel, i, 0);
    lvel[1] = *(float *)PyArray_GETPTR2(vel, i, 1);
    lvel[2] = *(float *)PyArray_GETPTR2(vel, i, 2);

    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    lobservable = sph_evaluate_div(self, lpos, lvel, lhsml);
    *(float *)PyArray_GETPTR1(vobservable, i) = lobservable;
  }

  return PyArray_Return(vobservable);
}

static PyObject *Tree_SphEvaluateRot(Tree *self, PyObject *args) {

  PyArrayObject *pos, *vel, *hsml;
  PyArrayObject *Density;
  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "OOOOdd", &pos, &vel, &hsml, &Density, &DesNumNgb,
                        &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vobservable;
  int i;
  double lhsml;
  int input_dimension;
  FLOAT lpos[3], lvel[3];
  double lrotx, lroty, lrotz;

  npy_intp ld[2];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  if (PyArray_DIM(Density, 0) != self->NumPart)
    PyErr_SetString(PyExc_ValueError,
                    "len of third argument must equal NumPart\n");

  /* create a NumPy object */
  // vobservable = (PyArrayObject *)
  // PyArray_FromDims(pos->nd,pos->dimensions,pos->descr->type_num);
  ld[0] = PyArray_DIM(pos, 0);
  ld[1] = PyArray_DIM(pos, 1);
  /* there is a kind of bug here ! I cannt replace ld by pos->dimensions */
  vobservable = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(pos), ld,
                                                   PyArray_TYPE(pos));

  self->All.DesNumNgb = DesNumNgb;
  self->All.MaxNumNgbDeviation = MaxNumNgbDeviation;

  for (i = 0; i < self->NumPart; i++) {
    self->P[i].Density = *(float *)PyArray_GETPTR1(Density, i);
  }

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lvel[0] = *(float *)PyArray_GETPTR2(vel, i, 0);
    lvel[1] = *(float *)PyArray_GETPTR2(vel, i, 1);
    lvel[2] = *(float *)PyArray_GETPTR2(vel, i, 2);

    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    sph_evaluate_rot(self, lpos, lvel, lhsml, &lrotx, &lroty, &lrotz);
    *(float *)PyArray_GETPTR2(vobservable, i, 0) = lrotx;
    *(float *)PyArray_GETPTR2(vobservable, i, 1) = lroty;
    *(float *)PyArray_GETPTR2(vobservable, i, 2) = lrotz;
  }

  return PyArray_Return(vobservable);
}

static PyObject *Tree_SphEvaluateNgb(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;
  double DesNumNgb, MaxNumNgbDeviation;

  if (!PyArg_ParseTuple(args, "OOdd", &pos, &hsml, &DesNumNgb,
                        &MaxNumNgbDeviation))
    return PyUnicode_FromString("error");

  PyArrayObject *vnumngb;
  int i;
  double lhsml;
  int numngb;
  npy_intp ld[1];
  int input_dimension;
  FLOAT lpos[3];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  // vnumngb    = (PyArrayObject *) PyArray_FromDims(1,ld,NPY_INT);
  vnumngb = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_INT);

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    numngb = sph_evaluate_neighbours(self, lpos, lhsml);
    *(int *)PyArray_GETPTR1(vnumngb, i) = numngb;
  }

  return PyArray_Return(vnumngb);
}

static PyObject *Tree_SphEvaluateNearestNgb(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;

  if (!PyArg_ParseTuple(args, "OO", &pos, &hsml))
    return PyUnicode_FromString("error");

  PyArrayObject *vjmin;
  int i, jmin;
  double lhsml;
  npy_intp ld[1];
  int input_dimension;
  FLOAT lpos[3];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = PyArray_DIM(pos, 0);
  vjmin = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_INT);

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    jmin = sph_evaluate_nearest_neighbour(self, lpos, lhsml);

    *(int *)PyArray_GETPTR1(vjmin, i) = jmin;
  }

  return PyArray_Return(vjmin);
}

static PyObject *Tree_SphGetNgb(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;

  if (!PyArg_ParseTuple(args, "OO", &pos, &hsml))
    return PyUnicode_FromString("error");

  PyArrayObject *ngb_lst;
  int i;
  int input_dimension, startnode;

  FLOAT lpos[3];
  double lhsml;
  int numngb = 0;

  npy_intp ld[2];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  for (i = 0; i < PyArray_DIM(pos, 0); i++) {

    startnode = self->All.MaxPart;

    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    numngb = ngb_treefind_variable(self, lpos, lhsml, &startnode);
  }

  /* create a NumPy object */
  ld[0] = numngb;
  ngb_lst = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_INT);

  for (i = 0; i < PyArray_DIM(ngb_lst, 0); i++) {

    *(int *)PyArray_GETPTR1(ngb_lst, i) = self->Ngblist[i];
  }

  return PyArray_Return(ngb_lst);
}




static PyObject *Tree_SphGetTrueNgb(Tree *self, PyObject *args) {

  PyArrayObject *pos;
  double lhsml;

  if (!PyArg_ParseTuple(args, "Od", &pos, &lhsml))
    return PyUnicode_FromString("error");

  PyArrayObject *ngb_lst;
  PyArrayObject *wij;
  int i, j, k;
  int input_dimension, startnode;

  FLOAT lpos[3];
  int numngb = 0;
  int truenumngb;

  double dx, dy, dz, r2, r;
  double h2, hinv, hinv3;
  double wk;
  double u;

  npy_intp ld[2];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 1)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 1");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  
  lpos[0] = *(float *)PyArray_GETPTR1(pos, 0);
  lpos[1] = *(float *)PyArray_GETPTR1(pos, 1);
  lpos[2] = *(float *)PyArray_GETPTR1(pos, 2);
  
  
  startnode = self->All.MaxPart;
  numngb = ngb_treefind_variable(self, lpos, lhsml, &startnode);
        

  h2 = lhsml * lhsml;
  hinv = 1.0 / lhsml;
  hinv3 = hinv * hinv * hinv;
  truenumngb = 0;
    

  /* first loop, determine the number of true ngbs */

  for (i = 0, k = 0; i < numngb; i++) {
    j = self->Ngblist[i];

    dx = lpos[0] - self->P[j].Pos[0];
    dy = lpos[1] - self->P[j].Pos[1];
    dz = lpos[2] - self->P[j].Pos[2];

    r2 = dx * dx + dy * dy + dz * dz;
    if (r2 < h2) truenumngb++;
  }

  //printf("numngb=%d\n", numngb);
  //printf("truenumngb=%d\n", truenumngb);

  /* create a NumPy object */
  ld[0] = truenumngb;
  ngb_lst = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_INT);
  wij = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

  /* second loop use only true ngbs */
  for (i = 0, k = 0; i < numngb; i++) {
    j = self->Ngblist[i];

    dx = lpos[0] - self->P[j].Pos[0];
    dy = lpos[1] - self->P[j].Pos[1];
    dz = lpos[2] - self->P[j].Pos[2];

    r2 = dx * dx + dy * dy + dz * dz;
    if (r2 < h2) {
      r = sqrt(r2);

      u = r * hinv;

      if (u < 0.5) {
        wk = hinv3 * (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
        // dwk = hinv4 * u * (KERNEL_COEFF_3 * u - KERNEL_COEFF_4);
      } else {
        wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) * (1.0 - u);
        // dwk = hinv4 * KERNEL_COEFF_6 * (1.0 - u) * (1.0 - u);
      }

      *(int *)PyArray_GETPTR1(ngb_lst, k) = j;

      *(double *)PyArray_GETPTR1(wij, k) = wk;

      k++;
    }
  }

  return Py_BuildValue("OO", ngb_lst, wij);
  // return PyArray_Return(ngb_lst);
}




static PyObject *Tree_SphGetTrueNgbMulti(Tree *self, PyObject *args) {
  
  // !!! this function is not implemented yet !!!

  PyArrayObject *pos, *hsml;

  if (!PyArg_ParseTuple(args, "OO", &pos, &hsml))
    return PyUnicode_FromString("error");

  PyArrayObject *ngb_lst;
  PyArrayObject *wij;
  int i, j, k;
  int input_dimension, startnode;

  FLOAT lpos[3];
  double lhsml = 1e-6;
  int numngb = 0;
  int truenumngb;

  double dx, dy, dz, r2, r;
  double h2, hinv, hinv3;
  double wk;
  double u;

  npy_intp ld[2];

  input_dimension = PyArray_NDIM(pos);

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (PyArray_TYPE(pos) != NPY_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");


  if (PyArray_DIM(pos, 0) > 1)
    return PyUnicode_FromString("only one particle may be given here.");


  for (i = 0; i < PyArray_DIM(pos, 0); i++) {
    
    startnode = self->All.MaxPart;

    lpos[0] = *(float *)PyArray_GETPTR2(pos, i, 0);
    lpos[1] = *(float *)PyArray_GETPTR2(pos, i, 1);
    lpos[2] = *(float *)PyArray_GETPTR2(pos, i, 2);
    lhsml = *(float *)PyArray_GETPTR1(hsml, i);

    numngb = ngb_treefind_variable(self, lpos, lhsml, &startnode);
        
  }

  h2 = lhsml * lhsml;
  hinv = 1.0 / lhsml;
  hinv3 = hinv * hinv * hinv;
  truenumngb = 0;
    

  /* first loop, determine the number of true ngbs */

  for (i = 0, k = 0; i < numngb; i++) {
    j = self->Ngblist[i];

    dx = lpos[0] - self->P[j].Pos[0];
    dy = lpos[1] - self->P[j].Pos[1];
    dz = lpos[2] - self->P[j].Pos[2];

    r2 = dx * dx + dy * dy + dz * dz;
    if (r2 < h2) truenumngb++;
  }

  printf("numngb=%d\n", numngb);
  printf("truenumngb=%d\n", truenumngb);

  /* create a NumPy object */
  ld[0] = truenumngb;
  ngb_lst = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_INT);
  wij = (PyArrayObject *)PyArray_SimpleNew(1, ld, NPY_DOUBLE);

  /* second loop use only true ngbs */
  for (i = 0, k = 0; i < numngb; i++) {
    j = self->Ngblist[i];

    dx = lpos[0] - self->P[j].Pos[0];
    dy = lpos[1] - self->P[j].Pos[1];
    dz = lpos[2] - self->P[j].Pos[2];

    r2 = dx * dx + dy * dy + dz * dz;
    if (r2 < h2) {
      r = sqrt(r2);

      u = r * hinv;

      if (u < 0.5) {
        wk = hinv3 * (KERNEL_COEFF_1 + KERNEL_COEFF_2 * (u - 1) * u * u);
        // dwk = hinv4 * u * (KERNEL_COEFF_3 * u - KERNEL_COEFF_4);
      } else {
        wk = hinv3 * KERNEL_COEFF_5 * (1.0 - u) * (1.0 - u) * (1.0 - u);
        // dwk = hinv4 * KERNEL_COEFF_6 * (1.0 - u) * (1.0 - u);
      }

      *(int *)PyArray_GETPTR1(ngb_lst, k) = j;

      *(double *)PyArray_GETPTR1(wij, k) = wk;

      k++;
    }
  }

  return Py_BuildValue("OO", ngb_lst, wij);
  // return PyArray_Return(ngb_lst);
}









static PyMethodDef Tree_methods[] = {

    {"name", (PyCFunction)Tree_name, METH_NOARGS,
     "Return the name, combining the first and last name"},

    {"info", (PyCFunction)Tree_info, METH_NOARGS, "Return info"},

    {"Potential", (PyCFunction)Tree_Potential, METH_VARARGS,
     "This function computes the potential at a given position using the tree"},

    {"Acceleration", (PyCFunction)Tree_Acceleration, METH_VARARGS,
     "This function computes the acceleration at a given position using the "
     "tree"},

    {"Density", (PyCFunction)Tree_Density, METH_VARARGS,
     "This function computes the density at a given position using the tree"},

    {"InitHsml", (PyCFunction)Tree_InitHsml, METH_VARARGS,
     "This function is used to find an initial smoothing length for each "
     "particle"},

    {"SphEvaluate", (PyCFunction)Tree_SphEvaluate, METH_VARARGS,
     "This function is used to evaluate an observable, using SPH."},

    {"SphEvaluateDiv", (PyCFunction)Tree_SphEvaluateDiv, METH_VARARGS,
     "This function is used to evaluate divergeance, using SPH."},

    {"SphEvaluateRot", (PyCFunction)Tree_SphEvaluateRot, METH_VARARGS,
     "This function is used to evaluate rotational, using SPH."},

    {"SphEvaluateNgb", (PyCFunction)Tree_SphEvaluateNgb, METH_VARARGS,
     "This function return the number of real neighbours."},

    {"SphEvaluateNearestNgb", (PyCFunction)Tree_SphEvaluateNearestNgb,
     METH_VARARGS, "This function return the nearest neighbor of a particle."},

    {"SphGetNgb", (PyCFunction)Tree_SphGetNgb, METH_VARARGS,
     "This function returns indexes of neighbour particles in a box (may be "
     "incomplete...)."},

    {"SphGetTrueNgb", (PyCFunction)Tree_SphGetTrueNgb, METH_VARARGS,
     "This function returns indexes of neighbour particles in a sphere."},

    {"SphGetTrueNgbMulti", (PyCFunction)Tree_SphGetTrueNgbMulti, METH_VARARGS,
     "This function returns indexes of neighbour particles in a sphere."},

    {NULL} /* Sentinel */
};

static PyTypeObject TreeType = {
    PyVarObject_HEAD_INIT(NULL, 0)            /*ob_size*/
    "tree.Tree",                              /*tp_name*/
    sizeof(Tree),                             /*tp_basicsize*/
    0,                                        /*tp_itemsize*/
    (destructor)Tree_dealloc,                 /*tp_dealloc*/
    0,                                        /*tp_print*/
    0,                                        /*tp_getattr*/
    0,                                        /*tp_setattr*/
    0,                                        /*tp_compare*/
    0,                                        /*tp_repr*/
    0,                                        /*tp_as_number*/
    0,                                        /*tp_as_sequence*/
    0,                                        /*tp_as_mapping*/
    0,                                        /*tp_hash */
    0,                                        /*tp_call*/
    0,                                        /*tp_str*/
    0,                                        /*tp_getattro*/
    0,                                        /*tp_setattro*/
    0,                                        /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Tree objects",                           /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,                                        /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    0,                                        /* tp_iter */
    0,                                        /* tp_iternext */
    Tree_methods,                             /* tp_methods */
    Tree_members,                             /* tp_members */
    0,                                        /* tp_getset */
    0,                                        /* tp_base */
    0,                                        /* tp_dict */
    0,                                        /* tp_descr_get */
    0,                                        /* tp_descr_set */
    0,                                        /* tp_dictoffset */
    (initproc)Tree_init,                      /* tp_init */
    0,                                        /* tp_alloc */
    Tree_new,                                 /* tp_new */
    0,                                        /* tp_free */
    0,                                        /* tp_is_gc */
    0,                                        /* tp_bases */
    0,                                        /* tp_mro */
    0,                                        /* tp_cache */
    0,                                        /* tp_subclasses */
    0,                                        /* tp_weaklist */
    0,                                        /* tp_del */
    0,                                        /* tp_version_tag */
    0,                                        /* tp_finalize */
};

static PyMethodDef module_methods[] = {
    {NULL} /* Sentinel */
};

static PyModuleDef treemodule = {
    PyModuleDef_HEAD_INIT,
    "tree",
    "Treelib module",
    -1,
    module_methods,
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_treelib(void) {
  PyObject *m;
  if (PyType_Ready(&TreeType) < 0) return NULL;

  m = PyModule_Create(&treemodule);
  if (m == NULL) return NULL;

  Py_INCREF(&TreeType);
  PyModule_AddObject(m, "Tree", (PyObject *)&TreeType);

  import_array();

  return m;
}
