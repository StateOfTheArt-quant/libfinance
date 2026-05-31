cmake_minimum_required(VERSION 3.16)
project(libfinance_cpp_subscribe_demo CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(mdapi)

add_executable(cpp_subscribe_demo main.cpp)
target_link_libraries(cpp_subscribe_demo PRIVATE mdapi)
