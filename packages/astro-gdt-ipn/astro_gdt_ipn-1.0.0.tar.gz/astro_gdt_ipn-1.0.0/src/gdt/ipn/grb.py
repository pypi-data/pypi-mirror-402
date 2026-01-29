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
from scipy.spatial.transform import Rotation

class Grb():
    """Class for GRB properties
    
    Parameters:
        ra (float): The Right Ascension of the GRB in decimal degrees
        dec (float): The Declination of the GRB in decimal degrees
        spectrum (:class:`gbm.spectra.function.Function`): The photon model
        spectrum_params (list): The photon model parameters
        lightcurve (function): The lightcurve model
        lightcurve (params): The lightcurve parameters
    
    Attributes:
        location (float, float): The RA, Dec of the GRB location
        spectrum (:class:`gbm.spectra.function.Function`, list):
                 The spectral model and parameters
        lightcurve (function, list): The lightcurve model and parameters
    """
    def __init__(self, ra, dec, spectrum, spectrum_params, lightcurve,
                 lightcurve_params):
        if ra < 0.0 or ra > 360.0:
            raise ValueError("RA must be between 0-360 degrees")
        if dec < -90.0 or dec > 90.0:
            raise ValueError("Dec must be between -90 and 90 degrees")
        
        self._ra = ra
        self._dec = dec
        self._spectrum = (spectrum, spectrum_params)
        self._lightcurve = (lightcurve, lightcurve_params)
    
    @property
    def location(self):
        return (self._ra, self._dec)
    
    @property
    def spectrum(self):
        return self._spectrum
    
    @property
    def lightcurve(self):
        return self._lightcurve
    
    @classmethod
    def from_random_location(cls, spectrum, spectrum_params, lightcurve,
                             lightcurve_params):
        """Create a new GRB with a random sky position
        
        Args:
            spectrum (:class:`gbm.spectra.function.Function`): The photon model
            spectrum_params (list): The photon model parameters
            lightcurve (function): The lightcurve model
            lightcurve (params): The lightcurve parameters
        
        Returns:        
            :class:`Grb`: The Grb object
        """
        ra, dec = rand_equatorial(1)
        obj = cls(ra[0], dec[0], spectrum, spectrum_params, lightcurve, 
                  lightcurve_params)
        
        return obj


def rand_equatorial(n):
    """Produce random equatorial directions
    
    Args:
        n (int): Number of random points to generate
    
    Returns:        
        (np.array, np.array): The RA and Dec points
    """        
    vecs = Rotation.random(n).apply([1.0, 0.0, 0.0])
    r = np.linalg.norm(vecs, axis=1)
    ra = 180.0-np.rad2deg(np.arctan2(vecs[:,1], vecs[:,0]))
    dec = 90.0-np.rad2deg(np.arccos(vecs[:,2]/r))
    return (ra, dec)
