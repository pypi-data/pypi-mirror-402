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

from unittest import TestCase
from gdt.ipn.grb import Grb, rand_equatorial
from gdt.core.spectra.functions import Comptonized

class TestGrb(TestCase):
    
    def test_rand_equatorial(self):
        '''Test rand_quatorial'''
        num = 1000
        ra, dec = rand_equatorial(num)
        
        # check sizes of output arrays
        self.assertEqual(ra.size, num)
        self.assertEqual(dec.size, num)
        
        # check the ranges are valid
        self.assertGreaterEqual(ra.min(), 0.0)
        self.assertLessEqual(ra.max(), 360.0)
        self.assertGreaterEqual(dec.min(), -90.0)
        self.assertLessEqual(dec.max(), 90.0)

    def test_grb_init(self):
        '''Test normal creation of Grb'''
        ra = 20.0
        dec = -37.0
        spec = Comptonized()
        spec_params = (1.0, 500.0, -0.5)
        lc = dummy_lc_function
        lc_params = (1.0, 2.0, 3.0)
    
        # create GRB and check the properties
        grb = Grb(ra, dec, spec, spec_params, lc, lc_params)
        self.assertTupleEqual(grb.location, (ra, dec))
        
        func, params = grb.spectrum
        self.assertEqual(func, spec)
        self.assertTupleEqual(params, spec_params)
        
        func, params = grb.lightcurve
        self.assertEqual(func, lc)
        self.assertTupleEqual(params, lc_params)
    
    def test_grb_random_loc(self):
        '''Test the randomized location of Grb'''
        spec = Comptonized()
        spec_params = (1.0, 500.0, -0.5)
        lc = dummy_lc_function
        lc_params = (1.0, 2.0, 3.0)
        
        # create random GRB and ensure it is of the right class
        grb = Grb.from_random_location(spec, spec_params, lc, lc_params)
        self.assertIsInstance(grb, Grb)
    
    def test_errors(self):
        '''Test the invalid inputs'''
        ra = 20.0
        dec = -37.0
        spec = Comptonized()
        spec_params = (1.0, 500.0, -0.5)
        lc = dummy_lc_function
        lc_params = (1.0, 2.0, 3.0)
                
        with self.assertRaises(ValueError):
            grb = Grb(-5.0, dec, spec, spec_params, lc, lc_params)
        with self.assertRaises(ValueError):
            grb = Grb(365.0, dec, spec, spec_params, lc, lc_params)
        with self.assertRaises(ValueError):
            grb = Grb(ra, -95.0, spec, spec_params, lc, lc_params)
        with self.assertRaises(ValueError):
            grb = Grb(ra, 95.0, spec, spec_params, lc, lc_params)

        with self.assertRaises(ValueError):
            rand_equatorial(-1)

def dummy_lc_function(x, params):
    return x
