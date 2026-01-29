/* Minimal declarations for cuDSS using void* and int (no cudss.h typedefs).
 * Link with -lcudss. cudss_bindings.pyx uses this to avoid cudss.h's strong types
 * that conflict with C++ when passing pointers. Phase/status constants come from
 * cudss.h via a separate cdef extern block.
 */
#ifndef CUDASS_CUDSS_DECLS_H
#define CUDASS_CUDSS_DECLS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int cudssCreate(void** handle);
int cudssDestroy(void* handle);
int cudssSetStream(void* handle, void* stream);
int cudssConfigCreate(void** config);
int cudssConfigDestroy(void* config);
int cudssDataCreate(void* handle, void** data);
int cudssDataDestroy(void* handle, void* data);
int cudssExecute(void* handle, int phase, void* config, void* data,
                 void* inputMatrix, void* solution, void* rhs);
int cudssMatrixCreateCsr(void** matrix, int64_t nrows, int64_t ncols, int64_t nnz,
                         void* rowStart, void* rowEnd, void* colIndices, void* values,
                         int indexType, int valueType, int mtype, int mview, int indexBase);
int cudssMatrixCreateDn(void** matrix, int64_t nrows, int64_t ncols, int64_t ld,
                        void* values, int valueType, int layout);
int cudssMatrixDestroy(void* matrix);
int cudssMatrixSetValues(void* matrix, void* values);
int cudssMatrixSetCsrPointers(void* matrix, void* rowStart, void* rowEnd,
                              void* colIndices, void* values);

#ifdef __cplusplus
}
#endif

#endif
