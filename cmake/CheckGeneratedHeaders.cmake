if (NOT DEFINED QL_SOURCE_DIR OR NOT DEFINED QL_BINARY_DIR)
    message(FATAL_ERROR "QL_SOURCE_DIR and QL_BINARY_DIR must be set")
endif()

set(SOURCE_DIR "${QL_SOURCE_DIR}")
set(BINARY_DIR "${QL_BINARY_DIR}/generated-header-visibility-test")
file(REMOVE_RECURSE "${BINARY_DIR}")
include("${SOURCE_DIR}/cmake/GenerateHeaders.cmake")

file(READ "${BINARY_DIR}/ql/time/all.hpp" time_headers)
file(READ "${BINARY_DIR}/ql/utilities/all.hpp" utility_headers)
file(READ "${BINARY_DIR}/ql/quantlib.hpp" quantlib_header)

foreach (header IN ITEMS
        varianceclockbundle.hpp
        varianceclockbundlesource.hpp
        varianceclockbundletypes.hpp)
    string(FIND "${time_headers}" "#include <ql/time/${header}>" position)
    if (position EQUAL -1)
        message(FATAL_ERROR "Public time header ${header} is missing from all.hpp")
    endif()
endforeach()

foreach (header IN ITEMS
        varianceclockdetail.hpp
        varianceclockbundlecapture.hpp
        varianceclockbundledata.hpp
        varianceclockbundleevidence.hpp
        varianceclockcsv.hpp
        varianceclockmanifest.hpp)
    string(FIND "${time_headers}" "#include <ql/time/${header}>" position)
    if (NOT position EQUAL -1)
        message(FATAL_ERROR "Private time header ${header} leaked into all.hpp")
    endif()
endforeach()

if (utility_headers MATCHES "detail/")
    message(FATAL_ERROR "Private utilities/detail headers leaked into all.hpp")
endif()
if (EXISTS "${BINARY_DIR}/ql/utilities/detail/all.hpp")
    message(FATAL_ERROR "A private utilities/detail aggregate was generated")
endif()

foreach (header IN ITEMS ql/time/all.hpp ql/utilities/all.hpp)
    string(FIND "${quantlib_header}" "#include <${header}>" position)
    if (position EQUAL -1)
        message(FATAL_ERROR "Root umbrella is missing ${header}")
    endif()
endforeach()
