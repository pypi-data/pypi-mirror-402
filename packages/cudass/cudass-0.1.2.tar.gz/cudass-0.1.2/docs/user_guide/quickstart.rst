.. _quickstart:

Quick Start
-----------

This page walks through a minimal example: a 2×2 symmetric positive definite system
:math:`A x = b`. You will see how to build the sparse matrix, create the solver,
and obtain the solution.

The example
~~~~~~~~~~~

We solve:

.. math::

   \begin{pmatrix} 4 & 1 \\ 1 & 3 \end{pmatrix}
   \begin{pmatrix} x_0 \\ x_1 \end{pmatrix}
   =
   \begin{pmatrix} 1 \\ 2 \end{pmatrix}

.. code-block:: python
   :linenos:

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 1. Sparse matrix A in COO: (index [2,nnz], value [nnz], m, n)
   #    A[0,0]=4, A[0,1]=1, A[1,0]=1, A[1,1]=3
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float64)
   m, n = 2, 2

   # 2. Right-hand side b [m]
   b = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float64)

   # 3. Create solver, set A, solve
   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   print(x)                    # tensor([0.0909, 0.6364], device='cuda:0', dtype=torch.float64)
   print(solver.backend_name)  # 'cudss' or 'cusolver_dn'

What each part does
~~~~~~~~~~~~~~~~~~~

**Lines 7–9 — Sparse matrix in COO**

* ``index[0]`` = row indices ``[0, 0, 1, 1]``, ``index[1]`` = column indices ``[0, 1, 0, 1]``.
* ``value`` = ``[4, 1, 1, 3]`` for entries (0,0), (0,1), (1,0), (1,1).
* ``m, n = 2, 2``: 2×2 matrix. All tensors must be on CUDA and ``index`` must be ``int64``.

**Line 12 — Right-hand side**

* ``b`` has shape ``[m]`` = ``[2]``. For multiple RHS, use shape ``[m, k]``.

**Lines 15–17 — Solver and solve**

* ``CUDASparseSolver(matrix_type=MatrixType.SPD, ...)``: we declare :math:`A` as SPD so
  the solver can use Cholesky (via cuDSS or cuSOLVER).
* ``update_matrix((index, value, m, n))``: sets :math:`A` and factorizes it. Call again
  whenever :math:`A` (or its sparsity) changes.
* ``solve(b)``: returns :math:`x` with shape ``[n]`` on the same device and dtype as ``b``.

**Line 20 — Backend**

* ``solver.backend_name`` is ``'cudss'`` if the cuDSS backend is in use, or
  ``'cusolver_dn'`` if it fell back to cuSOLVER Dense.

Running it
~~~~~~~~~~

Save the script (e.g. ``quickstart.py``) and run:

.. code-block:: bash

   python quickstart.py

Ensure PyTorch sees CUDA (``torch.cuda.is_available() == True``) and that cudass
is installed (see :ref:`getting_started`).

Reusing the factorization
~~~~~~~~~~~~~~~~~~~~~~~~~~

If :math:`A` stays the same and only :math:`b` changes, call ``solve`` multiple
times without calling ``update_matrix`` again:

.. code-block:: python

   x1 = solver.solve(b)
   b2 = torch.tensor([0.5, 1.5], device="cuda", dtype=torch.float64)
   x2 = solver.solve(b2)

The factorization from the first ``update_matrix`` is reused (and cached when
``use_cache=True``).

Next steps
~~~~~~~~~~

* :ref:`basic_usage` — More matrix types (general, symmetric) and multiple RHS.
* :ref:`rectangular_singular` — Over/underdetermined and singular systems.
* :ref:`advanced_options` — ``prefer_dense``, ``force_backend``, cache, and dtypes.
