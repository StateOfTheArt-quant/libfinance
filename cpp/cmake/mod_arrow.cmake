include_guard(GLOBAL)

# Apache Arrow C++: table answers arrive as Arrow IPC and are handed to callers as arrow::Table.
# Found with find_package (conda's pyarrow ships it: -DCMAKE_PREFIX_PATH=$CONDA_PREFIX; images use
# the apache-arrow apt repository).
# Arrow 21 moved the compute kernels (cast, sort, take) into libarrow_compute, which must be linked
# and registered (arrow::compute::Initialize) before use; older Arrow has them inside libarrow.
macro(load_arrow)
    find_package(Arrow REQUIRED)
    message(STATUS "Arrow ${Arrow_VERSION} from ${Arrow_DIR}")
    set(LIBFINANCE_ARROW_COMPUTE "")
    if(Arrow_VERSION VERSION_GREATER_EQUAL 21)
        find_package(ArrowCompute REQUIRED)
        set(LIBFINANCE_ARROW_COMPUTE ArrowCompute::arrow_compute_shared)
    endif()
endmacro()
