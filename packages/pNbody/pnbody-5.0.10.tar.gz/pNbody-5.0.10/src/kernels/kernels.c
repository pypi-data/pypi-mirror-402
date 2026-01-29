#include <Python.h>
#include <math.h>
#include "kernels.h"

/**
 * @brief Minimum of two numbers
 *
 * This macro evaluates its arguments exactly once.
 */
#define min(a, b)                 \
  ({                              \
    const __typeof__(a) _a = (a); \
    const __typeof__(b) _b = (b); \
    _a < _b ? _a : _b;            \
  })

/**
 * @brief Maximum of two numbers
 *
 * This macro evaluates its arguments exactly once.
 */
#define max(a, b)                 \
  ({                              \
    const __typeof__(a) _a = (a); \
    const __typeof__(b) _b = (b); \
    _a > _b ? _a : _b;            \
  })


/*
  normalization constants
*/

#define C_cub_spline_1D  2.6666666666666665
#define C_qua_spline_1D  4.069010416666667
#define C_qui_spline_1D  6.075

#define C_cub_spline_2D  3.6378272706718935
#define C_qua_spline_2D  6.222175110452539
#define C_qui_spline_2D  10.19457332131308

#define C_cub_spline_3D  5.092958178940651
#define C_qua_spline_3D  9.71404681957369
#define C_qui_spline_3D  17.403593027098754

/*
  H/h ratio
  h is the smoothing scale
  H is the kernel-support radius
*/

#define Hh_cub_spline_1D 1.732051
#define Hh_qua_spline_1D 1.936492
#define Hh_qui_spline_1D 2.121321

#define Hh_cub_spline_2D 1.778002
#define Hh_qua_spline_2D 1.977173
#define Hh_qui_spline_2D 2.158131

#define Hh_cub_spline_3D 1.825742
#define Hh_qua_spline_3D 2.018932
#define Hh_qui_spline_3D 2.195775


/*
 *  1D kernels
 * 
 */



/*! Normalized 1D cubic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wcub_1D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_cub_spline_1D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),3);
  w = w -4*pow(max(0.5-r,0.0),3);
  w = w *C_cub_spline_1D/h;
  
  return w;
}


/*! Normalized 1D quadratic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqua_1D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qua_spline_1D;  
  
  /* scale the radius */
  r = r/h;
    
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),4);
  w = w -5.0*pow(max(3.0/5.0-r,0.0),4);
  w = w +10.0*pow(max(1.0/5.0-r,0.0),4);
  w = w *C_qua_spline_1D/h;
  
  return w;
}

/*! Normalized 1D quintic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqui_1D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qui_spline_1D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),5);
  w = w -6.0*pow(max(2.0/3.0-r,0.0),5);
  w = w +15.0*pow(max(1.0/3.0-r,0.0),5);
  w = w *C_qui_spline_1D/h;
  
  return w;
}


/*
 *  2D kernels
 * 
 */



/*! Normalized 2D cubic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wcub_2D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_cub_spline_2D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),3);
  w = w -4*pow(max(0.5-r,0.0),3);
  w = w *C_cub_spline_2D/(h*h);
  
  return w;
}


/*! Normalized 2D quadratic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqua_2D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qua_spline_2D;  
  
  /* scale the radius */
  r = r/h;
    
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),4);
  w = w -5.0*pow(max(3.0/5.0-r,0.0),4);
  w = w +10.0*pow(max(1.0/5.0-r,0.0),4);
  w = w *C_qua_spline_2D/(h*h);
  
  return w;
}

/*! Normalized 1D quintic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqui_2D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qui_spline_2D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),5);
  w = w -6.0*pow(max(2.0/3.0-r,0.0),5);
  w = w +15.0*pow(max(1.0/3.0-r,0.0),5);
  w = w *C_qui_spline_2D/(h*h);
  
  return w;
}



/*
 *  2D kernels
 * 
 */



/*! Normalized 3D cubic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wcub_3D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_cub_spline_3D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),3);
  w = w -4*pow(max(0.5-r,0.0),3);
  w = w *C_cub_spline_3D/(h*h*h);
  
  return w;
}


/*! Normalized 3D quadratic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqua_3D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qua_spline_3D;  
  
  /* scale the radius */
  r = r/h;
    
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),4);
  w = w -5.0*pow(max(3.0/5.0-r,0.0),4);
  w = w +10.0*pow(max(1.0/5.0-r,0.0),4);
  w = w *C_qua_spline_3D/(h*h*h);
  
  return w;
}

/*! Normalized 3D quintic kernel
 *  h : the smoothing scale (2 sigma)
 */
double Wqui_3D(double r, double h){
  
  double w;
  
  /* h becomes now H, the kernel-support radius */
  h = h*Hh_qui_spline_3D;  
  
  /* scale the radius */
  r = r/h;
  
  /* normalized kernel part */
  w = 0;
  w = w +  pow(max(1-r,0.0),5);
  w = w -6.0*pow(max(2.0/3.0-r,0.0),5);
  w = w +15.0*pow(max(1.0/3.0-r,0.0),5);
  w = w *C_qui_spline_3D/(h*h*h);
  
  return w;
}













/*
 *  1D kernels
 * 
 */


static PyObject *
kernels_Wcub_1D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wcub_1D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqua_1D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqua_1D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqui_1D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqui_1D(r,h);
    
    return PyFloat_FromDouble(w);
}


/*
 *  2D kernels
 * 
 */


static PyObject *
kernels_Wcub_2D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wcub_2D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqua_2D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqua_2D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqui_2D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqui_2D(r,h);
    
    return PyFloat_FromDouble(w);
}


/*
 *  3D kernels
 * 
 */


static PyObject *
kernels_Wcub_3D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wcub_3D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqua_3D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqua_3D(r,h);
    
    return PyFloat_FromDouble(w);
}

static PyObject *
kernels_Wqui_3D(PyObject *self, PyObject *args)
{
    double r,h,w;

    if (!PyArg_ParseTuple(args, "dd", &r,&h))
        return NULL;
    
    w = Wqui_3D(r,h);
    
    return PyFloat_FromDouble(w);
}






static PyMethodDef kernelsMethods[] = {

    {"Wcub_1D",  kernels_Wcub_1D, METH_VARARGS,
     "Normalized 1D cubic kernel"},

    {"Wqua_1D",  kernels_Wqua_1D, METH_VARARGS,
     "Normalized 1D quadratic kernel"},

    {"Wqui_1D",  kernels_Wqui_1D, METH_VARARGS,
     "Normalized 1D quintic kernel"},
     
    {"Wcub_2D",  kernels_Wcub_2D, METH_VARARGS,
     "Normalized 2D cubic kernel"},

    {"Wqua_2D",  kernels_Wqua_2D, METH_VARARGS,
     "Normalized 2D quadratic kernel"},

    {"Wqui_2D",  kernels_Wqui_2D, METH_VARARGS,
     "Normalized 2D quintic kernel"},     

    {"Wcub_3D",  kernels_Wcub_3D, METH_VARARGS,
     "Normalized 3D cubic kernel"},

    {"Wqua_3D",  kernels_Wqua_3D, METH_VARARGS,
     "Normalized 3D quadratic kernel"},

    {"Wqui_3D",  kernels_Wqui_3D, METH_VARARGS,
     "Normalized 3D quintic kernel"},  



    {NULL, NULL, 0, NULL}        /* Sentinel */
};



static struct PyModuleDef kernelsmodule = {
    PyModuleDef_HEAD_INIT,
    "kernels",   /* name of module */
    "Defines some kernels functions", /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    kernelsMethods
};




PyMODINIT_FUNC
PyInit_kernels(void)
{
    return PyModule_Create(&kernelsmodule);
}



