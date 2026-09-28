include_guard(GLOBAL)

# Apache Arrow C++: table answers arrive as Arrow IPC and are handed to callers as arrow::Table.
# Found with find_package (conda's pyarrow ships it: -DCMAKE_PREFIX_PATH=$CONDA_PREFIX; images use
# the apache-arrow apt repository).
macro(load_arrow)
    find_package(Arrow REQUIRED)
    message(STATUS "Arrow ${Arrow_VERSION} from ${Arrow_DIR}")
endmacro()
