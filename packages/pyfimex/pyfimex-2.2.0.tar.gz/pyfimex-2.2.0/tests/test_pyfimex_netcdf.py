# Fimex, modules/python/test_pyfimex1.py
#
# Copyright (C) 2018-2022 met.no
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

import numpy
import pytest

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_OpenAndInspect():
    test_ncfile = os.path.join(test_srcdir, "testdata_vertical_ensemble_in.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)

    assert type(r.getDataSlice("hybrid", 0).values()[0]) is numpy.float64

    assert r.getDataSlice("upward_air_velocity_ml", 0).values()[0] == 305
    assert r.getScaledDataSlice("upward_air_velocity_ml", 0).values()[
        0
    ] == pytest.approx(0.0305)
    assert r.getScaledDataSliceInUnit("upward_air_velocity_ml", "mm/s", 0).values()[
        0
    ] == pytest.approx(30.5)
    assert numpy.isnan(r.getScaledDataSlice("upward_air_velocity_ml", 1).values()[-1])

    r_cdm = r.getCDM()

    d_ens = r_cdm.getDimension("ensemble_member")
    d_ens_len = d_ens.getLength()
    assert 3 == d_ens_len
    assert not d_ens.isUnlimited()

    d_time = r_cdm.getDimension("time")
    assert d_time.isUnlimited()

    r_dims = r_cdm.getDimensionNames()
    assert "time" in r_dims

    r_vars = r_cdm.getVariableNames()
    assert "surface_geopotential" in r_vars


def test_AttributeFromFile():
    test_ncfile = os.path.join(test_srcdir, "testdata_vertical_ensemble_in.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)
    r_cdm = r.getCDM()

    assert "long_name" in r_cdm.getAttributeNames("x_wind_10m")
    r_att = r_cdm.getAttribute("x_wind_10m", "long_name")
    assert "Zonal 10 metre wind (U10M)" == r_att.getStringValue()

    assert "title" in r_cdm.getGlobalAttributeNames()
    r_gatt = r_cdm.getGlobalAttribute("title")
    assert "MEPS 2.5km" == r_gatt.getStringValue()


def test_VariableFromFile():
    test_ncfile = os.path.join(test_srcdir, "testdata_vertical_ensemble_in.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)
    r_cdm = r.getCDM()

    v_xwind10m = r_cdm.getVariable("x_wind_10m")
    v_xwind10m_name = v_xwind10m.getName()
    assert "x_wind_10m" == v_xwind10m_name

    assert v_xwind10m.getShape() == ["x", "y", "ensemble_member", "height7", "time"]
