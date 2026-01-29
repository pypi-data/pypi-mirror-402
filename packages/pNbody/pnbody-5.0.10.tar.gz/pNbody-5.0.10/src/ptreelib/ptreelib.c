#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "endrun.h"
#include "proto.h"
#include "ptreelib.h"

/******************************************************************************

TREE OBJECT

*******************************************************************************/

static void Tree_dealloc(Tree *self) {

  /* here, we have to deallocate all what we have allocated */

  /* should free : Gravdata, Densdata ??? */

  free(self->Exportflag);

  ngb_treefree(self);

  force_treefree(self);

  domain_deallocate(self);

  free(self->CommBuffer);
  free(self->P);
  free(self->SphP);

  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *Tree_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  Tree *self;

  self = (Tree *)type->tp_alloc(type, 0);
  if (self != NULL) {

    /* not clear what I have to put here */
  }

  return (PyObject *)self;
}

static PyObject *Tree_init(Tree *self, PyObject *args, PyObject *kwds) {

  import_array();

  int i;
  size_t bytes;

  PyObject *filename;

  static char *kwlist[] = {"filename", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &filename)) {
    return NULL;
  }

  /* MPI init */

  MPI_Comm_rank(MPI_COMM_WORLD, &self->ThisTask);
  MPI_Comm_size(MPI_COMM_WORLD, &self->NTask);

  for (self->PTask = 0; self->NTask > (1 << self->PTask); self->PTask++)
    ;

  /* init parameters */
  Tree_InitDefaultParameters(self);

  // if (PyDict_Check(params)) Tree_SetParameters(self, params);

  /* count number of particles */

  /* self->NtypeLocal[0] = *(int *)(ntype->data + 0 * (ntype->strides[0])); */
  /* self->NtypeLocal[1] = *(int *)(ntype->data + 1 * (ntype->strides[0])); */
  /* self->NtypeLocal[2] = *(int *)(ntype->data + 2 * (ntype->strides[0])); */
  /* self->NtypeLocal[3] = *(int *)(ntype->data + 3 * (ntype->strides[0])); */
  /* self->NtypeLocal[4] = *(int *)(ntype->data + 4 * (ntype->strides[0])); */
  /* self->NtypeLocal[5] = *(int *)(ntype->data + 5 * (ntype->strides[0])); */

  self->NumPart = 0;
  self->N_gas = self->NtypeLocal[0];
  for (i = 0; i < 6; i++) self->NumPart += self->NtypeLocal[i];

  MPI_Allreduce(&self->NumPart, &self->All.TotNumPart, 1, MPI_INT, MPI_SUM,
                MPI_COMM_WORLD);
  MPI_Allreduce(&self->N_gas, &self->All.TotN_gas, 1, MPI_INT, MPI_SUM,
                MPI_COMM_WORLD);

  for (i = 0; i < 6; i++)
    self->All.SofteningTable[i] = 0.1; /* a changer !!!! */

  for (i = 0; i < 6; i++)
    self->All.ForceSoftening[i] = 0.1; /* a changer !!!! */

  /* update parameters */

  self->All.MaxPart =
      self->All.PartAllocFactor * (self->All.TotNumPart / self->NTask);
  self->All.MaxPartSph =
      self->All.PartAllocFactor * (self->All.TotN_gas / self->NTask);
  self->All.MinGasHsml =
      self->All.MinGasHsmlFractional * self->All.ForceSoftening[0];

  self->All.BunchSizeDomain =
      (self->All.BufferSize * 1024 * 1024) /
      (sizeof(struct particle_data) + sizeof(struct sph_particle_data) +
       sizeof(peanokey));

  if (self->All.BunchSizeDomain & 1)
    self->All.BunchSizeDomain -=
        1; /* make sure that All.BunchSizeDomain is even
              --> 8-byte alignment of DomainKeyBuf for 64bit processors */

  self->All.BunchSizeForce =
      (self->All.BufferSize * 1024 * 1024) /
      (sizeof(struct gravdata_index) + 2 * sizeof(struct gravdata_in));

  if (self->All.BunchSizeForce & 1)
    self->All.BunchSizeForce -=
        1; /* make sure that All.BunchSizeForce is an even number
      --> 8-byte alignment for 64bit processors */

  self->All.BunchSizeDensity =
      (self->All.BufferSize * 1024 * 1024) /
      (2 * sizeof(struct densdata_in) + 2 * sizeof(struct densdata_out));

  self->first_flag = 0;

  /*********************/
  /* some allocation   */
  /*********************/

  if (!(self->CommBuffer =
            malloc(bytes = self->All.BufferSize * 1024 * 1024))) {
    printf("failed to allocate memory for `CommBuffer' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 2);
  }

  self->Exportflag = malloc(self->NTask * sizeof(char));
  self->GravDataIndexTable = (struct gravdata_index *)self->CommBuffer;
  self->GravDataIn = (struct gravdata_in *)(self->GravDataIndexTable +
                                            self->All.BunchSizeForce);
  self->GravDataGet = self->GravDataIn + self->All.BunchSizeForce;
  self->GravDataOut = self->GravDataIn;
  self->GravDataResult = self->GravDataGet;

  self->DensDataIn = (struct densdata_in *)self->CommBuffer;
  self->DensDataGet = self->DensDataIn + self->All.BunchSizeDensity;
  self->DensDataResult =
      (struct densdata_out *)(self->DensDataGet + self->All.BunchSizeDensity);
  self->DensDataPartialResult =
      self->DensDataResult + self->All.BunchSizeDensity;

  /*********************/
  /* create P          */
  /*********************/

  if (!(self->P =
            malloc(bytes = self->All.MaxPart * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `P' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  if (!(self->SphP = malloc(bytes = self->All.MaxPartSph *
                                    sizeof(struct sph_particle_data)))) {
    printf("failed to allocate memory for `SphP' (%g MB) %ld.\n",
           bytes / (1024.0 * 1024.0), sizeof(struct sph_particle_data));
    endrun(self, 1);
  }

  /*********************/
  /* init P            */
  /*********************/

  /* for (i = 0; i < pos->dimensions[0]; i++) { */
  /*   self->P[i].Pos[0] = */
  /*       *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
   */
  /*   self->P[i].Pos[1] = */
  /*       *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
   */
  /*   self->P[i].Pos[2] = */
  /*       *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
   */
  /*   self->P[i].Vel[0] = */
  /*       *(float *)(vel->data + i * (vel->strides[0]) + 0 * vel->strides[1]);
   */
  /*   self->P[i].Vel[1] = */
  /*       *(float *)(vel->data + i * (vel->strides[0]) + 1 * vel->strides[1]);
   */
  /*   self->P[i].Vel[2] = */
  /*       *(float *)(vel->data + i * (vel->strides[0]) + 2 * vel->strides[1]);
   */
  /*   self->P[i].Mass = *(float *)(mass->data + i * (mass->strides[0])); */
  /*   self->P[i].ID = *(unsigned int *)(num->data + i * (num->strides[0])); */
  /*   self->P[i].Type = */
  /*       *(int *)(tpe->data + */
  /*                i * (tpe->strides[0])); /\* this should be changed... *\/ */
  /*   self->P[i].Active = 1; */
  /* } */

  /***************************************
   * init ewald   *
  /***************************************/

  if (self->All.PeriodicBoundariesOn) ewald_init(self);

  /***************************************
   * domain decomposition construction   *
  /***************************************/

  domain_allocate(self);
  domain_Decomposition(self);

  return 0;
}

static PyObject *Tree_info(Tree *self) {

  // static PyObject *format = NULL;
  // PyObject *args, *result;

  printf("(%d) NumPart = %d\n", self->ThisTask, self->NumPart);
  printf("(%d) N_gas   = %d\n", self->ThisTask, self->N_gas);

  printf("(%d) DomainLen	= %g\n", self->ThisTask, self->DomainLen);
  printf("(%d) DomainCenter x = %g\n", self->ThisTask, self->DomainCenter[0]);
  printf("(%d) DomainCenter y = %g\n", self->ThisTask, self->DomainCenter[1]);
  printf("(%d) DomainCenter z = %g\n", self->ThisTask, self->DomainCenter[2]);
  printf("(%d) DomainCorner x = %g\n", self->ThisTask, self->DomainCorner[0]);
  printf("(%d) DomainCorner y = %g\n", self->ThisTask, self->DomainCorner[1]);
  printf("(%d) DomainCorner z = %g\n", self->ThisTask, self->DomainCorner[2]);
  printf("(%d) NTopnodes = %d\n", self->ThisTask, self->NTopnodes);
  printf("(%d) NTopleaves = %d\n", self->ThisTask, self->NTopleaves);

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_InitEwald(Tree *self) {
  if (self->All.PeriodicBoundariesOn) ewald_init(self);
}

static PyObject *Tree_InitDefaultParameters(Tree *self) {
  /* list of Gadget parameters */

  self->All.ComovingIntegrationOn = 0;
  self->All.PeriodicBoundariesOn = 0;

  self->All.Omega0 = 0;
  self->All.OmegaLambda = 0;
  self->All.OmegaBaryon = 0;
  self->All.HubbleParam = 0;
  self->All.G = 1; /* new */
  self->All.BoxSize = 0;

  self->All.ErrTolTheta = 0.7;
  self->All.TypeOfOpeningCriterion = 0;
  self->All.ErrTolForceAcc = 0.005;

  self->All.DesNumNgb = 33;
  self->All.MaxNumNgbDeviation = 3;

  self->All.PartAllocFactor = 2.0;
  self->All.TreeAllocFactor = 2.0;
  self->All.BufferSize = 30;

  self->All.MinGasHsmlFractional = 0.25;

  self->All.SofteningGas = 0.5;
  self->All.SofteningHalo = 0.5;
  self->All.SofteningDisk = 0.5;
  self->All.SofteningBulge = 0.5;
  self->All.SofteningStars = 0.5;
  self->All.SofteningBndry = 0.5;

  self->All.SofteningGasMaxPhys = 0.5;
  self->All.SofteningHaloMaxPhys = 0.5;
  self->All.SofteningDiskMaxPhys = 0.5;
  self->All.SofteningBulgeMaxPhys = 0.5;
  self->All.SofteningStarsMaxPhys = 0.5;
  self->All.SofteningBndryMaxPhys = 0.5;

  self->All.OutputInfo = 0;        /* output info */
  self->All.PeanoHilbertOrder = 0; /* peano hilbert order */

  return Py_BuildValue("i", 1);
}

/* set parameters */

static void Tree_SetComovingIntegrationOn(Tree *self, int val) {
  self->All.ComovingIntegrationOn = (int)val;
}

static void Tree_SetPeriodicBoundariesOn(Tree *self, int val) {
  self->All.PeriodicBoundariesOn = (int)val;
}

static void Tree_SetOmega0(Tree *self, double val) {
  self->All.Omega0 = (double)val;
}

static void Tree_SetOmegaLambda(Tree *self, double val) {
  self->All.OmegaLambda = (double)val;
}

static void Tree_SetOmegaBaryon(Tree *self, double val) {
  self->All.OmegaBaryon = (double)val;
}

static void Tree_SetHubbleParam(Tree *self, double val) {
  self->All.HubbleParam = (double)val;
}

static void Tree_SetG(Tree *self, double val) { self->All.G = (double)val; }

static void Tree_SetBoxSize(Tree *self, int val) {
  self->All.BoxSize = (int)val;
}

static void Tree_SetErrTolTheta(Tree *self, double val) {
  self->All.ErrTolTheta = (double)val;
}

static void Tree_SetTypeOfOpeningCriterion(Tree *self, int val) {
  self->All.TypeOfOpeningCriterion = (int)val;
}

static void Tree_SetErrTolForceAcc(Tree *self, double val) {
  self->All.ErrTolForceAcc = (double)val;
}

static void Tree_SetDesNumNgb(Tree *self, int val) {
  self->All.DesNumNgb = (int)val;
}

static void Tree_SetMaxNumNgbDeviation(Tree *self, int val) {
  self->All.MaxNumNgbDeviation = (int)val;
}

static void Tree_SetPartAllocFactor(Tree *self, double val) {
  self->All.PartAllocFactor = (double)val;
}

static void Tree_SetTreeAllocFactor(Tree *self, double val) {
  self->All.TreeAllocFactor = (double)val;
}

static void Tree_SetBufferSize(Tree *self, int val) {
  self->All.BufferSize = (int)val;
}

static void Tree_SetMinGasHsmlFractional(Tree *self, double val) {
  self->All.MinGasHsmlFractional = (double)val;
}

static void Tree_SetSofteningGas(Tree *self, double val) {
  self->All.SofteningGas = (double)val;
}

static void Tree_SetSofteningHalo(Tree *self, double val) {
  self->All.SofteningHalo = (double)val;
}

static void Tree_SetSofteningDisk(Tree *self, double val) {
  self->All.SofteningDisk = (double)val;
}

static void Tree_SetSofteningBulge(Tree *self, double val) {
  self->All.SofteningBulge = (double)val;
}

static void Tree_SetSofteningStars(Tree *self, double val) {
  self->All.SofteningStars = (double)val;
}

static void Tree_SetSofteningBndry(Tree *self, double val) {
  self->All.SofteningBndry = (double)val;
}

static void Tree_SetSofteningGasMaxPhys(Tree *self, double val) {
  self->All.SofteningGasMaxPhys = (double)val;
}

static void Tree_SetSofteningHaloMaxPhys(Tree *self, double val) {
  self->All.SofteningHaloMaxPhys = (double)val;
}

static void Tree_SetSofteningDiskMaxPhys(Tree *self, double val) {
  self->All.SofteningDiskMaxPhys = (double)val;
}

static void Tree_SetSofteningBulgeMaxPhys(Tree *self, double val) {
  self->All.SofteningBulgeMaxPhys = (double)val;
}

static void Tree_SetSofteningStarsMaxPhys(Tree *self, double val) {
  self->All.SofteningStarsMaxPhys = (double)val;
}

static void Tree_SetSofteningBndryMaxPhys(Tree *self, double val) {
  self->All.SofteningBndryMaxPhys = (double)val;
}

static void Tree_SetOutputInfo(Tree *self, int val) {
  self->All.OutputInfo = (int)val;
}

static void Tree_SetPeanoHilbertOrder(Tree *self, int val) {
  self->All.PeanoHilbertOrder = (int)val;
}

/* get parameters */

static int Tree_GetComovingIntegrationOn(Tree *self, int val) {
  return self->All.ComovingIntegrationOn;
}

static int Tree_GetPeriodicBoundariesOn(Tree *self, int val) {
  return self->All.PeriodicBoundariesOn;
}

static double Tree_GetOmega0(Tree *self, double val) {
  return self->All.Omega0;
}

static double Tree_GetOmegaLambda(Tree *self, double val) {
  return self->All.OmegaLambda;
}

static double Tree_GetOmegaBaryon(Tree *self, double val) {
  return self->All.OmegaBaryon;
}

static double Tree_GetHubbleParam(Tree *self, double val) {
  return self->All.HubbleParam;
}

static double Tree_GetG(Tree *self, double val) { return self->All.G; }

static int Tree_GetBoxSize(Tree *self, int val) { return self->All.BoxSize; }

static double Tree_GetErrTolTheta(Tree *self, double val) {
  return self->All.ErrTolTheta;
}

static int Tree_GetTypeOfOpeningCriterion(Tree *self, int val) {
  return self->All.TypeOfOpeningCriterion;
}

static double Tree_GetErrTolForceAcc(Tree *self, double val) {
  return self->All.ErrTolForceAcc;
}

static int Tree_GetDesNumNgb(Tree *self, int val) {
  return self->All.DesNumNgb;
}

static int Tree_GetMaxNumNgbDeviation(Tree *self, int val) {
  return self->All.MaxNumNgbDeviation;
}

static double Tree_GetPartAllocFactor(Tree *self, double val) {
  return self->All.PartAllocFactor;
}

static double Tree_GetTreeAllocFactor(Tree *self, double val) {
  return self->All.TreeAllocFactor;
}

static int Tree_GetBufferSize(Tree *self, int val) {
  return self->All.BufferSize;
}

static double Tree_GetMinGasHsmlFractional(Tree *self, double val) {
  return self->All.MinGasHsmlFractional;
}

static double Tree_GetSofteningGas(Tree *self, double val) {
  return self->All.SofteningGas;
}

static double Tree_GetSofteningHalo(Tree *self, double val) {
  return self->All.SofteningHalo;
}

static double Tree_GetSofteningDisk(Tree *self, double val) {
  return self->All.SofteningDisk;
}

static double Tree_GetSofteningBulge(Tree *self, double val) {
  return self->All.SofteningBulge;
}

static double Tree_GetSofteningStars(Tree *self, double val) {
  return self->All.SofteningStars;
}

static double Tree_GetSofteningBndry(Tree *self, double val) {
  return self->All.SofteningBndry;
}

static double Tree_GetSofteningGasMaxPhys(Tree *self, double val) {
  return self->All.SofteningGasMaxPhys;
}

static double Tree_GetSofteningHaloMaxPhys(Tree *self, double val) {
  return self->All.SofteningHaloMaxPhys;
}

static double Tree_GetSofteningDiskMaxPhys(Tree *self, double val) {
  return self->All.SofteningDiskMaxPhys;
}

static double Tree_GetSofteningBulgeMaxPhys(Tree *self, double val) {
  return self->All.SofteningBulgeMaxPhys;
}

static double Tree_GetSofteningStarsMaxPhys(Tree *self, double val) {
  return self->All.SofteningStarsMaxPhys;
}

static double Tree_GetSofteningBndryMaxPhys(Tree *self, double val) {
  return self->All.SofteningBndryMaxPhys;
}

static int Tree_GetOutputInfo(Tree *self, int val) {
  return self->All.OutputInfo;
}

static int Tree_GetPeanoHilbertOrder(Tree *self, int val) {
  return self->All.PeanoHilbertOrder;
}

static PyObject *Tree_SetParameters(Tree *self, PyObject *args) {

  PyObject *dict;
  PyObject *key;
  PyObject *value;
  int ivalue;
  float fvalue;
  double dvalue;

  /* here, we can have either arguments or dict directly */

  if (PyDict_Check(args)) {
    dict = args;
  } else {
    if (!PyArg_ParseTuple(args, "O", &dict)) return NULL;
  }

  /* check that it is a PyDictObject */
  if (!PyDict_Check(dict)) {
    PyErr_SetString(PyExc_AttributeError, "argument is not a dictionary.");
    return NULL;
  }

  Py_ssize_t pos = 0;
  while (PyDict_Next(dict, &pos, &key, &value)) {

    if (PyUnicode_Check(key)) {

      if (strcmp(PyBytes_AsString(key), "ComovingIntegrationOn") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetComovingIntegrationOn(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "PeriodicBoundariesOn") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetPeriodicBoundariesOn(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "Omega0") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetOmega0(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "OmegaLambda") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetOmegaLambda(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "OmegaBaryon") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetOmegaBaryon(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "HubbleParam") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetHubbleParam(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "G") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetG(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "BoxSize") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetBoxSize(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "ErrTolTheta") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetErrTolTheta(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "TypeOfOpeningCriterion") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetTypeOfOpeningCriterion(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "ErrTolForceAcc") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetErrTolForceAcc(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "DesNumNgb") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetDesNumNgb(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "MaxNumNgbDeviation") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetMaxNumNgbDeviation(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "PartAllocFactor") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetPartAllocFactor(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "TreeAllocFactor") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetTreeAllocFactor(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "BufferSize") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetBufferSize(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "MinGasHsmlFractional") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetMinGasHsmlFractional(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningGas") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningGas(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningHalo") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningHalo(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningDisk") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningDisk(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningBulge") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningBulge(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningStars") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningStars(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningBndry") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningBndry(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningGasMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningGasMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningHaloMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningHaloMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningDiskMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningDiskMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningBulgeMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningBulgeMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningStarsMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningStarsMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "SofteningBndryMaxPhys") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          dvalue = PyFloat_AsDouble(value);
          Tree_SetSofteningBndryMaxPhys(self, dvalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "OutputInfo") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetOutputInfo(self, ivalue);
        }
      }

      if (strcmp(PyBytes_AsString(key), "PeanoHilbertOrder") == 0) {
        if ( PyLong_Check(value) || PyFloat_Check(value)) {
          ivalue = PyLong_AsLong(value);
          Tree_SetPeanoHilbertOrder(self, ivalue);
        }
      }
    }
  }

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_GetParameters(Tree *self) {

  PyObject *dict;
  PyObject *key;
  PyObject *value;

  dict = PyDict_New();

  key = PyUnicode_FromString("ComovingIntegrationOn");
  value = PyLong_FromLong(self->All.ComovingIntegrationOn);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("PeriodicBoundariesOn");
  value = PyLong_FromLong(self->All.PeriodicBoundariesOn);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("Omega0");
  value = PyFloat_FromDouble(self->All.Omega0);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("OmegaLambda");
  value = PyFloat_FromDouble(self->All.OmegaLambda);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("OmegaBaryon");
  value = PyFloat_FromDouble(self->All.OmegaBaryon);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("HubbleParam");
  value = PyFloat_FromDouble(self->All.HubbleParam);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("G");
  value = PyFloat_FromDouble(self->All.G);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("BoxSize");
  value = PyFloat_FromDouble(self->All.BoxSize);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("ErrTolTheta");
  value = PyFloat_FromDouble(self->All.ErrTolTheta);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("TypeOfOpeningCriterion");
  value = PyLong_FromLong(self->All.TypeOfOpeningCriterion);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("ErrTolForceAcc");
  value = PyFloat_FromDouble(self->All.ErrTolForceAcc);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("DesNumNgb");
  value = PyLong_FromLong(self->All.DesNumNgb);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("PartAllocFactor");
  value = PyFloat_FromDouble(self->All.PartAllocFactor);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("TreeAllocFactor");
  value = PyFloat_FromDouble(self->All.TreeAllocFactor);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("BufferSize");
  value = PyLong_FromLong(self->All.BufferSize);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("MinGasHsmlFractional");
  value = PyFloat_FromDouble(self->All.MinGasHsmlFractional);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningGas");
  value = PyFloat_FromDouble(self->All.SofteningGas);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningHalo");
  value = PyFloat_FromDouble(self->All.SofteningHalo);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningDisk");
  value = PyFloat_FromDouble(self->All.SofteningDisk);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningBulge");
  value = PyFloat_FromDouble(self->All.SofteningBulge);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningStars");
  value = PyFloat_FromDouble(self->All.SofteningStars);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningBndry");
  value = PyFloat_FromDouble(self->All.SofteningBndry);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningGasMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningGasMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningHaloMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningHaloMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningDiskMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningDiskMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningBulgeMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningBulgeMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningStarsMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningStarsMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("SofteningBndryMaxPhys");
  value = PyFloat_FromDouble(self->All.SofteningBndryMaxPhys);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("OutputInfo");
  value = PyFloat_FromDouble(self->All.OutputInfo);
  PyDict_SetItem(dict, key, value);

  key = PyUnicode_FromString("PeanoHilbertOrder");
  value = PyFloat_FromDouble(self->All.PeanoHilbertOrder);
  PyDict_SetItem(dict, key, value);

  return Py_BuildValue("O", dict);
}

static PyObject *Tree_GetExchanges(Tree *self) {

  PyArrayObject *a_num, *a_procs;
  int i;
  npy_intp ld[1];

  /* create a NumPy object */
  ld[0] = self->NSend;

  PyArrayObject *pos;
  a_num = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_INT);
  a_procs = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_INT);

  for (i = 0; i < a_num->dimensions[0]; i++) {
    *(int *)(a_num->data + i * (a_num->strides[0])) = self->DomainIdProc[i].ID;
    *(int *)(a_procs->data + i * (a_procs->strides[0])) =
        self->DomainIdProc[i].Proc;
  }

  return Py_BuildValue("OO", a_num, a_procs);
}

static PyObject *Tree_SetParticles(Tree *self, PyObject *args) {

  int i;

  PyArrayObject *ntype, *pos, *vel, *mass, *num, *tpe;

  if (!PyArg_ParseTuple(args, "OOOOOO", &ntype, &pos, &vel, &mass, &num, &tpe))
    return Py_BuildValue("i", -1);

  /* count number of particles */

  self->NtypeLocal[0] = *(int *)(ntype->data + 0 * (ntype->strides[0]));
  self->NtypeLocal[1] = *(int *)(ntype->data + 1 * (ntype->strides[0]));
  self->NtypeLocal[2] = *(int *)(ntype->data + 2 * (ntype->strides[0]));
  self->NtypeLocal[3] = *(int *)(ntype->data + 3 * (ntype->strides[0]));
  self->NtypeLocal[4] = *(int *)(ntype->data + 4 * (ntype->strides[0]));
  self->NtypeLocal[5] = *(int *)(ntype->data + 5 * (ntype->strides[0]));

  self->NumPart = 0;
  self->N_gas = self->NtypeLocal[0];
  for (i = 0; i < 6; i++) self->NumPart += self->NtypeLocal[i];

  MPI_Allreduce(&self->NumPart, &self->All.TotNumPart, 1, MPI_INT, MPI_SUM,
                MPI_COMM_WORLD);
  MPI_Allreduce(&self->N_gas, &self->All.TotN_gas, 1, MPI_INT, MPI_SUM,
                MPI_COMM_WORLD);

  /*********************/
  /* init P		 */
  /*********************/

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->P[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->P[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->P[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->P[i].Vel[0] =
        *(float *)(vel->data + i * (vel->strides[0]) + 0 * vel->strides[1]);
    self->P[i].Vel[1] =
        *(float *)(vel->data + i * (vel->strides[0]) + 1 * vel->strides[1]);
    self->P[i].Vel[2] =
        *(float *)(vel->data + i * (vel->strides[0]) + 2 * vel->strides[1]);
    self->P[i].Mass = *(float *)(mass->data + i * (mass->strides[0]));
    self->P[i].ID = *(unsigned int *)(num->data + i * (num->strides[0]));
    self->P[i].Type = *(int *)(tpe->data + i * (tpe->strides[0]));
    /* this should be changed... */
  }

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_BuildTree(Tree *self) {

  /************************
  /* tree construction    *
  /************************/
  force_treeallocate(self, self->All.TreeAllocFactor * self->All.MaxPart,
                     self->All.MaxPart);
  force_treebuild(self, self->NumPart);

  /************************
  /* ngb                  *
  /************************/
  ngb_treeallocate(self, self->NumPart);

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_AllPotential(Tree *self) {
  compute_potential(self);
  // printf("\n %g %g %g
  // %g\n",self->P[0].Pos[0],self->P[0].Pos[1],self->P[0].Pos[2],self->P[0].Potential);
  return Py_BuildValue("i", 1);
}

static PyObject *Tree_AllAcceleration(Tree *self) {

  /* gravitational acceleration */
  gravity_tree(self);

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_AllDensity(Tree *self) {

  /* here, we need hsml */
  density_init_hsml(self);

  /* gravitational acceleration */
  density(self);

  return Py_BuildValue("i", 1);
}

static PyObject *Tree_GetAllPotential(Tree *self) {

  PyArrayObject *pot;
  npy_intp ld[1];
  int i;

  ld[0] = self->NumPart;

  pot = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_FLOAT);

  for (i = 0; i < pot->dimensions[0]; i++) {
    *(float *)(pot->data + i * (pot->strides[0])) = self->P[i].Potential;
  }

  return PyArray_Return(pot);
}

static PyObject *Tree_GetAllAcceleration(Tree *self) {

  PyArrayObject *acc;
  npy_intp ld[1];
  int i;

  acc = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_FLOAT);

  return PyArray_Return(acc);
}

static PyObject *Tree_GetAllDensity(Tree *self) {

  PyArrayObject *density;
  npy_intp ld[1];
  int i;

  density = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_FLOAT);

  return PyArray_Return(density);
}

static PyObject *Tree_Potential(Tree *self, PyObject *args) {

  PyArrayObject *pos;
  float eps;

  if (!PyArg_ParseTuple(args, "Of", &pos, &eps))
    return PyUnicode_FromString("error");

  PyArrayObject *pot;
  int i;
  npy_intp ld[1];
  int input_dimension;
  size_t bytes;

  input_dimension = pos->nd;

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (pos->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = pos->dimensions[0];
  pot = (PyArrayObject *)PyArray_SimpleNew(1, ld, PyArray_FLOAT);

  self->NumPartQ = pos->dimensions[0];
  self->ForceSofteningQ = eps;

  if (!(self->Q =
            malloc(bytes = self->NumPartQ * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `Q' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->Q[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->Q[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->Q[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->Q[i].Type = 0;
    self->Q[i].Potential = 0;
  }

  compute_potential_sub(self);

  for (i = 0; i < pos->dimensions[0]; i++) {
    *(float *)(pot->data + i * (pot->strides[0])) = self->Q[i].Potential;
  }

  free(self->Q);

  return PyArray_Return(pot);
}

static PyObject *Tree_Acceleration(Tree *self, PyObject *args) {

  PyArrayObject *pos;
  float eps;

  if (!PyArg_ParseTuple(args, "Of", &pos, &eps))
    return PyUnicode_FromString("error");

  PyArrayObject *acc;
  int i;
  int ld[1];
  int input_dimension;
  size_t bytes;

  input_dimension = pos->nd;

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (pos->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  /* create a NumPy object */
  ld[0] = pos->dimensions[0];
  acc = (PyArrayObject *)PyArray_SimpleNew(pos->nd, pos->dimensions,
                                           pos->descr->type_num);

  self->NumPartQ = pos->dimensions[0];
  self->ForceSofteningQ = eps;

  if (!(self->Q =
            malloc(bytes = self->NumPartQ * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `Q' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->Q[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->Q[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->Q[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->Q[i].Type = 0;
    self->Q[i].GravAccel[0] = 0;
    self->Q[i].GravAccel[1] = 0;
    self->Q[i].GravAccel[2] = 0;
  }

  gravity_tree_sub(self);

  for (i = 0; i < pos->dimensions[0]; i++) {
    *(float *)(acc->data + i * (acc->strides[0]) + 0 * acc->strides[1]) =
        self->Q[i].GravAccel[0];
    *(float *)(acc->data + i * (acc->strides[0]) + 1 * acc->strides[1]) =
        self->Q[i].GravAccel[1];
    *(float *)(acc->data + i * (acc->strides[0]) + 2 * acc->strides[1]) =
        self->Q[i].GravAccel[2];
  }

  free(self->Q);

  return PyArray_Return(acc);
}

static PyObject *Tree_oldDensity(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;

  if (!PyArg_ParseTuple(args, "OO", &pos, &hsml))
    return PyUnicode_FromString("error");

  PyArrayObject *vden, *vhsml;
  int i;
  int ld[1];
  int input_dimension;
  size_t bytes;

  input_dimension = pos->nd;

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (pos->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  if (hsml->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 2 must be of type Float32");

  if (pos->dimensions[0] != hsml->dimensions[0])
    PyErr_SetString(PyExc_ValueError,
                    "pos and hsml must have the same dimension.");

  /* create a NumPy object */
  ld[0] = pos->dimensions[0];
  vden = (PyArrayObject *)PyArray_SimpleNew(1, pos->dimensions,
                                            pos->descr->type_num);
  vhsml = (PyArrayObject *)PyArray_SimpleNew(1, pos->dimensions,
                                             pos->descr->type_num);

  self->NumPartQ = pos->dimensions[0];
  self->N_gasQ;
  self->NumSphUpdateQ;

  if (!(self->Q =
            malloc(bytes = self->NumPartQ * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `Q' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  if (!(self->SphQ =
            malloc(bytes = self->N_gasQ * sizeof(struct sph_particle_data)))) {
    printf("failed to allocate memory for `SphP' (%g MB) %ld.\n",
           bytes / (1024.0 * 1024.0), sizeof(struct sph_particle_data));
    endrun(self, 1);
  }

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->Q[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->Q[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->Q[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->Q[i].Type = 0;
    self->Q[i].GravAccel[0] = 0;
    self->Q[i].GravAccel[1] = 0;
    self->Q[i].GravAccel[2] = 0;

    self->SphQ[i].Hsml = 0.1; /* !!!!!! this must be changed !!!! */
  }

  // density_sub(self);

  for (i = 0; i < pos->dimensions[0]; i++) {
    *(float *)(vden->data + i * (vden->strides[0])) = self->SphQ[i].Density;
    *(float *)(vhsml->data + i * (vhsml->strides[0])) = self->SphQ[i].Hsml;
  }

  free(self->Q);
  free(self->SphQ);

  // return Py_BuildValue("OO",vden,vhsml);
  return Py_BuildValue("i", 1);
}

static PyObject *Tree_Density(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;

  if (!PyArg_ParseTuple(args, "OO", &pos, &hsml))
    return PyUnicode_FromString("error");

  PyArrayObject *vden, *vhsml;
  int i;
  int ld[1];
  int input_dimension;
  size_t bytes;

  input_dimension = pos->nd;

  if (input_dimension != 2)
    PyErr_SetString(PyExc_ValueError, "dimension of first argument must be 2");

  if (pos->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 1 must be of type Float32");

  if (hsml->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError, "argument 2 must be of type Float32");

  if (pos->dimensions[0] != hsml->dimensions[0])
    PyErr_SetString(PyExc_ValueError,
                    "pos and hsml must have the same dimension.");

  /* create a NumPy object */
  ld[0] = pos->dimensions[0];
  vden = (PyArrayObject *)PyArray_SimpleNew(1, pos->dimensions,
                                            pos->descr->type_num);
  vhsml = (PyArrayObject *)PyArray_SimpleNew(1, pos->dimensions,
                                             pos->descr->type_num);

  self->NumPartQ = pos->dimensions[0];
  self->N_gasQ = pos->dimensions[0];

  if (!(self->Q =
            malloc(bytes = self->NumPartQ * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `Q' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  if (!(self->SphQ =
            malloc(bytes = self->N_gasQ * sizeof(struct sph_particle_data)))) {
    printf("failed to allocate memory for `SphP' (%g MB) %ld.\n",
           bytes / (1024.0 * 1024.0), sizeof(struct sph_particle_data));
    endrun(self, 1);
  }

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->Q[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->Q[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->Q[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->Q[i].Type = 0;
    self->Q[i].GravAccel[0] = 0;
    self->Q[i].GravAccel[1] = 0;
    self->Q[i].GravAccel[2] = 0;

    self->Q[i].Active = 1;
    self->SphQ[i].Hsml = *(float *)(hsml->data + i * (hsml->strides[0]));
  }

  density_sub(self);

  for (i = 0; i < pos->dimensions[0]; i++) {
    *(float *)(vden->data + i * (vden->strides[0])) = self->SphQ[i].Density;
    *(float *)(vhsml->data + i * (vhsml->strides[0])) = self->SphQ[i].Hsml;
  }

  free(self->Q);
  free(self->SphQ);

  return Py_BuildValue("OO", vden, vhsml);
}

static PyObject *Tree_SphEvaluate(Tree *self, PyObject *args) {

  PyArrayObject *pos, *hsml;
  PyArrayObject *Density, *Observable;

  if (!PyArg_ParseTuple(args, "OOOO", &pos, &hsml, &Density, &Observable))
    return PyUnicode_FromString("error");

  PyArrayObject *vobservable;
  int i;
  int ld[1];
  size_t bytes;

  if (pos->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError,
                    "argument 1 (pos) must be of type Float32");

  if (hsml->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError,
                    "argument 2 (hsml) must be of type Float32");

  if (Density->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError,
                    "argument 3 (Density) must be of type Float32");

  if (Observable->descr->type_num != PyArray_FLOAT)
    PyErr_SetString(PyExc_ValueError,
                    "argument 4 (Observable) must be of type Float32");

  if (pos->nd != 2)
    PyErr_SetString(PyExc_ValueError,
                    "dimension of first argument (pos) must be 2");

  if (hsml->nd != 1)
    PyErr_SetString(PyExc_ValueError,
                    "dimension of first argument (hsml) must be 1");

  if (Density->nd != 1)
    PyErr_SetString(PyExc_ValueError,
                    "dimension of first argument (Density) must be 1");

  if (Observable->nd != 1)
    PyErr_SetString(PyExc_ValueError,
                    "dimension of first argument (Observable) must be 1");

  if (Density->dimensions[0] != self->N_gas)
    PyErr_SetString(PyExc_ValueError,
                    "len of third argument (Density) must be NumPart\n");

  if (Observable->dimensions[0] != self->N_gas)
    PyErr_SetString(PyExc_ValueError,
                    "len of fourth argument (Observable) must be NumPart\n");

  /* create a NumPy object */
  vobservable =
      (PyArrayObject *)PyArray_SimpleNew(1, pos->dimensions, PyArray_FLOAT);

  self->NumPartQ = pos->dimensions[0];
  self->N_gasQ = pos->dimensions[0];

  if (!(self->Q =
            malloc(bytes = self->NumPartQ * sizeof(struct particle_data)))) {
    printf("failed to allocate memory for `Q' (%g MB).\n",
           bytes / (1024.0 * 1024.0));
    endrun(self, 1);
  }

  if (!(self->SphQ =
            malloc(bytes = self->N_gasQ * sizeof(struct sph_particle_data)))) {
    printf("failed to allocate memory for `SphP' (%g MB) %ld.\n",
           bytes / (1024.0 * 1024.0), sizeof(struct sph_particle_data));
    endrun(self, 1);
  }

  for (i = 0; i < pos->dimensions[0]; i++) {
    self->Q[i].Pos[0] =
        *(float *)(pos->data + i * (pos->strides[0]) + 0 * pos->strides[1]);
    self->Q[i].Pos[1] =
        *(float *)(pos->data + i * (pos->strides[0]) + 1 * pos->strides[1]);
    self->Q[i].Pos[2] =
        *(float *)(pos->data + i * (pos->strides[0]) + 2 * pos->strides[1]);
    self->Q[i].Type = 0;
    self->Q[i].GravAccel[0] = 0;
    self->Q[i].GravAccel[1] = 0;
    self->Q[i].GravAccel[2] = 0;

    self->Q[i].Active = 1;
    self->SphQ[i].Hsml = *(float *)(hsml->data + i * (hsml->strides[0]));
  }

  /* now, give observable value for P */

  for (i = 0; i < self->N_gas; i++) {
    self->SphP[i].Density =
        *(float *)(Density->data + i * (Density->strides[0]));
    self->SphP[i].Observable =
        *(float *)(Observable->data + i * (Observable->strides[0]));
  }

  sph_sub(self);

  for (i = 0; i < pos->dimensions[0]; i++) {
    *(float *)(vobservable->data + i * (vobservable->strides[0])) =
        self->SphQ[i].Observable;
  }

  free(self->Q);
  free(self->SphQ);

  return Py_BuildValue("O", vobservable);
}

static PyMemberDef Tree_members[] = {

    //{"first", T_OBJECT_EX, offsetof(Tree, first), 0,
    // "first name"},
    //{"list", T_OBJECT_EX, offsetof(Tree, list), 0,
    // "list of"},
    //{"number", T_INT, offsetof(Tree, number), 0,
    // "Tree number"},

    {NULL} /* Sentinel */
};

static PyMethodDef Tree_methods[] = {

    {"info", (PyCFunction)Tree_info, METH_NOARGS, "Return some info"},

    {"InitDefaultParameters", (PyCFunction)Tree_InitDefaultParameters,
     METH_NOARGS, "Init defaults tree parameters"},

    {"InitEwald", (PyCFunction)Tree_InitEwald, METH_NOARGS,
     "Init ewald parameters"},

    {"SetParameters", (PyCFunction)Tree_SetParameters, METH_VARARGS,
     "Set tree parameters"},

    {"GetParameters", (PyCFunction)Tree_GetParameters, METH_NOARGS,
     "Get tree parameters"},

    {"GetExchanges", (PyCFunction)Tree_GetExchanges, METH_NOARGS,
     "This function returns the list of particles that have been exchanged and "
     "the corresponding processor."},

    {"SetParticles", (PyCFunction)Tree_SetParticles, METH_VARARGS,
     "Set values of particles"},

    {"BuildTree", (PyCFunction)Tree_BuildTree, METH_NOARGS, "Build the tree"},

    {"Potential", (PyCFunction)Tree_Potential, METH_VARARGS,
     "Computes the potential at a given position using the tree"},

    {"Acceleration", (PyCFunction)Tree_Acceleration, METH_VARARGS,
     "Computes the acceleration at a given position using the tree"},

    {"Density", (PyCFunction)Tree_Density, METH_VARARGS,
     "Computes densities at a given position using the tree"},

    {"SphEvaluate", (PyCFunction)Tree_SphEvaluate, METH_VARARGS,
     "Compute value of an observable at a given position using SPH."},

    {"AllPotential", (PyCFunction)Tree_AllPotential, METH_VARARGS,
     "Computes the potential for each particle"},

    {"AllAcceleration", (PyCFunction)Tree_AllAcceleration, METH_VARARGS,
     "Computes the acceleration for each particle"},

    {"AllDensity", (PyCFunction)Tree_AllDensity, METH_VARARGS,
     "Computes the density for each particle"},

    {"GetAllPotential", (PyCFunction)Tree_GetAllPotential, METH_VARARGS,
     "Get the potential for each particle"},

    {"GetAllAcceleration", (PyCFunction)Tree_GetAllAcceleration, METH_VARARGS,
     "Get the acceleration for each particle"},

    {"GetAllDensity", (PyCFunction)Tree_GetAllDensity, METH_VARARGS,
     "Get the density for each particle"},

    {NULL} /* Sentinel */
};

#ifndef PyVarObject_HEAD_INIT
    #define PyVarObject_HEAD_INIT(type, size) \
        PyObject_HEAD_INIT(type) size,
#endif

static PyTypeObject TreeType = {
    PyVarObject_HEAD_INIT(NULL, 0)            /*ob_size*/
    "tree.Tree",                              /*tp_name*/
    sizeof(Tree),                             /*tp_basicsize*/
    0,                                        /*tp_itemsize*/
    (destructor)Tree_dealloc,                 /*tp_dealloc*/
    0,                                        /*tp_print*/
    0,                                        /*tp_getattr*/
    0,                                        /*tp_setattr*/
    0,                                        /*tp_reserved*/
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
    (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE), /*tp_flags*/
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
};

#ifndef PyMODINIT_FUNC /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

static struct PyModuleDef ptreelibmodule = {
    PyModuleDef_HEAD_INIT,
    "ptreelib",
    "Example module that creates an extension type."
    -1,
    NULL, /* no moudle methods*/
    NULL, /* m_slots */
    NULL, /* m_traverse */
    NULL, /* m_clear */
    NULL  /* m_free */
};

PyMODINIT_FUNC PyInit_ptreelib(void) {

  PyObject *m;

  if (PyType_Ready(&TreeType) < 0) return NULL;
  
  m = PyModule_Create(&ptreelibmodule);
  if (m == NULL) return NULL;

  Py_INCREF(&TreeType);
  PyModule_AddObject(m, "Tree", (PyObject *)&TreeType);

  return m;
}
