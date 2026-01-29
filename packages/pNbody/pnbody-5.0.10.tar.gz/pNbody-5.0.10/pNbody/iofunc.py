#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      iofunc.py
#  brief:     Input/Output functions
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


# standard modules
import os
import sys
import string
import types
import pickle
import csv
import io
import yaml
import getpass
import time
  
# array module
import numpy as np
import astropy.io.fits as pyfits
from . import mpiwrapper as mpi
from . import libutil
import pNbody

#################################
def checkfile(name):
    #################################
    """
    Check if a file exists. An error is generated if the file
    does not exists.

    Parameters
    ----------
    name : the path to a filename



    Examples
    --------
    >>> io.checkfile('an_existing_file')
    >>>

    >>> io.checkfile('a_non_existing_file')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/epfl/revaz/local/lib64/python2.6/site-packages/pNbody/io.py", line 33, in checkfile
        raise IOError(915,'file %s not found ! Pease check the file name.'%(name))
    IOError: [Errno 915] file nofile not found ! Pease check the file name.

    """

    if name is None:
        raise Exception("file name set to None ! Please check the file name.")

    if not os.path.isfile(name):
        raise IOError(
            915,
            'file %s not found ! Pease check the file name.' %
            (name))


#################################
def end_of_file(f, pio='no', MPI=None):
    #################################
    """
    Return True if we have reached the end of the file f, False instead

    Parameters
    ----------
    f : ndarray or matrix object
        an open file
    pio : 'yes' or 'no'
        if the file is read in parallel or not
    MPI : MPI communicator


    Returns
    -------
    status : Bool
             True if the we reached the end of the file
             False if not
    """

    if pio == 'no':

        # here, the master decide for all slaves

        if mpi.ThisTask == 0:

            p1 = f.tell()
            f.seek(0, 2)
            p2 = f.tell()
            f.seek(p1)

            if p1 == p2:
                status = True
            else:
                status = False

        else:
            status = None

        status = mpi.mpi_bcast(status, 0)

        return status

    else:

        # each processus decide for himself

        p1 = f.tell()
        f.seek(0, 2)
        p2 = f.tell()
        f.seek(p1)

        if p1 == p2:
            status = True
        else:
            status = False

        return status

#####################################################


def write_array(file, vec):
    #####################################################
    """
    Write an array to a file, in a very simple ascii format.

    Parameters
    ----------
    file : the path to a file
    vec : an ndarray object


    Examples
    --------
    >>> from numpy import *
    >>> x = array([1,2,3])
    >>> io.write_array('/tmp/array.dat',x)
    """

    f = open(file, 'w')
    for i in range(len(vec)):
        f.write("%f\n" % vec[i])
    f.close()


#####################################################
def read_ascii(
        file,
        columns=None,
        lines=None,
        dtype=np.float32,
        skipheader=False,
        cchar='#'):
    #####################################################
    """
    Read an ascii file.
    The function allows to set the number of columns or line to read.
    If it contains a header, the header is used to label all column. In
    this case, a dictionary is returned.


    Parameters
    ----------
    file : the path to a file or an open file
    columns : list
               the list of the columns to read
               if none, all columns are read
    lines : list
            the list of the lines to read
            if none, all lines are read
    dtype : dtype
            the ndtype of the objects to read
    skipheader : bool
                 if true, do not read the header
                 if there is one
    cchar : char
            lines begining with cchar are skiped
            the first line is considered as the header

    Returns
    -------
    data : Dict or ndarray
           A python dictionary or an ndarray object

    Examples
    --------
    >>> from numpy import *
    >>> x = arange(10)
    >>> y = x*x
    >>> f = open('afile.txt','w')
    >>> f.write("# x y")
    >>> for i in xrange(len(x)):
    ...	f.write('%g %g'%(x[i],y[i]))
    ...
    >>> f.close()
    >>> from pNbody import iofunc as io
    >>> data = io.read_ascii("afile.txt")
    >>> data['x']
    array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9.])
    >>> data['y']
    array([  0.,   1.,   4.,   9.,  16.,  25.,  36.,  49.,  64.,  81.])
    """

    def RemoveComments(l):
        if l[0] == cchar:
            return None
        else:
            return l

    def toNumList(l):
        return list(map(dtype, l))

    if not isinstance(file, io.TextIOWrapper):
        f = open(file, 'r')
    else:
        f = file

    # read header while there is one
    while True:
        fpos = f.tell()
        header = f.readline()
        if header[0] != cchar:
            f.seek(fpos)
            header = None
            break
        else:
            if skipheader:
                header = None
            else:
                # create dict from header
                header = str.strip(header[2:])
                elts = str.split(header)
                break

    """
  # read header if there is one
  header = f.readline()
  if header[0] != cchar:
    f.seek(0)
    header = None
  else:
    if skipheader:
      header = None
    else:
      # create dict from header
      header = str.strip(header[2:])
      elts = str.split(header)
  """

    # now, read the file content
    lines = f.readlines()

    # remove trailing
    lines = list(map(str.strip, lines))

    # remove comments
    #lines = map(RemoveComments, lines)

    # split
    lines = list(map(str.split, lines))

    # convert into float
    lines = list(map(toNumList, lines))

    # convert into array
    lines = np.array(list(map(np.array, lines)))

    # transpose
    lines = np.transpose(lines)

    if header is not None:
        iobs = {}
        i = 0
        for elt in elts:
            iobs[elt] = i
            i = i + 1

        vals = {}
        for key in list(iobs.keys()):
            vals[key] = lines[iobs[key]]

        return vals

    # return
    if columns is None:
        return lines
    else:
        return lines.take(axis=0, indices=columns)


#####################################################
def write_dmp(file, data):
    #####################################################
    """
    Write a dmp (pickle) file. In other word,
    dump the data object.

    Parameters
    ----------
    file : the path to a file
    data : a pickable python object

    Examples
    --------
    >>> x = {'a':1,'b':2}
    >>> io.write_dmp('/tmp/afile.dmp',x)
    """

    f = open(file, 'wb')
    pickle.dump(data, f)
    f.close()


#####################################################
def read_dmp(file):
    #####################################################
    """
    Read a dmp (pickle) file.

    Parameters
    ----------
    file : the path to a file

    Returns
    -------
    data : a python object

    Examples
    --------
    >>> x = {'a':1,'b':2}
    >>> io.write_dmp('/tmp/afile.dmp',x)
    >>> y = io.read_dmp('/tmp/afile.dmp')
    >>> y
    {'a': 1, 'b': 2}
    """

    f = open(file, 'rb')
    data = pickle.load(f)
    f.close()
    return data


#####################################################
def old_WriteFits(data, filename, extraHeader=None):
    #####################################################
    """
    Write a fits file
    """
    # image creation
    fitsimg = pyfits.HDUList()

    # add data
    hdu = pyfits.PrimaryHDU()
    hdu.data = data
    fitsimg.append(hdu)

    # add keys
    keys = []
    if extraHeader is not None:
        # keys.append(('INSTRUME','st4 SBIG ccd camera','Instrument name'))
        # keys.append(('LOCATION',"175 OFXB St-Luc (VS)",'Location'))
        keys = extraHeader

    hdr = fitsimg[0].header
    for key in keys:
        hdr.update(key[0], key[1], comment=key[2])

    fitsimg.writeto(filename)

#####################################################
def WriteFits(data, filename, extraHeader=None):
#####################################################
  """
  Write a fits file
  """

  from astropy.io import fits
  
  hdu = fits.PrimaryHDU(data)
  hdu.writeto(filename)
  
  

#####################################################
def ReadFits(filename):
    #####################################################
    """
    Read a fits file.
    """
    # read image
    fitsimg = pyfits.open(filename)
    data = fitsimg[0].data
    return data


#################################
def computeBlockSize(shape, data_type):
    #################################
    # compute the number of bytes that should be read
    nbytes_to_read = None
    if shape is not None:
        shape_a = np.array(shape)
        nelts_to_read = shape_a[0]
        for n in shape_a[1:]:
            nelts_to_read = nelts_to_read * n
        nbytes_to_read = nelts_to_read * np.dtype(data_type).itemsize
    return nbytes_to_read


#################################
def readblock(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        skip=False,
        htype=np.int32):
    #################################
    """
    data_type = int,float32,float
    or
    data_type = array

    shape	    = tuple
    """

    nbytes_to_read = computeBlockSize(shape, data_type)

    try:
        nb1 = np.frombuffer(f.read(4), htype)
        if sys.byteorder != byteorder:
            nb1.byteswap(True)
        nb1 = nb1[0]

        nbytes = nb1

        # check
        if nbytes_to_read:
            if nbytes_to_read != nbytes:
                print(
                    "inconsistent block header, using nbytes=%d instead" %
                    nbytes_to_read)
                nbytes = nbytes_to_read

    except IndexError:
        raise IOError("ReadBlockError")

    if skip:
        f.seek(nbytes, 1)
        data = None
        shape = None
        print("  skipping %d bytes... " % (nbytes))

    else:

        if isinstance(data_type, tuple):

            data = []
            for tpe in data_type:

                if isinstance(tpe, int):
                    val = f.read(tpe)
                else:
                    bytes = np.dtype(tpe).itemsize
                    val = np.frombuffer(f.read(bytes), tpe)
                    if sys.byteorder != byteorder:
                        val.byteswap(True)

                    val = val[0]

                data.append(val)

        else:
            data = np.frombuffer(f.read(nbytes), data_type)
            if sys.byteorder != byteorder:
                data.byteswap(True)

    nb2 = np.frombuffer(f.read(4), htype)
    if sys.byteorder != byteorder:
        nb2.byteswap(True)
    nb2 = nb2[0]

    if nb1 != nb2:
        raise IOError("ReadBlockError", "nb1=%d nb2=%d" % (nb1, nb2))

    # reshape if needed
    if shape is not None:
        data.shape = shape

    return data


#################################
def ReadBlock(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        pio='no',
        htype=np.int32):
    #################################
    """
    data_type = int,float32,float
    or
    data_type = array

    shape	    = tuple

    pio   : parallel io, 'yes' or 'no'
            if 'yes', each proc read each file
            if 'no',  proc 0 read and send to each other

    """

    if mpi.NTask == 1:
        data = readblock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            htype=htype)
        return data

    if pio == 'yes':
        data = readblock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            htype=htype)
        return data

    else:
        data = mpi.mpi_ReadAndSendBlock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            htype=htype)
        return data


#################################
def ReadArray(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        pio='no',
        nlocal=None,
        htype=np.int32):
    #################################
    """
    data_type = int,float32,float
    or
    data_type = array

    shape	    = tuple

    """

    if mpi.NTask == 1:
        data = readblock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            htype=np.int32)
        return data

    if pio == 'yes':
        data = readblock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            htype=np.int32)
        return data

    else:
        data = mpi.mpi_OldReadAndSendArray(
            f,
            data_type,
            shape=shape,
            byteorder=byteorder,
            nlocal=nlocal,
            htype=np.int32)

    return data

#################################


def ReadDataBlock(
        f,
        data_type,
        shape=None,
        byteorder=sys.byteorder,
        pio='no',
        npart=None,
        skip=False):
    #################################
    """

    Read a block containg data.
    If NTask = 1 or  pio = 'yes', the block is read normally.
    If NTask > 1 and pio = 'no',  the master reads the block and send the data to the slaves.


    In the second case :

    a) the master send N/Ntask element to each task.
    b) if the var npart is present, he send Np/Ntask to each task, for each Np of npart.


    data_type = array

    shape	    = tuple

    """

    if mpi.NTask == 1 or pio == 'yes':
        data = readblock(
            f,
            data_type=data_type,
            shape=shape,
            byteorder=byteorder,
            skip=skip)
        return data

    else:
        data = mpi.mpi_ReadAndSendArray(
            f,
            data_type,
            shape=shape,
            byteorder=byteorder,
            npart=npart,
            skip=skip)

    return data


#################################
def writeblock(f, data, byteorder=sys.byteorder, htype=np.int32):
    #################################
    """
    data = array
    or
    data = ((x,float32),(y,int),(z,float32),(label,40))

    shape	    = tuple
    """

    if isinstance(data, tuple):

        # first, compute nbytes
        nbytes = 0
        for dat in data:
            if isinstance(dat[0], bytes) or isinstance(dat[0], str):
                nbytes = nbytes + dat[1]
            else:
                nbytes = nbytes + np.array([
                    dat[0]], dat[1]).dtype().bytes * np.array([
                        dat[0]], dat[1]).size()

        nbytes = np.array([nbytes], htype)

        # write block
        if sys.byteorder != byteorder:
            nbytes.byteswap(True)

        f.write(nbytes.tostring())
        for dat in data:
            if isinstance(dat[0], bytes) or isinstance(dat[0], str):
                f.write(str.ljust(dat[0], dat[1])[:dat[1]])
            else:
                ar = np.array([dat[0]], dat[1])
                if sys.byteorder != byteorder:
                    ar.byteswap(True)
                f.write(ar.tostring())

        f.write(nbytes.tostring())

    else:
        # write block
        #nbytes = array([data.type().bytes*data.size()],int)
        nbytes = np.array([data.nbytes], htype)

        if sys.byteorder != byteorder:
            nbytes.byteswap(True)
            data.byteswap(True)

        f.write(nbytes.tostring())
        f.write(data.tostring())
        f.write(nbytes.tostring())


#################################
def WriteBlock(f, data, byteorder=sys.byteorder, htype=np.int32):
    #################################
    """
    data = ((x,float32),(y,int),(z,float32),(label,40))

    shape	    = tuple
    """

    if f is not None:

        if isinstance(data, tuple):

            # first, compute nbytes
            nbytes = 0
            for dat in data:
                if isinstance(dat[0], str):
                    nbytes = nbytes + dat[1]
                elif isinstance(dat[0], bytes):
                    nbytes = nbytes + dat[1]
                else:
                    nbytes = nbytes + np.array([dat[0]], dat[1]).nbytes
            nbytes = np.array([nbytes], htype)

            # write block
            if sys.byteorder != byteorder:
                nbytes.byteswap(True)

            f.write(nbytes.tostring())
            for dat in data:
                if isinstance(dat[0], bytes):
                    f.write(bytes.ljust(dat[0], dat[1])[:dat[1]])
                elif isinstance(dat[0], str):
                    tmp = dat[0].encode("utf-8")
                    f.write(bytes.ljust(tmp, dat[1])[:dat[1]])
                else:
                    ar = np.array([dat[0]], dat[1])
                    if sys.byteorder != byteorder:
                        ar.byteswap(True)
                    f.write(ar.tostring())

            f.write(nbytes.tostring())


#################################
def WriteArray(
        f,
        data,
        byteorder=sys.byteorder,
        pio='no',
        npart=None,
        htype=np.int32):
    #################################
    """
    data = array

    shape	    = tuple
    """

    if mpi.NTask == 1 or pio == 'yes':
        writeblock(f, data, byteorder=byteorder, htype=htype)

    else:
        mpi.mpi_GatherAndWriteArray(
            f, data, byteorder=byteorder, npart=npart, htype=htype)


#################################
def WriteDataBlock(f, data, byteorder=sys.byteorder, pio='no', npart=None):
    #################################
    """

    Write a block containg data.
    If NTask = 1 or  pio = 'yes', the block is written normally.
    If NTask > 1 and pio = 'no',  the master get the block from the slaves and write it.

    In the second case :

    a) the master get N/Ntask element from each task.
    b) if the var npart is present, he get Np/Ntask from each task, for each Np of npart.


    data = array

    shape	    = tuple
    """

    if mpi.NTask == 1 or pio == 'yes':
        writeblock(f, data, byteorder=byteorder)

    else:
        mpi.mpi_GatherAndWriteArray(f, data, byteorder=byteorder, npart=npart)


###############################################################
#
# some special function reading gadget related files
#
###############################################################


#################################
def read_cooling(file):
    #################################
    """
    Read cooling file
    """

    f = open(file, 'r')
    f.readline()
    f.readline()
    lines = f.readlines()
    f.close()

    lines = list(map(str.strip, lines))
    elts = list(map(str.split, lines))

    logT = np.array([float(x[0]) for x in elts])
    logL0 = np.array([float(x[1]) for x in elts])
    logL1 = np.array([float(x[2]) for x in elts])
    logL2 = np.array([float(x[3]) for x in elts])
    logL3 = np.array([float(x[4]) for x in elts])
    logL4 = np.array([float(x[5]) for x in elts])
    logL5 = np.array([float(x[6]) for x in elts])
    logL6 = np.array([float(x[7]) for x in elts])

    return logT, logL0, logL1, logL2, logL3, logL4, logL5, logL6


#################################
def read_params(file):
    #################################
    """
    Read params Gadget file and return the content in
    a dictionary
    """

    f = open(file, "rb")
    lines = f.readlines()
    f.close()

    # remove empty lines
    lines = [l for l in lines if l != b'\n']

    # remove trailing
    lines = list(map(bytes.strip, lines))

    # remove comments
    lines = [x for x in lines if len(x.decode("latin-1"))>0 and ( x.decode("latin-1")[0] != '%' or x.decode("latin-1")[0] != '#') ]
    
    # split lines
    elts = list(map(bytes.split, lines))
    

    

    # make dictionary
    params = {}
    for e in elts:
            
        name = e[0].decode("latin-1")
        try:
            params[name] = float(e[1])
        except ValueError:
            params[name] = e[1]

    return params


class RockstarReader:
    def __init__(self, filename):
        self.filename = filename

        d = {}

        with open(filename, "r") as f:
            f = [row for row in f if row[0] != '#' or row[:3] == "#ID"]
            reader = csv.DictReader(f, delimiter=' ')
            for i in reader.fieldnames:
                d[i] = []

            for row in reader:
                for i in reader.fieldnames:
                    d[i].append(row[i])
        for key in d:
            d[key] = np.array(d[key], dtype=np.float32)

        self.data = d

    @property
    def pos(self):
        pos = np.array([
            self.data["X"],
            self.data["Y"],
            self.data["Z"]
        ])
        return pos.transpose()

    @property
    def vel(self):
        vel = np.array([
            self.data["VX"],
            self.data["VY"],
            self.data["VZ"]
        ])
        return vel.transpose()

    @property
    def mvir(self):
        return self.data["Mvir"]

    @property
    def rvir(self):
        return self.data["Rvir"]

    @property
    def num(self):
        return self.data["#ID"]

    @property
    def npart(self):
        return self.data["Np"]

    def __getitem__(self, i):
        output = {}
        for key in self.data:
            output[key] = self.data[key][i]
        return output



###############################################################
#
# some special function/class to read LG pickle files
#
###############################################################


class sdict(dict):
  """
  a slightly extended dictionnary class
  """
  
  def selectc(self,c): 
    """
    return a subset of the dictionnary 
    with only elements where the condition is true 
    """ 
    d = copy.deepcopy(self)
    for key in d.keys(): 
      d[key] = np.compress(c,d[key])
    return d  
    
  def insert(self,entry):
    """
    insert a new entry
    the entry must be a dictionary.
    """
    for key in self.keys():
      if key in entry:
        self[key] = np.concatenate((self[key],np.array([entry[key]])))
      else:
        self[key] = np.concatenate((self[key],np.array([None])))
  
    
    

def readLGData(file):
  
  f = open(file,"rb")
  data = pickle.load(f,encoding='latin1')
  f.close()
      
  odata = sdict()  

  names = np.array([])
  for name in data.keys():
    names = np.append(names,name)
    
  odata["name"] = names
    
  attrs =  data[name].keys()

  # loop over 
  for attr_name in attrs:
  
    # create a variable with the name attr
    vect = np.array([],float)
   
    # loop over all galaxies
    for name in names:
       vect = np.append( vect, data[name][attr_name] )
           
    odata[attr_name] = vect
       
  return odata     
     

###############################################################
#
# function to read yaml files
#
###############################################################

def ReadYaml(file_name,parameter_name=None,encoding="latin-1"):
  """
  read a yaml file and return a dictionary
  """

  with open(file_name, mode="rt", encoding=encoding) as file_name:
    data = yaml.safe_load(file_name)

  if parameter_name is not None:
    if parameter_name in data:
      return data[parameter_name]
    else:
      raise KeyError      

  else:
    return data


###############################################################
#
# Single Stellar Population Tables
#
###############################################################


class SSPGrid():

  def __init__(self, filename):
    self.filename = filename
  
  def write(self,Ages,MH,magnitudes=None,luminosities=None,bolometric_luminosities=None,minimfin=None,SunAbsMag=None,cmdline=""):
    
    import h5py
    with h5py.File(self.filename, 'w') as f:
      
      # Header
      f.create_group("Header")
      dset = f["Header"]
      
      # some attributes
      dset.attrs["version"]  = pNbody.__version__
      dset.attrs["author"]   = libutil.get_UserName()
      dset.attrs["date"]     = libutil.get_Date()
      dset.attrs["cmdline"]  = libutil.get_CommandLine()
      dset.attrs['git_tag']  = libutil.get_GitTag()
      
      # sun absolute magnitude in the given filter
      if SunAbsMag is not None:
        dset.attrs['SunAbsMag']     = SunAbsMag
      
      
      # Data
      f.create_group("Data")
      dset = f["Data"]    
      
      data_set = dset.create_dataset('Ages', data=Ages)
      data_set.attrs['units'] = "[Myr]"

      data_set = dset.create_dataset('MH', data=MH)
      data_set.attrs['units'] = "log10([M/H)"
      
      if magnitudes is not None:
        data_set = dset.create_dataset('Magnitudes', data=magnitudes)
        data_set.attrs['units'] = "[magnitudes/IMF_initial_mass]"

      if luminosities is not None:
        data_set = dset.create_dataset('Luminosities', data=luminosities)
        data_set.attrs['units'] = "[log10(Lsol)/IMF_initial_mass]"
        
      if bolometric_luminosities is not None:
        data_set = dset.create_dataset('Bolometric Luminosities', data=bolometric_luminosities)
        data_set.attrs['units'] = "[log10(Lsol)/IMF_initial_mass]"        
        
      if minimfin is not None:
        data_set = dset.create_dataset('MiniMfin', data=minimfin)
        data_set.attrs['units'] = "[-]"
        
                
        
      
  def info(self):
    
    import h5py
    with h5py.File(self.filename, 'r') as f:
      
      content = self.read()
      
      # Header
      hattrs = content["Header"]
      print("version     : %s"%str(hattrs["version"]))
      print("author      : %s"%str(hattrs["author"]))
      print("date        : %s"%str(hattrs["date"]))
      print("cmdline     : %s"%str(hattrs["cmdline"]))
      
      # Data
      dset = content["Data"]
      print()
      print("        Ages: %s"%str(dset["Ages"].shape))
      print("            : %s"%str(dset["Ages_units"]))
      print("         max: %s"%str(dset["Ages"].max()))
      print("         min: %s"%str(dset["Ages"].min())) 
      
      print()
      print("          MH: %s"%str(dset["MH"].shape))
      print("            : %s"%str(dset["MH_units"]))
      print("         max: %s"%str(dset["MH"].max()))
      print("         min: %s"%str(dset["MH"].min())) 
      
      if "Magnitudes" in dset:
        print()
        print("  Magnitudes: %s"%str(dset["Magnitudes"].shape))
        print("         max: %s"%str(dset["Magnitudes"].max()))
        print("         min: %s"%str(dset["Magnitudes"].min()))  
        print("        mean: %s"%str(dset["Magnitudes"].mean()))   
        print("         std: %s"%str(dset["Magnitudes"].std())) 
        print("            : %s"%str(dset["Magnitudes_units"]))


      if "Bolometric Luminosities" in dset:
        print()
        print("Bolo Luminosities: %s"%str(dset["Bolometric Luminosities"].shape))
        print("              max: %s"%str(dset["Bolometric Luminosities"].max()))
        print("              min: %s"%str(dset["Bolometric Luminosities"].min()))
        print("             mean: %s"%str(dset["Bolometric Luminosities"].mean()))   
        print("              std: %s"%str(dset["Bolometric Luminosities"].std()))          
        print("                 : %s"%str(dset["Bolometric Luminosities_units"]))

      if "Luminosities" in dset:
        print()
        print("Luminosities: %s"%str(dset["Luminosities"].shape))
        print("         max: %s"%str(dset["Luminosities"].max()))
        print("         min: %s"%str(dset["Luminosities"].min()))
        print("        mean: %s"%str(dset["Luminosities"].mean()))   
        print("         std: %s"%str(dset["Luminosities"].std()))          
        print("            : %s"%str(dset["Luminosities_units"]))

        
      if "MiniMfin" in dset:
        print()
        print("   MiniMfin : %s"%str(dset["MiniMfin"].shape))
        print("         max: %s"%str(dset["MiniMfin"].max()))
        print("         min: %s"%str(dset["MiniMfin"].min()))
        print("        mean: %s"%str(dset["MiniMfin"].mean()))   
        print("         std: %s"%str(dset["MiniMfin"].std()))     
        print("            : %s"%str(dset["MiniMfin_units"]))
                      
      
      
  def read(self):
    
    import h5py
    with h5py.File(self.filename, 'r') as f:
      
      content = {}
      
      hattrs = f["Header"].attrs
      content["Header"] = {}
      
      content["Header"]["version"] = hattrs["version"]
      content["Header"]["author"]  = hattrs["author"]
      content["Header"]["date"]    = hattrs["date"]
      content["Header"]["cmdline"] = hattrs["cmdline"]
      
      if "SunAbsMag" in hattrs:
        content["Header"]["SunAbsMag"] = hattrs["SunAbsMag"]
      

      # data
      dset = f["Data"]
      content["Data"] = {}
        
      content["Data"]["Ages"]       = dset["Ages"][:]
      content["Data"]["Ages_units"] = dset["Ages"].attrs["units"]
      
      content["Data"]["MH"]         = dset["MH"][:]  
      content["Data"]["MH_units"]   = dset["MH"].attrs["units"]
      
      if "Magnitudes" in  dset: 
        content["Data"]["Magnitudes"] = dset["Magnitudes"][:]
        content["Data"]["Magnitudes_units"] = dset["Magnitudes"].attrs["units"]

      if "Luminosities" in  dset: 
        content["Data"]["Luminosities"] = dset["Luminosities"][:]
        content["Data"]["Luminosities_units"] = dset["Luminosities"].attrs["units"]

      if "Bolometric Luminosities" in  dset: 
        content["Data"]["Bolometric Luminosities"] = dset["Bolometric Luminosities"][:]
        content["Data"]["Bolometric Luminosities_units"] = dset["Bolometric Luminosities"].attrs["units"]


      if "MiniMfin" in  dset: 
        content["Data"]["MiniMfin"] = dset["MiniMfin"][:]
        content["Data"]["MiniMfin_units"] = dset["MiniMfin"].attrs["units"]
        
                
    
    return content  
    
    
        
  
  
  
  
  
  
    







