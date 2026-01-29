cmake_minimum_required(VERSION 3.24)

# Try to find CUDA compiler from environment or standard locations
if(NOT DEFINED CMAKE_CUDA_COMPILER AND NOT DEFINED ENV{CUDACXX})
    # Check common CUDA installation paths
    if(WIN32)
        file(GLOB CUDA_PATHS "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v*")
        if(CUDA_PATHS)
            list(SORT CUDA_PATHS)
            list(REVERSE CUDA_PATHS)
            list(GET CUDA_PATHS 0 CUDA_TOOLKIT_ROOT_DIR)
            set(CMAKE_CUDA_COMPILER "${CUDA_TOOLKIT_ROOT_DIR}/bin/nvcc.exe")
        endif()
    else()
        # Linux: check standard paths
        foreach(CUDA_VER 12.4 12.3 12.2 12.1 12.0)
            if(EXISTS "/usr/local/cuda-${CUDA_VER}/bin/nvcc")
                set(CMAKE_CUDA_COMPILER "/usr/local/cuda-${CUDA_VER}/bin/nvcc")
                break()
            endif()
        endforeach()
        if(NOT CMAKE_CUDA_COMPILER AND EXISTS "/usr/local/cuda/bin/nvcc")
            set(CMAKE_CUDA_COMPILER "/usr/local/cuda/bin/nvcc")
        endif()
    endif()
endif()

project(etb LANGUAGES CXX CUDA)

# C++ and CUDA standards
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# CUDA architecture targets: SM 90 (Hopper) and SM 100 (Blackwell)
set(CMAKE_CUDA_ARCHITECTURES 90 100)

# Find required packages
find_package(CUDAToolkit 12.0 REQUIRED)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Fetch pybind11
include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.11.1
)
FetchContent_MakeAvailable(pybind11)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)

# Core library (C++ only)
add_library(etb_core STATIC
    src/bit_coordinate.cpp
    src/path.cpp
    src/bit_extraction.cpp
    src/path_generator.cpp
    src/path_count.cpp
    src/signature.cpp
    src/heuristics.cpp
    src/early_stopping.cpp
    src/prefix_trie.cpp
    src/memoization.cpp
    src/bit_pruning.cpp
    src/scoring.cpp
    src/config.cpp
    src/reporting.cpp
)
target_include_directories(etb_core PUBLIC ${CMAKE_SOURCE_DIR}/include)

# CUDA library
add_library(etb_cuda STATIC
    src/cuda/cuda_common.cu
    src/cuda/gpu_memory.cu
    src/cuda/path_generator_kernel.cu
    src/cuda/heuristics_kernel.cu
    src/cuda/signature_kernel.cu
    src/cuda/prefix_pruner_kernel.cu
    src/cuda/arch_optimizations.cu
    src/cuda/etb_cuda.cu
)
target_include_directories(etb_cuda PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(etb_cuda PUBLIC CUDA::cudart)

# Add MSVC standard conforming preprocessor for CCCL compatibility
if(MSVC)
    target_compile_options(etb_cuda PRIVATE $<$<COMPILE_LANGUAGE:CUDA>:-Xcompiler=/Zc:preprocessor>)
endif()

set_target_properties(etb_cuda PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    CUDA_RESOLVE_DEVICE_SYMBOLS ON
)

# Combined library (interface library since it just links others)
add_library(etb_full INTERFACE)
target_link_libraries(etb_full INTERFACE etb_core etb_cuda)

# Python bindings
pybind11_add_module(_etb python/bindings.cpp)
target_link_libraries(_etb PRIVATE etb_core)
target_compile_definitions(_etb PRIVATE VERSION_INFO="${PROJECT_VERSION}")
set_target_properties(_etb PROPERTIES
    OUTPUT_NAME "_etb"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/etb"
)

# Tests
enable_testing()
add_subdirectory(tests)

# Installation
install(TARGETS etb_core DESTINATION lib)
install(TARGETS _etb DESTINATION etb)
install(DIRECTORY include/ DESTINATION include)
install(FILES python/etb/__init__.py DESTINATION etb)
install(FILES python/etb/__init__.pyi DESTINATION etb)
install(FILES python/etb/py.typed DESTINATION etb)

# Copy Python files to build directory for development
file(COPY python/etb/__init__.py DESTINATION ${CMAKE_BINARY_DIR}/etb)
file(COPY python/etb/__init__.pyi DESTINATION ${CMAKE_BINARY_DIR}/etb)
file(COPY python/etb/py.typed DESTINATION ${CMAKE_BINARY_DIR}/etb)
