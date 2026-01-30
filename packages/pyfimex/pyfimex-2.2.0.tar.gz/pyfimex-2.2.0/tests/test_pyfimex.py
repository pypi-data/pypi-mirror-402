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

import numpy

import pyfimex1


def test_MifiVersion():
    mv = pyfimex1.mifi_version()
    assert 4 == len(mv)
    major, minor, patch, status = mv
    assert type(major) is int
    assert (major == 0 and minor > 0) or (major > 0 and minor >= 0)


def test_DataString():
    d = pyfimex1.createData("hello")
    assert pyfimex1.CDMDataType.STRING == d.getDataType()
    assert 5 == d.size()
    assert "hello" == d.values()

    d = pyfimex1.createData(pyfimex1.CDMDataType.STRING, "values")
    assert pyfimex1.CDMDataType.STRING == d.getDataType()
    assert 6 == d.size()
    assert "values" == d.values()


def test_DataFloat():
    d = pyfimex1.createData(pyfimex1.CDMDataType.FLOAT, [1, 2, 3])
    assert pyfimex1.CDMDataType.FLOAT == d.getDataType()
    assert 3 == d.size()
    assert numpy.float32 == d.values().dtype


def test_DataChar():
    d = pyfimex1.createData(numpy.arange(5, dtype=numpy.int8))
    assert pyfimex1.CDMDataType.CHAR == d.getDataType()
    assert 5 == d.size()


def test_DataUChar():
    d = pyfimex1.createData(numpy.arange(5, dtype=numpy.uint8))
    assert pyfimex1.CDMDataType.UCHAR == d.getDataType()


def test_AttributeString():
    att = pyfimex1.CDMAttribute("name", "value")
    assert "name" == att.getName()
    assert "value" == att.getStringValue()
    assert pyfimex1.CDMDataType.STRING == att.getDataType()

    att.setName("navn")
    assert "navn" == att.getName()

    att.setData(pyfimex1.createData("content"))
    assert "content" == att.getStringValue()
    assert pyfimex1.CDMDataType.STRING == att.getDataType()


def test_AttributeFloat():
    att = pyfimex1.CDMAttribute(
        "f", pyfimex1.createData(pyfimex1.CDMDataType.FLOAT, [1])
    )
    assert "f" == att.getName()
    assert "1" == att.getStringValue()
    assert [1.0] == att.getData().values()
    assert pyfimex1.CDMDataType.FLOAT == att.getDataType()


def test_AttributeUChar():
    l = [0, 12, 234]
    att = pyfimex1.CDMAttribute("u", pyfimex1.createData(pyfimex1.CDMDataType.UCHAR, l))
    assert " ".join([str(x) for x in l]) == att.getStringValue()
    d = att.getData()
    assert len(l) == d.size()
    v = d.values()
    assert numpy.uint8 == v.dtype
    assert l == list(v)


def test_VariableFloat():
    shp = ["x", "y", "time"]
    var = pyfimex1.CDMVariable("f", pyfimex1.CDMDataType.FLOAT, shp)
    assert "f" == var.getName()
    assert shp == var.getShape()


def test_CDM_variables():
    cdm = pyfimex1.CDM()
    assert 0 == len(cdm.getVariableNames())

    cdm.addVariable(
        pyfimex1.CDMVariable("varf", pyfimex1.CDMDataType.FLOAT, ["x", "y"])
    )
    assert ["varf"] == cdm.getVariableNames()

    cdm.addAttribute(
        "varf",
        pyfimex1.CDMAttribute(
            "_FillValue", pyfimex1.createData(pyfimex1.CDMDataType.FLOAT, -1)
        ),
    )
    assert 1 == len(cdm.getAttributeNames("varf"))

    cdm.removeVariable("varf")
    assert 0 == len(cdm.getVariableNames())
