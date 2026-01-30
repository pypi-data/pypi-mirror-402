#!/usr/bin/env python

import os.path

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_writeExtracted():
    test_ncfile = os.path.join(test_srcdir, "testdata_vertical_ensemble_in.nc")
    r1 = pyfimex1.createFileReader("netcdf", test_ncfile)

    v_x_wind = "x_wind_10m"
    r1v_x_wind = r1.getDataSlice(v_x_wind, 0).values()

    extra = pyfimex1.createExtractor(r1)
    extra.selectVariables([v_x_wind])

    outfile = "out_cdmwriter_extracted.nc"
    pyfimex1.createNetCDFWriter(extra, outfile)

    del extra
    del r1

    r2 = pyfimex1.createFileReader("netcdf", outfile)
    r2v_x_wind = r2.getDataSlice(v_x_wind, 0).values()

    for v1, v2 in zip(r1v_x_wind, r2v_x_wind):
        assert v1 == v2

    os.remove(outfile)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    test_writeExtracted()
