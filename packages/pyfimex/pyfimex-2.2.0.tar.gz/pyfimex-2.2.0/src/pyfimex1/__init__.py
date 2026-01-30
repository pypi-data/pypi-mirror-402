import os
import typing

# the __version__ attribute is parsed by cmake
__version__ = '2.2.0'

if not typing.TYPE_CHECKING and os.getenv("PYBIND11_PROJECT_PYTHON_DEBUG"):
    from ._pyfimex1_d import *  # noqa: F403
else:
    from ._pyfimex1 import *  # noqa: F403
