# Fimex, modules/python/test_pyfimex1_coordinatesystem.py
#
# Copyright (C) 2018 met.no
#
# Contact information:
# Norwegian Meteorological Institute
# Box 43 Blindern
# 0313 OSLO
# NORWAY
# email: diana@met.no
#
# Project Info:  https://wiki.met.no/fimex/start
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

import os.path

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_listCoordinateSystems():
    test_ncfile = os.path.join(test_srcdir, "testdata_vertical_ensemble_in.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)

    cs = pyfimex1.listCoordinateSystems(r)
    assert len(cs) == 6

    cs_var = pyfimex1.findCompleteCoordinateSystemFor(cs, "x_wind_10m")
    assert cs_var.id() == "CF-1.X:ensemble_member,height7,latitude,longitude,time,x,y"

    cax1 = cs_var.findAxisOfType(pyfimex1.CoordinateAxisType.GeoX)
    assert cax1.getName() == "x"

    cax2 = cs_var.findAxisOfType(
        [pyfimex1.CoordinateAxisType.GeoX, pyfimex1.CoordinateAxisType.Lon]
    )
    assert cax2.getName() == "x"
