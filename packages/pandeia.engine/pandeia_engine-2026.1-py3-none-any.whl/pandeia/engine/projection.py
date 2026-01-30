# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np

from .coords import Grid, IrregularGrid
from .utils import recursive_subclasses
from .custom_exceptions import EngineOutputError, EngineInputError

def ProjectionFactory(projection_type):
    """
    Function to take projection type and return the appropriate projection-dependent functions.

    Parameters
    ----------
    projection_type: string
        String with six valid values: "image", "image_scan", "spec", "slitless", 
        "slitless_scan", "multiorder".
    """

    types = recursive_subclasses(Projection)
    projections = [t.__name__.lower().replace('projection', '') for t in types]
    type_map = dict(list(zip(projections, types)))

    if projection_type not in projections:
        msg = "Unsupported or not yet implemented projection: %s" % projection_type
        raise EngineInputError(value=msg)
    else:
        cls = type_map[projection_type]()
        return cls


class Projection:
    """
    Abstract class with projection-type dependent code. Currently only includes 
    projection-dependent aspects of the Report class, but should eventually be expanded to 
    include projection-dependent parts of signal.py, noise.py, and possibly instrument.py

    Note that none of these correspond to the actual 2D results of the IFU projection type, 
    which technically isn't a projection as it reports the full scene cubes.

    It also does not include Coronagraphy, which (uniquely) has no background to subtract 
    from its _2d results.

    """

    def __init__(self):
        pass

    def _2d(self, extracted, saturation, signal):
        """
        2-D results from a generic projection

        Parameters
        ----------
        extracted : dict
            A Strategy output dictionary
        saturation : np.ndarray
            A 2d saturation bitmap
        signal : DetectorSignal
            DetectorSignal instance
        """

        self.signal = signal

        # Signal and noise in 2D. Get from extracted products
        s = extracted['detector_signal']
        n = extracted['detector_noise']
        t = extracted['detector_saturation']

        # This is the background rate in each pixel without sources
        self.bg_pix = signal.rate_plus_bg - signal.rate

        # The noise is undefined if the pixel is fully saturated.
        # The engine currently returns noise=0 if the pixel has full saturation, which is
        # confusing since the noise is not 0, but rather undetermined or infinite. Setting
        # the noise to NaN ensures that the S/N of saturated pixels are NaNs.
        n[t == 2] = np.nan
        self.detector_sn = (s - self.bg_pix) / n
        self.detector_signal = s + n * np.random.randn(n.shape[0], n.shape[1])
        self.saturation = t
        self.ngroups_map = extracted['detector_ngroups']


class ImageProjection(Projection):

    def _2d(self, extracted, saturation, signal):
        """
        Create the Imaging projection 2D products

        Parameters
        ----------
        extracted : dict
            A Strategy extraction dictionary
        saturation : np.ndarray
            2D saturation bitmap
        signal : DetectorSignal
            A DetectorSignal instance

        Returns
        -------
        dict
            Dict of 2D projection results
        """
        Projection._2d(self,extracted,saturation,signal)

        return {'detector': self.detector_signal, 'snr': self.detector_sn, 'saturation': self.saturation, \
                f'{signal.current_instrument.quanta}_map': self.ngroups_map}, self.bg_pix

    def _project(self, signal, extracted):
        """
        Return the Imaging projection products

        Parameters
        ----------
        signal : DetectorSignal
            A DetectorSignal object
        extracted : dict
            A Strategy extraction dictionary

        Returns
        -------
        grid: CoordinateGrid or IrregularGrid
            The observation's *Grid instance
        wave_pix: np.ndarray
            The observation's detector wavelength grid
        pixgrid: CoordinateGrid or IrregularGrid
            The pixel grid instance.
        """

        return signal.grid, signal.wave_pix, signal.pixgrid_list[0]

class Image_ScanProjection(ImageProjection):
    pass
class SpecProjection(Projection):

    def _2d(self, extracted, saturation, signal):
        """
        Create the Spec projection 2D products. Y-dispersed spectra will need to be
        rotated into the X-axis; X-dispersed spectra merely need to be mirrored vertically
        to the correct orientation.

        Parameters
        ----------
        extracted : dict
            A Strategy extraction dictionary
        saturation : np.ndarray
            2D saturation bitmap
        signal : DetectorSignal
            A DetectorSignal instance

        Returns
        -------
        dict
            Dict of 2D projection results
        """
        Projection._2d(self,extracted,saturation,signal)

        if self.signal.dispersion_axis == 'y':
            if self.signal.current_instrument.instrument["disperser"] in ["p750l", "prism"]:
                # y-dispersed spectra need to be flipped vertically.
                det_signal = self.detector_signal[::-1,:]
                det_sn = self.detector_sn[::-1,:]
                det_sat = self.saturation[::-1,:]
                det_groups = self.ngroups_map[::-1,:]
            else:
                # where projection is slitless and axis is y (and not the MIRI p750l disperser or Roman WFI dispersers)
                # need to rotate these 90 deg clockwise to match our normal axis orientation. np.rot90 only works CCW
                # so we need to rotate 3 times.
                det_sn = np.rot90(self.detector_sn, 3)[::-1,:]
                det_signal = np.rot90(self.detector_signal, 3)[::-1,:]
                det_sat = np.rot90(self.saturation, 3)[::-1,:]
                det_groups = np.rot90(self.ngroups_map, 3)[::-1,:]
        else: 
            # this correctly applies to both x and -y dispersion (only used by Roman WFI Spectroscopy as of 2025-11-19)
            det_signal = self.detector_signal
            det_sn = self.detector_sn
            det_sat = self.saturation
            det_groups = self.ngroups_map

        return {'detector_unrotated': self.detector_signal, 'snr_unrotated': self.detector_sn, \
                'saturation_unrotated': self.saturation, f'{signal.current_instrument.quanta}_map_unrotated': self.ngroups_map, \
                'detector':det_signal, 'snr':det_sn, 'saturation':det_sat, f'{signal.current_instrument.quanta}_map': det_groups}, \
               self.bg_pix

    def _project(self, signal, extracted):
        """
        Return the Spec projection products

        Parameters
        ----------
        signal : DetectorSignal
            A DetectorSignal object
        extracted : dict
            A Strategy extraction dictionary

        Returns
        -------
        grid: CoordinateGrid or IrregularGrid
            The observation's *Grid instance
        extracted_wavelength: np.ndarray
            The observation's detector wavelength grid
        pixgrid: CoordinateGrid or IrregularGrid
            The output pixel grid instance.
        """

        return signal.grid, extracted['wavelength'], signal.pixgrid_list[0]


class SlitlessProjection(Projection):

    def _2d(self, extracted, saturation, signal):
        """
        Create the Slitless projection 2D products. Y-dispersed spectra
        will need to be rotated into the X-axis; X-dispersed spectra merely need to be
        mirrored vertically to the correct orientation.

        Parameters
        ----------
        extracted : dict
            A Strategy extraction dictionary
        saturation : np.ndarray
            2D saturation bitmap
        signal : DetectorSignal
            A DetectorSignal instance

        Returns
        -------
        dict
            Dict of 2D projection results
        """

        Projection._2d(self,extracted,saturation,signal)

        if self.signal.dispersion_axis == 'y':
            if self.signal.current_instrument.instrument["disperser"] in ["p750l", "prism"]:
                # y-dispersed spectra need to be flipped vertically.
                det_signal = self.detector_signal[::-1,:]
                det_sn = self.detector_sn[::-1,:]
                det_sat = self.saturation[::-1,:]
                det_groups = self.ngroups_map[::-1,:]
            else:
                # where projection is slitless and axis is y (and not the MIRI p750l disperser)
                # need to rotate these 90 deg clockwise to match our normal axis orientation. np.rot90 only works CCW
                # so we need to rotate 3 times.
                det_sn = np.rot90(self.detector_sn, 3)[::-1,:]
                det_signal = np.rot90(self.detector_signal, 3)[::-1,:]
                det_sat = np.rot90(self.saturation, 3)[::-1,:]
                det_groups = np.rot90(self.ngroups_map, 3)[::-1,:]
        else:
            # this correctly applies to both x and -y dispersion (only used by Roman WFI Spectroscopy as of 2025-11-19)
            det_signal = self.detector_signal
            det_sn = self.detector_sn
            det_sat = self.saturation
            det_groups = self.ngroups_map

        return {'detector_unrotated': self.detector_signal, 'snr_unrotated': self.detector_sn, \
                'saturation_unrotated': self.saturation, f'{signal.current_instrument.quanta}_map_unrotated': self.ngroups_map, \
                'detector':det_signal, 'snr':det_sn, 'saturation':det_sat, f'{signal.current_instrument.quanta}_map': det_groups}, \
               self.bg_pix

    def _project(self, signal, extracted):
        '''
        This function handles (almost) all projection-type dependent factors (which are independent of strategy)
        This primarily includes wave_pix and pix_grid.

        The 2D projection types for slitless are handled in _2d()

        Parameters
        ----------
        signal : DetectorSignal
            A DetectorSignal object
        extracted : dict
            A Strategy extraction dictionary

        Returns
        -------
        grid: CoordinateGrid or IrregularGrid
            The observation's *Grid instance
        wave_pix: np.ndarray
            The observation's detector wavelength grid
        pix_grid: CoordinateGrid or IrregularGrid
            The output pixel grid instance.
        '''
        # this is the spatial grid for the calculation. It needs to be added as an attribute for the
        # common/scene/coordinates tests to work.
        grid = signal.grid
        wave_pix = extracted['wavelength']
        if signal.dispersion_axis == 'y': # does not apply to the -y axis.
            wave_pix = wave_pix[::-1]
        # this is the detector plane pixel grid. for most modes we just grab and use it directly.
        # however, slitless we want to redefine it to be spatial on both axes.
        orig_grid = signal.pixgrid_list[0]
        # detector plane gets rotated depending on dispersion_axis so adjust accordingly
        if signal.dispersion_axis == 'x' or signal.current_instrument.instrument["disperser"] in ["p750l", "grism", "prism"]:
            pix_grid = Grid(grid.xsamp, orig_grid.ysamp, orig_grid.nx, orig_grid.ny)
        else:
            pix_grid = Grid(grid.ysamp, orig_grid.xsamp, orig_grid.ny, orig_grid.nx)

        return grid, wave_pix, pix_grid

class Slitless_ScanProjection(SlitlessProjection):
    pass

class MultiorderProjection(SlitlessProjection):

    def _2d(self, extracted, saturation, signal):
        """
        Create the Multiorder projection 2D products. Y-dispersed spectra will need to be
        rotated into the X-axis but the rotation is different from slitless. We currently
        have no X-dispersed multiorder spectra.

        Parameters
        ----------
        extracted : dict
            A Strategy extraction dictionary
        saturation : np.ndarray
            2D saturation bitmap
        signal : DetectorSignal
            A DetectorSignal instance

        Returns
        -------
        dict
            Dict of 2D projection results
        """
        Projection._2d(self,extracted,saturation,signal)
        
        return {'detector_unrotated': self.detector_signal, 'snr_unrotated': self.detector_sn, \
                'saturation_unrotated': self.saturation, f'{signal.current_instrument.quanta}_map_unrotated': self.ngroups_map, \
                'detector':np.rot90(self.detector_signal), 'snr':np.rot90(self.detector_sn),
                'saturation':np.rot90(self.saturation), f'{signal.current_instrument.quanta}_map': np.rot90(self.ngroups_map)}, self.bg_pix

    def _project(self, signal, extracted):
        '''
        This function handles (almost) all projection-type dependent factors (which are independent of strategy)
        This primarily includes wave_pix and pix_grid.

        The 2D projection types for multiorder are handled in _2d()

        Parameters
        ----------
        signal : DetectorSignal
            A DetectorSignal object
        extracted : dict
            A Strategy extraction dictionary

        Returns
        -------
        grid: CoordinateGrid or IrregularGrid
            The observation's *Grid instance
        wave_pix: np.ndarray
            The observation's detector wavelength grid
        pix_grid: CoordinateGrid or IrregularGrid
            The output pixel grid instance.
        '''
        # this is the spatial grid for the calculation. It needs to be added as an attribute for the
        # common/scene/coordinates tests to work.
        grid = signal.grid
        # this is the wavelength sampling on the detector.
        wave_pix = extracted['wavelength']  # this is already a 1D np.array

        orig_grid = signal.pixgrid_list[0]
        pix_grid = IrregularGrid(np.arange(orig_grid.nx,0,-1), np.arange(orig_grid.ny))

        return grid, wave_pix, pix_grid
