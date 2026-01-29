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
import healpy as hp
from scipy.stats import norm
import astropy.constants as constants
from matplotlib.pyplot import contour as Contour

from gdt.core.healpix import HealPix
from gdt.core.plot.lib import circle as sky_circle

__all__ = ['Annulus', 'IpnHealPixLocalization']

class Annulus:
    """Calculates a light-travel timing annulus between two spacecraft given a 
    time difference.
    
    Parameters:
        spacecraft1 (:class:`Spacecraft`): The reference spacecraft
        spacecraft2 (:class:`Spacecraft`): The other spacecraft
        time_offset (:class:`TimeUncertainty`): The time offset between the
                                                two spacecraft; time at 
                                                spacecraft1 - time at 
                                                spacecraft2
    """
    def __init__(self, spacecraft1, spacecraft2, time_offset):
        self._sc1 = spacecraft1
        self._sc2 = spacecraft2
        self._time_offset = time_offset
        
        speed_units = self._sc1.position.unit + '/' + self._sc1.time_uncert.unit
        self._c = constants.c.to(speed_units).value
    
    def center(self, deg=True):
        """Calculates the direction of the center point of the annulus in 
        equatorial coordinates, which is defined by the vector connecting the
        two spacecraft. The convention is that the vector points from the other
        spacecraft to the reference spacecraft.
        
        Args:
            deg (bool, optional): If True, return in degrees, otherwise radians.
                                  Default is True.
                    
        Returns:
            (tuple): RA and Dec
        """
        center = self._sc1.position.baseline(self._sc2.position)
        if deg:
            center = tuple(np.rad2deg(center))
        return center
    
    def center_error(self, deg=True):
        """Calculates the uncertainty in the direction of the center point of
        the annulus. This accounts for the positional uncertainty of both
        spacecraft.
        
        Args:
            deg (bool, optional): If True, return in degrees, otherwise radians.
                                  Default is True.
                    
        Returns:
            (tuple): error in RA and Dec
        """
        center_err = self._sc1.position.baseline_uncertainty(self._sc2.position)
        if deg:
            center_err = tuple(np.rad2deg(center_err))
        return center_err
    
    def radius(self, deg=True):
        """Calculates the radius of the annulus, which is the angular distance 
        between the center point and the center of the annulus width.
        
        Args:
            deg (bool, optional): If True, return in degrees, otherwise radians.
                                  Default is True.
                    
        Returns:
            (float): The annulus radius
        """
        distance = self._sc1.position.distance(self._sc2.position, sign=True)
        theta = np.arccos(self._c*self._time_offset.dt/distance)
        if deg:
            theta = np.rad2deg(theta)
        return theta
    
    def radius_error(self, deg=True):
        """Calculates the uncertainty in the annulus radius.  
        The uncertainties in the position of the spacecraft, their 
        intrinsic clock uncertainties, and the uncertainty in the time offset
        all contribute to the radius uncertainty.
        
        Args:
            deg (bool, optional): If True, return in degrees, otherwise radians.
                                  Default is True.
                    
        Returns:
            (float): The annulus radius uncertainty
        """
        dt_tot = self._sc1.time_uncert + self._sc2.time_uncert + \
                 self._time_offset
        distance = self._sc1.position.distance(self._sc2.position)
        dist_err = self._sc1.position.distance_uncertainty(self._sc2.position)
        theta_rad = self.radius(deg=False)

        dtheta_dt = self._c * dt_tot.err / (distance * np.sin(theta_rad))
        dtheta_D = (self._c * self._time_offset.dt * dist_err) / \
                   (distance**2 * np.sin(theta_rad))
        err = np.sqrt(dtheta_dt**2 + dtheta_D**2)
        if deg:
            err = np.rad2deg(err)
        return err
    
    def total_width(self, deg=True):
        """Calculates the total (1 sigma) width of the annulus.  The uncertainty
        in the annulus center and the uncertainty in the radius both contribute.
        
        Args:
            deg (bool, optional): If True, return in degrees, otherwise radians.
                                  Default is True.
                    
        Returns:
            (float): The total annulus width
        """
        center_err = np.array(self.center_error(deg=deg))
        theta_err = self.radius_error(deg=deg)
        return np.sqrt(center_err**2 + theta_err**2)

class IpnHealPixLocalization(HealPix):
    """Class for localization HEALPix files
    """
    def __init__(self):
        super().__init__()
        self._sig = None

    @property
    def prob(self):
        """(np.array): The HEALPix array for the probability/pixel"""
        return self._hpx

    @property
    def sig(self):
        """(np.array): The HEALPix array for the significance of each pixel"""
        return self._sig

    def _assert_prob(self, prob):
        # ensure that the pixels have valid probability:
        # each pixel must be > 0 and sum == 1.
        prob[prob < 0.0] = 0.0
        prob /= prob.sum()
        return prob

    def _assert_sig(self, sig):
        # ensure that the pixels have valid significance:
        # each pixel must have significance [0, 1]
        if sig is not None:
            sig[sig < 0.0] = 0.0
            sig[sig > 1.0] = 1.0
        return sig

    @staticmethod
    def _credible_levels(p):
        """Calculate the credible levels of a probability array using a greedy
        algorithm.

        Args:
            p (np.array): The probability array

        Returns:
             (np.array)
        """
        p = np.asarray(p)
        p_flat = p.flatten()
        idx = np.argsort(p_flat)[::-1]
        clevels = np.empty_like(p_flat)
        clevels[idx] = np.cumsum(p_flat[idx])
        return clevels.reshape(p.shape)
        
    def prob_array(self, numpts_ra=360, numpts_dec=180, sqdegrees=True,
                   sig=False):
        """Return the localization probability mapped to a grid on the sky

        Args:
            numpts_ra (int, optional): The number of grid points along the RA
                                       axis. Default is 360.
            numpts_dec (int, optional): The number of grid points along the Dec
                                        axis. Default is 180.
            sqdegrees (bool, optional):
                If True, the prob_array is in units of probability per square
                degrees, otherwise in units of probability per pixel.
                Default is True
            sig (bool, optional): Set True to retun the significance map on a
                                  grid instead of the probability.
                                  Default is False.

        Returns:
            3-tuple containing:

            - *np.array*: The probability (or significance) array with shape \
                      (``numpts_dec``, ``numpts_ra``)
            - *np.array*: The RA grid points
            - *np.array*: The Dec grid points
        """
        grid_pix, phi, theta = self._mesh_grid(numpts_ra, numpts_dec)

        if sig:
            sqdegrees = False
            prob_arr = self.sig[grid_pix]
        else:
            prob_arr = self.prob[grid_pix]
        if sqdegrees:
            prob_arr /= self.pixel_area
        return (prob_arr, self._phi_to_ra(phi), self._theta_to_dec(theta))

    def confidence_region_path(self, clevel, numpts_ra=360, numpts_dec=180):
        """Return the bounding path for a given confidence region.

        Args:
            clevel (float): The localization confidence level (valid range 0-1)
            numpts_ra (int, optional): The number of grid points along the RA
                                       axis. Default is 360.
            numpts_dec (int, optional): The number of grid points along the Dec
                                        axis. Default is 180.

        Returns:
            ([(np.array, np.array), ...]): A list of RA, Dec points, where each
                                           item in the list is a continuous
                                           closed path.
        """
        if clevel < 0.0 or clevel > 1.0:
            raise ValueError('clevel must be between 0 and 1')

        # create the grid and integrated probability array
        grid_pix, phi, theta = self._mesh_grid(numpts_ra, numpts_dec)
        sig_arr = 1.0 - self.sig[grid_pix]
        ra = self._phi_to_ra(phi)
        dec = self._theta_to_dec(theta)

        # use matplotlib contour to produce a path object
        contour = Contour(ra, dec, sig_arr, [clevel])

        # extract all the vertices
        pts = contour.allsegs[0]

        # unfortunately matplotlib will plot this, so we need to remove
        contour.remove()

        return pts

    @classmethod
    def from_annulus(cls, center_ra, center_dec, radius, sigma, nside=None,
                     trigtime=None, filename=None, **kwargs):
        """Create a HealPixLocalization object of a Gaussian-width annulus.

        Args:
            center_ra (float): The RA of the center of the annulus
            center_dec (float): The Dec of the center of the annulus
            radius (float): The radius of the annulus, in degrees, measured to
                            the center of the of the annulus
            sigma (float, list of floats): The Gaussian standard deviation width 
                                            of the annulus, in degrees
            nside (int, optional): The nside of the HEALPix to make. By default,
                                   the nside is automatically determined by the
                                   ``sigma`` width.  Set this argument to
                                   override the default.
            trigtime (float, optional): The reference time for the map
            filename (str, optional): The filename

        Return:
            (:class:`HealPixLocalization`)
        """
        if isinstance(sigma, float):
            sigma = list(sigma)
        try:
            center_ra = float(center_ra)
            center_dec = float(center_dec)
            radius = float(radius)
            sigma = [float(s) for s in sigma]
        except:
            raise TypeError('center_ra, center_dec, radius, and sigma must be' \
                            ' floats')

        center_ra = center_ra % 360.0
        if center_dec < -90.0 or center_dec > 90.0:
            raise ValueError('center_dec must be between -90 and 90')
        if radius < 0:
            raise ValueError('radius must be positive')
        for s in sigma:
            if s < 0:
                raise ValueError('sigma must be positive')

        # Automatically calculate appropriate nside by taking the closest nside
        # with an average resolution that matches 0.2*sigma
        if nside is None:
            nsides = 2**np.arange(15)
            pix_res = hp.nside2resol(nsides, True)/60.0
            idx = np.abs(pix_res-sigma/5.0).argmin()
            nside = nsides[idx]

        # get everything in the right units
        center_phi = cls._ra_to_phi(center_ra)
        center_theta = cls._dec_to_theta(center_dec)
        radius_rad = np.deg2rad(radius)
        sigma_rad = np.deg2rad(sigma)

        # number of points in the circle based on the approximate arclength
        # and resolution
        res = hp.nside2resol(nside)

        # calculate normal distribution about annulus radius with sigma width
        x = np.linspace(0.0, np.pi, int(10.0*np.pi/res))
        if isinstance(sigma_rad, float):
            pdf = norm.pdf(x, loc=radius_rad, scale=sigma_rad)
        else:
            mask_lo = x <= radius_rad
            mask_hi = x > radius_rad
            pdf_lo = norm.pdf(x[mask_lo], loc=radius_rad, scale=sigma_rad[0])
            pdf_hi = norm.pdf(x[mask_hi], loc=radius_rad, scale=sigma_rad[1])
            pdf_lo /= max(pdf_lo)
            pdf_hi /= max(pdf_hi)
            pdf = np.array(list(pdf_lo) + list(pdf_hi))

        # cycle through annuli of radii from 0 to 180 degree with the
        # appropriate amplitude and fill the probability map
        probmap = np.zeros(hp.nside2npix(nside))
        for i in range(x.size):
            # no need to waste time on pixels that will have ~0 probability...
            if pdf[i]/pdf.max() < 1e-10:
                continue

            # approximate arclength determines number of points in each annulus
            arclength = 2.0 * np.pi * x[i]
            numpts = int(np.ceil(arclength/res)) * 10
            circ = sky_circle(center_phi, center_theta, x[i], num_points=numpts)
            theta = np.pi / 2.0 - circ[1]
            phi = circ[0]

            # convert to pixel indixes and fill the map
            idx = hp.ang2pix(nside, theta, phi)
            probmap[idx] = pdf[i]
            mask = (probmap[idx] > 0.0)
            probmap[idx[~mask]] = pdf[i]
            probmap[idx[mask]] = (probmap[idx[mask]] + pdf[i])/2.0

        obj = cls.from_data(probmap, trigtime=trigtime, filename=filename,
                            **kwargs)
        return obj

    @classmethod
    def from_data(cls, prob_arr, trigtime=None, filename=None, **kwargs):
        """Create a HealPixLocalization object from a HEALPix probability array.

        Args:
            prob_arr (np.array): The HEALPix array
            trigtime (float, optional): The reference time for the map
            filename (str, optional): The filename

        Returns:
            (:class:`HealPixLocalization`)
        """
        obj = super().from_data(prob_arr, trigtime=trigtime, filename=filename,
                                **kwargs)
        obj._hpx = obj._assert_prob(obj._hpx)
        obj._sig = obj._assert_sig(1.0 - cls._credible_levels(obj.prob))
        return obj

    def __repr__(self):
        s = '<{0}: \n'.format(self.__class__.__name__)
        s += ' NSIDE={0}; trigtime={1};\n'.format(self.nside, self.trigtime)
        s += ' centroid={}>'.format(self.centroid)
        return s
