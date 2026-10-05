# libfinance 的 C++ 示例：每个数据族一个可执行文件（01_calendar.cpp -> libfinance_01_calendar）。
#
# 单独使用（下载这个目录即可，只需事先装好 Apache Arrow C++）：
#
#   cmake -S . -B build -DCMAKE_PREFIX_PATH=<Arrow 的安装前缀>
#   cmake --build build -j
#   build/libfinance_03_daybar
#
# libfinance 由 FetchContent 下载并一起编译（LIBFINANCE_GIT_TAG 选版本；本地已有源码时传
# -DFETCHCONTENT_SOURCE_DIR_LIBFINANCE=<libfinance 仓库>）。在 libfinance 仓库里以
# -DBUILD_EXAMPLES=ON 构建时直接用那里的 libfinance，不再下载。
cmake_minimum_required(VERSION 3.18 FATAL_ERROR)
project(libfinance_examples LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT TARGET libfinance::libfinance)
    include(FetchContent)
    set(LIBFINANCE_GIT_TAG "main" CACHE STRING "libfinance git ref (branch, tag or commit) to build the examples against")
    # only the library: no tools, tests or nested examples
    set(BUILD_TOOLS OFF CACHE BOOL "" FORCE)
    set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(ENABLE_UNITTEST OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        libfinance
        GIT_REPOSITORY https://github.com/StateOfTheArt-quant/libfinance.git
        GIT_TAG        ${LIBFINANCE_GIT_TAG}
        GIT_SHALLOW    TRUE
        SOURCE_SUBDIR  cpp            # the C++ client is libfinance/cpp
    )
    FetchContent_MakeAvailable(libfinance)
endif()

file(GLOB EXAMPLES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/[0-9][0-9]_*.cpp)
foreach(source ${EXAMPLES})
    get_filename_component(stem ${source} NAME_WE)
    add_executable(libfinance_${stem} ${source})
    target_link_libraries(libfinance_${stem} PRIVATE libfinance::libfinance)
endforeach()
