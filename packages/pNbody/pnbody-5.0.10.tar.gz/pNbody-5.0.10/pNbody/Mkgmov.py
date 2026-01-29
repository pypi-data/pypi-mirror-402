#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      Mkgmov.py
#  brief:     Mkgmov.py
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

import Mtools
import Mtools as mt

import os
import glob
from pNbody import *
from pNbody import iofunc
from pNbody.param import Params
import copy
import types
import numpy as np

import gzip


##########################################################################
#
#  Some info on the structure :
#
#  1) nb   : the full nbody object (main loop)
#
#  2) nbf  : normally set the display parameters, position of the observer
#            but could be used to set the component
#
#  3) nbfc : normally set the component to display and/or the value to dispplay
#
#      component['id'][0] == '@'
#        this is used to open simple nbody object (to draw a box, for example)
#      component['id'][0] == '#'
#        no selection
#      component['id']    == 'gas'
#        selection gas
#
#
#
#
#  a script may be called at level 2)
#
#    frame['ext_cmd'] = []
#    frame['ext_cmd'].append("""from plot_P import MakePlot""")
#    frame['ext_cmd'].append("""MakePlot([nbf],output)""")
#
#    it must save an output output, the latter is opened as an img
#    and appened to imgs
#
#
#  a script may be called at level 3)
#
#    1)
#    component['ext_cmd'] = []
#    component['ext_cmd'].append("""from plot_P import MakePlot""")
#    component['ext_cmd'].append("""MakePlot([nbfc],output)""")
#
#    it must save an output output, the latter is opened as an img
#    and appened to imgs
#
#
#    2) using
#    component['to_img']='script_name'
#
#
##########################################################################


#######################################################################
# some useful functions
#######################################################################


def ReadNbodyParameters(paramname):
    """
    read param from a parameter Nbody file
    """

    gparams = Params(paramname, None)

    param = {}
    # create new params
    for p in gparams.params:
        param[p[0]] = p[3]

    return param


def gzip_compress(file):

    f = open(file, 'rb')
    content = f.read()
    f.close()

    f = gzip.open(file + '.gz', 'wb')
    f.write(content)
    f.close()


#######################################################################
#
#	C L A S S   D E F I N I T I O N
#
#######################################################################


class Movie():

    def __init__(
            self,
            parameterfile='filmparam.py',
            format=None,
            imdir=None,
            timesteps=None,
            pio=False,
            compress=True,
            ifile=0):

        self.DEFAULT_TIMESTEPS = None
        self.DEFAULT_FORMAT = "fits"
        self.DEFAULT_IMDIR = "fits"
        self.DEFAULT_PIO = False
        self.DEFAULT_COMPRESS = True

        self.DEFAULT_SCALE = "log"
        self.DEFAULT_CD = 0.
        self.DEFAULT_MN = 0.
        self.DEFAULT_MX = 0.
        self.DEFAULT_PALETTE = "light"

        self.DEFAULT_SKIPPED_IO_BLOCKS = []

        self.parameterfile = parameterfile

        # read the parameter file
        self.read_parameterfile()

        # use options
        if format is not None:
            self.film['format'] = format
        if imdir is not None:
            self.film['imdir'] = imdir
        if timesteps is not None:
            self.film['timesteps'] = timesteps
        if pio is not None:
            self.film['pio'] = pio
        if compress is not None:
            self.film['compress'] = compress

        self.imdir = self.film['imdir']
        self.pio = self.film['pio']
        self.compress = self.film['compress']

        # deal with timesteps
        self.set_timesteps()

        self.ifile = ifile - 1
        self.file_offset = 0

        # whith gmkgmov, the init is only runned by the master, this line is
        # not needed...
        if mpi.mpi_IsMaster():

            if self.pio:
                self.pio = "yes"
            else:
                self.pio = "no"

            if self.parameterfile is None:
                print("you must specify a parameter file")
                sys.exit()

            if not os.path.exists(self.parameterfile):
                print(("file %s does not exists" % self.parameterfile))
                sys.exit()

            if not os.path.exists(self.imdir):
                os.mkdir(self.imdir)
            else:
                print(("directory %s exists !!!" % self.imdir))

                files = os.listdir(self.imdir)
                print(("the directory %s contains %d files" % (self.imdir,len(files))))

                # png files
                png_files = glob.glob(os.path.join(self.imdir, "*.png"))
                n_png_files = len(png_files)

                print(("the directory %s contains %d png files" % (self.imdir, n_png_files)))

                # fits files
                #fits_files = glob.glob(os.path.join(self.imdir, "*.fits"))
                fits_files = glob.glob(os.path.join(self.imdir, "*.fits.gz"))
                n_fits_files = len(fits_files)

                print(("the directory %s contains %d fits files" % (self.imdir, n_fits_files)))
                
                
                n_images_per_file = len(self.film['frames'][0]['components'])
                print()
                print(n_images_per_file)
                print()

                if n_png_files > 0:
                    self.file_offset = n_png_files/n_images_per_file  
                    
                if n_fits_files > 0:
                    self.file_offset = n_fits_files/n_images_per_file    
                    


    def info(self):
        print("INFO INFO INFO")
        # print self.film
        print((self.parameterfile))
        print((self.getftype()))
        print("INFO INFO INFO")

    def read_parameterfile(self):

        if not os.path.isfile(self.parameterfile):
            raise IOError(
                915, 'file %s not found ! Pease check the file name.' %
                (self.parameterfile))

        # import the parameter file as a module

        module_name = os.path.basename(os.path.splitext(self.parameterfile)[0])
        module_dir = os.path.dirname(self.parameterfile)

        if sys.path.count(module_dir) == 0:
            sys.path.append(module_dir)
        
        filmparam = __import__(module_name)

        self.film = filmparam.film

        # set some defaults
        if 'timesteps' not in self.film:
            self.film['timesteps'] = self.DEFAULT_TIMESTEPS
        if 'imdir' not in self.film:
            self.film['imdir'] = self.DEFAULT_IMDIR
        if 'format' not in self.film:
            self.film['format'] = self.DEFAULT_FORMAT
        if 'pio' not in self.film:
            self.film['pio'] = self.DEFAULT_PIO
        if 'compress' not in self.film:
            self.film['compress'] = self.DEFAULT_COMPRESS
        if 'skipped_io_blocks' not in self.film:
            self.film['skipped_io_blocks'] = self.DEFAULT_SKIPPED_IO_BLOCKS

        self.setftype(self.film['ftype'])

        # post process
        for i, frame in enumerate(self.film['frames']):
            frame['id'] = i

        # check
        # for frame in self.film['frames']:
        #  print frame['id']
        #  for component in frame['components']:
        #	print "  ",component['id']

    ##################################
    # time steps stuffs
    ##################################

    def set_timesteps(self):
        """
        define self.times (which is a list) based
        on the value contained in self.film['timesteps']
        """

        # self.times
        if self.film['timesteps'] == 'every':
            self.times = "every"

        elif isinstance(self.film['timesteps'], bytes):
            fname = self.film['timesteps']
            if not os.path.isfile(fname):
                raise IOError(
                    916,
                    'file %s not found ! Pease check the file name.' %
                    (fname))
            times = iofunc.read_ascii(fname, [0])[0]
            times = np.take(
                times,
                len(times) -
                1 -
                np.arange(
                    len(times)))  # invert order
            times = times.tolist()
            self.times = times

        elif isinstance(self.film['timesteps'], list):
            self.times = self.film['timesteps']

        elif isinstance(self.film['timesteps'], tuple):
            t0 = self.film['timesteps'][0]
            t1 = self.film['timesteps'][1]
            dt = self.film['timesteps'][2]
            times = np.arange(t0, t1, dt)
            times = np.take(
                times,
                len(times) -
                1 -
                np.arange(
                    len(times)))  # invert order
            times = times.tolist()
            self.times = times

        else:
            self.times = []

    def set_next_time(self):
        if self.times != "every":
            if len(self.times) > 0:
                self.times.pop()

    def get_next_time(self):
        if self.times == "every":
            return 0.0

        if len(self.times) == 0:
            return None
        else:
            return self.times[-1]

    def getftype(self):
        return self.ftype

    def setftype(self, ftype):
        self.ftype = ftype

    def get_skipped_io_blocks(self):
        return self.film["skipped_io_blocks"]

    def ApplyFilmParam(self, nb, film):
        
        # set time reference for this file
        exec("nb.tnow = %s" % film['time'])
        # exec1
        if 'exec' in film:
            if film['exec'] is not None:
                exec(film['exec'])

        # macro
        if 'macro' in film:
            if film['macro'] is not None:
                exec(
                    compile(
                        open(
                            film['macro']).read(),
                        film['macro'],
                        'exec'))

        return nb

    def ApplyFrameParam(self, nb, frame):

        global nbf
        
        nbf = nb

        # exec
        if 'exec' in frame:
            if frame['exec'] is not None:
                exec(frame['exec'])

        # macro
        if 'macro' in frame:
            if frame['macro'] is not None:
                exec(
                    compile(
                        open(
                            frame['macro']).read(),
                        frame['macro'],
                        'exec'))

        return nbf

    def ApplyComponentParam(self, nbf, component):

        global nbfc
        
        if component['id'][0] == '@':
            # here, all tasks must have an object containing all particles
            # ok, but not in the right order !!!
            nbfc = Nbody(componentid, self.getftype())
            nbfc = sorted(nbfc.SendAllToAll())
            nbfc.componentid = component['id']  # [1:]
        elif component['id'][0] == '#':
            nbfc = nbf
            nbfc.componentid = component['id']  # [1:]
        else:
            nbfc = nbf.select(component['id'])
            nbfc.componentid = component['id']

        # exec
        if 'exec' in component:
            if component['exec'] is not None:
                exec(component['exec'])

        # macro
        if 'macro' in component:
            if component['macro'] is not None:
                exec(
                    compile(
                        open(
                            component['macro']).read(),
                        component['macro'],
                        'exec'))

        # print "------------------------"
        # print min(nbfc.u),max(nbfc.u)
        # print min(nbfc.rho),max(nbfc.rho)
        # print min(nbfc.tpe),max(nbfc.tpe)
        # print "temperature",min(nbfc.T()),max(nbfc.T())
        # print nbfc.nbody
        # print min(nbfc.rsp),max(nbfc.rsp)
        # print "------------------------"

        return nbfc

    def dump(self, dict):

        # exctract dict
        atime = dict['atime']
        pos = dict['pos']

        # create nbody object
        nb = Nbody(pos=pos, ftype='gadget')
        nb.atime = atime

        # add other arrays
        if 'vel' in dict:
            nb.vel = dict['vel']

        if 'num' in dict:
            nb.num = dict['num']

        if 'mass' in dict:
            nb.mass = dict['mass']

        if 'tpe' in dict:
            nb.tpe = dict['tpe']

        if 'u' in dict:
            nb.u = dict['u']
        if 'rho' in dict:
            nb.rho = dict['rho']
        if 'rsp' in dict:
            nb.rsp = dict['rsp']

        if 'metals' in dict:
            nb.metals = dict['metals']

            #!!!
            nb.flag_chimie_extraheader = 1
            nb.ChimieNelements = 5
            nb.flag_metals = 5
            nb.ChimieSolarMassAbundances = {}
            nb.ChimieSolarMassAbundances['Fe'] = 0.00176604

        nb.init()

        # print "################################"
        # print "writing qq.dat"
        # print "################################"
        # nb.rename('qq.dat')
        # nb.write()

        self.dumpimage(nb=nb)

    def dumpimage(self, nb=None, file=None):

        # increment counter
        self.ifile += 1

        # skip file if needed
        if self.ifile < self.file_offset:
            if mpi.mpi_IsMaster():
                print(("skipping file %04d" % self.ifile))

            return

        # for each frame one can create an img
        imgs = []

        if file is not None:
            # print "(task=%04d) reading
            # "%(mpi.ThisTask),file,self.getftype(),self.pio

            if mpi.mpi_IsMaster():
                print()
                print("#############################################################")
                print(("reading...", file))
                print("#############################################################")

            nb = Nbody(file, ftype=self.getftype(), pio=self.pio,
                       skipped_io_blocks=self.get_skipped_io_blocks())
        else:
            if nb is None:
                raise Exception(
                    "you must specify at least a file or give an nbody object")

        film = self.film

        nb = self.ApplyFilmParam(nb, film)

        for frame in film['frames']:
            nbf = self.ApplyFrameParam(nb, frame)

            if 'ext_cmd' in frame:
                if len(frame['ext_cmd']) > 0:
                    #################################################
                    # 1) use an outer script to create an img		(this is a bit redundant with 2.2, see below )
                    #################################################
                    output = "/tmp/%015d.png" % (int(np.random.random() * 1e17))

                    for cmd in frame['ext_cmd']:
                        exec(cmd)

                    if mpi.mpi_IsMaster():
                        img = Image.open(output)
                        imgs.append(img)

                        if os.path.exists(output):
                            os.remove(output)

                continue

            # composition parameters

            if 'cargs' in frame:
                if len(frame['cargs']) != 0:
                    frame['compose'] = True
                    datas = []
                else:
                    frame['compose'] = False
            else:
                frame['cargs'] = []
                frame['compose'] = False

            for component in frame['components']:
                if mpi.mpi_IsMaster():
                    print("------------------------")
                    print(("component", component['id']))
                    print("------------------------")

                nbfc = self.ApplyComponentParam(nbf, component)

                # find the observer position
                # 1) from params
                # 2) from pfile
                # 3) from tdir
                # and transform into parameter

                if frame['tdir'] is not None:

                    tfiles = sorted(
                        glob.glob(
                            os.path.join(
                                frame['tdir'],
                                "*")))

                    bname = os.path.basename(file)

                    tfiles_for_this_file = []
                    for j in range(len(tfiles)):
                        tfile = "%s.%05d" % (bname, j)
                        # tfile = "%s.0.%05d"%(bname,j) # old or new version ?
                        tmp_tfile = os.path.join(frame['tdir'], tfile)

                        if os.path.exists(tmp_tfile):
                            tfiles_for_this_file.append(tmp_tfile)

                elif frame['pfile'] is not None:

                    if not os.path.isfile(frame['pfile']):
                        print((
                            "parameter file %s does not exists(1)..." %
                            (frame['pfile'])))

                    # read from pfile defined in frame
                    param = ReadNbodyParameters(frame['pfile'])
                    tfiles_for_this_file = [None]

                else:

                    # take frame as parameter
                    param = copy.copy(frame)
                    tfiles_for_this_file = [None]

                # loop over different oberver positions for this file
                for iobs, tfile in enumerate(tfiles_for_this_file):

                    if tfile is not None:
                        if mpi.mpi_IsMaster():
                            print(("  using tfile : %s" % (tfile)))
                        param = ReadNbodyParameters(tfile)

                    # add parameters defined by user in the parameter file
                    for key in list(component.keys()):
                        param[key] = component[key]

                    # set image shape using frame
                    param['shape'] = (frame['width'], frame['height'])

                    # compute map
                    mat = nbfc.CombiMap(param)

                    if mpi.mpi_IsMaster():

                        if frame['compose']:
                            datas.append(mat)

                        if 'ext_cmd' in component:
                            #################################################
                            # 1) use an outer script to create an img
                            #################################################
                            if len(component['ext_cmd']) > 0:

                                output = "/tmp/%015d.png" % (
                                    int(np.random.random() * 1e17))

                                for cmd in component['ext_cmd']:
                                    exec(cmd)

                                if mpi.mpi_IsMaster():
                                    img = Image.open(output)
                                    imgs.append(img)

                                    if os.path.exists(output):
                                        os.remove(output)

                        elif self.film["format"] == "fits":
                            #################################
                            # 1) save fits file
                            #################################
                            output = '%04d_%04d-%s-%06d.fits' % (
                                self.ifile, frame['id'], component['id'], iobs)
                            output = os.path.join(self.imdir, output)
                            print((nb.atime, output))

                            if os.path.exists(output):
                                os.remove(output)

                            header = [('TIME', nb.tnow, 'snapshot time')]
                            iofunc.WriteFits(
                                np.transpose(mat), output, extraHeader=header)

                            # compress
                            if self.compress:
                                gzip_compress(output)
                                os.remove(output)

                        elif self.film["format"] == "png":
                            #################################
                            # 2) output png file or ...
                            #################################

                            output = '%04d_%04d-%s-%06d.png' % (
                                self.ifile, frame['id'], nbfc.componentid, iobs)

                            output = os.path.join(self.imdir, output)
                            print((nb.atime, output))

                            # here, we should use component['scale'] ... not
                            # frame['scale'], no ?

                            if 'scale' not in frame:
                                frame['scale'] = self.DEFAULT_SCALE
                            if 'cd' not in frame:
                                frame['cd'] = self.DEFAULT_CD
                            if 'mn' not in frame:
                                frame['mn'] = self.DEFAULT_MN
                            if 'mx' not in frame:
                                frame['mx'] = self.DEFAULT_MX

                            if 'palette' not in frame:
                                frame['palette'] = self.DEFAULT_PALETTE

                            matint, mn_opt, mx_opt, cd_opt = set_ranges(
                                mat, scale=frame['scale'], cd=frame['cd'], mn=frame['mn'], mx=frame['mx'])
                            frame['mn'] = mn_opt
                            frame['mx'] = mx_opt
                            frame['cd'] = cd_opt
                            img = get_image(
                                matint, palette_name=frame['palette'])
                            img.save(output)

                            print((frame['mn'], frame['mx'], frame['cd']))

                        # need to create an img
                        if 'to_img' in component:

                            if component['to_img']:
                                ##########################################
                                # 2.1) create an img and apply commmands
                                ##########################################

                                # get params
                                if 'scale' not in component:
                                    component['scale'] = self.DEFAULT_SCALE
                                if 'cd' not in component:
                                    component['cd'] = self.DEFAULT_CD
                                if 'mn' not in component:
                                    component['mn'] = self.DEFAULT_MN
                                if 'mx' not in component:
                                    component['mx'] = self.DEFAULT_MX
                                if 'palette' not in component:
                                    component['palette'] = self.DEFAULT_PALETTE

                                matint, mn_opt, mx_opt, cd_opt = set_ranges(
                                    mat, scale=component['scale'], cd=component['cd'], mn=component['mn'], mx=component['mx'])
                                img = get_image(
                                    matint, palette_name=component['palette'])

                                print((mn_opt, mx_opt, cd_opt))

                                # here we can add img commands....
                                if 'img_cmd' in component:
                                    if len(component['img_cmd']) > 0:

                                        for cmd in component['img_cmd']:
                                            exec(cmd)

                                # append img to list
                                img.atime = nb.atime
                                imgs.append(img)

                            elif isinstance(component['to_img'], bytes):
                                ##########################################
                                # 2.2) use an outer script to create an img from mat
                                ##########################################

                                output = "/tmp/%015d.png" % (
                                    int(np.random.random() * 1e17))

                                # get params
                                if 'scale' not in component:
                                    component['scale'] = self.DEFAULT_SCALE
                                if 'cd' not in component:
                                    component['cd'] = self.DEFAULT_CD
                                if 'mn' not in component:
                                    component['mn'] = self.DEFAULT_MN
                                if 'mx' not in component:
                                    component['mx'] = self.DEFAULT_MX
                                if 'palette' not in component:
                                    component['palette'] = self.DEFAULT_PALETTE

                                component['atime'] = nbfc.atime

                                mk = __import__(component['to_img'])
                                mk.MkImage(mat, output, component)

                                img = Image.open(output)
                                imgs.append(img)

                                os.remove(output)

            del nbf

            #######################
            # compose components
            #######################

            if frame['compose']:

                if mpi.mpi_IsMaster():

                    img, cargs = Mtools.fits_compose_colors_img(
                        datas, frame['cargs'])

                    # save
                    #output = '%04d_%04d.png'%(self.ifile,frame['id'])
                    #output = os.path.join(self.imdir,output)
                    # img.save(output)

                    # append img to list
                    img.atime = nb.atime
                    imgs.append(img)

        del nb

        #######################
        # compose frames
        #######################

        if mpi.mpi_IsMaster():
            if 'img_cmd' in film:
                if len(film['img_cmd']) > 0:

                    for cmd in film['img_cmd']:
                        exec(cmd)

                    output = '%04d.png' % (self.ifile)
                    output = os.path.join(self.imdir, output)
                    img.save(output)

                    img.i = 0
