cmake_minimum_required(VERSION 3.16 FATAL_ERROR)

configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/include/libfinance/version.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/generated/libfinance/version.h
    @ONLY
)

file(GLOB_RECURSE ALL_SRC_FILES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)

add_library(libfinance SHARED ${ALL_SRC_FILES})
add_library(libfinance::libfinance ALIAS libfinance)
set_target_properties(libfinance PROPERTIES
    OUTPUT_NAME finance          # liblibfinance.so would read oddly
    VERSION     ${PROJECT_VERSION}
    SOVERSION   ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
)
target_include_directories(libfinance
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/generated>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)
# PUBLIC: the headers return arrow::Table and nlohmann::json
target_link_libraries(libfinance
    PUBLIC
        nlohmann_json::nlohmann_json
        Arrow::arrow_shared
    PRIVATE
        LZ4::lz4
)
target_compile_options(libfinance PRIVATE -Wall -Wextra)

install(TARGETS libfinance
    EXPORT   libfinanceTargets
    LIBRARY  DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE  DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME  DESTINATION ${CMAKE_INSTALL_BINDIR}
    INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    PATTERN "*.in" EXCLUDE
)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/generated/libfinance/version.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/libfinance
)
install(EXPORT libfinanceTargets
    FILE        libfinanceTargets.cmake
    NAMESPACE   libfinance::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/libfinance
)
