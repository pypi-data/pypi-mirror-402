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
#include "ptreelib.h"

/*! This function puts the particles into Peano-Hilbert order by sorting them
 *  according to their keys. The latter half already been computed in the
 *  domain decomposition. Since gas particles need to stay at the beginning of
 *  the particle list, they are sorted as a separate block.
 */
void peano_hilbert_order(Tree *self) {
  int i;

  if (self->ThisTask == 0) printf("begin Peano-Hilbert order...\n");

  if (self->N_gas) {
    self->mp = malloc(sizeof(struct peano_hilbert_data) * self->N_gas);
    self->Id = malloc(sizeof(int) * self->N_gas);

    for (i = 0; i < self->N_gas; i++) {
      self->mp[i].index = i;
      self->mp[i].key = self->Key[i];
    }

    qsort(self->mp, self->N_gas, sizeof(struct peano_hilbert_data),
          compare_key);

    for (i = 0; i < self->N_gas; i++) self->Id[self->mp[i].index] = i;

    reorder_gas(self);

    free(self->Id);
    free(self->mp);
  }

  if (self->NumPart - self->N_gas > 0) {
    self->mp = malloc(sizeof(struct peano_hilbert_data) *
                      (self->NumPart - self->N_gas));
    self->mp -= (self->N_gas);

    self->Id = malloc(sizeof(int) * (self->NumPart - self->N_gas));
    self->Id -= (self->N_gas);

    for (i = self->N_gas; i < self->NumPart; i++) {
      self->mp[i].index = i;
      self->mp[i].key = self->Key[i];
    }

    qsort(self->mp + self->N_gas, self->NumPart - self->N_gas,
          sizeof(struct peano_hilbert_data), compare_key);

    for (i = self->N_gas; i < self->NumPart; i++)
      self->Id[self->mp[i].index] = i;

    reorder_particles(self);

    self->Id += self->N_gas;
    free(self->Id);
    self->mp += self->N_gas;
    free(self->mp);
  }

  if (self->ThisTask == 0) printf("Peano-Hilbert done.\n");
}

/*! This function is a comparison kernel for sorting the Peano-Hilbert keys.
 */
int compare_key(const void *a, const void *b) {
  if (((struct peano_hilbert_data *)a)->key <
      (((struct peano_hilbert_data *)b)->key))
    return -1;

  if (((struct peano_hilbert_data *)a)->key >
      (((struct peano_hilbert_data *)b)->key))
    return +1;

  return 0;
}

/*! This function brings the gas particles into the same order as the sorted
 *  keys. (The sort is first done only on the keys themselves and done
 *  directly on the gas particles in order to reduce the amount of data that
 *  needs to be moved in memory. Only once the order is established, the gas
 *  particles are rearranged, such that each particle has to be moved at most
 *  once.)
 */
void reorder_gas(Tree *self) {
  int i;
  struct particle_data Psave, Psource;
  struct sph_particle_data SphPsave, SphPsource;
  int idsource, idsave, dest;

  for (i = 0; i < self->N_gas; i++) {
    if (self->Id[i] != i) {
      Psource = self->P[i];
      SphPsource = self->SphP[i];

      idsource = self->Id[i];
      dest = self->Id[i];

      do {
        Psave = self->P[dest];
        SphPsave = self->SphP[dest];
        idsave = self->Id[dest];

        self->P[dest] = Psource;
        self->SphP[dest] = SphPsource;
        self->Id[dest] = idsource;

        if (dest == i) break;

        Psource = Psave;
        SphPsource = SphPsave;
        idsource = idsave;

        dest = idsource;
      } while (1);
    }
  }
}

/*! This function brings the collisionless particles into the same order as
 *  the sorted keys. (The sort is first done only on the keys themselves and
 *  done directly on the particles in order to reduce the amount of data that
 *  needs to be moved in memory. Only once the order is established, the
 *  particles are rearranged, such that each particle has to be moved at most
 *  once.)
 */
void reorder_particles(Tree *self) {
  int i;
  struct particle_data Psave, Psource;
  int idsource, idsave, dest;

  for (i = self->N_gas; i < self->NumPart; i++) {
    if (self->Id[i] != i) {
      Psource = self->P[i];
      idsource = self->Id[i];

      dest = self->Id[i];

      do {
        Psave = self->P[dest];
        idsave = self->Id[dest];

        self->P[dest] = Psource;
        self->Id[dest] = idsource;

        if (dest == i) break;

        Psource = Psave;
        idsource = idsave;

        dest = idsource;
      } while (1);
    }
  }
}

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

static int flag_quadrants_inverse = 1;
static char quadrants_inverse_x[24][8];
static char quadrants_inverse_y[24][8];
static char quadrants_inverse_z[24][8];

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
