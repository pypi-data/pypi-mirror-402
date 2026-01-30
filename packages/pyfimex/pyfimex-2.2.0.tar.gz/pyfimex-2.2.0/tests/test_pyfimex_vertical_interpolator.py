import os.path

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_FixedLevels():
    test_ncfile = os.path.join(test_srcdir, "testdata_altitude_height_in.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)

    vertical = pyfimex1.createVerticalInterpolator(r, "altitude", "linear_const_extra")

    level1 = [800, 400, 100, 50]
    vertical.interpolateToFixed(level1)
    vertical.ignoreValidityMin(False)
    vertical.ignoreValidityMax(False)

    v_cdm = vertical.getCDM()
    assert len(level1) == v_cdm.getDimension("height_above_msl").getLength()

    values = vertical.getDataSlice("vmro3", 0).values()
    assert len(values) == 19 * 10 * 4
    assert abs(values[0] - 3.01479730069332e-10) < 1e-12
