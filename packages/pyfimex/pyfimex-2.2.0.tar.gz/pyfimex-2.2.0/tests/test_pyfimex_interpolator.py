import os.path

import pyfimex1

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_LonLatPoints():
    test_ncfile = os.path.join(test_srcdir, "erai.sfc.40N.0.75d.200301011200.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)

    inter_ll = pyfimex1.createInterpolator(r)

    lats = [
        59.109,
        59.052,
        58.994,
        58.934,
        58.874,
        58.812,
        58.749,
        58.685,
        58.62,
        64.0,
    ]
    lons = [4.965, 5.13, 5.296, 5.465, 5.637, 5.81, 5.986, 6.164001, 6.344, 3.0]
    inter_ll.changeProjection(pyfimex1.InterpolationMethod.BILINEAR, lons, lats)

    i_cdm = inter_ll.getCDM()
    assert len(lons) == i_cdm.getDimension("x").getLength()
    assert 1 == i_cdm.getDimension("y").getLength()

    for v in inter_ll.getDataSlice("ga_skt", 0).values():
        assert (v < 281.1) and (v > 266)


def test_Proj4():
    test_ncfile = os.path.join(test_srcdir, "erai.sfc.40N.0.75d.200301011200.nc")
    r = pyfimex1.createFileReader("netcdf", test_ncfile)

    inter_ll = pyfimex1.createInterpolator(r)

    inter_ll.changeProjection(
        pyfimex1.InterpolationMethod.BILINEAR,
        "+proj=utm +zone=32 +datum=WGS84 +no_defs",
        range(250000, 280000, 10000),  # 3 x-axis values
        range(6630000, 6680000, 10000),  # 6 y-axis values
        "m",  # x-axis unit
        "m",  # y-axis unit
    )

    values = inter_ll.getDataSlice("ga_skt", 0).values()
    for v in values:
        assert (v < 281.1) and (v > 266)
