cmake_minimum_required(VERSION 3.18...4.0)
project(pyfimex1 LANGUAGES CXX VERSION 2.2.0) # must match __version__ in src/pyfimex1/__init__.py

set(PY_VERSION_SUFFIX "")
set(PY_FULL_VERSION ${PROJECT_VERSION}${PY_VERSION_SUFFIX})

if (DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)
  # with py-build-cmake, make sure that the Python and CMake versions match
  if (NOT "${PY_BUILD_CMAKE_PROJECT_VERSION}" MATCHES "^${PY_FULL_VERSION}$")
      message(FATAL_ERROR "Version number does not match "
                          "(${PY_BUILD_CMAKE_PROJECT_VERSION} - ${PY_FULL_VERSION}).")
  endif()
else(DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)
  # without py-build-cmake, search for __version__ attribute in __init__.py
  file(STRINGS src/pyfimex1/__init__.py version_lines REGEX "^__version__ *=")
  if (version_lines)
     list(GET version_lines 0 version_line)
     message(STATUS "Found version line: ${version_line}")
     string(REGEX REPLACE "^__version__ *= *'\([0-9][^']+\)'.*$" "\\1" PY_INIT_VERSION ${version_line})
     message(STATUS "Extracted Project Version: '${PY_INIT_VERSION}'")
     if (NOT "${PY_INIT_VERSION}" MATCHES "^${PY_FULL_VERSION}$")
       message(FATAL_ERROR "Version number does not match "
         "(__init__.py: '${PY_INIT_VERSION}'; cmake: '${PY_FULL_VERSION}').")
     endif()
  else()
    message(FATAL_ERROR "Could not find __version__ in __init__.py")
  endif()

endif(DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)


# Find the Python interpreter and the development files
if (CMAKE_CROSSCOMPILING AND NOT (APPLE AND "$ENV{CIBUILDWHEEL}" STREQUAL "1"))
    find_package(Python3 REQUIRED COMPONENTS Development.Module)
else()
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
endif()


# Find the pybind11 package
include(cmake/QueryPythonForPybind11.cmake)
find_pybind11_python_first()


pybind11_add_module(_pyfimex1 MODULE
  src/_pyfimex/pyfimex_logging.cc
  src/_pyfimex/pyfimex_CDM.cc
  src/_pyfimex/pyfimex_CDMInterpolator.cc
  src/_pyfimex/pyfimex_CDMTimeInterpolator.cc
  src/_pyfimex/pyfimex_CDMVerticalInterpolator.cc
  src/_pyfimex/pyfimex_CDMExtractor.cc
  src/_pyfimex/pyfimex_CDMMerger.cc
  src/_pyfimex/pyfimex_CDMReader.cc
  src/_pyfimex/pyfimex_CDMReaderWriter.cc
  src/_pyfimex/pyfimex_CDMWriter.cc
  src/_pyfimex/pyfimex_CoordinateSystem.cc
  src/_pyfimex/pyfimex_Data.cc
  src/_pyfimex/pyfimex_NcmlCDMReader.cc
  src/_pyfimex/pyfimex_AggregationReader.cc
  src/_pyfimex/pyfimex.cc
)
target_compile_definitions(_pyfimex1 PRIVATE
    MODULE_NAME=$<TARGET_FILE_BASE_NAME:_pyfimex1>
    VERSION_INFO="${PY_FULL_VERSION}"
)
# Hide all symbols by default (including external libraries on Linux)
set_target_properties(_pyfimex1 PROPERTIES
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN true)
if (CMAKE_SYSTEM_NAME MATCHES "Linux")
    target_link_options(_pyfimex1 PRIVATE "LINKER:--exclude-libs,ALL")
endif()

find_package(fimex 2.1 REQUIRED)
target_link_libraries(_pyfimex1
  PRIVATE
  libfimex
)

if (DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)
  # with py-build-cmake, install the Python module
  install(TARGETS _pyfimex1
        EXCLUDE_FROM_ALL
        COMPONENT python_modules
        DESTINATION ${PY_BUILD_CMAKE_IMPORT_NAME})
else (DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)
  # without py-build-cmake, find install location and install there
  IF (PYFIMEX_INSTALL_LIBDIR)
    MESSAGE (STATUS "Configured PYFIMEX_INSTALL_LIBDIR='${PYFIMEX_INSTALL_LIBDIR}'")
  ELSE ()
    EXECUTE_PROCESS(OUTPUT_VARIABLE PYFIMEX_INSTALL_LIBDIR
      RESULT_VARIABLE PYFIMEX_INSTALL_EXIT_STATUS
      COMMAND ${Python3_EXECUTABLE} -c "
import sys
if sys.version_info >= (3, 10):
  import sysconfig as s
  pl = s.get_path('platlib', 'posix_prefix', vars={'platbase':'${CMAKE_INSTALL_PREFIX}'})
else:
  from distutils import sysconfig as ds
  pl = ds.get_python_lib(plat_specific=True, prefix='${CMAKE_INSTALL_PREFIX}')
sys.stdout.write(pl)
")
    IF (PYFIMEX_INSTALL_EXIT_STATUS)
      MESSAGE(FATAL_ERROR "Could not detect PYFIMEX_INSTALL_LIBDIR")
    ELSE ()
      MESSAGE (STATUS "Detected PYFIMEX_INSTALL_LIBDIR='${PYFIMEX_INSTALL_LIBDIR}'")
    ENDIF()
  ENDIF()
  set_target_properties(_pyfimex1 PROPERTIES LIBRARY_OUTPUT_DIRECTORY "pyfimex1")
  SET(PYFIMEX_INSTALL_DIR "${PYFIMEX_INSTALL_LIBDIR}/pyfimex1")
  install(TARGETS _pyfimex1
        COMPONENT python_modules
        DESTINATION ${PYFIMEX_INSTALL_DIR})
  install(FILES src/pyfimex1/__init__.py DESTINATION ${PYFIMEX_INSTALL_DIR})
  install(DIRECTORY src/pyfimex1/xarray DESTINATION ${PYFIMEX_INSTALL_DIR})
endif (DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)

# Generate stubs for the Python module
set(WITH_PY_STUBS_DEFAULT On)
if (CMAKE_CROSSCOMPILING)
  set(WITH_PY_STUBS_DEFAULT Off)
endif()
option(WITH_PY_STUBS
  "Generate Python stub files (.pyi) for the Python module."
  ${WITH_PY_STUBS_DEFAULT})
if (WITH_PY_STUBS)
  include(cmake/Pybind11Stubgen.cmake)
  pybind11_stubgen(_pyfimex1
    PACKAGE ${PY_BUILD_CMAKE_IMPORT_NAME}
    COMPONENT python_stubs)
endif()

if (NOT DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)
  ENABLE_TESTING()

  # without py-build-cmake, call pytest-3 to run tests and set
  # PYTHONPATH and FIMEX_IO_PLUGINS_PATH to use this build
  ADD_TEST(NAME test_pyfimex
    COMMAND pytest-3 "${CMAKE_CURRENT_SOURCE_DIR}"
  )
  SET(TESTS_PYTHONPATH "${CMAKE_CURRENT_BINARY_DIR}:$ENV{PYTHONPATH}" )
  FILE(COPY src/pyfimex1/__init__.py src/pyfimex1/xarray DESTINATION pyfimex1)
  SET_PROPERTY(
    TEST test_pyfimex
    APPEND PROPERTY ENVIRONMENT "PYTHONPATH=${TESTS_PYTHONPATH}"
  )
endif (NOT DEFINED PY_BUILD_CMAKE_PROJECT_VERSION)

# dummy target to tell IDEs that these files are part of the project
ADD_CUSTOM_TARGET(python_pyfimex_testfiles SOURCES
  tests/test_pyfimex_coordinatesystem.py
  tests/test_pyfimex_netcdf_cdmreaderwriter.py
  tests/test_pyfimex_PyCDMReader.py
  tests/test_pyfimex_extractor.py
  tests/test_pyfimex_netcdf_cdmwriter.py
  tests/test_pyfimex_vertical_interpolator.py
  tests/test_pyfimex_interpolator.py
  tests/test_pyfimex_netcdf.py
  tests/test_pyfimex_merger.py
  tests/test_pyfimex.py

  tests/test_fimex_xarray.py
)
