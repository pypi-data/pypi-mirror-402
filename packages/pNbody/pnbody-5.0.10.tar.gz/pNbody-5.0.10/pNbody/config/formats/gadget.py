###########################################################################################
#  package:   pNbody
#  file:      gadget.py
#  brief:     Gadget format (binary)
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################

##########################################################################
#
# GADGET CLASS
#
##########################################################################

import sys
import os
import string
import types
from pNbody import mpiwrapper as mpi
from pNbody import errorfuncs as error
from pNbody import iofunc as io 
from pNbody import libutil
from pNbody import parameters
from pNbody import units, ctes, cosmo, thermodyn

import numpy as np
# define some units

try:				# all this is usefull to read files
    from mpi4py import MPI
except BaseException:
    MPI = None


class Nbody_gadget:

    def _init_spec(self):
        # define some units
        Unit_atom = ctes.PROTONMASS.into(units.cgs) * units.Unit_g
        Unit_atom.set_symbol('atom')
        out_units = units.UnitSystem(
            'local', [units.Unit_cm, Unit_atom, units.Unit_s, units.Unit_K])
        self.DensityUnit_in_AtomPerCC = out_units.UnitDensity

    def get_excluded_extension(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        return []
        
    def getParticleMatchingDict(self):
        """
        Return a list of file to avoid when extending the default class.
        """
        
        index = {
            'gas':    0,
            'halo':   2,
            'disk':   2,
            'bulge':  3,
            'stars':  1,
            'bndry':  5,
            'stars1': 1,
            'halo1':  2}
        
        return index      
        

    def check_spec_ftype(self):
        # read the first 4 bites and check that they are equal to 256
        for name in self.p_name:
            mpi_test = mpi.mpi_NTask() > 1 and self.pio == "no"
            if mpi.mpi_IsMaster() or self.pio == "yes":
                f = open(name, 'rb')

                try:
                    htype = np.int32
                    nb1 = np.frombuffer(f.read(4), htype)
                    if sys.byteorder != sys.byteorder:
                        nb1.byteswap(True)
                    nb1 = nb1[0]
                except BaseException:
                    if mpi_test:
                        mpi.mpi_bcast(False)
                    f.close()
                    raise error.FormatError("gadget")

                if nb1 != 256:
                    if mpi_test:
                        mpi.mpi_bcast(False)
                    f.close()
                    raise error.FormatError("gadget")
                elif mpi_test:
                    mpi.mpi_bcast(True)
                f.close()
            else:
                test = mpi.mpi_bcast(None)
                if test is False:
                    raise error.FormatError("gadget")

    def get_read_fcts(self):
        return [self.read_particles]

    def get_write_fcts(self):
        return [self.write_particles]

    def get_mxntpe(self):
        return 6

    def get_default_spec_vars(self):
        '''
        return specific variables default values for the class
        '''
        return {'massarr': np.array([0, 0, self.nbody, 0, 0, 0]),
                'atime': 0.,
                'redshift': 0.,
                'flag_sfr': 0,
                'flag_feedback': 0,
                'nall': np.array([0, 0, self.nbody, 0, 0, 0]),
                'flag_cooling': 0,
                'num_files': 1,
                'boxsize': 0.,
                'omega0': 0.,
                'omegalambda': 0.,
                'hubbleparam': 0.,
                'flag_age': 0.,
                'hubbleparam': 0.,
                'flag_metals': 0.,
                'nallhw': np.array([0, 0, 0, 0, 0, 0]),
                'flag_entr_ic': 0,
                'flag_chimie_extraheader': 0,
                'flag_thermaltime': 0,
                'critical_energy_spec': 0.,
                'empty': '',
                'comovingintegration': None,
                'hubblefactorcorrection': None,
                'comovingtoproperconversion': False,
                'utype':"gear",
                }

    def initComovingIntegration(self):
        """
        set true if the file has been runned using
        the comoving integration scheme
        
        this function is specific to the gadget format
        """

        # do nothing, if the value is already set
        if self.comovingintegration is not None:
            return

        flag = True

        # this is not very good, however, there is not other choice...
        if self.omega0 == 0 and self.omegalambda == 0:
            flag = False

        self.comovingintegration = flag
        
    def initHubbleFactorCorrection(self):
        """
        set true if physical quantities must be corrected from the Hubble parameter
        
        this function is specific to the gadget format
        """

        if self.comovingintegration==False or self.hubbleparam==1:
          self.hubblefactorcorrection = False
        else:  
          self.hubblefactorcorrection = True  


    def get_massarr_and_nzero(self):
        """
        return massarr and nzero

        !!! when used in //, if only a proc has a star particle,
        !!! nzero is set to 1 for all cpu, while massarr has a length of zero !!!
        """

        if self.has_var('massarr') and self.has_var('nzero'):
            if self.massarr is not None and self.nzero is not None:
                self.warning("warning : get_massarr_and_nzero : here we use massarr and nzero %s %s"%(self.massarr,self.nzero))
                return self.massarr, self.nzero

        massarr = np.zeros(len(self.npart), float)
        nzero = 0

        # for each particle type, see if masses are equal
        for i in range(len(self.npart)):
            first_elt = sum((np.arange(len(self.npart)) < i) * self.npart)
            last_elt = first_elt + self.npart[i]

            if first_elt != last_elt:
                c = (self.mass[first_elt] ==
                     self.mass[first_elt:last_elt]).astype(int)
                if sum(c) == len(c):
                    massarr[i] = self.mass[first_elt]
                else:
                    nzero = nzero + len(c)

        return massarr.tolist(), nzero


    def read_particles(self, f):
        '''
        read gadget file
        '''
        ##########################################
        # read the header and send it to each proc
        ##########################################
        tpl = (
            24,
            48,
            float,
            float,
            np.int32,
            np.int32,
            24,
            np.int32,
            np.int32,
            float,
            float,
            float,
            float,
            np.int32,
            np.int32,
            24,
            np.int32,
            np.int32,
            np.int32,
            float,
            44)
        header = io.ReadBlock(f, tpl, byteorder=self.byteorder, pio=self.pio)
        npart, massarr, atime, redshift, flag_sfr, flag_feedback, nall, flag_cooling, num_files, boxsize, omega0, omegalambda, hubbleparam, flag_age, flag_metals, nallhw, flag_entr_ic, flag_chimie_extraheader, flag_thermaltime, critical_energy_spec, empty = header

        if np.fabs(
                flag_chimie_extraheader) > 1:		# if the header is empty, it may be indetermined
            flag_chimie_extraheader = 0

        npart = np.frombuffer(npart, np.int32)
        massarr = np.frombuffer(massarr, float)
        nall = np.frombuffer(nall, np.int32)
        nallhw = np.frombuffer(nallhw, np.int32)

        if sys.byteorder != self.byteorder:
            npart.byteswap(True)
            massarr.byteswap(True)
            nall.byteswap(True)
            nallhw.byteswap(True)

        if flag_metals:		# gas metal properties
            NELEMENTS = flag_metals
            self.NELEMENTS = NELEMENTS
        else:
            NELEMENTS = 0
            self.NELEMENTS = NELEMENTS

        if flag_thermaltime != 1:
            flag_thermaltime = 0

        ##########################################
        # computes nzero
        ##########################################
        # count number of particles that have non constant masses and then
        # have masses storded further

        if self.pio == 'no':

            npart_tot = npart
            npart_all = libutil.get_npart_all(npart, mpi.mpi_NTask())
            npart = npart_all[mpi.mpi_ThisTask()]			# local
            npart_read = npart_tot
            nbody_read = sum(npart_read)

            npart_m_read = npart_tot * (massarr == 0)

            ngas = npart[0]
            ngas_read = npart_tot[0]
            nstars = npart[1]
            nstars_read = npart_tot[1]

            # compute nzero
            nzero = 0
            mass = np.array([])
            for i in range(len(npart_tot)):
                if massarr[i] == 0:
                    nzero = nzero + npart_tot[i]
                else:
                    mass = np.concatenate(
                        (mass, np.ones(npart[i]) * massarr[i]))

        else:

            npart_tot = mpi.mpi_allreduce(npart)
            npart_all = None						# each proc read for himself
            npart = npart						# local
            npart_read = None						# each proc read for himself
            nbody_read = sum(npart)

            npart_m_read = None						# each proc read for himself

            ngas = npart[0]
            ngas_read = ngas
            nstars = npart[1]
            nstars_read = nstars

            # compute nzero
            nzero = 0
            mass = np.array([])
            for i in range(len(npart)):
                if massarr[i] == 0:
                    nzero = nzero + npart[i]
                else:
                    mass = np.concatenate(
                        (mass, np.ones(npart[i]) * massarr[i]))

        nbody = sum(npart)
        nbody_tot = sum(npart_tot)

        if npart_m_read is not None:
            if sum(npart_m_read) != nzero:
                raise Exception(
                    "sum(npart_m) (%d) != nzero (%d)" %
                    (sum(npart_m_read), nzero)(npart_m_read))

        ##########################################
        # optionnally read extra header
        ##########################################
        if flag_chimie_extraheader == 1:
            self.message("reading chimie extra-header...")
            tpl = (np.int32, int(NELEMENTS) * 4, 256 - 4 - int(NELEMENTS) * 4)

            nelts, ChimieSolarMassAbundances, labels = io.ReadBlock(
                f, tpl, byteorder=self.byteorder, pio=self.pio)

            labels = labels.decode("utf-8")

            nelts = int(nelts)
            self.ChimieNelements = nelts

            ChimieElements = str.split(labels, ',')[:nelts]
            self.ChimieElements = ChimieElements

            ChimieSolarMassAbundances = np.frombuffer(
                ChimieSolarMassAbundances, np.float32)
            self.ChimieSolarMassAbundances = {}
            for i, elt in enumerate(self.ChimieElements):
                self.ChimieSolarMassAbundances[elt] = ChimieSolarMassAbundances[i]
        else:
            self.ChimieNelements = int(NELEMENTS)
            self.ChimieElements = ['Fe', 'Mg', 'O', 'Metals']

            self.ChimieSolarMassAbundances = {}
            self.ChimieSolarMassAbundances['Fe'] = 0.001771
            self.ChimieSolarMassAbundances['Mg'] = 0.00091245
            self.ChimieSolarMassAbundances['O'] = 0.0108169
            self.ChimieSolarMassAbundances['Metals'] = 0.02

        ##########################################
        # read and send particles attribute
        ##########################################
        vec = 'pos'
        self.message("reading %s..." % vec)
        pos = io.ReadDataBlock(f, np.float32, shape=(nbody_read, 3),
                               byteorder=self.byteorder, pio=self.pio,
                               npart=npart_read,
                               skip=self.skip_io_block(vec))

        vec = 'vel'
        self.message("reading %s..." % vec)
        vel = io.ReadDataBlock(f, np.float32, shape=(nbody_read, 3),
                               byteorder=self.byteorder, pio=self.pio,
                               npart=npart_read,
                               skip=self.skip_io_block(vec))

        vec = 'num'
        self.message("reading %s..." % vec)
        num = io.ReadDataBlock(f, np.int32, shape=(nbody_read,),
                               byteorder=self.byteorder, pio=self.pio,
                               npart=npart_read,
                               skip=self.skip_io_block(vec))

        ##########################################
        # read mass if needed
        ##########################################
        if nzero != 0:

            vec = 'mass'
            self.message("reading %s..." % vec)
            massnzero = io.ReadDataBlock(
                f, np.float32, shape=(nzero,),
                byteorder=self.byteorder, pio=self.pio,
                npart=npart_m_read, skip=self.skip_io_block(vec))

            if nzero == nbody_tot:
                mass = massnzero
            else:
                mass = np.array([])
                i1 = 0
                i2 = None
                for i in range(len(npart)):
                    if npart[i] != 0:		# particles belong to the class
                        if massarr[i] != 0:
                            mass = np.concatenate(
                                (mass, np.ones(npart[i]) * massarr[i]))
                        else:
                            i2 = i1 + npart[i]
                            mass = np.concatenate((mass, massnzero[i1:i2]))
                            i1 = i2

                if i2 is not None and i2 != len(massnzero):
                    raise Exception("i2=", i2, """!=len(massnzero)""")

                if len(mass) != nbody:				# if pio, we should maybee put nbody_tot ???
                    raise Exception("len(mass)=", len(mass), "!=nbody")

        '''
	  if massarr[i] == 0:
	    if npart[i]!=0:
	      if len(massnzero)!=npart[i]:
		raise "this case is not taken into account, sorry !"
      	      mass = concatenate((mass,massnzero))
	  else:
      	    mass = concatenate((mass,ones(npart[i])*massarr[i]))
    '''

        # extentions
        u = None
        rho = None
        rsp = None
        opt1 = None
        opt2 = None
        erd = None
        dte = None
        pot = None
        acc = None
        tstar = None
        minit = None
        idp = None
        metals = None
        thtsnii = None
        thtsnia = None

        if not io.end_of_file(f, pio=self.pio, MPI=MPI) and ngas_read != 0:
            vec = 'u'
            self.message("reading %s..." % vec)
            u = io.ReadDataBlock(
                f, np.float32, shape=(ngas_read,),
                byteorder=self.byteorder, pio=self.pio,
                npart=None, skip=self.skip_io_block(vec))
            
            if u is not None:
                u = np.concatenate(
                    (u, np.zeros(nbody - ngas).astype(np.float32))
                )

        if not io.end_of_file(f, pio=self.pio, MPI=MPI) and ngas_read != 0:
            vec = 'rho'
            self.message("reading %s..." % vec)
            rho = io.ReadDataBlock(
                f, np.float32, shape=(ngas_read,),
                byteorder=self.byteorder, pio=self.pio,
                npart=None, skip=self.skip_io_block(vec))
            if rho is not None:
                rho = np.concatenate(
                    (rho, np.zeros(nbody - ngas).astype(np.float32)))

        if not io.end_of_file(f, pio=self.pio, MPI=MPI) and ngas_read != 0:
            vec = 'rsp'
            self.message("reading %s..." % vec)
            rsp = io.ReadDataBlock(
                f, np.float32, shape=(ngas_read,),
                byteorder=self.byteorder, pio=self.pio,
                npart=None, skip=self.skip_io_block(vec))

            if rsp is not None:
                rsp = np.concatenate(
                    (rsp, np.zeros(nbody - ngas).astype(np.float32))
                )

        # here it is the end of the minimal output

        if flag_metals:		# gas metal properties

            if not io.end_of_file(f, pio=self.pio, MPI=MPI):
                vec = 'metals'
                self.message("reading %s..." % vec)
                metals = io.ReadDataBlock(
                    f, np.float32, shape=(ngas_read, NELEMENTS),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))
                if metals is not None:
                    metals = np.concatenate(
                        (metals, np.zeros((nbody - ngas, NELEMENTS)).astype(np.float32))
                    )

        if flag_thermaltime:  # gas thermal(adiabatic) time

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and ngas_read != 0:
                vec = 'thtsnii'
                self.message("reading %s..." % vec)
                thtsnii = io.ReadDataBlock(
                    f, np.float32, shape=(ngas_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))

                if thtsnii is not None:
                    thtsnii = np.concatenate(
                        (thtsnii, np.zeros(nbody - ngas).astype(np.float32)))

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and ngas_read != 0:
                vec = 'thtsnia'
                self.message("reading %s..." % vec)
                thtsnia = io.ReadDataBlock(
                    f, np.float32, shape=(ngas_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))

                if thtsnia is not None:
                    thtsnia = np.concatenate(
                        (thtsnia, np.zeros(nbody - ngas).astype(np.float32)))

        if flag_age:		# stellar properties

            if not io.end_of_file(f, pio=self.pio,MPI=MPI) and nstars_read != 0:
                vec = 'tstar'
                self.message("reading %s..." % vec)
                tstar = io.ReadDataBlock(
                    f, np.float32, shape=(nstars_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))

                if tstar is not None:
                    tstar = np.concatenate(
                        (-1 * np.ones(ngas).astype(np.float32),
                         tstar, -1 * np.ones(nbody - ngas - nstars).astype(np.float32))
                    )

            if (not io.end_of_file(f, pio=self.pio, MPI=MPI)
                    and nstars_read != 0):
                vec = 'minit'
                self.message("reading %s..." % vec)
                minit = io.ReadDataBlock(
                    f, np.float32, shape=(nstars_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))

                if minit is not None:
                    minit = np.concatenate(
                        (np.zeros(ngas).astype(np.float32),
                         minit,
                         np.zeros(nbody - ngas - nstars).astype(np.float32))
                    )

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and nstars_read != 0:
                vec = 'idp'
                self.message("reading %s..." % vec)
                idp = io.ReadDataBlock(
                    f, np.int32, shape=(nstars_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block(vec))

                if idp is not None:
                    idp = np.concatenate((-1 * np.ones(ngas).astype(np.float32),
                                          idp, -1 * np.ones(nbody - ngas - nstars).astype(np.float32)))

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and nstars_read != 0:
                vec = 'rho_stars'
                self.message("reading %s..." % vec)
                rho_stars = io.ReadDataBlock(
                    f, np.float32, shape=(nstars_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block('rho'))
                if rho_stars is not None:
                    if rho is None:
                        rho = np.concatenate(
                            (rho_stars,
                             np.zeros(nbody - ngas - nstars).astype(np.float32)))
                    else:
                        rho = np.concatenate((rho[:ngas], rho_stars, np.zeros(
                            nbody - ngas - nstars).astype(np.float32)))

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and nstars_read != 0:
                vec = 'rsp_stars'
                self.message("reading %s..." % vec)
                rsp_stars = io.ReadDataBlock(
                    f, np.float32, shape=(nstars_read,),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block('rsp'))
                
                if rsp_stars is not None:
                    if rsp is None:
                        rsp = np.concatenate(
                            (rsp_stars,
                             np.zeros(nbody - ngas - nstars).astype(np.float32))
                        )
                    else:
                        rsp = np.concatenate((rsp[:ngas], rsp_stars, np.zeros(
                            nbody - ngas - nstars).astype(np.float32)))

        if flag_metals:	      # stars metal properties

            if not io.end_of_file(f, pio=self.pio, MPI=MPI) and nstars_read != 0:
                vec = 'metals_stars'
                self.message("reading %s..." % vec)
                metals_stars = io.ReadDataBlock(
                    f, np.float32, shape=(nstars_read, NELEMENTS),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None, skip=self.skip_io_block('metals'))

                if metals_stars is not None:
                    metals = np.concatenate((metals[:ngas, :], metals_stars, np.zeros(
                        (nbody - ngas - nstars, NELEMENTS)).astype(np.float32)))

        # other variables
        if not io.end_of_file(f, pio=self.pio, MPI=MPI):
            pass

        if not io.end_of_file(f, pio=self.pio, MPI=MPI):
            vec = 'opt1'
            self.message("reading %s..." % vec)
            opt1 = io.ReadDataBlock(
                f,
                np.float32,
                shape=(
                    ngas_read,
                ),
                byteorder=self.byteorder,
                pio=self.pio,
                npart=None,
                skip=self.skip_io_block(vec))
            if opt1 is not None:
                if (len(opt1) == ngas):
                    opt1 = np.concatenate(
                        (opt1,
                         np.zeros(
                             nbody -
                             ngas).astype(
                             np.float32)))

        if not io.end_of_file(f, pio=self.pio, MPI=MPI):
            vec = 'opt2'
            self.message("reading %s..." % vec)
            opt2 = io.ReadDataBlock(
                f,
                np.float32,
                shape=(
                    ngas_read,
                ),
                byteorder=self.byteorder,
                pio=self.pio,
                npart=None,
                skip=self.skip_io_block(vec))
            if opt2 is not None:
                if (len(opt2) == ngas):
                    opt2 = np.concatenate(
                        (opt2,
                         np.zeros(
                             nbody -
                             ngas).astype(
                             np.float32)))

        if not io.end_of_file(f, pio=self.pio, MPI=MPI):
            vec = 'erd'
            self.message("reading %s..." % vec)
            erd = io.ReadDataBlock(
                f,
                np.float32,
                shape=(
                    ngas_read,
                ),
                byteorder=self.byteorder,
                pio=self.pio,
                npart=None,
                skip=self.skip_io_block(vec))
            if (len(erd) == ngas):
                erd = np.concatenate(
                    (erd,
                     np.zeros(
                         nbody -
                         ngas).astype(
                         np.float32)))

        if not io.end_of_file(f, pio=self.pio, MPI=MPI):
            vec = 'dte'
            self.message("reading %s..." % vec)
            dte = io.ReadDataBlock(
                f,
                np.float32,
                shape=(
                    ngas_read,
                ),
                byteorder=self.byteorder,
                pio=self.pio,
                npart=None,
                skip=self.skip_io_block(vec))
            dte = np.concatenate(
                (dte,
                 np.zeros(
                     nbody -
                     ngas).astype(
                     np.float32)))

        # if not io.end_of_file(f,pio=self.pio,MPI=MPI):
        #  pot  = io.ReadDataBlock(f,np.float32,shape=(ngas_read,),byteorder=self.byteorder,pio=self.pio,npart=None)

        # make global
        self.npart = npart
        self.massarr = massarr

        self.atime = atime
        self.redshift = redshift
        self.flag_sfr = flag_sfr
        self.flag_feedback = flag_feedback
        self.nall = nall
        self.flag_cooling = flag_cooling
        self.num_files = num_files
        self.boxsize = boxsize
        self.omega0 = omega0
        self.omegalambda = omegalambda
        self.hubbleparam = hubbleparam
        self.flag_age = flag_age
        self.flag_metals = flag_metals
        self.flag_thermaltime = flag_thermaltime
        self.nallhw = nallhw
        self.flag_entr_ic = flag_entr_ic
        self.flag_chimie_extraheader = flag_chimie_extraheader
        self.critical_energy_spec = critical_energy_spec
        self.empty = empty
        self.nbody = nbody

        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.num = num

        self.tpe = np.array([], np.int32)
        for i in range(len(npart)):
            self.tpe = np.concatenate((self.tpe, np.ones(npart[i]) * i))

        self.nzero = nzero
        self.u = u
        self.rho = rho

        self.tstar = tstar
        self.minit = minit
        self.idp = idp
        self.metals = metals

        self.thtsnii = thtsnii
        self.thtsnia = thtsnia

        self.opt1 = opt1
        self.opt2 = opt2
        self.erd = erd
        self.dte = dte
        self.pot = pot
        self.acc = acc

        self.rsp = rsp

        if isinstance(self.massarr, np.ndarray):
            self.massarr = self.massarr.tolist()
        if isinstance(self.nall, np.ndarray):
            self.nall = self.nall.tolist()
        if isinstance(self.nallhw, np.ndarray):
            self.nallhw = self.nallhw.tolist()

        # init comoving integration
        self.comovingintegration = None
        self.initComovingIntegration()
        self.initHubbleFactorCorrection()
        
        # set 
        if self.comovingintegration:
          self.comovingtoproperconversion=True
        else:
          self.comovingtoproperconversion=False  
        

    def write_particles(self, f):
        '''
        specific format for particle file
        '''

        # here, we must let the user decide if we creates
        # the mass block or not, event if all particles have the same mass
        massarr, nzero = self.get_massarr_and_nzero()

        if self.pio == 'yes':

            '''
            here, we have to compute also
            mass for each proc
            '''

            npart = self.npart
            nall = self.npart_tot
            num_files = mpi.NTask

            npart_write = None
            npart_m_write = None

        else:

            npart = self.npart
            nall = self.npart_tot
            npart_all = np.array(mpi.mpi_allgather(npart))
            num_files = 1

            npart_write = self.npart
            npart_m_write = np.array(self.npart) * \
                (np.array(self.massarr) == 0)

            # compute the global massarr and global nzero
            nzero_tot = mpi.mpi_sum(nzero)
            massarr_all = np.array(mpi.mpi_allgather(massarr))
            massarr_tot = np.zeros(len(npart), float)

            for i in range(len(npart)):

                # keep only values where there are particles
                massarr_all_red = np.compress(
                    npart_all[:, i] != 0, massarr_all[:, i])

                if len(massarr_all_red) > 0:
                    if (massarr_all_red == massarr_all_red).all():
                        massarr_tot[i] = massarr_all[0, i]
                    else: 		  # not equal
                        raise Exception("this case is not implemented")
                        massarr_tot[i] = 0.0
                        nzero_tot = nzero_tot + sum(npart_write[:, i])

            # now, re-compute nzero for the current node
            massarr = massarr_tot
            nzero = 0
            for i in range(len(npart)):
                if massarr[i] == 0:
                    nzero = nzero + npart[i]

        # now that we have the right massarr and nzero,
        # we can compute massnzero for each node
        nzero_all = np.zeros((mpi.NTask, len(self.npart)))

        if nzero != 0:
            ni = 0
            massnzero = np.array([], np.float32)
            for i in range(len(self.npart)):
                if npart[i] != 0 and massarr[i] == 0.:
                    massnzero = np.concatenate(
                        (massnzero, self.mass[ni:ni + self.npart[i]]))
                    nzero_all[mpi.ThisTask,
                              i] = nzero_all[mpi.ThisTask,
                                             i] + npart[i]

                ni = ni + self.npart[i]

        nzero_all = mpi.mpi_allreduce(nzero_all)

        if self.pio == 'yes':
            if nzero != 0 and len(
                    massnzero) == 0:		# !!! because zere is a bug see warning in get_massarr_and_nzero
                nzero = 0
        else:
            npart = self.npart_tot
            nzero = mpi.mpi_allreduce(nzero)  # to ensure that all nodes
            # will do -> write mass if needed

        # header
        if sys.byteorder == self.byteorder:
            npart = np.array(npart, np.int32).tostring()
            massarr = np.array(massarr, float).tostring()
        else:
            npart = np.array(npart, np.int32).byteswap().tostring()
            massarr = np.array(massarr, float).byteswap().tostring()

        atime = self.atime
        redshift = self.redshift
        flag_sfr = self.flag_sfr
        flag_feedback = self.flag_feedback

        if sys.byteorder == self.byteorder:
            nall = np.array(nall, np.int32).tostring()
        else:
            nall = np.array(nall, np.int32).byteswap().tostring()

        flag_cooling = self.flag_cooling
        num_files = num_files
        boxsize = self.boxsize
        omega0 = self.omega0
        omegalambda = self.omegalambda
        hubbleparam = self.hubbleparam
        flag_age = self.flag_age
        flag_metals = self.flag_metals

        if sys.byteorder == self.byteorder:
            nallhw = np.array(self.nallhw, float).tostring()
        else:
            nallhw = np.array(self.nallhw, float).byteswap().tostring()

        flag_entr_ic = self.flag_entr_ic
        flag_chimie_extraheader = self.flag_chimie_extraheader
        flag_thermaltime = self.flag_thermaltime
        critical_energy_spec = self.critical_energy_spec
        empty = self.empty

        # header
        tpl = (
            (npart, 24),
            (massarr, 48),
            (atime, float),
            (redshift, float),
            (flag_sfr, np.int32),
            (flag_feedback, np.int32),
            (nall, 24),
            (flag_cooling, np.int32),
            (num_files, np.int32),
            (boxsize, float),
            (omega0, float),
            (omegalambda, float),
            (hubbleparam, float),
            (flag_age, np.int32),
            (flag_metals, np.int32),
            (nallhw, 24),
            (flag_entr_ic, np.int32),
            (flag_chimie_extraheader, np.int32),
            (flag_thermaltime, np.int32),
            (critical_energy_spec, float),
            (empty, 44))
        io.WriteBlock(f, tpl, byteorder=self.byteorder)

        # extra header
        if self.flag_chimie_extraheader:
            self.message("writing chimie extra-header...")

            SolarMassAbundances = np.zeros(self.ChimieNelements, np.float32)
            labels = ""
            for i, elt in enumerate(self.ChimieElements):
                SolarMassAbundances[i] = self.ChimieSolarMassAbundances[elt]
                labels = labels + "%s," % elt

            labels_len = (256 - 4 - self.ChimieNelements * 4)
            labels = labels + (labels_len - len(labels)) * " "
            labels.encode("utf-8")

            tpl = ((self.ChimieNelements, np.int32),
                   (SolarMassAbundances, np.float32), (labels, len(labels)))

            io.WriteBlock(f, tpl, byteorder=self.byteorder)

        # positions
        io.WriteArray(
            f,
            self.pos.astype(
                np.float32),
            byteorder=self.byteorder,
            pio=self.pio,
            npart=npart_write)
        # velocities
        io.WriteArray(
            f,
            self.vel.astype(
                np.float32),
            byteorder=self.byteorder,
            pio=self.pio,
            npart=npart_write)
        # id
        io.WriteArray(
            f,
            self.num.astype(
                np.int32),
            byteorder=self.byteorder,
            pio=self.pio,
            npart=npart_write)

        # write mass if needed
        if nzero != 0:
            io.WriteArray(
                f,
                massnzero.astype(
                    np.float32),
                byteorder=self.byteorder,
                pio=self.pio,
                npart=npart_m_write)

        # write extension
        if self.has_array('u'):
            if self.u is not None and self.npart[0] > 0:
                io.WriteArray(f, self.u[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write u")
        if self.has_array('rho'):
            if self.rho is not None and self.npart[0] > 0:
                io.WriteArray(f, self.rho[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write rho")
        if self.has_array('rsp'):
            if self.rsp is not None and self.npart[0] > 0:
                io.WriteArray(f, self.rsp[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write rsp")

        # this is the end of the minimal output

        if self.flag_metals:
            if self.has_array('metals'):
                io.WriteArray(f, self.metals[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write metals")

        if flag_thermaltime:
            if self.has_array('thtsnii'):
                io.WriteArray(f, self.thtsnii[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write thtsnii")

            if self.has_array('thtsnia'):
                io.WriteArray(f, self.thtsnia[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write thtsnia")

        if self.flag_age:
            if self.has_array('tstar') and self.npart[1] > 0:
                io.WriteArray(f, self.tstar[self.npart[0]:self.npart[0] + self.npart[1]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write tstar")

            if self.has_array('minit') and self.npart[1] > 0:
                io.WriteArray(f, self.minit[self.npart[0]:self.npart[0] + self.npart[1]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write minit")

            if self.has_array('idp') and self.npart[1] > 0:
                io.WriteArray(f, self.idp[self.npart[0]:self.npart[0] + self.npart[1]].astype(
                    np.int32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write idp")

            if self.has_array('rho') and self.npart[1] > 0:
                data = self.rho[self.npart[0]:self.npart[0] +
                                self.npart[1]].astype(np.float32)
                if len(data) > 0:
                    io.WriteArray(
                        f, data, byteorder=self.byteorder,
                        pio=self.pio, npart=None)
                    self.message("write rho (stars)")

            if self.has_array('rsp') and self.npart[1] > 0:
                data = self.rsp[self.npart[0]:self.npart[0] +
                                self.npart[1]].astype(np.float32)
                if len(data) > 0:
                    io.WriteArray(
                        f, data, byteorder=self.byteorder,
                        pio=self.pio, npart=None)
                    self.message("write rsp (stars)")

        if self.flag_metals:
            if self.has_array('metals') and self.npart[1] > 0:
                data = self.metals[self.npart[0]:self.npart[0] +
                                   self.npart[1]].astype(np.float32)
                if len(data) > 0:
                    io.WriteArray(
                        f, data, byteorder=self.byteorder,
                        pio=self.pio, npart=None)
                    self.message("write metals (stars)")

        if self.has_array('pot'):
            if self.pot is not None:
                io.WriteArray(
                    f, self.pot.astype(np.float32),
                    byteorder=self.byteorder, pio=self.pio,
                    npart=None)
                self.message("write pot")

        if self.has_array('acc'):
            if self.acc is not None:
                io.WriteArray(
                    f, self.acc.astype(np.float32),
                    byteorder=self.byteorder,
                    pio=self.pio, npart=None)
                self.message("write acc")

        if self.has_array('opt1'):
            if self.opt1 is not None:
                io.WriteArray(f, self.opt1[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write opt1")

        if self.has_array('opt2'):
            if self.opt2 is not None:
                io.WriteArray(f, self.opt2[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
                self.message("write opt2")

        if self.has_array('erd'):
            if self.erd is not None:
                io.WriteArray(f, self.erd[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
        if self.has_array('dte'):
            if self.dte is not None:
                io.WriteArray(f, self.dte[:self.npart[0]].astype(
                    np.float32), byteorder=self.byteorder, pio=self.pio, npart=None)
