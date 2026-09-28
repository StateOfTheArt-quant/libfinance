include_guard(GLOBAL)

# contextrpc's client (contextrpc/client.h + codec.h, header-only). Only the client is used, so
# only its dependencies are needed: msgpack-c headers and lz4 -- no libevent, no spdlog.
#   1. -DCONTEXTRPC_SOURCE_DIR=<contextrpc checkout>
#   2. third_party/contextrpc, cloned at CONTEXTRPC_REF when missing
macro(load_contextrpc_client root_dir)
    set(CONTEXTRPC_REF "main" CACHE STRING "contextrpc git ref to fetch when no source dir is given")
    if(NOT CONTEXTRPC_SOURCE_DIR)
        set(CONTEXTRPC_SOURCE_DIR "${root_dir}/third_party/contextrpc")
        if(NOT EXISTS "${CONTEXTRPC_SOURCE_DIR}/contextrpc/include/contextrpc/client.h")
            download_library(contextrpc ${CONTEXTRPC_SOURCE_DIR} ${CONTEXTRPC_REF}
                             https://github.com/walkacross/contextrpc.git)
        endif()
    endif()
    set(CONTEXTRPC_INCLUDE_DIR "${CONTEXTRPC_SOURCE_DIR}/contextrpc/include")
    if(NOT EXISTS "${CONTEXTRPC_INCLUDE_DIR}/contextrpc/client.h")
        message(FATAL_ERROR "contextrpc client not found at ${CONTEXTRPC_SOURCE_DIR}")
    endif()
    find_path(MSGPACK_INCLUDE_DIR msgpack.hpp REQUIRED)
    find_path(LZ4_INCLUDE_DIR lz4frame.h REQUIRED)
    find_library(LZ4_LIBRARY NAMES lz4 REQUIRED)
    find_package(Threads REQUIRED)

    add_library(contextrpc_client INTERFACE)
    add_library(contextrpc::client ALIAS contextrpc_client)
    target_include_directories(contextrpc_client SYSTEM INTERFACE
        $<BUILD_INTERFACE:${CONTEXTRPC_INCLUDE_DIR}>
        $<BUILD_INTERFACE:${MSGPACK_INCLUDE_DIR}>
        $<BUILD_INTERFACE:${LZ4_INCLUDE_DIR}>)
    target_compile_definitions(contextrpc_client INTERFACE MSGPACK_NO_BOOST)
    target_link_libraries(contextrpc_client INTERFACE nlohmann_json::nlohmann_json ${LZ4_LIBRARY} Threads::Threads)
    message(STATUS "contextrpc client from ${CONTEXTRPC_SOURCE_DIR}")
endmacro()
