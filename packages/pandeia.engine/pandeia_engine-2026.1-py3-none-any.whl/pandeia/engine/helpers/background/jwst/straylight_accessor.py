import os
telescope = os.environ.get("ETC_TELESCOPE", "jwst").lower()

import numpy as np

from pandeia.engine.helpers.background.multimission.mod_healpix_func import ang2pix_ring
import pandeia.engine.helpers.background.multimission.accessor_globals as glb
from pandeia.engine.helpers.background.multimission.accessor_funcs import nonzodi_pix_dtype, zodi_sl_dtype
from pandeia.engine.custom_exceptions import StraylightPositionError
from pandeia.engine.custom_exceptions import StraylightDataError

def get_stray_light_bg(ra, dec, mjd2000, ra_dec_str, date_str):
    """
    Provides equivalent straylight background spectra for pointing and mjd2000.

    Parameters
    ----------
    ra : double
        Right Ascension [degrees]
    dec : double
        declination [degrees]
    mjd2000 : int
        Modified Julian Day 2000
    ra_dec_str: str
        String representation of RA and DEC (for sexigesimal in messages)
    date_str: str
        String representation of date (for Gregorian calendar dates)

    Returns
    -------
    tuple of:
    wave : numpy.ndarray
        Wavelengths of background values [microns]
    stray_light_bg : numpy.ndarray
        Equivalent in field background from the scattered zodi, ism, cbi, stellar.

    If the target is not in the Field of Regard on iday, then an exception is raised.
    """

    # Cache is based on DOY 2020 so convert MJD2000 to DOY.
    # 51544 is Jan 1, 2000
    iday = int(float(mjd2000) % 365.25) + 1

    # Find the HEALPix number and the subdirectory
    ipix = ang2pix_ring(glb.nside, ra*glb.D2R, dec*glb.D2R)
    ipix_dir = ipix // 100

    # Set up the numpy arrays
    wave = np.array(glb.wavelist, dtype='double')

    sl_path = os.environ['SL_CACHE_DIR']
    file_name = "%s/%04d/sl_pix_%06d.bin" % (sl_path, ipix_dir, ipix)
    if not os.path.exists(file_name):
        msg = 'Stray light data is not available for position (%s) on %s.' % (ra_dec_str, date_str)
        raise StraylightDataError(msg)
    nonzodi_bg = np.fromfile(file_name, dtype=nonzodi_pix_dtype, count=1)
    iday_pt = nonzodi_bg['iday_index'][0][iday-1]
    if iday_pt == -1:
        msg = 'Specified position ({}) is not observable on {}.'.format(ra_dec_str, date_str)
        if telescope == 'jwst':
              msg += '\nUse of the ' \
              '<a href="https://jwst-docs.stsci.edu/jwst-other-tools/jwst-target-visibility-tools/jwst-general-target-visibility-tool-help" '\
              'target="_blank">General Target Visibility Tool (GTVT)</a> is recommended for determining the visibility'\
              ' of the specified position on the specified date'
        raise StraylightPositionError(msg)
    zodi_sl_bgs = np.memmap(
        file_name,
        offset=nonzodi_pix_dtype.itemsize + zodi_sl_dtype.itemsize * iday_pt,
        mode='r',
        dtype=zodi_sl_dtype
    )
    stray_light_bg = np.array(zodi_sl_bgs['stray_light_bg'][0], dtype='double')
    return (wave, stray_light_bg)
