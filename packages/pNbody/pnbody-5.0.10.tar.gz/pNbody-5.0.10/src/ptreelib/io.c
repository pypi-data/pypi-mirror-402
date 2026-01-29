
#include <Python.h>
#include <mpi.h>
#include <numpy/arrayobject.h>
#include "structmember.h"

#include "allvars.h"
#include "endrun.h"
#include "proto.h"
#include "ptreelib.h"

/*! This catches I/O errors occuring for my_fwrite(). In this case we
 *  better stop.
 */
size_t my_fwrite(Tree *self, void *ptr, size_t size, size_t nmemb,
                 FILE *stream) {
  size_t nwritten;

  if ((nwritten = fwrite(ptr, size, nmemb, stream)) != nmemb) {
    printf("I/O error (fwrite) on task=%d has occured: %s\n", self->ThisTask,
           strerror(errno));
    fflush(stdout);
    endrun(self, 777);
  }
  return nwritten;
}

/*! This catches I/O errors occuring for fread(). In this case we
 *  better stop.
 */
size_t my_fread(Tree *self, void *ptr, size_t size, size_t nmemb,
                FILE *stream) {
  size_t nread;

  if ((nread = fread(ptr, size, nmemb, stream)) != nmemb) {
    printf("I/O error (fread) on task=%d has occured: %s\n", self->ThisTask,
           strerror(errno));
    fflush(stdout);
    endrun(self, 778);
  }
  return nread;
}
