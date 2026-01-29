.. _user_guide_overview:

Overview
--------

What is cudass?
~~~~~~~~~~~~~~~

**cudass** is a high-performance sparse linear solver for `PyTorch <https://pytorch.org>`_.
It solves systems :math:`A x = b` where :math:`A` is a sparse matrix on GPU. It supports:

* **Multiple matrix types**: general, symmetric, SPD, rectangular, and singular
* **Several backends**: cuDSS (primary), cuSOLVER Dense (fallback), cuSolverSp (optional)
* **PyTorch integration**: tensors on CUDA, ``float32``/``float64``, and batched RHS

You provide :math:`A` in **COO (coordinate) sparse format** and a right-hand side :math:`b`;
cudass chooses a backend, factorizes :math:`A`, and returns :math:`x`.

When to use cudass
~~~~~~~~~~~~~~~~~~

Use cudass when:

* You have **sparse** :math:`A` and want to reuse the factorization for many :math:`b`
* You need **min-norm** or **least-squares** solutions for singular or rectangular systems
* You want a **single API** that switches between cuDSS, cuSOLVER Dense, and cuSolverSp
  according to the matrix type

For dense matrices or one-off solves, `torch.linalg.solve` may be simpler. For very
large or distributed systems, consider specialized solvers or iterative methods.

Matrix format: COO
~~~~~~~~~~~~~~~~~~

cudass expects :math:`A` as a tuple ``(index, value, m, n)``:

* **``index``**: ``[2, nnz]``, ``int64``, on CUDA. Row indices in ``index[0]``, column
  indices in ``index[1]``. Duplicate :math:`(i,j)` entries are not coalesced; the
  backend will merge them as required.
* **``value``**: ``[nnz]``, ``float32`` or ``float64``, on CUDA. The non-zero values.
* **``m``**, **``n``**: integers. Number of rows and columns.

Example: the matrix

.. math::

   A = \begin{pmatrix} 4 & 1 \\ 1 & 3 \end{pmatrix}

in COO:

.. code-block:: python

   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float64)
   m, n = 2, 2

You can build ``(index, value)`` from ``torch.sparse_coo_tensor`` or from your own
structure; ensure ``index`` and ``value`` are on the same CUDA device and that
``index.dtype == torch.int64``.

Matrix types
~~~~~~~~~~~~

You must pass a **``MatrixType``** when creating the solver. It selects the algorithm
and backend. Choose the one that matches your matrix:

+------------------------------------+------------------+--------------------------------------------------+
| Type                               | Shape            | Description                                      |
+====================================+==================+==================================================+
| ``GENERAL``                        | :math:`m=n`      | General non-singular square                      |
+------------------------------------+------------------+--------------------------------------------------+
| ``SYMMETRIC``                      | :math:`m=n`      | Symmetric (non-singular)                         |
+------------------------------------+------------------+--------------------------------------------------+
| ``SPD``                            | :math:`m=n`      | Symmetric positive definite                      |
+------------------------------------+------------------+--------------------------------------------------+
| ``GENERAL_SINGULAR``               | :math:`m=n`      | General singular, min-norm solution              |
+------------------------------------+------------------+--------------------------------------------------+
| ``SYMMETRIC_SINGULAR``             | :math:`m=n`      | Symmetric singular, min-norm                     |
+------------------------------------+------------------+--------------------------------------------------+
| ``GENERAL_RECTANGULAR``            | :math:`m \neq n` | Rectangular, full rank, least-squares            |
+------------------------------------+------------------+--------------------------------------------------+
| ``GENERAL_RECTANGULAR_SINGULAR``   | :math:`m \neq n` | Rectangular, rank-deficient                      |
+------------------------------------+------------------+--------------------------------------------------+

.. note::

   Picking the correct ``MatrixType`` matters: it affects both accuracy and
   performance. Use ``SPD`` only when :math:`A` is truly positive definite;
   otherwise prefer ``SYMMETRIC`` or ``GENERAL``.

Backends
~~~~~~~~

cudass uses one of these backends internally:

* **cuDSS** — Primary for general, symmetric, and SPD square systems. Fast when
  available; requires the cuDSS bindings to be built.
* **cuSOLVER Dense** — Used for singular, rectangular, and as a fallback when
  cuDSS is missing or returns "not supported". Densifies :math:`A` and uses
  cuSOLVER (via PyTorch / cuBLAS).
* **cuSolverSp** — Reserved for future use (e.g. OOM fallback).

You usually do not need to pick a backend; the solver does it from ``MatrixType``
and shape. Options :ref:`prefer_dense` and :ref:`force_backend` override this when
needed.

Right-hand side and solution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Single RHS**: ``b`` of shape ``[m]``. ``solve(b)`` returns ``x`` of shape ``[n]``.
* **Multiple RHS**: ``b`` of shape ``[m, k]``. ``solve(b)`` returns ``x`` of shape ``[n, k]``.

:math:`A` has shape :math:`(m, n)`, so :math:`b` has :math:`m` rows and :math:`x`
has :math:`n` rows. ``b`` and ``x`` must be on the same CUDA device as the solver
and use ``float32`` or ``float64`` to match the matrix.
