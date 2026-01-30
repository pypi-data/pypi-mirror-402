import os

import numpy as np
import xarray

import pyfimex1
from pyfimex1.xarray import FimexBackendEntrypoint

test_srcdir = os.path.join(os.path.dirname(__file__), "data")


def test_open_path():
    path = os.path.join(test_srcdir, "erai.sfc.40N.0.75d.200301011200.nc")
    ds = xarray.open_dataset(
        path,
        engine=FimexBackendEntrypoint,
    )
    var_actual = ds["ga_skt"].isel(latitude=[4], longitude=range(2, 3)).values
    var_expected = [
        [[[279.02410889]]],
        [[[278.93823242]]],
        [[[278.41725159]]],
        [[[278.25561523]]],
        [[[278.2467804]]],
        [[[278.04940796]]],
        [[[277.78135681]]],
        [[[277.67596436]]],
    ]
    assert np.allclose(var_actual, var_expected, equal_nan=True)


def test_open_cdmreader():
    path = os.path.join(test_srcdir, "erai.sfc.40N.0.75d.200301011200.nc")
    reader = pyfimex1.createFileReader("netcdf", path)
    ds = xarray.open_dataset(
        reader,
        engine=FimexBackendEntrypoint,
    )
    values_actual = (
        ds["ga_skt"].isel(time=1, surface=[0], latitude=4, longitude=5).values
    )
    values_expected = [260.76049805]
    assert np.allclose(values_actual, values_expected, equal_nan=True)


def test_isel_slice():
    path = os.path.join(test_srcdir, "erai.sfc.40N.0.75d.200301011200.nc")
    ds = xarray.open_dataset(
        path,
        engine=FimexBackendEntrypoint,
    )

    var = ds["ga_skt"]

    var_sub = ds.isel(time=slice(None, None, None))["ga_skt"]
    assert np.array_equal(var, var_sub, equal_nan=True)

    var_sub = ds.isel(time=slice(2, None, None))["ga_skt"]
    var_isel = var.isel(time=slice(2, None, None))
    assert np.array_equal(var_isel, var_sub, equal_nan=True)

    var_sub = ds.isel(time=slice(2, 4, None))["ga_skt"]
    var_isel = var.isel(time=slice(2, 4, None))
    assert np.array_equal(var_isel, var_sub, equal_nan=True)
