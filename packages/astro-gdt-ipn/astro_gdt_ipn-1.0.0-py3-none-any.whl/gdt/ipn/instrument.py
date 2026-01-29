#  CONTAINS TECHNICAL DATA/COMPUTER SOFTWARE DELIVERED TO THE U.S. GOVERNMENT WITH UNLIMITED RIGHTS
#
#  Contract No.: CA 80NSSC24M0035
#  Contractor Name: Universities Space Research Association
#  Contractor Address: 7178 Columbia Gateway Drive, Columbia, MD 21046
#
#  Copyright 2021-2025 by Universities Space Research Association (USRA). All rights reserved.
#
#  Original IPN development funded through FY21 USRA Internal Research and Development Funds
#  and FY21 NASA-MSFC Center Innovation Funds
#
#  IPN code developed by:
#
#                Corinne Fletcher, Rachel Hamburg and Adam Goldstein
#                Universities Space Research Association
#                Science and Technology Institute
#                https://sti.usra.edu
#
#                Peter Veres
#                University of Alabama in Huntsville
#                Huntsville, AL
#
#                Michelle Hui
#                National Aeronautics and Space Administration (NASA)
#                Marshall Space Flight Center
#                Astrophysics Branch (ST-12)
#
#
#  With code contributions by:
#
#                Dmitry Svinkin
#                Ioffe Institute
#                St. Petersburg, Russia
#
#  Included in the Gamma-Ray Data Toolkit
#  Copyright 2017-2025 by Universities Space Research Association (USRA). All rights reserved.
#
#  Developed by: William Cleveland and Adam Goldstein
#                Universities Space Research Association
#                Science and Technology Institute
#                https://sti.usra.edu
#
#  Developed by: Daniel Kocevski
#                National Aeronautics and Space Administration (NASA)
#                Marshall Space Flight Center
#                Astrophysics Branch (ST-12)
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under the License
#  is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied. See the License for the specific language governing permissions and limitations under the
#  License.

import numpy as np
import astropy.units as units
import astropy.constants as constants
import astropy.coordinates as a_coords
from gdt.core.coords.spacecraft.frame import *
from gdt.core.data_primitives import TimeBins


class SpacecraftPosition:
    """Represents a spacecraft position in Geocentric Cartesian coordinates,
    including an uncertainty in the position. The uncertainty is assumed to be
    Gaussian and can either be a scalar or be defined for each of the
    Cartesian coordinates.

    Parameters:
        unit (str, optional): The distance units. Default is 'km'

    Attributes:
        origin_distance (float): Distance from the coordinate system origin
        origin_distance_uncertainty (float): Uncertainty in the distance from
                                             the coordinate origin
        unit (str): The distance units being used
        unit_vector (np.array): Unit position vector
        vector (np.array): The position vector
        vector_err (np.array): The position uncertainty vector
    """
    def __init__(self, unit='km'):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.x_err = 0.0
        self.y_err = 0.0
        self.z_err = 0.0

        self._unit = units.Unit(unit)

    @property
    def unit(self):
        return self._unit.to_string()

    @property
    def vector(self):
        return np.array((self.x, self.y, self.z))

    @property
    def unit_vector(self):
        return self.vector/self.origin_distance

    @property
    def vector_err(self):
        return np.array((self.x_err, self.y_err, self.z_err))

    @property
    def origin_distance(self):
        return np.linalg.norm(self.vector)

    @property
    def origin_distance_uncertainty(self):
        err = np.sqrt(np.sum((self.vector * self.vector_err)**2) / \
              np.sum(self.vector**2))
        return err

    @property
    def unit_vector_uncertainty(self):
        err = np.sqrt( (self.vector*self.origin_distance_uncertainty/self.origin_distance**2)**2 + \
                       (self.vector_err/self.origin_distance)**2 )
        return err

    @classmethod
    def from_distance(cls, dist, err, **kwargs):
        """Create a :class:`SpacecraftPosition` object from a coordinate system
        origin distance and scalar position uncertainty.

        Args:
            dist (float):  The scalar distance
            err (float): The scalar distance uncertainty
            unit (str, optional): The distance units. Default is 'km'

        Returns:
            :class:`SpacecraftPosition`
        """
        if dist == 0.0 or err < 0.0:
            raise ValueError('Distance must be positive and error must be ' \
                              'non-negative')
        vec = np.sqrt(dist**2/3.0)
        return cls.from_vectors(np.full(3, vec), np.full(3, err), **kwargs)

    @classmethod
    def from_vectors(cls, pos_vec, uncert_vec, **kwargs):
        """Create a :class:`SpacecraftPosition` object from a position vector
        and an uncertainty vector.

        Args:
            pos_vec (np.array):  The position vector
            uncert_vec (np.array): The uncertainty vector
            unit (str, optional): The distance units. Default is 'km'

        Returns:
            :class:`SpacecraftPosition`
        """
        if len(pos_vec) != 3 or len(uncert_vec) != 3:
            raise ValueError('vectors must have 3 components')

        obj = cls(**kwargs)
        obj.x, obj.y, obj.z = pos_vec
        obj.x_err, obj.y_err, obj.z_err = uncert_vec
        return obj

    @classmethod
    def from_celestial(cls, ra, dec, distance, coord_unit='deg', **kwargs):
        """Create a :class:`SpacecraftPosition` object from a RA, DEC, distance

        Args:
            ra (float): right ascension (radians or degress)
            dec (float): declination (radians or degrees)
            coord_unit (str, optional): The ra, dec units. Default is 'deg'
            dist_unit (str, optional): The distance units. Default is 'km'

        Returns:
            :class:`SpacecraftPosition`
        """
        if coord_unit=='deg':
            ra = np.deg2rad(ra)
            dec = np.deg2rad(dec)

        x = distance * np.cos(dec) * np.cos(ra)
        y = distance * np.cos(dec) * np.sin(ra)
        z = distance * np.sin(dec)
        return cls.from_vectors(np.array([x, y, z]), np.array([0.,0.,0.]), **kwargs)

    def to_units(self, unit):
        """Converts from current distance units to the new units and returns a
        new object.

        Args:
            unit (str): The distance units

        Returns:
            :class:`SpacecraftPosition`
        """
        vec = self.vector * self._unit
        vec_err = self.vector_err * self._unit

        new_unit = units.Unit(unit)
        new_vec = vec.to(new_unit).value
        new_vec_err = vec_err.to(new_unit).value

        cls = type(self)
        return cls.from_vectors(new_vec, new_vec_err, unit=unit)

    def distance(self, other_position, sign=False):
        """The distance between this spacecraft and another spacecraft.

        Args:
            other_position (:class:`SpacecraftPosition`): The other spacecraft
                                                          position
            sign (Boolean): whether or not to include vector directionality 
                in the distance

        Returns:
            (float): The distance in this object's units
        """
        # make sure we're working with consistent units
        if other_position.unit != self.unit:
            other_position = other_position.to_units(self.unit)

        vector = self.vector - other_position.vector

        if sign is not False:
            dsign = np.sign(np.arctan2(vector[1], vector[0]))
            return np.linalg.norm(vector) * dsign
        else:
            return np.linalg.norm(vector)

    def distance_uncertainty(self, other_position):
        """The uncertainty in the distance between this spacecraft and another
        spacecraft.

        Args:
            other_position (:class:`SpacecraftPosition`): The other spacecraft
                                                          position

        Returns:
            (float): The distance uncertainty in this object's units
        """
        # make sure we're working with consistent units
        if other_position.unit != self.unit:
            other_position = other_position.to_units(self.unit)

        vector = self.vector - other_position.vector
        vector_err = np.sqrt(self.vector_err**2 + other_position.vector_err**2)

        err = np.sqrt(np.sum((vector * vector_err)**2) / np.sum(vector**2))
        return err

    def light_travel_time(self, other_position, time_unit='s'):
        """The light travel time between this spacecraft and another spacecraft.
        This is the time it takes light to travel the vector connecting the two
        spacecraft.  The uncertainty in the light travel time due to the 
        positional uncertainty of the spacecraft is also returned.
        
        Args:
            other_position (:class:`SpacecraftPosition`): The other spacecraft
                                                          position
            time_unit (str, optional): The time unit. Default is 's'
             
        Returns:
            (float, float): The light travel time and uncertainty
        """
        dist = self.distance(other_position)
        dist_err = self.distance_uncertainty(other_position)
        dt = dist/constants.c.to(self.unit+'/'+time_unit).value
        dt_err = dist_err/constants.c.to(self.unit+'/'+time_unit).value
        return (dt, dt_err)

    def baseline_uncertainty(self, other_position):
        """The uncertainty in the baseline vector pointing from another
        spacecraft to this spacecraft in equatorial coordinates.

        Args:
            other_position (:class:`SpacecraftPosition`): The other spacecraft
                                                          position

        Returns:
            (float, float): The uncertainty in RA and Dec represented in
                            decimal degrees
        """
        # make sure we're working with consistent units
        if other_position.unit != self.unit:
            other_position = other_position.to_units(self.unit)

        unit_vec = self.unit_vector - other_position.unit_vector

        # problem when unit vector is all zeros
        mask = (unit_vec < 1e-10)
        unit_vec[mask] = 1e-10

        unit_err = np.sqrt(self.unit_vector_uncertainty**2 +
                           other_position.unit_vector_uncertainty**2)

        denom = (unit_vec[:2]**2).sum()
        ra_var = (unit_err[0]**2 * unit_vec[1]**2 / denom) + \
                 (unit_err[1]**2 * unit_vec[0]**2 / denom)
        ra_err = np.sqrt(ra_var)
        dec_err = unit_err[2]/np.sqrt(1.0-unit_vec[2]**2)

        return (ra_err, dec_err)

    def baseline(self, other_position):
        """The baseline vector pointing from another spacecraft to this
        spacecraft in equatorial coordinates.

        Args:
            other_position (:class:`SpacecraftPosition`): The other spacecraft
                                                          position

        Returns:
            (float, float): The RA and Dec of the baseline vector
        """
        unit_vec = self.unit_vector - other_position.unit_vector
        dec = np.arcsin(unit_vec[2])
        ra = np.arctan2(unit_vec[1], unit_vec[0])
        if ra < 0.0:
            ra += 2.0*np.pi
        return (ra, dec)

    def geocenter_correction(self, ra, dec, coord_unit='deg', time_unit='s'):
        """The light-travel time correction in geocentric coordinates. In other
        words, the geocenter is the coordinate reference point and the arrival
        time at the detector is calculated relative to the arrival time at the
        geocenter.  A negative correction indicates the arrival time at the
        detector is earlier than at the geocenter.

        Args:
            ra (float): The RA
            dec (float): The Dec
            coord_unit (str, optional): RA/Dec unit. Default is s'deg'
            time_unit (str, optional): The time unit. Default is 's'
        Returns:
            float: The time correction
        """

        if coord_unit=='deg':
            ra = np.deg2rad(ra)
            dec = np.deg2rad(dec)

        src_coords = np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    
        #src_coords = radec_to_cartesian(ra, dec)

        d = np.sum(-src_coords*self.vector)
        return d/constants.c.to(self.unit+'/'+time_unit).value


class TimeUncertainty():
    """Represents a time duration and uncertainty, which is assumed to be
    Gaussian.  Multiple :class:`TimeUncertainty` objects can be added or
    subtracted using the `+` and `-` operators.

    Parameters:
        dt (float): A time duration
        dt_err (float or tuple): The uncertainty in the time duration
        unit (str, optional): The time units. Default is 's'

    Attributes:
        dt (float): The time duration
        err (flat): The duration uncertainty
        unit (str): The time units being used
    """
    def __init__(self, dt, dt_err, unit='s'):
        self._dt = dt
        self._err = dt_err
        self._unit = units.Unit(unit)

    @property
    def dt(self):
        return self._dt
    @property
    def err(self):
        return self._err
    @property
    def unit(self):
        return self._unit.to_string()

    @classmethod
    def systematic(cls, err, unit='s'):
        """Creates a :class:`TimeUncertainty` object representing a systematic
        error component

        Args:
            err (float): The systematic error
            unit (str, optional): The time unit. Default is 's'

        Returns:
            :class:`TimeUncertainty`
        """
        return cls(0.0, err, unit=unit)

    def to_units(self, unit):
        """Converts from current time units to the new units and returns a
        new object.

        Args:
            unit (str): The time unit

        Returns:
            :class:`TimeUncertainty`
        """
        dt = self.dt * self._unit
        err = self.err * self._unit
        new_dt = dt.to(unit).value
        new_err = err.to(unit).value

        cls = type(self)
        return cls(new_dt, new_err, unit=unit)

    def __add__(self, other):
        """Adds two objects"""
        # make sure we're working with consistent units
        if other.unit != self.unit:
            other = other.to_units(self.unit)

        dt = self.dt + other.dt
        err = self._combine_errors(self.err, other.err)
        
        cls = type(self)
        return cls(dt, err, unit=self.unit)

    def __sub__(self, other):
        """Subtracts two objects"""
        # make sure we're working with consistent units
        if other.unit != self.unit:
            other = other.to_units(self.unit)

        dt = self.dt - other.dt
        err = self._combine_errors(self.err, other.err)

        cls = type(self)
        return cls(dt, err, unit=self.unit)
    
    def _combine_errors(self, err1, err2):
        """Combines errors using root-sum-squares"""
        err1 = np.array(err1)
        err2 = np.array(err2)

        try:
            combined = np.sqrt(err1**2 + err2**2)
        except ValueError:
            raise ValueError("Error terms must be compatible shapes for broadcasting.")

        if combined.size == 1:
            return float(combined)
        else:
            return combined


class Spacecraft:
    """A simple container representing properties of a spacecraft

    Parameters:
        position (:class:`SpacecraftPosition`): The position of the spacecraft
        observation (:class:`Observation`, optional): The time history and background
                                                        observation observed by the spacecraft
        time_uncert (float, optional): The onboard clock uncertainty
        dist_units (str, optional): The units to use for the spacecraft
                                    position. Default is 'km'
        time_units (str, optional): The units to use for the clock uncertainty.
                                    Default is 's'.

    Attributes:
        position (:class:`SpacecraftPosition`): The position of the spacecraft
        time_uncert (:class:`TimeUncertainty`): The clock uncertainty
        observation (:class:`Observation`): The time history and background
                                            observation observed by the spacecraft
    """
    def __init__(self, position, observation=None, time_uncert=0.0, dist_units='km', time_units='s'):
        self.position = position.to_units(dist_units)
        self.time_uncert = TimeUncertainty.systematic(time_uncert)
        self.set_observation(observation)
    
    @property
    def observation(self):
        return self._observation
    
    def set_observation(self, observation):
        """Set the observation for the instrument
        
        Args:
            observation (:class:`Observation`): The time history and background
                                                observation
        """
        if observation is not None and not isinstance(observation, Observation):
            raise TypeError("Input must be of class 'Observation'")
        self._observation = observation
        return



class Observation:
    """A simple container representing a time history observation and background
    model
    
    Parameters:
        data (:class:`TimeBins`): Time history data
        background (:class:`BackgroundRates`, optional): A background model
        
    Attributes:
        data (:class:`TimeBins`): Time history data
        background (:class:`BackgroundRates`, optional): A background model
    """
    def __init__(self, data, background=None):
        self._data = data
        self._background = background
    
    @property
    def data(self):
        return self._data
    @property
    def background(self):
        return self._background
    @background.setter
    def background(self, val):
        self._background = val

    def background_subtract(self):
        """Performs a simple background subtraction.  
        Caveat Emptor: Doing this assumes Gaussian signal and background, 
        which is probably not a correct assumption for your data.
        
        Returns:
            (:class:`TimeBins`): The background subtracted time history
        """
        if self.data.counts.shape != self.background.counts.shape:
            counts = self.data.counts - self.background.counts.flatten() 
        else:
            counts = self.data.counts - self.background.counts
        obj = TimeBins(counts, self.data.lo_edges, self.data.hi_edges, 
                       self.data.exposure)
        return obj
