.. _basic_usage:

Basic Usage
-----------

This section shows how to solve square non-singular systems with different
matrix types and with multiple right-hand sides.

Example: SPD (symmetric positive definite)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``MatrixType.SPD`` when :math:`A` is symmetric and positive definite.
The solver can use Cholesky factorization.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 3×3 SPD: diag [4,5,6] plus small off-diagonals
   # (In practice, use a proper SPD matrix from your problem.)
   index = torch.tensor(
       [[0, 0, 0, 1, 1, 1, 2, 2, 2],
        [0, 1, 2, 0, 1, 2, 0, 1, 2]],
       device="cuda", dtype=torch.int64
   )
   value = torch.tensor(
       [4.0, 0.1, 0.1, 0.1, 5.0, 0.1, 0.1, 0.1, 6.0],
       device="cuda", dtype=torch.float64
   )
   m = n = 3
   b = torch.tensor([1.0, 2.0, 3.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   # Check residual
   dense = torch.zeros(m, n, device="cuda", dtype=torch.float64)
   dense[index[0], index[1]] = value
   residual = (dense @ x - b).abs().max()
   print(residual.item())  # Should be small (e.g. < 1e-10)

Example: General square
~~~~~~~~~~~~~~~~~~~~~~~

For a general non-singular square matrix, use ``MatrixType.GENERAL``. The solver
uses an LU-style factorization.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 2×2 general: A = [[1, 2], [3, 4]]
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([1.0, 2.0, 3.0, 4.0], device="cuda", dtype=torch.float64)
   m = n = 2
   b = torch.tensor([1.0, 1.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.GENERAL, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)
   # True solution: x = [-1, 1]
   print(x)

Example: Symmetric (non-singular)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``MatrixType.SYMMETRIC`` when :math:`A = A^T` and :math:`A` is non-singular
but not necessarily positive definite. The solver can use a symmetric indefinite
factorization.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 2×2 symmetric: [[2, -1], [-1, 2]]
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([2.0, -1.0, -1.0, 2.0], device="cuda", dtype=torch.float64)
   m = n = 2
   b = torch.tensor([1.0, 0.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.SYMMETRIC, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)
   print(x)

.. tip::

   If :math:`A` is symmetric and you know it is positive definite, use
   ``MatrixType.SPD`` for better performance. If in doubt, ``SYMMETRIC`` is safe.

Example: Multiple right-hand sides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To solve :math:`A X = B` with :math:`B` having :math:`k` columns, pass ``b``
with shape ``[m, k]``. The result has shape ``[n, k]``.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # Same A as before (2×2 SPD)
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float64)
   m = n = 2

   # Three RHS: b has shape [2, 3]
   b = torch.tensor(
       [[1.0, 0.0, 2.0],
        [2.0, 1.0, 0.0]],
       device="cuda", dtype=torch.float64
   )

   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)   # x shape [2, 3]

   print(x.shape)  # torch.Size([2, 3])

Calling ``update_matrix`` once and then ``solve`` for many :math:`b` is efficient:
the factorization is reused.

Example: Building COO from a dense matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a dense :math:`A` and want to try cudass, you can convert to COO:

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   A_dense = torch.tensor(
       [[4.0, 1.0, 0.0],
        [1.0, 3.0, 0.5],
        [0.0, 0.5, 2.0]],
       device="cuda", dtype=torch.float64
   )
   # Convert to sparse COO (keeps zeros by default in to_sparse; for a "sparse"
   # view you might first threshold or use a sparsity mask)
   s = A_dense.to_sparse_coo()
   index = s.indices()
   value = s.values()
   m, n = A_dense.shape

   b = torch.tensor([1.0, 2.0, 1.0], device="cuda", dtype=torch.float64)
   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

.. note::

   For a dense matrix, ``torch.linalg.solve(A_dense, b)`` is simpler and often
   faster. cudass is aimed at **sparse** :math:`A` and settings where you reuse
   the factorization for many :math:`b`.

Next
~~~~

* :ref:`rectangular_singular` — Over/underdetermined and singular systems.
* :ref:`advanced_options` — Backend selection, cache, and dtypes.
