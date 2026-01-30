/*
 * Fimex, pyfimex1.cc
 *
 * (C) Copyright 2017-2022, met.no
 *
 * Project Info:  https://wiki.met.no/fimex/start
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
 * USA.
 *
 *  Created on: Aug 1, 2017
 *      Author: Alexander Bürger
 */

#include "fimex/CDMconstants.h"

#include <pybind11/pybind11.h>

namespace py = pybind11;

void pyfimex1_logging(py::module m);
void pyfimex1_Data(py::module m);
void pyfimex1_CDM(py::module m);
void pyfimex1_CDMInterpolator(py::module m);
void pyfimex1_CDMExtractor(py::module m);
void pyfimex1_CDMMerger(py::module m);
void pyfimex1_CDMReader(py::module m);
void pyfimex1_CDMReaderWriter(py::module m);
void pyfimex1_CDMTimeInterpolator(py::module m);
void pyfimex1_CDMVerticalInterpolator(py::module m);
void pyfimex1_CDMWriter(py::module m);
void pyfimex1_AggregationReader(py::module m);
void pyfimex1_CoordinateSystem(py::module m);
void pyfimex1_NcmlCDMReader(py::module m);

namespace {
py::tuple mifi_version()
{
    return py::make_tuple(mifi_version_major(), mifi_version_minor(), mifi_version_patch(), mifi_version_status());
}
} // namespace

PYBIND11_MODULE(MODULE_NAME, m)
{
    pyfimex1_logging(m);
    pyfimex1_Data(m);
    pyfimex1_CDM(m);
    pyfimex1_CDMReader(m);
    pyfimex1_CDMReaderWriter(m);
    pyfimex1_CDMWriter(m);
    pyfimex1_CDMInterpolator(m);
    pyfimex1_CDMTimeInterpolator(m);
    pyfimex1_CDMVerticalInterpolator(m);
    pyfimex1_CDMExtractor(m);
    pyfimex1_CDMMerger(m);
    pyfimex1_CoordinateSystem(m);
    pyfimex1_AggregationReader(m);
    pyfimex1_NcmlCDMReader(m);

    m.def("mifi_version", mifi_version, "Returns a 4-tuple with (major, minor, patch, status) version numbers.");
}
