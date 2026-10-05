# libfinance-call: one function by name with JSON arguments (conformance/ drives it).
add_executable(libfinance-call libfinance_call.cpp)
# rows_of() lives with the library's internals; the tool is part of this tree
target_include_directories(libfinance-call PRIVATE ${PROJECT_SOURCE_DIR}/libfinance/src)
target_link_libraries(libfinance-call PRIVATE libfinance::libfinance)
install(TARGETS libfinance-call RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
