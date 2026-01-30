"""
Functions to aid in creating valid tests and identifying valid instrument configurations.
"""
import os
import json
import numpy as np

import pandeia.engine.config as cf
from pandeia.engine.calc_utils import build_default_calc

class InstrumentConfiguration():
    """
    Class for parsing valid instrument configurations from config.json files.
    This is primarily in aid of generating tests, but can be used for anything
    that needs to find valid instrument configurations.

    Given a telescope and instrument, class objects will expose the available
     modes.
    If a mode is set, the class object will expose available apertures and
     strategies for that mode.
    If an aperture is set as well, the class object will expose the valid
     filters, dispersers, readout patterns, and subarrays,

    The remainder of the instrument configuration is available as self.config

    Parameters
    ----------
    telescope: string
        Telescope defined in pandeia_refdata. Currently 'jwst', 'roman',
        or 'hst'
    instrument: string
        One of the instruments defined in pandeia_refdata.
    webapp: bool (True)
        Controls whether constraints are applied within a mode selection.
    """

    def __init__(self, telescope, instrument, webapp=True):

        self.instrument = instrument
        self.telescope = telescope
        self.data_dir = cf.default_refdata_directory
        with open('{0:}/{1:}/{2:}/config.json'.format(self.data_dir,self.telescope,self.instrument)) as config_file:
            self.config = json.load(config_file)
        with open('{0:}/{1:}/telescope/config.json'.format(self.data_dir,self.telescope)) as telconfig_file:
            self.telconfig = json.load(telconfig_file)
        self.webapp = webapp
        self.get_modes()

        self.configurables = ["modes", 
                              "apertures", 
                              "filters", 
                              "dispersers", 
                              "subarrays", 
                              "readout_patterns", 
                              "slits", 
                              "slitlets", 
                              "cenwaves",
                              "strategies"]

    def get_modes(self, types=None):
        self.modes = self.config['modes']
        if types is not None:
            oftype = []
            for modetype in types:
                oftype.extend(self.telconfig[modetype])
            self.modes = np.intersect1d(self.modes, oftype)

        return self.modes

    def set_mode(self, mode):
        self.mode = mode
        self.get_apertures()
        self.get_strategies()
        self.get_detectors()

    def get_detectors(self):
        self.detectors_all = self.config['detectors']

        if 'detectors' in self.config['mode_config'][self.mode]:
            self.detectors = self.config['mode_config'][self.mode]['detectors']
        else:
            self.detectors = self.detectors_all

        return self.detectors

    def set_detector(self, detector):
        self.detector = detector

        self._lookup('dispersers')
        self._lookup('filters')
        self._lookup('subarrays')
        self._lookup('readout_patterns')
        self._lookup('slits')
        self._lookup('cenwaves')
        if self.instrument == "nirspec":
            self._lookup('slitlets')
        if self.telescope == "hst":
            self._lookup('gain')

    def set_element(self, element, value):

        # A little handholding, if someone decides to try "set_element" on one of the special cases
        if element == "aperture":
            self.set_aperture(value)
        elif element == "detector":
            self.set_detector(value)
        elif element == "mode":
            self.set_mode(value)
        else:
            setattr(self,element,value)
            # now to parse all the potential side effects of setting this particular element
            if self.webapp:
                constraint = element
                for configurable in self.configurables:
                    # this syntax is unavoidably backwards: We ARE attempting to constrain the "configurable" quantity on the "constraint" that was called element here.
                    self.constrain(element=configurable, constrain_on=constraint)

    def get_apertures(self):
        self.apertures_all = self.config['apertures']

        if 'apertures' in self.config['mode_config'][self.mode]:
            self.apertures = self.config['mode_config'][self.mode]['apertures']
        else:
            self.apertures = self.apertures_all

        return self.apertures

    def set_aperture(self,aperture):
        self.aperture = aperture
        self._lookup('dispersers')
        self._lookup('filters')
        self._lookup('subarrays')
        self._lookup('readout_patterns')
        self._lookup('slits')
        self._lookup('cenwaves')
        if self.instrument == "nirspec":
            self._lookup('slitlets')
        if self.instrument == "nircam":
            if aperture[-2:] in ["sw", "lw"]:
                self.set_detector(aperture[-2:])
        if self.telescope == "hst":
            self._lookup('detectors')



    def _lookup(self,element):
        # remove comments from lookup table
        try:
            setattr(self,'{0:}_all'.format(element),[x for x in self.config[element] if x != "comment"])
        except KeyError:
            setattr(self,'{0:}_all'.format(element), [])

        if element in self.config['mode_config'][self.mode]:
            setattr(self,element,self.config['mode_config'][self.mode][element])
        else:
            # if it's not found in mode_config, use the base list
            setattr(self,element,getattr(self,'{0:}_all'.format(element)))

        # Web constraints will remove some more items
        if self.webapp:
            self.constrain(element=element)

        if getattr(self,element) == []:
            setattr(self,element,[None])

    def get_strategies(self):
        self.strategies = self.config['strategy_config'][self.mode]['permitted_methods']

        return self.strategies


    def constrain(self, element=None, constrain_on='aperture'):
        # Config Constraints lists dispersers in one of four ways:
        # Under apertures/dispersers/<mode>
        # Under apertures/dispersers/default if it applies to all modes but a particular one
        # Under apertures/dispersers if it applies to ALL modes
        # If unlisted, use the mode or global values.

        # NIRSpec also constrains by disperser.

        survivors = None
        constraint = '{0:}s'.format(constrain_on)
        # Three things required to do this:
        # 1. The configuration dictionary must have a config_constraints section
        # 2. The element to constrain on must be defined (for example, aperture)
        # 3. The element to constrain on must be in the config_constraints section (as, example, apertures)
        if 'config_constraints' in self.config:
            if hasattr(self,constrain_on):
                const = getattr(self,constrain_on)
                if constraint in self.config['config_constraints']:
                    if const in self.config['config_constraints'][constraint]:
                        if element in self.config['config_constraints'][constraint][const]:
                            if self.mode in self.config['config_constraints'][constraint][const][element]:
                                survivors = self.config['config_constraints'][constraint][const][element][self.mode]
                            elif "default" in self.config['config_constraints'][constraint][const][element]:
                                survivors = self.config['config_constraints'][constraint][const][element]['default']
                            else:
                                survivors = self.config['config_constraints'][constraint][const][element]

        # only actually set a new list if there's something worth setting.
        if survivors is not None:
            setattr(self,element,survivors)

    def waverange(self, waveelements=[]):
        '''
        Test of wavelengths: Test that every filter/disperser for a given aperture has a
         defined wavelength range
        Deliver the overall wavelength range for this aperture. Pandeia will expect that
         PSFs exist for the range produced by this routine and crash (in
         pandeia.engine.PSFLibrary) if they don't exist. The data sanity checker will
         check for such inconsistencies.
        '''
        minwave = 99999
        maxwave = 0

        if len(waveelements) != 0:
            for waveelement in waveelements:
                if waveelement in self.config['range'][self.aperture]:
                    if self.config['range'][self.aperture][waveelement]['wmax'] > maxwave:
                        maxwave = self.config['range'][self.aperture][waveelement]['wmax']
                    if self.config['range'][self.aperture][waveelement]['wmin'] < minwave:
                        minwave = self.config['range'][self.aperture][waveelement]['wmin']
                else:
                    if self.aperture in self.config['range']:
                        if 'wmax' in self.config['range'][self.aperture]:
                            if self.config['range'][self.aperture]['wmax'] > maxwave:
                                maxwave = self.config['range'][self.aperture]['wmax']
                            if self.config['range'][self.aperture]['wmin'] < minwave:
                                minwave = self.config['range'][self.aperture]['wmin']
                        else:
                            print('   Wavelengths for {0:} are missing!'.format(self.aperture))
                    else:
                        print('   Wavelengths for {0:} are missing!'.format(self.aperture))

        return minwave, maxwave

def clean(calc):
    # the following keys are specified in defaults but should not appear in tests
    for x in range(len(calc['scene'])):
        calc['scene'][x]['position'].pop('position_parameters',None)
        calc['scene'][x]['shape'].pop('shape_parameters',None)
        calc['scene'][x]['spectrum'].pop('spectrum_parameters',None)
    calc['configuration'].pop('max_filter_leak',None)
    calc['configuration'].pop('max_saturated_pixels',None)
    calc['configuration'].pop('max_scene_size',None)
    calc['configuration'].pop('min_snr_threshold',None)
    calc['configuration'].pop('scene_size',None)
    calc['configuration'].pop('dynamic_scene',None)

    # need to get the telescope from the instrument somehow
    tel = {"acs": "hst", "cos": "hst", "miri": "jwst", "nircam": "jwst", "niriss": "jwst", "nirspec": "jwst", "stis": "hst", "wfc3": "hst", "wfi": "roman"}

    # the default calculation now sets the strategy, which means there will be a reference wavelength set,
    # which might not be valid if the test generator changed the disperser.
    def_calc = build_default_calc(tel[calc['configuration']['instrument']['instrument']], calc['configuration']['instrument']['instrument'], calc['configuration']['instrument']['mode'], method=calc['strategy']['method'])
    if "reference_wavelength" in def_calc['strategy']:
        if def_calc['configuration']['instrument']['disperser'] != calc['configuration']['instrument']['disperser']:
            calc['strategy']["reference_wavelength"] = None

    return calc

def remove_duplicate(calcs,itemsvaried):
    # dictionaries can't be hashed, so the list of calculations can't be pared down with
    #  just list(set(calcs)). Instead, we take the values of the specific items being
    #  varied by the calculation, turn them into a long string, and pull the unique
    #  indices out of the list of strings. That set of indices can then be used to pare
    #  down the list of calcs.

    totalindex = []
    # for every calculation...
    for calc in calcs:
        # create an inner list to hold its properties
        calcindex = []
        # loop through all of the items varied
        for item in itemsvaried:
            entries = item.split('__')
            value = calc
            # recursively scan down to the actual value
            for entry in entries:
                try:
                    value = value[entry]
                except KeyError:
                    pass
            # Bad things happen if the value is a list
            if isinstance(value,list):
                value = '_'.join(np.array(value,dtype=str).flatten())
            # append the actual value to the list
            calcindex.append(str(value))
        calcstring = '_'.join(calcindex)
        totalindex.append(calcstring)
    # now totalindex lists the values of interest for every calculation
    # get the unique calculations
    indicies = np.unique(np.asarray(totalindex),return_index=True, axis=0)[1]

    return np.asarray(calcs)[indicies]
