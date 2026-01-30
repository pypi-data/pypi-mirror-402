import os

import numpy as np
import astropy.units as u
from astropy.io import ascii
from astropy.coordinates import SkyCoord

from pandeia.engine.custom_exceptions import BackgroundError

def target_visibility(ra, dec, date, ra_dec_str, date_str):
    with open(f'{os.environ["SL_CACHE_DIR"]}/{os.environ["ROMAN_EPHEMERIS"]}') as infile:
        ephemfile = infile.readlines()
        # find the data block. Astropy cannot read this format, so we have to reformat manually.
        startidx = [idx for idx in range(len(ephemfile)) if "$$SOE" in ephemfile[idx]][0]
        endidx = [idx for idx in range(len(ephemfile)) if "$$EOE" in ephemfile[idx]][0]
        # header. Astropy can't read it in itself due to the last column being null.
        # Stripping strings manually is both necessary and makes it an empty string.
        header = [x.strip() for x in ephemfile[startidx-2].split(",")]
        # the data
        ephemtable = ephemfile[startidx+1:endidx]
    # now read in just the specific columns we're interested in.
    ephem = ascii.read(ephemtable, names=header, include_names=["JDTDB", "X", "Y", "Z"])
  
    date += 2451545.5
    idx = np.where(ephem["JDTDB"] == date)[0]
    # the ephemeris position vectors are all sun->spacecraft; we need the reverse 
    # jwst_tvt.py sun_position_vectors()
    coordx = ephem["X"][idx] * -1
    coordy = ephem["Y"][idx] * -1
    coordz = ephem["Z"][idx] * -1
    mag = (coordx**2 + coordy**2 + coordz**2)**0.5

    # convert the sun vectors into spherical projection 
    # jwst_tvt.py sun_position_coordinates()
    sundec = np.arcsin(coordz/mag)
    sunra = np.arctan2(coordy/mag, coordx/mag)

    # now get the angle between target and sun. We'll use SkyCoord for this.
    sun = SkyCoord(ra=sunra*u.rad, dec=sundec*u.rad)
    target = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)

    sep = target.separation(sun)

    # Now do the test. Throw an error if the target is closer to the Sun than the value of
    # ROMAN_REGARD.
    regard_min,regard_max = os.environ["ROMAN_REGARD"].split(",")
    if (sep.to_value(u.degree) < float(regard_min)) or sep.to_value(u.degree) > float(regard_max):
        msg = 'Specified position ({}) is not observable on {}.'.format(ra_dec_str, date_str)
        raise BackgroundError(msg)
