# Licensed under a 3-clause BSD style license - see LICENSE.rst

import itertools

import numpy as np
import numpy.ma as ma
from .custom_exceptions import EngineInputError, DataError

class ExposureSpec:
    """
    Parent class for all exposure times, MultiAccum and SingleAccum
    """
class ExposureSpec_MultiAccum(ExposureSpec):
    """
    Parent class for MultiAccum
    """

    def __init__(self, config={}, webapp=False, **kwargs):
        """
        Create a generic Exposure Specification.

        Inputs
        ------
        config: dict
            dictionary of detector configuration setups

        webapp: bool
            Switch to toggle strict API checking
            
        **kwargs: keyword/value pairs
            Additional configuration data
        """
        self.webapp = webapp

        # Required parameters
        self.readout_pattern = config["input_detector"]["readout_pattern"]
        self.subarray = config["input_detector"]["subarray"]
        self.ngroup = config["input_detector"]["ngroup"]
        self.nint = config["input_detector"]["nint"]
        self.nexp = config["input_detector"]["nexp"]
        self.nsuperstripe = config["subarray"]["default"][self.subarray]["nsuperstripe"]
        self.tframe = config["subarray"]["default"][self.subarray]["tframe"]
        self.tfffr = config["subarray"]["default"][self.subarray]["tfffr"]
        if self.readout_pattern in config["subarray"] and self.subarray in config["subarray"][self.readout_pattern]:
            self.tframe = config["subarray"][self.readout_pattern][self.subarray]["tframe"]
            self.tfffr = config["subarray"][self.readout_pattern][self.subarray]["tfffr"]

        # these errors specifically name the properties by their engine 
        # internal name; the client will catch errors for the web interface 
        # and thus the engine will never trigger this for web users. 
        # (JETC-1957)
        if not isinstance(self.ngroup, int):
            raise EngineInputError("ngroups must be an integer, got {}".format(type(self.ngroup)))
        if not isinstance(self.nint, int):
            raise EngineInputError("nint must be an integer, got {}".format(type(self.nint)))
        if not isinstance(self.nexp, int):
            raise EngineInputError("nexp must be an integer, got {}".format(type(self.nexp)))

        # Optional parameters
        # These are defined by the Instrument's reference data as Instrument properties.
        self.nframe = config["readout_pattern_config"][self.readout_pattern]["nframe"]
        self.ndrop2 = config["readout_pattern_config"][self.readout_pattern]["ndrop2"]

        self.nprerej = config["detector_config"]["nprerej"]
        self.npostrej = config["detector_config"]["npostrej"]
        # Going from general to specific: start with the default reset values, then check the defaults, then check
        # the actual readout pattern for this subarray. Use the most appropriate reset values for this setup, otherwise
        # the defaults
        self.nreset1 = 1
        self.nreset2 = 1
        if "nreset1" in config["subarray"]["default"][self.subarray]:
            self.nreset1 = config["subarray"]["default"][self.subarray]["nreset1"]
            self.nreset2 = config["subarray"]["default"][self.subarray]["nreset2"]
        if self.readout_pattern in config["subarray"] and self.subarray in config["subarray"][self.readout_pattern]:
            if "nreset1" in config["subarray"][self.readout_pattern][self.subarray]:
                self.nreset1 = config["subarray"][self.readout_pattern][self.subarray]["nreset1"]
                self.nreset2 = config["subarray"][self.readout_pattern][self.subarray]["nreset2"]
        if "nreset1" in config["readout_pattern_config"][self.readout_pattern]:
            self.nreset1 = config["readout_pattern_config"][self.readout_pattern]["nreset1"]
            self.nreset2 = config["readout_pattern_config"][self.readout_pattern]["nreset2"]


        # These are never specified in our data, currently; they were always the default
        # value from the ExposureSpec __init__ signature.
        if "ndrop1" in config["readout_pattern_config"][self.readout_pattern]:
            self.ndrop1 = config["readout_pattern_config"][self.readout_pattern]["ndrop1"]
        else:
            self.ndrop1 = 0
        if "ndrop3" in config["readout_pattern_config"][self.readout_pattern]:
            self.ndrop3 = config["readout_pattern_config"][self.readout_pattern]["ndrop3"]
        else:
            self.ndrop3 = 0
        self.frame0 = False
        if "frame0" in config["subarray"]["default"][self.subarray]:
            self.frame0 = config["subarray"]["default"][self.subarray]["frame0"]
        if self.readout_pattern in config["subarray"] and self.subarray in config["subarray"][self.readout_pattern]:
            if "frame0" in config["subarray"][self.readout_pattern][self.subarray]:
                self.nreset1 = config["subarray"][self.readout_pattern][self.subarray]["frame0"]

        # If these are trivial, we don't have to define them.
        if "nsample" in config["readout_pattern_config"][self.readout_pattern]:
            self.nsample = config["readout_pattern_config"][self.readout_pattern]["nsample"]
            self.nsample_skip = config["readout_pattern_config"][self.readout_pattern]["nsample_skip"]
        else:
            self.nsample = 1
            self.nsample_skip = 0

        # Target acqs only use a subset of the groups
        if "ngroup_extract" in config["input_detector"]:
            self.ngroup_extract = config["input_detector"]["ngroup_extract"]

        self.get_times()

        # Derived quantities
        self.nramps = self.nint * self.nexp

    def get_times(self):
        """
        The time formulae are defined in Holler et al. 2021, JWST-STScI-006013-A. Note
        that we have to subtract the groups that are rejected (by the pipeline) from the
        measurement time (nprerej+npostrej). The saturation time conservatively considers
        the ramp saturated even if saturation occurs in a rejected frame.

        Also note that these equations are generic, suitable for both H2RG and SiAs
        detectors.

        The equations in this method are duplicated in the front-end (workbook.js,
        update_detector_time_labels function). Please ensure that changes to these
        equations are reflected there.
        """

        self.tgroup = self.tframe * (self.nframe + self.ndrop2)

        # MIRI measurement time for ngroups < 5 is now handled with dropframes
        # This reduces to Equation 3 for H2RG detectors and Equation 5 for SiAs detectors.
        if self.ngroup == 1:
            # in the special case of a single group, the measurement is between the
            # superbias frame and the end of the only group (JETC-3290)
            self.measurement_time = self.nint * self.tframe * self.nsuperstripe * self.ngroup * \
                                    (self.nframe + self.ndrop2)
        else:
            self.measurement_time = self.nint * self.tframe * self.nsuperstripe * (self.ngroup - 1 - self.nprerej - self.npostrej) * \
                                    (self.nframe + self.ndrop2)
        # Equation 4
        if self.frame0:
            self.measurement_time += 0.5 * self.nint * self.tframe * (self.nframe - 1)

        # Equation 1, which naturally simplifies to Equation 2 for SiAs detectors.
        self.exposure_time = (self.tfffr * self.nint * self.nsuperstripe) + \
                              self.tframe * self.nsuperstripe * ( \
                                    self.nreset1 + \
                                        (self.nint - 1) * self.nreset2 + \
                                    self.nint * (
                                        self.ndrop1 + \
                                        (self.ngroup - 1) * (self.nframe + self.ndrop2) + \
                                        self.nframe + \
                                        self.ndrop3 )
                                )

        # Equation 6, which reduces to Equation 7 for SiAs detectors.
        self.saturation_time = self.tframe * \
                                (
                                    self.ndrop1 + \
                                    (self.ngroup - 1) * (self.nframe + self.ndrop2) + 
                                    self.nframe
                                )

        self.duty_cycle = self.saturation_time * self.nint / self.exposure_time
        self.total_exposure_time = self.nexp * self.exposure_time
        self.exposures = self.nexp

        self.total_integrations = self.nexp * self.nint

        # add photon collect time
        self.photon_collect = self.saturation_time * self.nint * self.nexp * self.nsuperstripe

class ExposureSpec_H2RG(ExposureSpec_MultiAccum):

    pass


class ExposureSpec_SiAs(ExposureSpec_MultiAccum):

    def get_times(self):
        """
        SiAs detectors obey the time formulae defined in Holler et al. 2021,
        JWST-STScI-006013-A. They need two additional values defined, which we compute
        here.
        """
        super().get_times()

        # This is where we adjust values so we can still use the same
        # MULTIACCUM formula as for the NIR detectors. We need the effective
        # "average time per sample" for MIRI.
        self.tsample = self.tframe / (self.nsample + self.nsample_skip)
        # 'nsample_total' for MIRI is the total number of non-skipped samples X number of
        # averaged frames. Note that in practice, it currently never happens that both the
        # number of samples and number of averaged frames are >1 (i.e., no SLOWGRPAVG
        # exists). However, this will deal with that situation, should it occur.
        self.nsample_total = self.nframe * self.nsample


class ExposureSpec_UnevenMultiAccum(ExposureSpec):

    def __init__(self, config={}, webapp=False, **kwargs):
        """
        Create a generic UnevenMultiAccum Exposure Specification.

        Inputs
        ------
        config: dict
            dictionary of detector configuration setups

        webapp: bool
            Switch to toggle strict API checking
            
        **kwargs: keyword/value pairs
            Additional configuration data
        """
        self.webapp = webapp

        # Required parameters
        self.ma_table_name = config["input_detector"]["ma_table_name"].lower()
        self.subarray = config["input_detector"]["subarray"]
        self.nresultants = config["input_detector"]["nresultants"]
        self.nexp = config["input_detector"]["nexp"]
        
        try:
            self.ma_table = config["readout_pattern_config"][self.ma_table_name]
        except KeyError:
            raise EngineInputError(f"Invalid MA Table name: {self.ma_table_name}")

        self.tframe = self.ma_table["frame_time"]
        self.treset = self.ma_table["reset_frame_time"]

        self.pre_science = self.ma_table["num_pre_science_resultants"]
        # Lots of complicated logic in here to set up the variables we need; put it in a
        # different function.
        self._enumerate_pattern()

        self.max_resultants = self.ma_table["num_science_resultants"]
        self.min_resultants = self.ma_table["min_science_resultants"]
        # Allow a simple "maximum number of resultants" option
        if self.nresultants == -1:
            self.nresultants = self.max_resultants

        if self.nresultants > self.max_resultants:
            raise EngineInputError(f"MA Table {self.ma_table_name} supports a maximum of {self.max_resultants} resultants.")
        if self.nresultants < 1:
            raise EngineInputError(f"MA Table {self.ma_table_name} supports a minimum of {self.min_resultants} resultants.")
        
        # create arrays truncated to the number of resultants requested.
        try:
            self.readout_pattern = self.readout_pattern_full[:self.nresultants] # we consider the pre-science resultants to be part of the resultants.
            self.readout_cum_time = self.readout_cum_time_full[:self.nresultants]
            self.readout_frametimes = self.readout_frametimes_full[:self.nresultants]
        except TypeError:
            raise EngineInputError(f"Number of resultants ({self.nresultants}) must be an integer.")
        # there aren't truncated versions of the _flat arrays because our current
        # application does not require them.

        self.max_total_samples = self.readout_pattern_full[-1][-1]
        self.max_samples = self.readout_pattern[-1][-1]

        # Get number of reads in each resultant
        self.nreads = np.array([len(i) for i in self.readout_pattern])
        # Get total number of frames (read and unread) in each resultant
        self.lastframe = [i[-1] for i in self.readout_pattern]
        self.lastframe_full = [i[-1] for i in self.readout_pattern_full]
        self.ntotal = np.append(len(self.readout_pattern[0]), np.diff(self.lastframe))

        self.get_times()

    def _enumerate_pattern(self):
        """
        Given an MA Table pattern description, write out the list of resultants and frames
        in each resultant

        The fundamental unit of Roman readouts is time, so make time arrays. There are
        three fundamental types of array we need here: 
        1. The full pattern of frames 
        2. The full pattern of cumulative frame times, equivalent to
           time_since_reset_read, but for every single frame
        3. A 1D array with the frame time associated with each resultant (assumption is 
           that it's uniform within the resultant)

        Additionally, we need each of those parameters in three different ways: 
        1. The full pattern, comprised of every read frame, divided into resultants (for
           some statistics, and the resultants_before_saturation plot) 
        2. The truncated pattern, comprised of every read frame within the resultants that
           will be used, divided into resultants (for exposure time and noise
           calculations) 
        3. The full flattened pattern of ALL frames taken (for determining saturation and
           cosmic rays). This is not merely a flattened version of (1), because it 
           includes even skipped frames that are not read out.
        (4. The truncated flattened pattern of all frames taken up to a point. This code 
            does not need them, so they were not created.)

        Not all of them are guaranteed to be used in the ETC noise code.

        readout_pattern_flat_full and readout_cum_time_flat_full are used in 
        Detector._frames_before_sat(). readout_cum_time_full is used by the ramp plot 
        maker

        Returns
        -------
        readout_pattern: list
            A list of resultants, where each resultant is a list of consitituent frames.
        """

        # The fundamental unit of Roman readouts is time. Make time arrays.
        # There are three things to consider here:
        # 1. How many resets and reference frames are taken?
        # 2. For each of them, are they downlinked as a resultant?
        # 3. Is the reference frame a ResetReference?


        self.readout_pattern_full = []
        readout_time_full = []
        self.readout_cum_time_full = []
        self.readout_pattern_flat_full = []
        self.readout_cum_time_flat_full = []
        self.readout_frametimes_full = []

        self.nreset = 0
        self.nreference = 0
        self.treference = 0
        pre_science_cum_time = 0
    
        if len(self.ma_table["pre_science_read_types"]) > 0:
            frames = 1 - self.pre_science # this is valid as long as all the pre-science resultants are single-frame resultants
            # How many resets and reference frames are taken?
            for idx, read in enumerate(self.ma_table["pre_science_read_types"]):
                if self.ma_table["pre_science_read_is_reference"][idx]: 
                    self.nreference += 1
                    if read == "read": # this will generally fail if more than one reference frame is taken, and also if they're different lengths
                        self.treference = self.tframe # elsewhere we need to track the reference time
                    elif read == "reset_read":
                        self.treference = self.treset
                    else:
                        raise DataError(f"Unknown read type '{read}' in MA Table {self.ma_table_name}")
                    pre_time = self.treference
                else: # if not reference then reset
                    self.nreset += 1
                    pre_time = self.treset
                # Are they downlinked as a resultant?
                if self.ma_table["pre_science_read_is_resultant"][idx]:
                    readout_time_full.append([pre_time])

            if len(readout_time_full) > 0:
                pre_science_cum_time = np.sum(readout_time_full)

        # For now, this is simple: All science frames are the same length.
        for resultant in self.ma_table["science_read_pattern"]:
            self.readout_cum_time_full.append(np.asarray(resultant) * self.tframe + pre_science_cum_time) # because we started tracking time at the first resultant
            self.readout_frametimes_full.append(self.tframe)

        self.readout_pattern_flat_full.extend(np.arange(self.ma_table["science_read_pattern"][-1][-1]) + 1) # the +1 is allowed because the pre-science resultant frames are numbered -1 and 0 (and the science frames themselves are 1-indexed)
        self.readout_cum_time_flat_full.extend(np.arange(1, self.ma_table["science_read_pattern"][-1][-1] + 1) * self.tframe + pre_science_cum_time)
        self.readout_pattern_full.extend(self.ma_table["science_read_pattern"])

    def get_times(self):
        """
        UnevenMultiaccum detectors follow the multiaccum table definitions specified in
        the Roman Timing Memo (Han 2025).

        In comparison to the ASDF MA tables, they are:

        measurement_time = effective_exposure_time: Time from the end of the Reference
            read to either the end of the resultant (if the last resultant is a single
            frame) or to the midpoint of the resultant (if the resultant is multiple
            frames)
        science_time = accumulated_exposure_time: Time from the end of the Reference read
            to the end of the last resultant. There is no JWST equivalent.
        saturation_time = (not in file): Time from the end of the Reset read to the
            end of the last resultant. Also known as photon collection time; this is the
            duration between resets during which a pixel might saturate.
        exposure_time = integration_duration: Entire MA table execution time, including
            reset reads, reference reads, and science frames.

        science_time and measurement_time are equal if and only if the last resultant is a
            single frame.
        saturation_time is science_time plus the reference reads.
        exposure_time is saturation_time plus the reset reads.

        For Roman, the timings are explicitly provided to us, this function merely exists
        to make it easy to find the mapping.

        The same data is duplicated in the front-end (workbook.js,
        update_detector_time_labels function). Please ensure that changes are reflected
        there.
        """

        # Measurement time: Time from the end of the reference frame to either the midpoint of the resultant (if multi-frame) or end of the resultant (if a single frame)
        self.measurement_time = self.ma_table["effective_exposure_time"][self.nresultants - 1]

        # Exposure time: The total time spent on one exposure, including resets
        self.exposure_time = self.ma_table["integration_duration"][self.nresultants - 1]

        # The total time spent exposing this observation (exposure time, times number of
        # exposures)
        self.total_exposure_time = self.exposure_time * self.nexp

        # Science time: The time spent accumulating science data
        self.science_time = self.ma_table["accumulated_exposure_time"][self.nresultants - 1]

        # Saturation time: The time that's important for computing saturation; the time spent collecting
        # photons between resets (which includes the reference frame)
        self.saturation_time = self.ma_table["accumulated_exposure_time"][self.nresultants - 1] + self.nreference * self.treference

        self.duty_cycle = self.saturation_time/self.exposure_time
        self.nramps = self.nexp
        self.exposures = self.nexp
        self.total_integrations = self.nexp

        # add photon collect time
        self.photon_collect = self.saturation_time * self.nexp

    def _midpoint(self, resultantnum):
        """
        Helper function to just get the midpoint of the particular resultant.
        This function assumes the skipped frames are always and only at the
        beginning of the resultant.

        No longer used.

        Parameters
        ----------
        resultantnum : int
            The number of the resultant to compute the midpoint of.

        Returns
        -------
        float
            the midpoint frame read
        """
        if resultantnum == -1:
            resultantnum = self.nresultants-1
        skip = self.ntotal[resultantnum]-self.nreads[resultantnum]
        reads = self.nreads[resultantnum]

        return skip + reads/2.

class ExposureSpec_H4RG(ExposureSpec_UnevenMultiAccum):

    pass

class ExposureSpec_SingleAccum(ExposureSpec):
    """
    Parent class for SingleAccum
    """

    def __init__(self, config={}, webapp=False, **kwargs):
        """
        Create a single accum Exposure Specification.

        Inputs
        ------
        config: dict
            dictionary of detector configuration setups

        webapp: bool
            Switch to toggle strict API checking

        **kwargs: keyword/value pairs
            Additional configuration data

        """
        self.webapp = webapp

        self.time = config["input_detector"]["time"]

        # Required parameters
        #self.readout_pattern = config["input_detector"]["readout_pattern_config"]
        #self.subarray = config["input_detector"]["subarray"]
        if "nexp" in config["input_detector"]:
            raise DataError("SingleAccum calculations cannot use nexp")
        self.nsplit = config["input_detector"]["nsplit"]

        self.get_times()

        # Derived quantities needed for the generic noise equation
        self.nramps = 1

    def get_times(self):
        """
        The following times are defined for use in Pandeia to parallel JWST usage.


        See also ExposureSpec_SingleAccum.set_time()
        """
        # measurement time is the time from the first measurement to the last read of the
        # exposure. HST has no skipped or dropped frames; this is simply the time for one
        # frame.
        self.measurement_time = self.time / self.nsplit

        # exposure time is the total time of one exposure (including any skipped reads,
        # reset reads, and the like - HST doesn’t have them.)
        self.exposure_time = self.time / self.nsplit

        # saturation time is the time the detector spends collecting photons between
        # resets, including skipped and dropped reads. It is the time that saturation
        # calculations depend on.
        self.saturation_time = self.time / self.nsplit

        # total exposure time is the time for the entire observation, including all
        # exposures and all the resets and skipped frames.
        self.total_exposure_time = self.time

        self.duty_cycle = self.saturation_time/self.exposure_time
        self.total_integrations = self.nsplit
        self.exposures = self.nsplit

        # add photon collect time
        self.photon_collect = self.time

class ExposureSpec_CCD(ExposureSpec_SingleAccum):

    pass

class ExposureSpec_H1R(ExposureSpec_CCD):

    pass

class ExposureSpec_MAMA(ExposureSpec_SingleAccum):

    pass

class ExposureSpec_XDL(ExposureSpec_MAMA):

    pass
