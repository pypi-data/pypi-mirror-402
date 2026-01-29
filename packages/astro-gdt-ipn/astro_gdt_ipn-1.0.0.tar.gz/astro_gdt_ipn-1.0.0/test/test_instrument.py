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
from gdt.ipn.instrument import *

class TestSpacecraftPosition(TestCase):

        def setUp(self):
            self.pos = SpacecraftPosition()


        def test_unit(self):
           self.assertAlmostEqual(self.pos.unit,'km')

        def test_vector(self):
            x,y,z = self.pos.vector
            self.assertAlmostEqual(x, 0.0)
            self.assertAlmostEqual(y, 0.0)
            self.assertAlmostEqual(z, 0.0)

        def test_vector_err(self):
            x_err,y_err,z_err = self.pos.vector_err
            self.assertAlmostEqual(x_err, 0.0)
            self.assertAlmostEqual(y_err, 0.0)
            self.assertAlmostEqual(z_err, 0.0)

        def test_origin_distance(self):
            dist = self.pos.origin_distance
            self.assertAlmostEqual(dist, 0.0)

        def test_from_distance(self):
            spacepos = self.pos.from_distance(5000, 50, unit='km')

            x,y,z = spacepos.vector
            self.assertAlmostEqual(x, 2886.751345, places=5)
            self.assertAlmostEqual(y, 2886.751345, places=5)
            self.assertAlmostEqual(z, 2886.751345, places=5)

            x_err,y_err,z_err = spacepos.vector_err
            self.assertAlmostEqual(x_err, 50.0, places=2)
            self.assertAlmostEqual(y_err, 50.0, places=2)
            self.assertAlmostEqual(z_err, 50.0, places=2)

            dist = spacepos.origin_distance
            self.assertAlmostEqual(dist, 5000.0, places=2)

            err = spacepos.origin_distance_uncertainty
            self.assertAlmostEqual(err, 50.0, places=2)

            unit_x, unit_y, unit_z = spacepos.unit_vector
            self.assertAlmostEqual(unit_x, 0.57735, places=5)
            self.assertAlmostEqual(unit_y, 0.57735, places=5)
            self.assertAlmostEqual(unit_z, 0.57735, places=5)

            unit_x_err, unit_y_err, unit_z_err = spacepos.unit_vector_uncertainty
            self.assertAlmostEqual(unit_x_err, 0.0115470, places=5)
            self.assertAlmostEqual(unit_y_err, 0.0115470, places=5)
            self.assertAlmostEqual(unit_z_err, 0.0115470, places=5)

        def test_from_vectors(self):
            vecpos = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')

            self.assertAlmostEqual(vecpos.unit,'m')

            x,y,z = vecpos.vector
            self.assertAlmostEqual(x, 5500, places=5)
            self.assertAlmostEqual(y, 6500, places=5)
            self.assertAlmostEqual(z, 7500, places=5)

            x_err,y_err,z_err = vecpos.vector_err
            self.assertAlmostEqual(x_err, 50.0, places=2)
            self.assertAlmostEqual(y_err, 60.0, places=2)
            self.assertAlmostEqual(z_err, 70.0, places=2)

            dist = vecpos.origin_distance
            self.assertAlmostEqual(dist, 11346.805717, places=5)

            err = vecpos.origin_distance_uncertainty
            self.assertAlmostEqual(err, 62.5261110, places=6)

            unit_x, unit_y, unit_z = vecpos.unit_vector
            self.assertAlmostEqual(unit_x, 0.4847179, places=6)
            self.assertAlmostEqual(unit_y, 0.572848, places=6)
            self.assertAlmostEqual(unit_z, 0.6609789, places=6)

            unit_x_err, unit_y_err, unit_z_err = vecpos.unit_vector_uncertainty
            self.assertAlmostEqual(unit_x_err, 0.005152, places=5)
            self.assertAlmostEqual(unit_y_err, 0.006158, places=5)
            self.assertAlmostEqual(unit_z_err, 0.007164, places=5)

        def test_to_units(self):
            spacepos = self.pos.from_distance(5000, 50, unit='km')

            new_units=spacepos.to_units(unit='m')
            self.assertAlmostEqual(new_units.unit,'m')

            x,y,z = new_units.vector
            self.assertAlmostEqual(x, 2886751.345, places=2)
            self.assertAlmostEqual(y, 2886751.345, places=2)
            self.assertAlmostEqual(z, 2886751.345, places=2)

            x_err,y_err,z_err = new_units.vector_err
            self.assertAlmostEqual(x_err, 50000.0, places=2)
            self.assertAlmostEqual(y_err, 50000.0, places=2)
            self.assertAlmostEqual(z_err, 50000.0, places=2)

            dist = new_units.origin_distance
            self.assertAlmostEqual(dist, 5000000.0, places=2)

            err = new_units.origin_distance_uncertainty
            self.assertAlmostEqual(err, 50000.0, places=2)

            unit_x, unit_y, unit_z = new_units.unit_vector
            self.assertAlmostEqual(unit_x, 0.57735, places=5)
            self.assertAlmostEqual(unit_y, 0.57735, places=5)
            self.assertAlmostEqual(unit_z, 0.57735, places=5)

            unit_x_err, unit_y_err, unit_z_err = new_units.unit_vector_uncertainty
            self.assertAlmostEqual(unit_x_err, 0.0115470, places=5)
            self.assertAlmostEqual(unit_y_err, 0.0115470, places=5)
            self.assertAlmostEqual(unit_z_err, 0.0115470, places=5)


        def test_distance(self):
            instrument1 = self.pos.from_distance(5000, 50, unit='km')
            instrument2 = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')

            dist1 =instrument1.distance(instrument2)
            self.assertAlmostEqual(dist1, 4988.741870, places=5)

            dist2 =instrument2.distance(instrument1)
            self.assertAlmostEqual(dist2, 4988741.87020, places=5)

            new_units = instrument2.to_units('km')
            dist_new=new_units.distance(instrument1)
            self.assertAlmostEqual(dist_new, dist1, places=1)

        def test_distance_uncertainty(self):
            instrument1 = self.pos.from_distance(5000, 50, unit='km')
            instrument2 = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')

            dist_unc1 =instrument1.distance_uncertainty(instrument2)
            self.assertAlmostEqual(dist_unc1, 50.0000366, places=5)

            dist_unc2 =instrument2.distance_uncertainty(instrument1)
            self.assertAlmostEqual(dist_unc2, 50000.03666, places=5)

        def test_baseline_uncertainty(self):
            instrument1 = self.pos.from_distance(5000, 50, unit='km')
            instrument2 = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')

            ra_unc1, dec_unc1=instrument1.baseline_uncertainty(instrument2)
            self.assertAlmostEqual(ra_unc1, 0.013085, places=5)
            self.assertAlmostEqual(dec_unc1,  0.0135888, places=5)


            ra_unc2, dec_unc2 =instrument2.baseline_uncertainty(instrument1)
            self.assertAlmostEqual(ra_unc2, 0.012867481, places=5)
            self.assertAlmostEqual(dec_unc2, 0.013636658, places=5)

        def test_baseline(self):
            instrument1 = self.pos.from_distance(5000, 50, unit='km')
            instrument2 = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')

            ra1, dec1 = instrument1.baseline(instrument2)
            self.assertAlmostEqual(ra1, 0.048560, places=5)
            self.assertAlmostEqual(dec1, -0.083726, places=5)

            ra2, dec2 =instrument2.baseline(instrument1)
            self.assertAlmostEqual(ra2, 3.1901532, places=5)
            self.assertAlmostEqual(dec2,  0.0837264, places=5)

        def test_geocenter_correction(self):
            geo_corr = self.pos.geocenter_correction(195,230, time_unit='s')
            self.assertAlmostEqual(geo_corr, 0.0, places=5)

            instrument1 = self.pos.from_vectors((5500,6500,7500),(50,60,70), unit='m')
            geo_corr1 = instrument1.geocenter_correction(100,230, time_unit='s')
            self.assertAlmostEqual(geo_corr1, 3.0841e-05, places=5)

            instrument2 = self.pos.from_distance(5000, 50, unit='km')
            geo_corr2 = instrument2.geocenter_correction(60,100, time_unit = 's')
            self.assertAlmostEqual(geo_corr2, -0.0071987, places=5)
