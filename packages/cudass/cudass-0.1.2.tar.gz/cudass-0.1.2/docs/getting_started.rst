.. _getting_started:

Getting Started
===============

This guide helps you install **cudass** and run your first solve. For a detailed
overview of concepts and many examples, see the :ref:`user_guide`.

Prerequisites
-------------

Before installing cudass, ensure you have:

* **Python 3.8+**
* **PyTorch ≥ 2.0** with CUDA support (`pip install torch` from `pytorch.org
  <https://pytorch.org>`_)
* **NVIDIA GPU** and a driver compatible with your PyTorch CUDA version
* **nvidia-cudss-cu12** or **nvidia-cudss-cu13** (>=0.6), chosen from PyTorch's
  ``torch.version.cuda`` (override: ``CUDASS_CUDA_MAJOR=12`` or ``13``). The
  build will pull the matching package.

.. note::

   cudass supports CUDA 12.x and 13.x. The matching ``nvidia-cudss-cu12`` or
   ``nvidia-cudss-cu13`` is chosen from PyTorch's ``torch.version.cuda`` at
   build/install time (override: ``CUDASS_CUDA_MAJOR=12`` or ``13``). No conda
   or system-wide cuDSS is required.

Installation
------------

From PyPI (recommended)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install cudass

This builds cudass from the sdist at install time. You need **nvcc**
(CUDA toolkit) on your system; the build pulls in Cython and torch, and
picks ``nvidia-cudss-cu12`` or ``cu13`` from your PyTorch CUDA.

From source
~~~~~~~~~~~

For development or to use the latest code:

.. code-block:: bash

   git clone https://github.com/MoCA-Technion/cudass.git
   cd cudass
   pip install torch Cython
   # Set CUDA_HOME if nvcc is not on PATH, e.g.:
   #   export CUDA_HOME=/usr/local/cuda
   #   or: module load cuda/12.4  (or cuda/13.0 for CUDA 13)
   pip install -e .
   # nvidia-cudss-cu12 or cu13 is chosen from torch.version.cuda; override:
   #   CUDASS_CUDA_MAJOR=13 pip install -e .

You need **nvcc** (CUDA Toolkit) and **Cython** to build the cuDSS bindings and
the optional ``sparse_to_dense`` CUDA kernel. If the latter fails, the package
still installs; the cuSOLVER Dense backend will densify matrices without it.

Verifying the installation
--------------------------

Check that cudass imports and a minimal solve works:

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # Small 2×2 system: A = [[4,1],[1,3]], b = [1, 2]
   # COO: rows [0,0,1,1], cols [0,1,0,1], values [4,1,1,3]
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float64)
   m, n = 2, 2
   b = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   print(x)           # e.g. tensor([0.0909, 0.6364], device='cuda:0')
   print(solver.backend_name)  # 'cudss' or 'cusolver_dn'

If this runs without errors, you are ready to use cudass.

Troubleshooting
---------------

**``RuntimeError: CUDA is not available``**

* Install PyTorch with CUDA: ``pip install torch`` from the `PyTorch website
  <https://pytorch.org>`_ and select a CUDA build.
* Ensure the NVIDIA driver supports your PyTorch CUDA version.

**``nvidia-cudss-cu12 not found`` / ``cudss_bindings not available``**

* Run: ``pip install nvidia-cudss-cu12``.
* If the cuDSS bindings still fail to build, the solver will fall back to the
  **cusolver_dn** backend. You can force it with
  ``CUDASparseSolver(..., force_backend="cusolver_dn")``.

**``sparse_to_dense kernel not built``**

* The optional ``sparse_to_dense`` kernel needs **nvcc** and **PyTorch** at
  build time. Set ``CUDA_HOME`` (or ``CUDA_PATH``) and reinstall: ``pip install -e .``.
* If it is not built, the cuSOLVER Dense backend uses ``torch.sparse`` to
  densify; slower but works.

**Slow first solve or OOM on large matrices**

* The first solve factors the matrix; later solves with the same structure are
  faster (especially with ``use_cache=True``).
* For very large or ill-conditioned systems, try
  ``force_backend="cusolver_dn"`` or ``prefer_dense=True``; or use a different
  matrix type if it is singular/rectangular.

Next steps
----------

* :ref:`user_guide_overview` — Concepts: matrix format, matrix types, backends.
* :ref:`quickstart` — A first example explained step by step.
* :ref:`basic_usage` — SPD, general, symmetric, and multiple RHS.
* :ref:`rectangular_singular` — Over/underdetermined and singular systems.
* :ref:`advanced_options` — ``prefer_dense``, ``force_backend``, cache, dtypes.
