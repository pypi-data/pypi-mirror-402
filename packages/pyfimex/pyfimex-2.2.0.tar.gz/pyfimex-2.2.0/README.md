# python bindings for fimex
- see [fimex](http://github.com/metno/fimex/)
- a python module `pyfimex0` has been part of the fimex source code for a while,
  this package supersedes that package
- installation requires local development files for fimex, a c++ compiler, cmake, ...

# Development
Install in a local venv with `pip install -e .`. Run `pytest`. The
tests require the `xarray` python package and NetCDF support in
fimex.

Build sdist package with `python3 -m build --sdist`. Do not build wheels as the package
depends on fimex, which is installed locally and not available on pypi.

When test installing from test.pypi.org, use `python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyfimex` to have the main pypi repo available for build dependencies.
