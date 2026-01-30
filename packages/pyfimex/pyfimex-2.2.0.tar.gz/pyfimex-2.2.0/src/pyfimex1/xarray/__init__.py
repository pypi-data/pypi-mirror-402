from __future__ import annotations
from collections.abc import Iterable

import pyfimex1
import numpy as np
import xarray
from xarray.backends import BackendEntrypoint, BackendArray
import os


DTYPE_MAPPINGS = {
    pyfimex1.CDMDataType.FLOAT: np.float32,
    pyfimex1.CDMDataType.DOUBLE: np.float64,
    pyfimex1.CDMDataType.INT: np.intc,
    pyfimex1.CDMDataType.INT64: np.int64,
    pyfimex1.CDMDataType.UINT: np.uint,
    pyfimex1.CDMDataType.UINT64: np.uint64,
    pyfimex1.CDMDataType.SHORT: np.short,
    pyfimex1.CDMDataType.USHORT: np.ushort,
    pyfimex1.CDMDataType.STRING: str,
    pyfimex1.CDMDataType.CHAR: np.byte,
    pyfimex1.CDMDataType.UCHAR: np.ubyte,
}


def get_attribute_values(attr: pyfimex1.CDMAttribute):
    v = attr.getData().values()
    if len(v) == 1:
        v = v[0]
    return v


def get_attributes(cdm: pyfimex1.CDM, var_name: str):
    attrs = dict()
    for attr_name in cdm.getAttributeNames(var_name):
        attr = cdm.getAttribute(var_name, attr_name)
        attrs[attr_name] = get_attribute_values(attr)
    return attrs


class FimexBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj: str | pyfimex1.CDMReader,
        *,
        drop_variables: Iterable[str] | None = None,
        config: str | None = None,
        filetype: str | None = None,
        mask_and_scale: bool = True,
        decode_times: bool = True,
        decode_timedelta: bool = True,
        decode_coords: bool = True,
    ):
        if isinstance(filename_or_obj, str):
            if filetype is None:
                filetype = ""
            if config is None:
                config = ""
            fh = pyfimex1.createFileReader(filetype, filename_or_obj, config)
        elif isinstance(filename_or_obj, pyfimex1.CDMReader):
            if (filetype is not None) or (config is not None):
                raise TypeError(
                    "for CDMReader, filetype and config parameters are not allowed"
                )
            fh = filename_or_obj
        else:
            raise TypeError("`filename_or_obj` must be a `str` or a `CDMReader`")

        cdm = fh.getCDM()

        global_attrs = dict()
        for name in cdm.getGlobalAttributeNames():
            global_attrs[name] = get_attribute_values(cdm.getGlobalAttribute(name))

        var_names = set(cdm.getVariableNames())
        coord_names = set(cdm.getDimensionNames())
        coords = dict()
        for name in coord_names.intersection(var_names):
            var = cdm.getVariable(name)
            dims = list(reversed(var.getShape()))
            attrs = get_attributes(cdm, name)
            data = fh.getData(name).values()
            xvar = xarray.Variable(data=data, dims=dims, attrs=attrs)
            xvar = xarray.conventions.decode_cf_variable(
                name,
                xvar,
                mask_and_scale=mask_and_scale,
                decode_times=decode_times,
                decode_timedelta=decode_timedelta,
            )
            coords[name] = xvar
            var_names.remove(name)

        if drop_variables is None:
            drop_variables = set()
        else:
            drop_variables = set(drop_variables)

        vars = dict()
        for name in var_names:
            if name in drop_variables:
                continue

            var = cdm.getVariable(name)
            dims = list(reversed(var.getShape()))
            attrs = get_attributes(cdm, name)

            data = FimexDataVariable(fh, cdm, var)
            data = xarray.core.indexing.LazilyIndexedArray(data)
            xvar = xarray.Variable(data=data, dims=dims, attrs=attrs)
            vars[name] = xvar

        data_vars, attrs, coord_names = xarray.conventions.decode_cf_variables(
            vars,
            global_attrs,
            mask_and_scale=mask_and_scale,
            decode_times=decode_times,
            decode_timedelta=decode_timedelta,
            decode_coords=decode_coords,
        )

        ds = xarray.Dataset(data_vars=data_vars, attrs=attrs, coords=coords)
        return ds

    open_dataset_parameters = (
        "filename_or_obj",
        "drop_variables",
        "config",
        "filetype",
        "mask_and_scale",
        "decode_times",
        "decode_timedelta",
        "decode_coords",
    )

    def guess_can_open(self, filename_or_obj):
        if isinstance(filename_or_obj, pyfimex1.CDMReader):
            return True

        try:
            _, ext = os.path.splitext(filename_or_obj)
        except TypeError:
            return False

        return ext in {".grbml", ".ncml", ".grb", ".nc"}

    description = "Read using fimex"
    url = "https://github.com/metno/fimex"


class FimexDataVariable(BackendArray):
    def __init__(
        self, fh: pyfimex1.CDMReader, cdm: pyfimex1.CDM, var: pyfimex1.CDMVariable
    ):
        super().__init__()
        self.fh = fh
        self.var = var
        self.cdm = cdm

        self.dims = list(reversed(self.var.getShape()))
        self.shape = tuple([cdm.getDimension(s).getLength() for s in self.dims])

        self.dtype = np.dtype(DTYPE_MAPPINGS[self.var.getDataType()])

    def __getitem__(
        self, key: xarray.core.indexing.ExplicitIndexer
    ) -> np.typing.ArrayLike:
        return xarray.core.indexing.explicit_indexing_adapter(
            key,
            self.shape,
            xarray.core.indexing.IndexingSupport.BASIC,
            self._raw_indexing_method,
        )

    def _raw_indexing_method(self, key: tuple) -> np.typing.ArrayLike:
        vname = self.var.getName()

        slicebuilder = pyfimex1.SliceBuilder(self.cdm, vname, False)
        dimsizes = []
        for k, dim, dimname in zip(key, self.shape, self.dims):
            if isinstance(k, int):
                slicebuilder.setStartAndSize(dimname, k, 1)
            elif isinstance(k, slice):
                start = k.start if k.start is not None else 0
                step = k.step if k.step is not None else 1
                stop = k.stop if k.stop is not None else dim
                size = (stop - start) // step
                slicebuilder.setStartAndSize(dimname, start, size)
                dimsizes.append(size)
            else:
                raise TypeError(f"Unknown type of {k}: {type(k)}")

        if len(dimsizes) == 0:
            # Bug? Fimex can't read scalar data?
            return -1

        data = self.fh.getDataSliceSB(vname, slicebuilder)
        data_shaped = np.reshape(data.values(), dimsizes)
        return data_shaped
