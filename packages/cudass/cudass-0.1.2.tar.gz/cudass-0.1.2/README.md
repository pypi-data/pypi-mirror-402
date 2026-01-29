# cudass

High-performance CUDA sparse linear solver supporting multiple matrix types, cuDSS, cuSOLVER Dense, and cuSolverSp backends.

**Docs:** [https://moca-technion.github.io/cudass/](https://moca-technion.github.io/cudass/)

## Requirements

- **PyTorch >= 2.0** with CUDA (from [pytorch.org](https://pytorch.org)).
- **nvidia-cudss-cu12** or **nvidia-cudss-cu13** (>=0.6), chosen from `torch.version.cuda` (override: `CUDASS_CUDA_MAJOR=12` or `13`). Install or let the build install it.
- NVIDIA GPU and a driver compatible with your PyTorch CUDA (12.x or 13.x).

## Installation

### From PyPI (recommended)

```bash
pip install cudass
```

Builds from the sdist at install time. Requires **nvcc** (CUDA toolkit) on your system; the build pulls in Cython and torch, and picks `nvidia-cudss-cu12` or `cu13` from your PyTorch’s CUDA.

### From source

```bash
pip install torch Cython   # nvidia-cudss-cu12 or cu13 is chosen from torch.version.cuda
# nvcc (CUDA toolkit): set CUDA_HOME or e.g. module load cuda/12.4 or cuda/13.0
pip install -e .
# Override: CUDASS_CUDA_MAJOR=13 pip install -e .  for CUDA 13
```

## Quick Start

```python
from cudass import CUDASparseSolver, MatrixType

solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
solver.update_matrix((index, value, m, n))
x = solver.solve(b)
```

## License

Apache 2.0. See [LICENSE](LICENSE).

This project uses third-party packages (e.g. PyTorch, NVIDIA cuDSS, Cython) and optional libraries (e.g. nvmath). See [NOTICE](NOTICE) for attributions and a pointer to their licenses. Your use of those components is subject to their terms.
