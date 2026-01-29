# cython: language_level=3
"""Cython bindings for cuDSS. cudss_decls.h for API (void*); link -lcudss.
Phase/status constants match cudss.h 0.6+ (nvidia-cudss-cu* >= 0.6)."""

from libc.stdint cimport int64_t

# ---- C API from cudss_decls.h (void* to avoid including cudss.h; no type conflicts) ----
cdef extern from "cudss_decls.h":
    int cudssCreate(void** handle)
    int cudssDestroy(void* handle)
    int cudssSetStream(void* handle, void* stream)
    int cudssConfigCreate(void** config)
    int cudssConfigDestroy(void* config)
    int cudssDataCreate(void* handle, void** data)
    int cudssDataDestroy(void* handle, void* data)
    int cudssExecute(void* handle, int phase, void* config, void* data,
                     void* inputMatrix, void* solution, void* rhs)
    int cudssMatrixCreateCsr(void** matrix, int64_t nrows, int64_t ncols, int64_t nnz,
                             void* rowStart, void* rowEnd, void* colIndices, void* values,
                             int indexType, int valueType, int mtype, int mview, int indexBase)
    int cudssMatrixCreateDn(void** matrix, int64_t nrows, int64_t ncols, int64_t ld,
                            void* values, int valueType, int layout)
    int cudssMatrixDestroy(void* matrix)
    int cudssMatrixSetValues(void* matrix, void* values)
    int cudssMatrixSetCsrPointers(void* matrix, void* rowStart, void* rowEnd,
                                  void* colIndices, void* values)

# ---- Constants: match cudss.h 0.6+ (>=0.6 required). Including cudss.h would pull ----
# ---- its strong-typed API and conflict with cudss_decls.h in C++, so we mirror.  ----
CUDSS_STATUS_SUCCESS = 0
CUDSS_STATUS_NOT_INITIALIZED = 1
CUDSS_STATUS_ALLOC_FAILED = 2
CUDSS_STATUS_INVALID_VALUE = 3
CUDSS_STATUS_NOT_SUPPORTED = 4
CUDSS_STATUS_EXECUTION_FAILED = 5
CUDSS_STATUS_INTERNAL_ERROR = 6
# Phases: 0.6+ bitmask (0.4/0.5 used different values)
CUDSS_PHASE_ANALYSIS = (1 << 0) | (1 << 1)
CUDSS_PHASE_FACTORIZATION = (1 << 2)
CUDSS_PHASE_SOLVE = (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 8) | (1 << 9)
CUDSS_MTYPE_GENERAL = 0
CUDSS_MTYPE_SYMMETRIC = 1
CUDSS_MTYPE_SPD = 3
CUDSS_MVIEW_FULL = 0
CUDSS_BASE_ZERO = 0
CUDSS_LAYOUT_COL_MAJOR = 0


def _check_status(int status):
    if status == CUDSS_STATUS_SUCCESS:
        return
    msg = f"cuDSS error: status={status}"
    if status == CUDSS_STATUS_NOT_SUPPORTED:
        msg = "cuDSS not supported for this matrix (try cuSOLVER Dense)"
    elif status == CUDSS_STATUS_ALLOC_FAILED:
        msg = "cuDSS allocation failed (OOM?)"
    elif status == CUDSS_STATUS_INVALID_VALUE:
        msg = "cuDSS invalid value"
    elif status == CUDSS_STATUS_EXECUTION_FAILED:
        msg = "cuDSS execution failed"
    elif status == CUDSS_STATUS_INTERNAL_ERROR:
        msg = "cuDSS internal error"
    raise RuntimeError(msg)


# cudaDataType_t: from cudass.cuda.cuda_types (matches CUDA library_types.h)
from cudass.cuda.cuda_types import CUDA_R_32F, CUDA_R_64F, CUDA_R_32I, CUDA_R_64I


def create_handle():
    cdef void* h = NULL
    _check_status(cudssCreate(<void**>&h))
    return <size_t>h


def destroy_handle(size_t handle):
    _check_status(cudssDestroy(<void*>handle))


def set_stream(size_t handle, size_t stream):
    _check_status(cudssSetStream(<void*>handle, <void*>stream))


def config_create():
    cdef void* c = NULL
    _check_status(cudssConfigCreate(<void**>&c))
    return <size_t>c


def config_destroy(size_t config):
    _check_status(cudssConfigDestroy(<void*>config))


def data_create(size_t handle):
    cdef void* d = NULL
    _check_status(cudssDataCreate(<void*>handle, <void**>&d))
    return <size_t>d


def data_destroy(size_t handle, size_t data):
    _check_status(cudssDataDestroy(<void*>handle, <void*>data))


def execute(size_t handle, int phase, size_t config, size_t data,
            size_t input_matrix, size_t solution, size_t rhs):
    _check_status(cudssExecute(
        <void*>handle, phase, <void*>config, <void*>data,
        <void*>input_matrix, <void*>solution, <void*>rhs
    ))


def matrix_create_csr(long long nrows, long long ncols, long long nnz,
                      size_t row_start_ptr, size_t col_indices_ptr, size_t values_ptr,
                      int index_type, int value_type, int mtype, int mview, int index_base,
                      size_t row_end_ptr=0):
    cdef void* mat = NULL
    cdef void* row_end = <void*>row_end_ptr if row_end_ptr else NULL
    _check_status(cudssMatrixCreateCsr(
        <void**>&mat, nrows, ncols, nnz,
        <void*>row_start_ptr, row_end, <void*>col_indices_ptr, <void*>values_ptr,
        index_type, value_type, mtype, mview, index_base
    ))
    return <size_t>mat


def matrix_create_dn(long long nrows, long long ncols, long long ld,
                     size_t values_ptr, int value_type, int layout):
    cdef void* mat = NULL
    _check_status(cudssMatrixCreateDn(
        <void**>&mat, nrows, ncols, ld, <void*>values_ptr,
        value_type, layout
    ))
    return <size_t>mat


def matrix_destroy(size_t matrix):
    _check_status(cudssMatrixDestroy(<void*>matrix))


def matrix_set_values(size_t matrix, size_t values_ptr):
    _check_status(cudssMatrixSetValues(<void*>matrix, <void*>values_ptr))


def matrix_set_csr_pointers(size_t matrix, size_t row_start_ptr, size_t col_indices_ptr,
                            size_t values_ptr, size_t row_end_ptr=0):
    cdef void* row_end = <void*>row_end_ptr if row_end_ptr else NULL
    _check_status(cudssMatrixSetCsrPointers(
        <void*>matrix, <void*>row_start_ptr, row_end,
        <void*>col_indices_ptr, <void*>values_ptr
    ))
