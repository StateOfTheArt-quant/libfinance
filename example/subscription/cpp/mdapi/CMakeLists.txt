# mdapi —— header-only 客户端 SDK，转发自 mdgateway 上游
# 把 include/ 暴露给下游，链接 pthread 即可

add_library(mdapi INTERFACE)

target_include_directories(mdapi INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(mdapi INTERFACE cxx_std_17)

find_package(Threads REQUIRED)
target_link_libraries(mdapi INTERFACE Threads::Threads)
