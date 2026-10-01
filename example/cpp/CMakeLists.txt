# One executable per example, named like the source: 01_calendar.cpp -> libfinance_01_calendar.
file(GLOB EXAMPLES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/[0-9][0-9]_*.cpp)
foreach(source ${EXAMPLES})
    get_filename_component(stem ${source} NAME_WE)
    add_executable(libfinance_${stem} ${source})
    target_link_libraries(libfinance_${stem} PRIVATE libfinance::libfinance)
endforeach()
