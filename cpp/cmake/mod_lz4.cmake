# liblz4 (lz4frame.h): the wire protocol's LZ4 frames. A system library (apt liblz4-dev, conda lz4-c).
macro(load_lz4)
    if(NOT TARGET LZ4::lz4)
        find_path(LZ4_INCLUDE_DIR lz4frame.h REQUIRED)
        find_library(LZ4_LIBRARY NAMES lz4 REQUIRED)
        add_library(LZ4::lz4 UNKNOWN IMPORTED)
        set_target_properties(LZ4::lz4 PROPERTIES
            IMPORTED_LOCATION             ${LZ4_LIBRARY}
            INTERFACE_INCLUDE_DIRECTORIES ${LZ4_INCLUDE_DIR})
        message(STATUS "lz4: ${LZ4_LIBRARY}")
    endif()
endmacro()
