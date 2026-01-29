.. _advanced_options:

Advanced Options
----------------

This section covers solver knobs and patterns: backend selection, factorization
cache, dtypes, and when to tell the solver that the sparsity pattern of :math:`A`
has changed.

.. _prefer_dense:

Prefer cuSOLVER Dense (``prefer_dense``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the solver tries **cuDSS** first for general, symmetric, and SPD
square systems. If you prefer to use **cuSOLVER Dense** instead (e.g. to avoid
cuDSS or to work around rectangular cuDSS limitations), set ``prefer_dense=True``:

.. code-block:: python

   from cudass import CUDASparseSolver, MatrixType

   solver = CUDASparseSolver(
       matrix_type=MatrixType.SPD,
       use_cache=True,
       prefer_dense=True,
   )
   # ... update_matrix, solve ...

The solver will choose the ``cusolver_dn`` backend for supported matrix types,
which densifies :math:`A` and uses cuSOLVER (via PyTorch).

.. _force_backend:

Forcing a specific backend (``force_backend``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can force a backend and disable fallback with ``force_backend``:

.. code-block:: python

   solver = CUDASparseSolver(
       matrix_type=MatrixType.GENERAL,
       force_backend="cusolver_dn",   # or "cudss", "cusolver_sp"
   )

* ``"cudss"`` — Use cuDSS only; raises if cuDSS bindings are missing or
  cuDSS returns "not supported".
* ``"cusolver_dn"`` — Use cuSOLVER Dense; works for all supported matrix types.
* ``"cusolver_sp"`` — Reserved for cuSolverSp (currently a stub).

Use ``force_backend`` when you need reproducibility, when debugging a specific
backend, or when fallback is undesirable (e.g. you want to detect that cuDSS
is unavailable).

.. note::

   If you set ``force_backend="cudss"`` and cuDSS is not built or returns
   "not supported" for the matrix, the solver will raise. Use
   ``force_backend="cusolver_dn"`` for a robust fallback.

Factorization cache (``use_cache``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``CUDASparseSolver(..., use_cache=True)`` (the default) caches factorizations so
that when you call ``update_matrix`` again with the **same sparsity pattern** and
matrix shape, only the values are updated and refactorization can be faster. The
cache has a limited size; old entries are evicted.

Set ``use_cache=False`` to disable caching (e.g. to reduce memory or if you
never reuse the same structure):

.. code-block:: python

   solver = CUDASparseSolver(matrix_type=MatrixType.SPD, use_cache=False)

Float32 vs float64
~~~~~~~~~~~~~~~~~~

You can use ``torch.float32`` or ``torch.float64`` for ``value`` and ``b``. Pass
``dtype`` when creating the solver if you want to enforce a specific precision;
otherwise it is inferred from the first ``update_matrix``.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   # Use float32; index, m, n as in other examples
   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float32)
   m, n = 2, 2
   b = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float32)

   solver = CUDASparseSolver(
       matrix_type=MatrixType.SPD,
       dtype=torch.float32,   # optional; can be inferred from value
   )
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)  # same dtype as b

``b`` and the solution :math:`x` must use the same dtype as the matrix values.
For ill-conditioned or large systems, ``float64`` can improve robustness.

Structure change vs value-only update
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you call ``update_matrix`` again because :math:`A` has changed, you can tell
the solver whether only the **values** changed or the **sparsity pattern** (or
shape) changed:

.. code-block:: python

   # Only values changed (same non-zero pattern, same m, n) — faster update
   solver.update_matrix((index_new, value_new, m, n), structure_changed=False)

   # Sparsity pattern or shape changed — full refactorization
   solver.update_matrix((index_new, value_new, m_new, n_new), structure_changed=True)

If you omit ``structure_changed`` (or pass ``None``), the solver **auto-detects**
by comparing with the previous :math:`A`: same shape and same ``index``
→ value-only; otherwise → structure change.

.. tip::

   For value-only updates, passing ``structure_changed=False`` avoids
   unnecessary checks. For a fully new matrix, ``structure_changed=True`` or
   ``None`` is fine.

Device
~~~~~~

The solver uses the device of the tensors you pass to ``update_matrix``. You can
also set ``device=torch.device("cuda:0")`` at construction to fix the device;
``update_matrix`` and ``solve`` will require tensors on that device.

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   solver = CUDASparseSolver(
       matrix_type=MatrixType.SPD,
       device=torch.device("cuda:1"),  # pin to GPU 1
   )
   # index, value, b must be on cuda:1

If ``device=None`` (the default), the device is taken from the first
``update_matrix`` call.

Inspecting the backend
~~~~~~~~~~~~~~~~~~~~~~

After the first ``update_matrix`` (or before, when no backend is chosen yet),
you can inspect which backend is in use:

.. code-block:: python

   print(solver.backend_name)  # 'cudss', 'cusolver_dn', 'cusolver_sp', or 'stub'

``'stub'`` appears only before the first ``update_matrix`` that triggers
factorization. After that, it is one of the real backend names.

Complete example: all options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import torch
   from cudass import CUDASparseSolver, MatrixType

   index = torch.tensor([[0, 0, 1, 1], [0, 1, 0, 1]], device="cuda", dtype=torch.int64)
   value = torch.tensor([4.0, 1.0, 1.0, 3.0], device="cuda", dtype=torch.float64)
   m, n = 2, 2
   b = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float64)

   solver = CUDASparseSolver(
       matrix_type=MatrixType.SPD,
       use_cache=True,
       dtype=torch.float64,
       device=None,
       prefer_dense=False,
       force_backend=None,
   )
   solver.update_matrix((index, value, m, n))
   x = solver.solve(b)
   print(solver.backend_name, x)

For more details, see the :doc:`API reference <../api/index>` and the docstrings
of :class:`cudass.CUDASparseSolver`.
