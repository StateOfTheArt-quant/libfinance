include_guard(GLOBAL)

# googletest：third_party/googletest 存在就直接用，否则从 GitHub 拉。
# （模板里的 github.com.cnpmjs.org 镜像已经停止服务，这里用官方地址，可用 GTEST_URL 覆盖。）
function(download_googletest)
    set(GTEST_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/googletest)
    set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

    if(EXISTS ${GTEST_DIR})
        message(STATUS "${GTEST_DIR} already exists, skip download")
        add_subdirectory(${GTEST_DIR} ${CMAKE_BINARY_DIR}/googletest EXCLUDE_FROM_ALL)
    else()
        set(GTEST_URL "https://github.com/google/googletest.git" CACHE STRING "googletest repository")
        set(GTEST_VER "1.14.0" CACHE STRING "googletest version to download")
        message(STATUS "Downloading googletest v${GTEST_VER} from ${GTEST_URL}")
        include(FetchContent)
        FetchContent_Declare(
            gtest_suites
            GIT_REPOSITORY ${GTEST_URL}
            GIT_TAG        v${GTEST_VER}
            GIT_SHALLOW    TRUE
            SOURCE_DIR     ${GTEST_DIR}
        )
        FetchContent_MakeAvailable(gtest_suites)
    endif()
endfunction()
