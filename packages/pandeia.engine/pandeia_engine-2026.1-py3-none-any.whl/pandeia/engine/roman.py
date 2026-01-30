# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import numpy as np
import scipy.sparse as sparse
from astropy.io import fits

from .telescope import Telescope
from .instrument import Instrument
from .custom_exceptions import EngineInputError, DataError, UnsupportedError
from .pandeia_warnings import instrument_warning_messages

class Roman(Telescope):

    """
    Roman-specific methods
    """
    def get_ote_eff(self, wave):
        """
        Get efficiency of the telescope optics, the OTE. For Roman, this is included in
        the filter and disperser throughput files.

        Parameters
        ----------
        wave: numpy.ndarray
            Wavelength vector to interpolate OTE efficiency onto

        Returns
        -------
        ote: numpy.ndarray or float
            If file exists, return ote_efficiency(wave). Else return 1.0.
        """

        return 1.0


class RomanInstrument(Instrument):

    """
    Generic Roman Instrument class
    """

    def __init__(self, mode=None, config={}, **kwargs):
        if "telescope_custom" in kwargs:
            kwargs = kwargs["telescope_custom"]
        telescope = Roman(**kwargs)
        # these are the required sections and need to be passed via API in webapp mode
        self.instrument_pars = {}
        self.instrument_pars['detector'] = ["nexp", "nresultants", "ma_table_name", "subarray"]
        self.instrument_pars['instrument'] = ["aperture", "disperser", "filter", "instrument", "mode", "detector"]
        self.api_parameters = list(self.instrument_pars.keys())
        self.quanta = "nresultants"

        # these are required for calculation, but ok to live with config file defaults
        self.api_ignore = ['dynamic_scene', 'max_scene_size', 'scene_size']

        Instrument.__init__(self, telescope=telescope, mode=mode, config=config, **kwargs)


class WFI(RomanInstrument):

    """
    Currently, the Roman WFI requires only one method beyond those provided by the generic
    Instrument class

    This is also the optimal place to check agreement of MA table and mode, and to
    implement the nresultants=-1 special behavior.
    """
    def __init__(self, mode=None, config={}, webapp=False, **kwargs):

        # We will stick with our own terminology, but allow for someone simply using "optical_element"
        # If present, it supercedes filter and disperser.
        if "optical_element" in config["instrument"]:
            if config["instrument"]["mode"] == "imaging":
                config["instrument"]["filter"] = config["instrument"]["optical_element"]
                config["instrument"]["disperser"] = None
            elif config["instrument"]["mode"] == "spectroscopy":
                config["instrument"]["disperser"] = config["instrument"]["optical_element"]
                config["instrument"]["filter"] = None

        RomanInstrument.__init__(self, mode=mode, config=config, webapp=webapp, **kwargs)

        if config["instrument"]["mode"] == "imaging" and config["instrument"]["filter"] not in self.filters:
            raise EngineInputError(f'Invalid filter: {config["instrument"]["filter"]}')
        elif config["instrument"]["mode"] == "spectroscopy" and config["instrument"]["disperser"] not in self.dispersers:
            raise EngineInputError(f'Invalid disperser: {config["instrument"]["disperser"]}')

        # Mixing the MA tables will not be allowed, so it should error.
        if self.instrument["mode"] == "imaging" and "wim" not in self.the_detector.exposure_spec.ma_table["observing_mode"]:
            raise EngineInputError(f"Invalid MA table {self.the_detector.exposure_spec.ma_table_name} for imaging.")
        if self.instrument["mode"] == "spectroscopy" and "wsm" not in self.the_detector.exposure_spec.ma_table["observing_mode"]:
            raise EngineInputError(f"Invalid MA table {self.the_detector.exposure_spec.ma_table_name} for spectroscopy.")
        
        if not self.no_psf:
            self._loadpsfs()

        # catch invalid number of resultants
        if self.the_detector.exposure_spec.nresultants < self.the_detector.exposure_spec.min_resultants:
            key = "roman_min_resultants"
            self.warnings[key] = instrument_warning_messages[key].format(self.the_detector.exposure_spec.nresultants, self.the_detector.exposure_spec.min_resultants)
        #TODO: Remove code once nresultants==1 is a valid choice (JETC-4209)
        if self.the_detector.exposure_spec.nresultants == 1:
            key = "roman_one_resultant"
            self.warnings[key] = instrument_warning_messages[key].format()


    def _get_disperser(self):
        """
        The same disperser can have different configurations depending on which order is
        being used. Use self.order to build a new key for looking up configuration data for the
        given order.

        Returns
        -------
        key: str
            Key to look up order-specific configuration data
        """
        key = f"{self.instrument['detector']}_{self.instrument['disperser']}"
        if self.order is not None:
            key = "%s_%d" % (key, self.order)
            key = key.replace('-','m')
        return key
    
    def get_filter_eff(self, wave):
        """
        Read in filter throughput curve

        Parameters
        ----------
        wave: numpy.ndarray
            Wavelength vector to interpolate throughput onto

        Returns
        -------
        eff: numpy.ndarray or float
            Filter throughput as a function of wave
        """
        key = f"{self.instrument['detector']}_{self.instrument['filter']}"
        eff = self._get_throughput(wave, key)
        return eff

    def get_internal_eff(self, wave, full_throughput=False):
        """
        Roman's internal efficiency is included in the filter and disperser throughput files

        Parameters
        ----------
        wave: numpy.ndarray
            Wavelength vector to interpolate throughput onto
        full_throughput: bool
            Controls whether certain instrument-specific variants use special behavior.

        Returns
        -------
        eff: numpy.ndarray or float
            Internal throughput as a function of wave
        """
        eff = np.ones_like(wave)
        return eff

    def get_detector_qe(self, wave):
        """
        Roman's detector quantum efficiency is included in the filter and disperser throughput files

        Parameters
        ----------
        wave: numpy.ndarray
            Wavelength vector to interpolate throughput onto

        Returns
        -------
        qe: numpy.ndarray or float
            Quantum efficiency as a function of wave
        """
        qe = np.ones_like(wave)
        return qe

    def _loadpsfs(self):
        """
        As of STPSF 2.1.0 (JETC-5181), all filters and dispersers have their own pupil masks.
        Because the ranges overlap, we need to switch between PSF libraries.
        The mask is attached to the actual glass, so selecting by filter seems appropriate
        """
        if self.instrument['mode'] == 'imaging':
            psf_key = f"{self.instrument['detector']}imaging{self.instrument['filter']}"
        elif self.instrument['mode'] == 'spectroscopy':
            psf_key = f"{self.instrument['detector']}spectroscopy{self.instrument['disperser']}"
        else:
            message = "Invalid mode specification: {}".format(str(self.instrument['mode']))
            raise EngineInputError(value=message)

        self.psf_library = self._load_psf_library(psf_key)


    def get_readnoise_correlation_matrix(self, shape):
        """
        Grab correlated readnoise data out of reference file and build a correlation
        matrix out of it.

        Roman's correlation matrix is a single fixed array; it does not vary by number of
        resultants or number of frames.

        Parameters
        ----------
        shape: list-like

        Returns
        -------
        correlation_matrix: Scipy.sparse.csr_matrix
            Compressed sparse row correlation matrix
        """
        key = "rn_corr"
        correlation_file = os.path.join(self.ref_dir, self.paths[key])
        try:
            correlation = fits.getdata(correlation_file)
        except IOError as e:
            msg = "Error reading RN correlation reference file: %s. " % correlation_file
            if self.webapp:
                msg += "(%s)" % type(e)
            else:
                msg += repr(e)
            raise DataError(value=msg)

        nx = correlation.shape[1]
        ny = correlation.shape[0]

        if nx != ny:
            message = 'Only square correlation matrices are supported.'
            raise UnsupportedError(value=message)

        correlation_data = sparse.csr_matrix(correlation[:, :], dtype=np.float32)

        empty_matrix = sparse.coo_matrix((1024, 1024))
        correlation_matrix = sparse.bmat([[empty_matrix, None, empty_matrix],
                                          [None, correlation_data, None],
                                          [empty_matrix, None, empty_matrix]])
        correlation_matrix = sparse.csr_matrix(correlation_matrix)

        return correlation_matrix


class IFU(RomanInstrument):

    """
    Currently the Roman IFU (deprecated) requires no extra methods beyond those provided by the generic Instrument class
    """
    pass
