"""cudaDataType_t values for cuDSS. No nvmath or CUDA include required.

These ints are passed to cuDSS (cudssMatrixCreateCsr, cudssMatrixCreateDn).
They must match the cudaDataType_t enum in the CUDA toolkit's library_types.h
that cuDSS was built against.

Canonical source: CUDA include/library_types.h (cudaDataType_t). The exact
order varies by CUDA version. The defaults below match CUDA 11+ as used by
typical cuDSS builds:

  CUDA_R_32F = 0   (float)
  CUDA_R_64F = 1   (double)
  CUDA_R_32I = 10  (int32, for row/col indices)
  CUDA_R_64I = 12  (int64)

Override via env: CUDASS_CUDA_R_32F, CUDASS_CUDA_R_64F, CUDASS_CUDA_R_32I.
"""

import os

# Match cudaDataType_t from CUDA 11+ library_types.h
_CUDA_R_32F = 0
_CUDA_R_64F = 1
_CUDA_R_32I = 10
_CUDA_R_64I = 12

# Optional override from environment (int values)
if os.environ.get("CUDASS_CUDA_R_32F") is not None:
    _CUDA_R_32F = int(os.environ["CUDASS_CUDA_R_32F"])
if os.environ.get("CUDASS_CUDA_R_64F") is not None:
    _CUDA_R_64F = int(os.environ["CUDASS_CUDA_R_64F"])
if os.environ.get("CUDASS_CUDA_R_32I") is not None:
    _CUDA_R_32I = int(os.environ["CUDASS_CUDA_R_32I"])

CUDA_R_32F = _CUDA_R_32F
CUDA_R_64F = _CUDA_R_64F
CUDA_R_32I = _CUDA_R_32I
CUDA_R_64I = _CUDA_R_64I
