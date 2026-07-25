set(QL_STDEXEC_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/external/stdexec/include"
    CACHE PATH "Location of the stdexec (P2300 reference implementation) headers")

if (NOT EXISTS "${QL_STDEXEC_INCLUDE_DIR}/stdexec/execution.hpp")
    message(FATAL_ERROR
        "stdexec headers not found under ${QL_STDEXEC_INCLUDE_DIR}. Clone it with\n"
        "  git clone --depth 1 https://github.com/NVIDIA/stdexec.git external/stdexec\n"
        "or point QL_STDEXEC_INCLUDE_DIR at an existing checkout.")
endif()

add_executable(quantlib-parallel-mc parallelmcbench.cpp)
target_include_directories(quantlib-parallel-mc PRIVATE ${QL_STDEXEC_INCLUDE_DIR})
target_link_libraries(quantlib-parallel-mc ql_library ${QL_THREAD_LIBRARIES})

# The gates assert bit-identity against results produced without contraction;
# fusing stdDeviation*dw + drift into an FMA changes the last bits.
target_compile_options(quantlib-parallel-mc PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-ffp-contract=off>
    $<$<CXX_COMPILER_ID:MSVC>:/fp:precise>)

add_test(NAME parallel-mc-gates COMMAND quantlib-parallel-mc)
