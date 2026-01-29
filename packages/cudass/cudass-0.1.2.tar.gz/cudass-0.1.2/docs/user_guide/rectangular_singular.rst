.. _rectangular_singular:

Rectangular and Singular Systems
--------------------------------

cudass can solve rectangular (over/underdetermined) and singular systems. You must
choose the correct :ref:`MatrixType <user_guide_overview>` and understand whether
you get a least-squares or min-norm solution.

Overdetermined systems (least-squares)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When :math:`A` has more rows than columns (:math:`m > n`) and is full rank, the
system :math:`A x = b` is overdetermined. Use ``MatrixType.GENERAL_RECTANGULAR``.
The solver returns a least-squares solution :math:`\min_x \|A x - b\|_2`.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 3×2 overdetermined: 3 equations, 2 unknowns
   # A = [[1, 0], [0, 1], [1, 1]], b = [1, 2, 2]
   # Least-squares solution (e.g. via pseudo-inverse): x ≈ [0.5, 1.5]
   index = torch.tensor([[0, 1, 2, 2], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([1.0, 1.0, 1.0, 1.0], device="cuda", dtype=torch.float64)
   m, n = 3, 2
   b = torch.tensor([1.0, 2.0, 2.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.GENERAL_RECTANGULAR, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   print(x.shape)  # [2]
   # Check residual norm
   dense = torch.zeros(m, n, device="cuda", dtype=torch.float64)
   dense[index[0], index[1]] = value
   res = (dense @ x - b).norm().item()
   print(res)  # Small (least-squares minimizes it)

Underdetermined systems (min-norm)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When :math:`A` has more columns than rows (:math:`m < n`) and is full rank, the
system has infinitely many solutions. Use ``MatrixType.GENERAL_RECTANGULAR``.
The solver returns the **minimum-norm** solution :math:`\min \|x\|_2` subject to
:math:`A x = b`.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 2×3 underdetermined: 2 equations, 3 unknowns
   # A = [[1, 0, 1], [0, 1, 1]], b = [1, 1]
   index = torch.tensor([[0, 0, 1, 1], [0, 2, 1, 2]], device="cuda", dtype=torch.int64)
   value = torch.tensor([1.0, 1.0, 1.0, 1.0], device="cuda", dtype=torch.float64)
   m, n = 2, 3
   b = torch.tensor([1.0, 1.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.GENERAL_RECTANGULAR, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   print(x.shape)  # [3]
   # x satisfies A @ x = b and has minimum 2-norm among such x

Square singular (min-norm)
~~~~~~~~~~~~~~~~~~~~~~~~~~

For a **square** but **singular** matrix, use:

* ``MatrixType.GENERAL_SINGULAR`` — general singular; min-norm solution.
* ``MatrixType.SYMMETRIC_SINGULAR`` — symmetric singular; min-norm solution.

The solver returns :math:`x` with minimum :math:`\|x\|_2` among those satisfying
:math:`A x = b` (in the least-squares sense when inconsistent).

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 2×2 singular: A = [[1, 1], [1, 1]], null space along (1, -1)
   # b = [2, 2] in the range; one solution is (1, 1), min-norm is (1, 1)
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([1.0, 1.0, 1.0, 1.0], device="cuda", dtype=torch.float64)
   m = n = 2
   b = torch.tensor([2.0, 2.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.GENERAL_SINGULAR, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

   print(x)  # e.g. [1, 1] (min-norm solution)

Rectangular and rank-deficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``MatrixType.GENERAL_RECTANGULAR_SINGULAR`` when :math:`m \neq n` and :math:`A`
is rank-deficient. The solver returns a min-norm least-squares solution (as with
:math:`A^+ b` via SVD).

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # 3×2 but rank 1: rows are [1,1], [2,2], [3,3]
   index = torch.tensor([[0, 0, 1, 1, 2, 2], [0, 1, 0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([1.0, 1.0, 2.0, 2.0, 3.0, 3.0], device="cuda", dtype=torch.float64)
   m, n = 3, 2
   b = torch.tensor([1.0, 2.0, 3.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(matrix_type=MatrixType.GENERAL_RECTANGULAR_SINGULAR, use_cache=True)
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)

.. tip::

   For singular or rectangular types, the backend is typically **cuSOLVER Dense**
   (densifies :math:`A` and uses SVD or similar). Ensure you have enough GPU
   memory for the dense :math:`m \times n` matrix.

Summary of matrix types for rectangular/singular
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-----------------------------------+------------------+--------------------------------------+
| Type                              | Shape            | Solution                             |
+===================================+==================+======================================+
| ``GENERAL_RECTANGULAR``           | :math:`m \neq n` | Least-squares or min-norm (full rank)|
+-----------------------------------+------------------+--------------------------------------+
| ``GENERAL_RECTANGULAR_SINGULAR``  | :math:`m \neq n` | Min-norm least-squares (rank-def.)   |
+-----------------------------------+------------------+--------------------------------------+
| ``GENERAL_SINGULAR``              | :math:`m = n`    | Min-norm                             |
+-----------------------------------+------------------+--------------------------------------+
| ``SYMMETRIC_SINGULAR``            | :math:`m = n`    | Min-norm (symmetric)                 |
+-----------------------------------+------------------+--------------------------------------+

Next
~~~~

* :ref:`advanced_options` — ``prefer_dense``, ``force_backend``, cache, and dtypes.
