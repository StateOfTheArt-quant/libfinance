project(unittest)

set(GTEST_LIB gtest gtest_main)

# Offline tests; the answers of a live server are compared with the Python client by contract/conformance/.
function(libfinance_test name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PRIVATE libfinance::libfinance ${GTEST_LIB})
  add_test(NAME ${name} COMMAND ${name})
endfunction()

libfinance_test(test_types test_types.cpp)
libfinance_test(test_tables test_tables.cpp)
libfinance_test(test_quote_protocol test_quote_protocol.cpp)
libfinance_test(test_quote_api test_quote_api.cpp)
libfinance_test(test_login test_login.cpp)
# its loopback server reads the client's LZ4-framed requests
target_link_libraries(test_login PRIVATE LZ4::lz4)
