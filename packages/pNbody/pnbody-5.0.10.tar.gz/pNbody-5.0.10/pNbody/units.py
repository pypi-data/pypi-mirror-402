#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      units.py
#  brief:     defines units systems
#  copyright: GPLv3
#             Copyright (C) 2019 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Yves Revaz <yves.revaz@epfl.ch>
#
# This file is part of pNbody.
###########################################################################################


import copy
import numpy
from pNbody import iofunc as pnio
from pNbody import param
from sys import exit



##########################################################################

from astropy import units as u


class unitSystem():
  '''
  New system units, compatible with astropy.
  By default the units are the Gadget-2 ones.
  '''
    
  def __init__(self,ULength=3.085678e21*u.cm,UMass=1.989e43*u.g,UVelocity=1e5*u.cm/u.s):
    
    self.ULength   = ULength
    self.UMass     = UMass
    self.UVelocity = UVelocity 
    self.Init()
  
  
  def setUnitLength(self,ULength):
    self.ULength   = ULength
    self.Init()

  def setUnitMass(self,UMass):
    self.UMass   = UMass
    self.Init()
    
  def setUnitVelocity(self,UVelocity):
    self.UVelocity   = UVelocity
    self.Init()        
    
    
  def Init(self):
    
    self.UnitLength               = u.def_unit(['Ul'],self.ULength)     
    self.UnitMass                 = u.def_unit(['Um'],self.UMass)           
    self.UnitVelocity             = u.def_unit(['Uv'],self.UVelocity)  
        
    self.UnitTime                 = u.def_unit(['Ut'], self.UnitLength/self.UnitVelocity)
    self.UnitTemperature          = u.def_unit(['UT'], u.K)
    self.UnitEnergySpec           = self.UnitVelocity**2
    self.UnitEnergy               = self.UnitVelocity**2*self.UnitMass
    self.UnitDensity              = self.UnitMass/self.UnitLength**3
    self.UnitPressure             = self.UnitEnergySpec*self.UnitDensity
    self.UnitBases                = self.UnitLength.bases + self.UnitMass.bases + self.UnitTime.bases + self.UnitTemperature.bases
    



##########################################################################
class Units:
    ##########################################################################
    """
    Units class.
    """

    def __init__(self, symbol, factor=1., power=1, ulist=None):
        """
        """
        self.symbol = symbol
        self.factor = float(factor)
        self.power = int(power)
        if ulist is None:
            self.ulist = []
        else:
            self.ulist = ulist
        self.bases = []

        self.GatherBaseUnits()

    def set_symbol(self, symbol):

        self.ulist = [copy.deepcopy(self)]
        self.power = 1
        self.factor = 1.0
        self.symbol = symbol
        self.GatherBaseUnits()

    def GatherBaseUnits(self):
        """
        create the self.bases list (recursively)
        """

        self.bases = []

        for unit in self.ulist:

            if len(unit.ulist) == 0:		# a base unit
                self.bases.append(unit)   	# add the unit

            else:				# go deeper in the tree
                unit.GatherBaseUnits()
                self.bases = self.bases + unit.bases

        self.ReduceBaseUnits()

    def ReduceBaseUnits(self):

        allunits = {}
        factorTot = 1.0
        for base in self.bases:
            factorTot = factorTot * base.factor
            if base.symbol in allunits:
                allunits[base.symbol] = allunits[base.symbol] + base.power
            else:
                allunits[base.symbol] = base.power

        self.bases = []
        flag = 1
        for key in list(allunits.keys()):
            factor = 1.0
            if flag:
                factor = factorTot
                flag = 0
            power = allunits[key]
            symbol = key
            ulist = []
            self.bases.append(Units(symbol, factor, power, ulist))

    def get_basefactor(self):
        """
        return the factor relative to the base units

        actually, it is stored as the factor of the first base unit
        """
        return self.bases[0].factor

    # def to_units(self,newunits):
    #   """
    #   return a new unit object in new units
    #   """
    #
    #   # check that the units are similar

    def str_base(self):

        string = ''

        if self.factor != 1.0:
            string = string + self.factor.__str__()

        if len(string) > 0:
            string = string + ' '
        if self.symbol is None:
            string = string + '-'
        else:
            string = string + self.symbol

        if self.power != 1:
            string = string + '^%d' % self.power

        return string

    def __str__(self):

        string = ''
        # (1) display using symbol
        if self.factor != 0:
            string = string + self.str_base()

        str1 = "[%s]" % string

        string = ''
        # (2) display using (base units)
        for base in self.bases:
            if len(string) > 0:
                string = string + ' '
            string = string + base.str_base()

        str2 = "[%s]" % string

        if str2 != '[]':
            str1 = "%s\t%s" % (str1, str2)

        return str1

    def __mul__(self, y):

        x = copy.deepcopy(self)
        y = copy.deepcopy(y)

        # multiply with a scalar
        if isinstance(y, int) or isinstance(y, float):
            x.factor = x.factor * y
            x.mul_list(x.ulist, y)
            x.GatherBaseUnits()
            return x

        # multiply with a unit
        elif isinstance(y, type(x)):

            if x.symbol == y.symbol:		# same units
                x.symbol = x.symbol
                x.power = x.power + y.power
                x.ulist = x.ulist + y.ulist
                x.GatherBaseUnits()
                return x

            else:				# different unit
                symbol = None
                power = 1
                factor = 1.0
                if x.ulist == []:			# case of a base unit
                    x.ulist = [copy.deepcopy(x)]
                if y.ulist == []:			# case of a base unit
                    y.ulist = [copy.deepcopy(y)]
                ulist = x.ulist + y.ulist
                return Units(symbol, factor, power, ulist)

    def __truediv__(self, y):

        x = copy.deepcopy(self)
        y = copy.deepcopy(y)

        # divide with a scalar
        if isinstance(y, int) or isinstance(y, float):
            x.factor = x.factor / y
            x.div_list(x.ulist, y)
            x.GatherBaseUnits()
            return x

        # divide with a unit
        elif isinstance(y, type(x)):

            if x.symbol == y.symbol:		# same units
                x.symbol = None
                x.power = 0
                x.ulist = []
                x.GatherBaseUnits()
                return x

            else:				# different unit
                symbol = None
                power = 1
                factor = 1.0
                if x.ulist == []:			# case of a base unit
                    x.ulist = [copy.deepcopy(x)]
                if y.ulist == []:			# case of a base unit
                    y.ulist = [copy.deepcopy(y)]
                y.pow_list(y.ulist, -1)
                y.GatherBaseUnits()
                ulist = x.ulist + y.ulist
                return Units(symbol, factor, power, ulist)

    def __rtruediv__(self, y):
        x = copy.deepcopy(self)

        # divide with a scalar
        if isinstance(y, int) or isinstance(y, float):
            return y * x**-1
        else:
            raise Exception(
                "TypeError",
                "unsupported operand type(s) for / or div()")

    def __pow__(self, y):

        x = copy.deepcopy(self)
        y = copy.deepcopy(y)

        # power with a scalar
        if isinstance(y, int) or isinstance(y, float):
            x.factor = x.factor**y
            x.power = x.power * y
            x.pow_list(x.ulist, y)
            x.GatherBaseUnits()
            return x

        else:
            raise Exception(
                "TypeError",
                "unsupported operand type(s) for ** or pow()")

    def mul_list(self, ulist, y):

        for u in ulist:
            if len(u.ulist) == 0:		# a base unit
                u.factor = u.factor * y
            else:				# go deeper in the tree
                u.mul_list(u.ulist, y)
                u.GatherBaseUnits()

    def div_list(self, ulist, y):

        for u in ulist:
            if len(u.ulist) == 0:		# a base unit
                u.factor = u.factor / y
            else:				# go deeper in the tree
                u.mul_list(u.ulist, y)
                u.GatherBaseUnits()

    def pow_list(self, ulist, y):

        for u in ulist:
            if len(u.ulist) == 0:		# a base unit
                u.factor = u.factor**y
                u.power = u.power * y
            else:				# go deeper in the tree
                u.pow_list(u.ulist, y)
                u.GatherBaseUnits()

    __rmul__ = __mul__


##########################################################################
class UnitSystem:
    ##########################################################################
    """
    Units system
    """

    def __init__(self, UnitSysName, UnitLst):
        """
        UnitDic = {'length':UnitLength,'mass':UnitMass,'time':UnitTime}

        The units used to define a system of units must be "basic", i.e.,
        not based on several units


        useful variables

        self.dic_of_factors		: value of base unit in current units
        self.UnitDic		    : contains base units and value of the chosen unit in this base units

        """

        UnitDic = {}
        for u in UnitLst:
            u.GatherBaseUnits()

            if len(u.bases) > 1:
                raise Exception(
                    "UnitSystemError",
                    "%s is not a pure Unit." %
                    u.symbol)

            elif len(u.bases) == 1:
                UnitDic[u.bases[0].symbol] = u.bases[0]

            elif len(u.bases) == 0:				# base unit
                UnitDic[u.symbol] = u

        self.set_dics(UnitDic)

        self.UnitSysName = UnitSysName
        self.UnitLst = UnitLst

    def set_dics(self, UnitDic):

        dic_of_factors = {}
        dic_of_powers = {}

        for UnitType in list(UnitDic.keys()):
            u = UnitDic[UnitType]

            if u.bases == []:					# base unit
                dic_of_factors[UnitType] = 1 / u.factor
                dic_of_powers[UnitType] = u.power
            else:
                dic_of_factors[UnitType] = 1 / u.bases[0].factor
                dic_of_powers[UnitType] = u.bases[0].power

        self.dic_of_factors = dic_of_factors		# value of base unit in current units
        self.dic_of_powers = dic_of_powers			# not useful

        self.UnitDic = UnitDic

        self.UnitLength = self.UnitDic['m']
        self.UnitMass = self.UnitDic['kg']
        self.UnitTime = self.UnitDic['s']

        self.UnitVelocity = self.UnitDic['m'] / self.UnitDic['s']
        self.UnitSpecEnergy = self.UnitVelocity**2
        self.UnitEnergy = self.UnitSpecEnergy * self.UnitMass

        self.UnitDensity = self.UnitMass / self.UnitLength**3
        self.UnitSurfaceDensity = self.UnitMass / self.UnitLength**2
        self.UnitSurface = self.UnitLength**2

    def get_UnitLength_in_cm(self):
        f = self.UnitDic['m'].factor
        c = PhysCte(f, Unit_m)
        return c.into(cgs)

    def get_UnitMass_in_g(self):
        f = self.UnitDic['kg'].factor
        c = PhysCte(f, Unit_kg)
        return c.into(cgs)

    def get_UnitTime_in_s(self):
        f = self.UnitDic['s'].factor
        c = PhysCte(f, Unit_s)
        return c.into(cgs)

    def get_UnitVelocity_in_cm_per_s(self):
        return self.get_UnitLength_in_cm() / self.get_UnitTime_in_s()

    def get_UnitEnergy_in_cgs(self):
        return self.get_UnitMass_in_g() * self.get_UnitVelocity_in_cm_per_s()**2

    def get_UnitDensity_in_cgs(self):
        return self.get_UnitMass_in_g() / self.get_UnitLength_in_cm()**3

    def info(self):
        """
        print some info
        """
        print("units info")
        print(("  UnitLength_in_cm         =%g" %
               (self.get_UnitLength_in_cm())))
        print(("  UnitVelocity_in_cm_per_s =%g" %
               (self.get_UnitVelocity_in_cm_per_s())))
        print(("  UnitMass_in_g            =%g" % (self.get_UnitMass_in_g())))

    def getparam(self):
        param = {}
        param["UnitLength_in_cm"] = self.get_UnitLength_in_cm()
        param["UnitVelocity_in_cm_per_s"] = self.get_UnitVelocity_in_cm_per_s()
        param["UnitMass_in_g"] = self.get_UnitMass_in_g()
        return param

    def convertionFactorTo(self, newUnits):
        """
        return the conversion factor to obtain the new units
        """

        f = 1.0

        # loop over all base units of the new Units
        if newUnits.bases == []:
            baselist = [newUnits]
        else:
            baselist = newUnits.bases

        for base in baselist:

            factor = base.factor
            symbol = base.symbol
            power = base.power

            # multiply by the right factor
            f = f / (factor * (self.dic_of_factors[symbol])**power)

        return f

    def into(self, newUnits):
        """
        return into the new units
        """
        return PhysCte(self.convertionFactorTo(newUnits), newUnits)

    def multiply_UnitLength(self, f):
        self.UnitDic['m'].factor *= f
        self.set_dics(self.UnitDic)

    def multiply_UnitMass(self, f):
        self.UnitDic['kg'].factor *= f
        self.set_dics(self.UnitDic)

    def multiply_UnitTime(self, f):
        self.UnitDic['s'].factor *= f
        self.set_dics(self.UnitDic)

    def CorrectFromHubbleParameter(self, HubbleParam):
        print(("Units Correction : HubbleParam = %g" % HubbleParam))
        self.multiply_UnitLength(1.0 / HubbleParam)
        self.multiply_UnitMass(1.0 / HubbleParam)
        self.multiply_UnitTime(1.0 / HubbleParam)


    def to_unitSystem(self):
      ULength = self.get_UnitLength_in_cm()*u.cm
      UMass = self.get_UnitMass_in_g()*u.g
      UVelocity = self.get_UnitVelocity_in_cm_per_s()*u.cm/u.s
    
      return unitSystem(ULength=ULength,UMass=UMass,UVelocity=UVelocity)




##########################################################################
class PhysCte():
    ##########################################################################
    """
    Physical constant
    """

    def __init__(self, value, Unit):
        # super(PhysCte,self).__init__(value)
        self.value = value
        self.Unit = Unit
        if isinstance(Unit, (list, numpy.ndarray)):
            msg = "Can't handle non-scalars with varying units. All units need to be the same."
            raise ValueError(msg)

    def factor_to_base(self):

        if self.Unit.bases == []:
            factor = self.Unit.factor
        else:
            factor = self.Unit.bases[0].factor

        return factor

    def __str__(self):
        if isinstance(self.value, (list, numpy.ndarray)):
            return self.value.__str__() + ' [%s]' % self.Unit
           # return self.value.dtype.__str__() + ' %s' % self.Unit
        else:
            return self.value.__str__() + ' [%s]' % self.Unit

    def into(self, SystemName):			# here, we could return an object

        f = self.value

        if self.Unit.bases == []:
            unit = self.Unit
            symbol = unit.symbol
            f = f * unit.factor * \
                (SystemName.dic_of_factors[symbol])**unit.power
        else:
            for unit in self.Unit.bases:
                symbol = unit.symbol
                f = f * unit.factor * \
                    (SystemName.dic_of_factors[symbol])**unit.power

        return float(f)

    def __float__(self):
        if isinstance(self.value, numpy.ndarray):
            print(self[0])
            return(self[:].value.astype(numpy.float))
        else:
            return float(self.value)

    def __mul__(self, y):
        if hasattr(y, 'Unit'):
            # if multiplying with something that has a unit, i.e. another PhysCte
            return PhysCte(self.value * y.value, self.Unit * y.Unit)
        elif isinstance(y, Units):
            from . import message
            message.todo_warning()
            return self
            # this doesn't work
            # return PhysCte(self.value * y.factor, self.Unit*y)
        else:
            return PhysCte(self.value*y, self.Unit)

    __rmul__ = __mul__

    def __add__(self, y):
        pass

    def __sub__(self, y):
        pass

    def __truediv__(self, y):
        if hasattr(y, 'Unit'):
            # if multiplying with something that has a unit
            return PhysCte(self.value / y.value, self.Unit / y.Unit)
        elif isinstance(y, Units):
            from . import message
            message.todo_warning()
            return self
            # this doesn't work
            # return PhysCte(self.value / y.factor, self.Unit/y)
        else:
            return PhysCte(self.value / y, self.Unit)
    __rtruediv__ = __truediv__

    def __pow__(self, y):
        pass


##########################################################################
# define some units
##########################################################################


# base units
Unit_m = Units('m')
Unit_kg = Units('kg')
Unit_s = Units('s')
Unit_mol = Units('mol')
Unit_C = Units('C')
Unit_K = Units('K')


# other length units
Unit_cm = 0.01 * Unit_m
Unit_cm.set_symbol('cm')
Unit_km = 1e3 * Unit_m
Unit_km.set_symbol('km')
Unit_Mm = 1e6 * Unit_m
Unit_Mm.set_symbol('Mm')
Unit_Gm = 1e9 * Unit_m
Unit_Gm.set_symbol('Gm')
Unit_kpc = 1000 * 3.085e18 * Unit_cm
Unit_kpc.set_symbol('kpc')
Unit_Mpc = 1000000 * 3.085e18 * Unit_cm
Unit_Mpc.set_symbol('Mpc')
Unit_pc = 3.085e18 * Unit_cm
Unit_pc.set_symbol('pc')
Unit_ua = 1.495978e11 * Unit_m
Unit_ua.set_symbol('ua')

# other mass units
Unit_g = 0.001 * Unit_kg
Unit_g.set_symbol('g')
Unit_Ms = 1.9891e33 * Unit_g
Unit_Ms.set_symbol('Ms')
Unit_Msol = 1.9891e33 * Unit_g
Unit_Msol.set_symbol('Ms')
Unit_Mg = 2.23e11 * Unit_Ms
Unit_Mg.set_symbol('Mg')
Unit_Mt = 5.9742e24 * Unit_kg
Unit_Mt.set_symbol('Mt')
Unit_Mj = 317.893 * Unit_Mt
Unit_Mj.set_symbol('Mj')

# other time units
Unit_h = 3600 * Unit_s
Unit_h.set_symbol('h')
Unit_yr = 31536000 * Unit_s
Unit_yr.set_symbol('yr')
Unit_kyr = 1e3 * Unit_yr
Unit_kyr.set_symbol('kyr')
Unit_Myr = 1e6 * Unit_yr
Unit_Myr.set_symbol('Myr')
Unit_Gyr = 1e9 * Unit_yr
Unit_Gyr.set_symbol('Gyr')
Unit_dy = 86400 * Unit_s
Unit_dy.set_symbol('days')
Unit_hr = 3600 * Unit_s
Unit_hr.set_symbol('hr')
Unit_century = 100 * Unit_yr
Unit_century.set_symbol('century')

# other speed units
Unit_kmh = Unit_km / Unit_h
Unit_kmh.set_symbol('kmh')
Unit_kms = Unit_km / Unit_s
Unit_kms.set_symbol('kms')

# other units
Unit_ms = Unit_m / Unit_s
Unit_ms2 = Unit_ms**2
Unit_J = Unit_kg * Unit_ms2
Unit_J.set_symbol('J')
Unit_erg = Unit_g * (Unit_cm / Unit_s)**2
Unit_erg.set_symbol('erg')
Unit_N = Unit_kg * Unit_m / Unit_s**2
Unit_N.set_symbol('N')
Unit_Pa = Unit_N / Unit_m**2
Unit_Pa.set_symbol('Pa')
Unit_G = Unit_N * Unit_m**2 / Unit_kg**2
Unit_d = Unit_kg / Unit_m**3
Unit_Lsol = 3.839 * Unit_erg / Unit_s
Unit_Lsol.set_symbol('Lsol')

##########################################################################
# define some common unit systems
##########################################################################

mks = UnitSystem('mks', [Unit_m, Unit_kg, Unit_s, Unit_K, Unit_mol, Unit_C])
cgs = UnitSystem('cgs', [Unit_cm, Unit_g, Unit_s, Unit_K, Unit_mol, Unit_C])
gal = UnitSystem(
    'gal', [
        Unit_kpc, Unit_Mg, Unit_Myr, Unit_K, Unit_mol, Unit_C])





##########################################################################
# define some functions
##########################################################################


#################################
def Set_SystemUnits_From_Params(params):
    #################################
    """
    return a system of units from given parameters

    params is a dictionary that must contain at least

        params['UnitVelocity_in_cm_per_s'],

        params['UnitMass_in_g'],

        params['UnitLength_in_cm']

    """
    UnitVelocity_in_cm_per_s = params['UnitVelocity_in_cm_per_s']
    UnitMass_in_g = params['UnitMass_in_g']
    UnitLength_in_cm = params['UnitLength_in_cm']
    UnitTime_in_s = UnitLength_in_cm / UnitVelocity_in_cm_per_s

    # now from the params, define a system of units

    Unit_length = Unit_cm * UnitLength_in_cm
    Unit_mass = Unit_g * UnitMass_in_g
    Unit_time = Unit_s * UnitTime_in_s

    localsystem = UnitSystem(
        'local', [
            Unit_length, Unit_mass, Unit_time, Unit_K, Unit_mol, Unit_C])

    return localsystem


#################################
def Set_SystemUnits_From_File(unitsfile):
    #################################
    """
    return a system of units from given file coding units

    unitsfile file is either a gadget parameter file or a pNbody  units file


    """
    params = {}

    # try to read a gadget file
    try:
        gparams = pnio.read_params(unitsfile)
        params['UnitLength_in_cm'] = gparams['UnitLength_in_cm']
        params['UnitMass_in_g'] = gparams['UnitMass_in_g']
        params['UnitVelocity_in_cm_per_s'] = gparams['UnitVelocity_in_cm_per_s']

        # params['Omega0']                   = gparams['Omega0']
        # params['OmegaLambda']              = gparams['OmegaLambda']
        # params['OmegaBaryon']              = gparams['OmegaBaryon']
        # params['BoxSize']                  = gparams['BoxSize']
        # params['ComovingIntegrationOn']    = gparams['ComovingIntegrationOn']

        params = gparams

    except BaseException:

        # try to read a pNbody units file
        try:
            gparams = param.Params(unitsfile, None)

            params['UnitLength_in_cm'] = gparams.get("UnitLength_in_cm")
            params['UnitMass_in_g'] = gparams.get("UnitMass_in_g")
            params['UnitVelocity_in_cm_per_s'] = gparams.get(
                "UnitVelocity_in_cm_per_s")

            # params['Omega0']                   = gparams.get('Omega0')
            # params['OmegaLambda']              = gparams.get('OmegaLambda')
            # params['OmegaBaryon']              = gparams.get('OmegaBaryon')
            # params['BoxSize']                  = gparams.get('BoxSize')
            # params['ComovingIntegrationOn']    = gparams.get('ComovingIntegrationOn')

        except BaseException:
            raise IOError(
                0o15,
                'format of unitsfile %s unknown ! Pease check.' %
                unitsfile)

    localsystem = Set_SystemUnits_From_Params(params)

    return localsystem


def GetUnitsFromString(UnitString):

    from pNbody import ctes

    #################
    # Mass Units
    #################
    if UnitString == "Msol":  # Msol
        return Unit_Msol

    elif UnitString == "g":       # gramm
        return Unit_g

    #################
    # Length Units
    #################
    elif UnitString == "cm":  # cm
        return Unit_cm

    elif UnitString == "pc":  # pc
        return Unit_pc

    elif UnitString == "kpc":  # kpc
        return Unit_kpc

    elif UnitString == "Mpc":  # Mpc
        return Unit_Mpc

    #################
    # Time Units
    #################
    elif UnitString == "yr":  # years
        return Unit_yr

    elif UnitString == "Myr":  # mega years
        return Unit_Myr

    elif UnitString == "Gyr":  # giga years
        return Unit_Gyr

    #################
    # Density Units
    #################
    elif UnitString == "a/cm3" or UnitString == "acc":  # atom/cm^3
        Unit_atom = ctes.PROTONMASS.into(cgs) * Unit_g
        return Unit_atom / (Unit_cm**3)

    elif UnitString == "g/cm3":		# gram/cm^3
        return Unit_g / (Unit_cm**3)

    elif UnitString == "Msol/kpc3":  # Msol/kpc3
        return Unit_Msol / (Unit_kpc**3)

    elif UnitString == "Msol/pc3":  # Msol/pc3
        return Unit_Msol / (Unit_pc**3)

    #################
    # Velocity Units
    #################

    elif UnitString == "m/s":		# m/s
        return Unit_m / Unit_s

    elif UnitString == "km/s":		# m/s
        return Unit_km / Unit_s

    #################
    # Energy Units
    #################

    elif UnitString == "erg":		# gram * (cm/s)**2
        return Unit_g * (Unit_cm**2) / (Unit_s**2)

    else:
        print(UnitString)
        print("unknown unit name")
        exit()
