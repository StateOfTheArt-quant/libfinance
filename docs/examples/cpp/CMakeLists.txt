# 参考页示例的 C++ 版本（每个数据族一个可执行文件），由 docs/_shared/update_examples.py 构建并运行。
#
# libfinance 用本仓库的 C++ 客户端：生成器传 -DFETCHCONTENT_SOURCE_DIR_LIBFINANCE=<本仓库>；
# 也可以单独构建（需要 Apache Arrow C++），见 example/cpp/CMakeLists.txt 的说明。
cmake_minimum_required(VERSION 3.18 FATAL_ERROR)
project(libfinance_doc_examples LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT TARGET libfinance::libfinance)
    include(FetchContent)
    set(BUILD_TOOLS OFF CACHE BOOL "" FORCE)
    set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(ENABLE_UNITTEST OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(
        libfinance
        GIT_REPOSITORY https://github.com/StateOfTheArt-quant/libfinance.git
        GIT_TAG        main
        GIT_SHALLOW    TRUE
        SOURCE_SUBDIR  cpp
    )
    FetchContent_MakeAvailable(libfinance)
endif()

file(GLOB EXAMPLES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/[0-9][0-9]_*.cpp)
foreach(source ${EXAMPLES})
    get_filename_component(stem ${source} NAME_WE)
    add_executable(libfinance_${stem} ${source})
    target_link_libraries(libfinance_${stem} PRIVATE libfinance::libfinance)
endforeach()
