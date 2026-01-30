#===============================================================================
# Copyright 2019 Intel Corporation
#
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#
# http://www.apache.org/licenses/LICENSE-2.0
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions
# and limitations under the License.
#
#===============================================================================

#
# Intel® Integrated Performance Primitives (Intel® IPP) library detection routine.
#
# To use it, add the lines below to your CMakeLists.txt:
# ~~~
#     find_package(IPP REQUIRED)
#     target_link_libraries(mytarget ${IPP_LIBRARIES})
# ~~~
#
# List of the variables defined in this file:
#
# * IPP_FOUND
# * IPP_LIBRARIES - list of all imported targets
#
# Configuration variables available:
#
# * IPP_SHARED     - set this to TRUE before find_package() to search for shared library.
# * IPP_TL_VARIANT - set this to 'OpenMP' or 'TBB' to use the corresponding variant of Intel® IPP Threading Layer (TL) libraries ('OpenMP' variant is
#   used by default if no IPP_TL_VARIANT variable is set)
#

if ("${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" LESS 3.11)
    message(FATAL_ERROR "Intel(R) IPP: CMake >= 3.11 required")
endif ()

include_guard()

include("${CMAKE_CURRENT_LIST_DIR}/IPPPathLayout.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/IPPUtils.cmake")

get_filename_component(ipp_cmake_package_dir "${CMAKE_CURRENT_LIST_DIR}" REALPATH)

# Initialize to default values
if (NOT IPP_LIBRARIES)
    set(IPP_LIBRARIES "")
endif ()

if (NOT DEFINED IPP_TL_VARIANT)
    set(IPP_TL_VARIANT "OpenMP")
endif ()

if (IPP_TL_VARIANT STREQUAL "OpenMP")
    set(ipp_tl_suffix "omp")
elseif (IPP_TL_VARIANT STREQUAL "TBB")
    set(ipp_tl_suffix "tbb")
else ()
    message(FATAL_ERROR "Intel(R) IPP: Possible values of the variable IPP_TL_VARIANT are 'OpenMP' and 'TBB'.")
endif ()

string(TOLOWER "${IPP_TL_VARIANT}" ipp_tl_directory)

# Dependencies between Intel® IPP domain
set(ippvm_deps ippcore)

set(ipps_deps ippvm ippcore)

set(ippdc_deps ipps ippvm ippcore)
set(ippi_deps ipps ippvm ippcore)

set(ippcc_deps ippi ipps ippvm ippcore)
set(ippcv_deps ippi ipps ippvm ippcore)

set(ippi_tl_deps ippi ipps ippvm ippcore)
set(ippcc_tl_deps ippcc ippi ipps ippvm ippcore)
set(ippcv_tl_deps ippcv ippi ipps ippvm ippcore)

set(ippi_tl_deps_tl ippcore_tl)
set(ippcc_tl_deps_tl ippi_tl ippcore_tl)
set(ippcv_tl_deps_tl ippi_tl ippcore_tl)

set(ipp_base_components
    ipp_iw
    ippe
    ippcore
    ippvm
    ipps
    ippdc
    ippi
    ippcc
    ippcv)

set(ipp_tl_components ippcore_tl ippi_tl ippcc_tl ippcv_tl)

set(ipp_components ${ipp_base_components} ${ipp_tl_components})

if (NOT IPP_FIND_COMPONENTS)
    set(IPP_BASE_FIND_COMPONENTS ${ipp_base_components})
    set(IPP_TL_FIND_COMPONENTS ${ipp_tl_components})
else ()
    list(REMOVE_DUPLICATES IPP_FIND_COMPONENTS)
    foreach (_component ${IPP_FIND_COMPONENTS})
        if (NOT _component IN_LIST ipp_components)
            message(FATAL_ERROR "Intel(R) IPP: Component '${_component}' not found! It must be one of the following values: ${ipp_components}!")
        endif ()
    endforeach ()

    foreach (_component ${IPP_FIND_COMPONENTS})
        if (_component IN_LIST ipp_base_components)
            list(APPEND IPP_BASE_FIND_COMPONENTS "${_component}")
        endif ()
        list(APPEND IPP_BASE_FIND_COMPONENTS ${${_component}_deps})
    endforeach ()
    list(REMOVE_DUPLICATES IPP_BASE_FIND_COMPONENTS)

    foreach (_component ${IPP_FIND_COMPONENTS})
        if (_component IN_LIST ipp_tl_components)
            list(APPEND IPP_TL_FIND_COMPONENTS "${_component}")
            list(APPEND IPP_TL_FIND_COMPONENTS ${${_component}_deps_tl})
        endif ()
    endforeach ()
    list(REMOVE_DUPLICATES IPP_TL_FIND_COMPONENTS)
endif ()

set(ipp_required_components ${IPP_BASE_FIND_COMPONENTS} ${IPP_TL_FIND_COMPONENTS})

foreach (_component ${ipp_required_components})
    set(IPP_FIND_REQUIRED_${_component} 1)
endforeach ()

set(IPP_ARCH "intel64")

function (
    add_imported_library_target
    _component
    PATH_TO_LIBRARY
    PATH_TO_IMPORT_LIB
    LINKAGE_TYPE
    component_found_variable
    ipp_found_variable
    ipp_libraries_variable)
    if (EXISTS "${PATH_TO_LIBRARY}")
        if (NOT TARGET IPP::${_component})
            add_library(IPP::${_component} ${LINKAGE_TYPE} IMPORTED)
            get_filename_component(_include_dir "${ipp_cmake_package_dir}/${IPP_INC_REL_PATH}" REALPATH)
            if (EXISTS "${_include_dir}")
                set_target_properties(IPP::${_component} PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "${_include_dir}" IMPORTED_LOCATION
                                                                                                                    "${PATH_TO_LIBRARY}")
                if (WIN32)
                    set_target_properties(IPP::${_component} PROPERTIES IMPORTED_IMPLIB "${PATH_TO_IMPORT_LIB}")
                endif ()
            else ()
                message(WARNING "Intel(R) IPP: Include directory does not exist: '${_include_dir}'. Intel(R) IPP installation may be corrupted.")
            endif ()
            unset(_include_dir)
        endif ()
        set(${component_found_variable}
            1
            PARENT_SCOPE)
        set(ipp_libraries ${${ipp_libraries_variable}})
        list(APPEND ipp_libraries IPP::${_component})
        set(${ipp_libraries_variable}
            ${ipp_libraries}
            PARENT_SCOPE)
    elseif (IPP_FIND_REQUIRED AND IPP_FIND_REQUIRED_${_component})
        message(STATUS "Intel(R) IPP: Missed required Intel(R) IPP component: ${_component}")
        message(STATUS "  library not found:\n   ${PATH_TO_LIBRARY}")
        if (${LINKAGE_TYPE} MATCHES "SHARED")
            message(STATUS "Intel(R) IPP: You may try to search for static libraries by unsetting IPP_SHARED variable.")
        endif ()
        set(${component_found_variable}
            0
            PARENT_SCOPE)
        set(${ipp_found_variable}
            0
            PARENT_SCOPE)
    endif ()
endfunction ()

function (add_components list_of_components tl_path tl_suffix ipp_libraries_variable)
    ipp_get_lib_version(IPP_INTERFACE_VERSION_MAJOR ipp_interface_version_major)
    if (WIN32)
        set(_ipp_library_prefix "")
        set(_ipp_static_library_suffix "mt${tl_suffix}.lib")
        set(_ipp_shared_library_suffix "${tl_suffix}.dll")
        set(_ipp_import_library_suffix "${tl_suffix}.lib")
    else ()
        set(_ipp_library_prefix "lib")
        set(_ipp_static_library_suffix "${tl_suffix}.a")
        if (APPLE)
            set(_ipp_shared_library_suffix "${tl_suffix}.dylib")
        else ()
            # Shared library suffix (`.<interface_version_major>` is added on Linux because PIP packages don't support symbolic links)
            set(_ipp_shared_library_suffix "${tl_suffix}.so.${ipp_interface_version_major}")
        endif ()
        set(_ipp_import_library_suffix "${tl_suffix}")
    endif ()
    set(ipp_libraries ${${ipp_libraries_variable}})
    foreach (_component ${list_of_components})
        set(full_component_name "${_component}")
        if (tl_suffix)
            string(REPLACE _tl "" _component "${_component}")
        endif ()
        set(IPP_${full_component_name}_FOUND 0)

        if (IPP_SHARED)
            set(_ipp_library_suffix "${_ipp_shared_library_suffix}")
            set(_linkage_type "SHARED")
        else ()
            set(_ipp_library_suffix "${_ipp_static_library_suffix}")
            set(_linkage_type "STATIC")
        endif ()
        if (full_component_name STREQUAL "ipp_iw")
            if (WIN32)
                set(_ipp_library_suffix ".lib")
            else ()
                set(_ipp_library_suffix ".a")
            endif ()
            set(_linkage_type "STATIC")
        endif ()

        if (WIN32 AND ${_linkage_type} MATCHES "SHARED")
            get_filename_component(
                _lib "${ipp_cmake_package_dir}/${IPP_REDIST_REL_PATH}/${tl_path}${_ipp_library_prefix}${_component}${_ipp_library_suffix}" REALPATH)
            get_filename_component(
                _imp_lib "${ipp_cmake_package_dir}/${IPP_LIB_REL_PATH}/${tl_path}${_ipp_library_prefix}${_component}${_ipp_import_library_suffix}"
                REALPATH)
        else ()
            get_filename_component(
                _lib "${ipp_cmake_package_dir}/${IPP_LIB_REL_PATH}/${tl_path}${_ipp_library_prefix}${_component}${_ipp_library_suffix}" REALPATH)
            set(_imp_lib "")
        endif ()
        add_imported_library_target(
            "${full_component_name}"
            "${_lib}"
            "${_imp_lib}"
            "${_linkage_type}"
            component_found
            ipp_found
            ipp_libraries)
        set(IPP_${full_component_name}_FOUND
            ${component_found}
            PARENT_SCOPE)
        if (NOT component_found)
            set(IPP_FOUND
                0
                PARENT_SCOPE)
        endif ()
    endforeach ()
    set(${ipp_libraries_variable}
        ${ipp_libraries}
        PARENT_SCOPE)
endfunction ()

set(IPP_FOUND 1)

add_components("${IPP_BASE_FIND_COMPONENTS}" "" "" IPP_LIBRARIES)
add_components("${IPP_TL_FIND_COMPONENTS}" "" "_tl_${ipp_tl_suffix}" IPP_LIBRARIES)

function (add_ipp_iw_include_directory iw_include_directory language)
    get_filename_component(_include_dir "${ipp_cmake_package_dir}/${IPP_INC_REL_PATH}/ipp/${iw_include_directory}" REALPATH)
    if (EXISTS "${_include_dir}")
        target_include_directories(IPP::ipp_iw INTERFACE $<$<COMPILE_LANGUAGE:${language}>:${_include_dir}>)
    else ()
        message(WARNING "Intel(R) IPP: Include directory does not exist: '${_include_dir}'. Intel(R) IPP installation may be corrupted.")
    endif ()
endfunction ()

if (IPP_FIND_REQUIRED_ipp_iw)
    add_ipp_iw_include_directory(iw C)
    add_ipp_iw_include_directory(iw++ CXX)
endif ()

list(REMOVE_DUPLICATES IPP_LIBRARIES)

# Dependencies between Intel® IPP libraries
if (IPP_FIND_REQUIRED_ippvm)
    target_link_libraries(IPP::ippvm INTERFACE IPP::ippcore)
endif ()

if (IPP_FIND_REQUIRED_ipps)
    target_link_libraries(IPP::ipps INTERFACE IPP::ippvm)
endif ()

if (IPP_FIND_REQUIRED_ippdc)
    target_link_libraries(IPP::ippdc INTERFACE IPP::ipps)
endif ()

if (IPP_FIND_REQUIRED_ippi)
    target_link_libraries(IPP::ippi INTERFACE IPP::ipps)
endif ()

if (IPP_FIND_REQUIRED_ippcc)
    target_link_libraries(IPP::ippcc INTERFACE IPP::ippi)
endif ()

if (IPP_FIND_REQUIRED_ippcv)
    target_link_libraries(IPP::ippcv INTERFACE IPP::ippi)
endif ()

if (IPP_FIND_REQUIRED_ippcore_tl)
    # 3rd party dependencies
    include(CMakeFindDependencyMacro)

    if (NOT IPP_SHARED)
        if (IPP_TL_VARIANT STREQUAL "TBB")
            find_dependency(TBB)
            if (TBB_FOUND)
                target_link_libraries(IPP::ippcore_tl INTERFACE TBB::tbb)
            endif ()
        endif ()
    endif ()
endif ()

if (IPP_FIND_REQUIRED_ippi_tl)
    target_link_libraries(IPP::ippi_tl INTERFACE IPP::ippi IPP::ippcore_tl)
endif ()

if (IPP_FIND_REQUIRED_ippcc_tl)
    target_link_libraries(IPP::ippcc_tl INTERFACE IPP::ippcc IPP::ippi_tl)
endif ()

if (IPP_FIND_REQUIRED_ippcv_tl)
    target_link_libraries(IPP::ippcv_tl INTERFACE IPP::ippcv IPP::ippi_tl)
endif ()
