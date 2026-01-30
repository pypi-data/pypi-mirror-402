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
# Intel® Integrated Performance Primitives (Intel® IPP) library detection routine (version detection utilities).
#

include_guard()

include("${CMAKE_CURRENT_LIST_DIR}/IPPPathLayout.cmake")

function (ipp_get_version_file_name version_file_name_var)
    set(version_file_name "${CMAKE_CURRENT_LIST_DIR}/${IPP_INC_REL_PATH}/ipp/ippversion.h")
    set("${version_file_name_var}"
        "${version_file_name}"
        PARENT_SCOPE)
endfunction ()

function (ipp_get_version_macro_list)
    set(version_list_arg_names SIMPLE_VERSIONS COMPLEX_VERSIONS ALL_VERSIONS)
    cmake_parse_arguments(
        "ARGUMENT" # prefix
        "" # options
        "${version_list_arg_names}" # one-value arguments
        "" # multi-value arguments
        ${ARGN})
    set(simple_versions IPP_VERSION_MAJOR IPP_VERSION_MINOR IPP_VERSION_UPDATE IPP_INTERFACE_VERSION_MAJOR IPP_INTERFACE_VERSION_MINOR)
    set(complex_versions IPP_VERSION IPP_INTERFACE_VERSION)
    set(all_versions ${simple_versions} ${complex_versions})
    foreach (version_list_arg_name ${version_list_arg_names})
        set(version_list_arg "ARGUMENT_${version_list_arg_name}")
        if (DEFINED "${version_list_arg}")
            string(TOLOWER "${version_list_arg_name}" version_list_var)
            set("${${version_list_arg}}"
                ${${version_list_var}}
                PARENT_SCOPE)
        endif ()
    endforeach ()
endfunction ()

function (ipp_get_lib_version_implementation)
    ipp_get_version_file_name(version_file_name)
    file(STRINGS "${version_file_name}" version_file_contents)
    ipp_get_version_macro_list(ALL_VERSIONS all_versions SIMPLE_VERSIONS simple_versions)
    foreach (version_file_line ${version_file_contents})
        foreach (simple_version ${simple_versions})
            set(ipp_version_macro_regex "^#define +${simple_version} +([0-9]+)$")
            if (${version_file_line} MATCHES "${ipp_version_macro_regex}")
                string(REGEX REPLACE "${ipp_version_macro_regex}" "\\1" "${simple_version}" "${version_file_line}")
            endif ()
        endforeach ()
    endforeach ()
    foreach (simple_version ${simple_versions})
        if (NOT DEFINED "${simple_version}" OR NOT "${${simple_version}}" MATCHES "^[0-9]+$")
            message(
                FATAL_ERROR
                    "Intel(R) IPP: Cannot parse version '${simple_version}' from 'ippversion.h' file. Intel(R) IPP installation may be corrupted.")
        endif ()
    endforeach ()
    set(IPP_VERSION "${IPP_VERSION_MAJOR}.${IPP_VERSION_MINOR}.${IPP_VERSION_UPDATE}")
    set(IPP_INTERFACE_VERSION "${IPP_INTERFACE_VERSION_MAJOR}.${IPP_INTERFACE_VERSION_MINOR}")
    foreach (version ${all_versions})
        set(${version}
            ${${version}}
            PARENT_SCOPE)
    endforeach ()
endfunction ()

function (ipp_get_lib_version_cache)
    ipp_get_version_file_name(version_file_name)
    file(TIMESTAMP "${version_file_name}" version_file_timestamp)
    if (DEFINED IPP_VERSION_FILE_TIMESTAMP AND IPP_VERSION_FILE_TIMESTAMP STREQUAL version_file_timestamp)
        return()
    endif ()
    set(IPP_VERSION_FILE_TIMESTAMP
        ${version_file_timestamp}
        CACHE INTERNAL "Timestamp of 'ippversion.h' file." FORCE)
    ipp_get_lib_version_implementation()
    ipp_get_version_macro_list(ALL_VERSIONS all_versions)
    foreach (version ${all_versions})
        set("IPP_MACRO_${version}"
            "${${version}}"
            CACHE INTERNAL "Stores the value of Intel(R) IPP '${version}' macro." FORCE)
    endforeach ()
endfunction ()

function (ipp_get_lib_version)
    ipp_get_version_macro_list(ALL_VERSIONS all_versions)
    cmake_parse_arguments(
        "ARGUMENT" # prefix
        "" # options
        "${all_versions}" # one-value arguments
        "" # multi-value arguments
        ${ARGN})
    ipp_get_lib_version_cache()
    foreach (version ${all_versions})
        if (DEFINED ARGUMENT_${version})
            set("${ARGUMENT_${version}}"
                "${IPP_MACRO_${version}}"
                PARENT_SCOPE)
        endif ()
    endforeach ()
endfunction ()
