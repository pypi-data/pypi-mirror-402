#!/usr/bin/env python

# Fimex, modules/python/test_pyfimex1_netcdf_cdmreaderwriter.py
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
import shutil

import pytest

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


# based on testNetCDFReaderWriter.cc
def test_update():
    test_rwfile = "out_cdmreaderwriter_update.nc"
    shutil.copyfile(os.path.join(test_srcdir, "test_merge_inner.nc"), test_rwfile)

    diff = 10.0
    scale = 1.2

    rw = pyfimex1.createFileReaderWriter("netcdf", test_rwfile)
    assert (rw) is not None

    read1 = rw.getDataSlice("ga_2t_1", 0)
    assert (read1) is not None

    write1 = pyfimex1.createData(
        pyfimex1.CDMDataType.DOUBLE, [diff + x * scale for x in read1.values()]
    )
    rw.putDataSlice("ga_2t_1", 0, write1)
    rw.sync()

    del rw

    r = pyfimex1.createFileReader("netcdf", test_rwfile)
    assert (r) is not None

    read2 = r.getScaledDataSlice("ga_2t_1", 0)
    assert (read2) is not None

    values1 = read1.values()
    values2 = read2.values()
    assert len(values1) == len(values2)
    for (
        i,
        (v1, v2),
    ) in enumerate(zip(values1, values2)):
        assert (diff + v1 * scale) == pytest.approx(v2)  # "at index {}".format(i)

    os.remove(test_rwfile)


def test_scaled():
    test_rwfile = "out_cdmreaderwriter_scaled.nc"
    shutil.copyfile(os.path.join(test_srcdir, "test_merge_inner.nc"), test_rwfile)

    addF = 1.0
    addK = addF * 5.0 / 9.0

    rw = pyfimex1.createFileReaderWriter("netcdf", test_rwfile)
    assert (rw) is not None

    read1 = rw.getScaledDataSlice("ga_2t_1", 0)
    assert (read1) is not None

    write1 = rw.getScaledDataSliceInUnit("ga_2t_1", "deg_F", 0)
    assert (write1) is not None

    wmod1 = pyfimex1.createData(
        pyfimex1.CDMDataType.DOUBLE, [x + addF for x in write1.values()]
    )
    rw.putScaledDataSliceInUnit("ga_2t_1", "deg_F", 0, wmod1)
    rw.sync()

    del rw

    # read back and compare
    r = pyfimex1.createFileReader("netcdf", test_rwfile)
    assert (r) is not None

    read2 = r.getScaledDataSlice("ga_2t_1", 0)
    assert (read2) is not None

    values1 = read1.values()
    values2 = read2.values()
    assert len(values1) == len(values2)
    for (
        i,
        (v1, v2),
    ) in enumerate(zip(values1, values2)):
        assert (v1 + addK) == pytest.approx(v2)  # msg="at index {}".format(i)

    os.remove(test_rwfile)
