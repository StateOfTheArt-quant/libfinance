cmake_minimum_required(VERSION 3.16 FATAL_ERROR)
project(libfinance VERSION 0.1.0 LANGUAGES CXX)

# ================================================================
# prerequisite
# ================================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

option(ENABLE_UNITTEST "unittest for libfinance" OFF)
option(BUILD_TOOLS "build libfinance-call (used by the conformance tests)" ON)
option(BUILD_EXAMPLES "build the examples" OFF)

message(STATUS "======================================================")
message(STATUS "libfinance (C++) version: ${PROJECT_VERSION}")
message(STATUS "unittest:                 ${ENABLE_UNITTEST}")
message(STATUS "======================================================")

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

set(CMAKE_INSTALL_RPATH "$ORIGIN/../${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# load custom cmake modules (cmake/mod_*.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/api.cmake)

# third-party
load_nlohmann_json(${CMAKE_CURRENT_SOURCE_DIR} v3.11.3)
load_arrow()
load_contextrpc_client(${CMAKE_CURRENT_SOURCE_DIR})

# ================================================================
# targets
# ================================================================

add_subdirectory(libfinance)
if(BUILD_TOOLS)
    add_subdirectory(tools)
endif()
if(BUILD_EXAMPLES)
    add_subdirectory(example)
endif()

# ================================================================
# package config: find_package(libfinance 0.1 REQUIRED)
# ================================================================

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/libfinanceConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/libfinanceConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/libfinance
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/libfinanceConfigVersion.cmake
    VERSION       ${PROJECT_VERSION}
    COMPATIBILITY SameMinorVersion
)
install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/libfinanceConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/libfinanceConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/libfinance
)

# ================================================================
# package: cmake --build build --target package
# ================================================================

if(NOT CMAKE_SYSTEM_PROCESSOR)
    execute_process(COMMAND uname -m OUTPUT_VARIABLE SYS_ARCH OUTPUT_STRIP_TRAILING_WHITESPACE)
else()
    set(SYS_ARCH ${CMAKE_SYSTEM_PROCESSOR})
endif()
set(CPACK_PACKAGE_NAME        "libfinance")
set(CPACK_PACKAGE_VERSION     ${PROJECT_VERSION})
set(CPACK_PACKAGE_VENDOR      "StateOfTheArt-quant")
set(CPACK_PACKAGE_DESCRIPTION "libfinance C++ client")
set(CPACK_GENERATOR           "TGZ")
set(CPACK_PACKAGE_FILE_NAME   "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}-${CMAKE_SYSTEM_NAME}-${SYS_ARCH}")
include(CPack)

# ================================================================
# unittest
# ================================================================

if(ENABLE_UNITTEST)
    download_googletest()
    enable_testing()
    add_subdirectory(test)
endif()
