API Reference
=============

.. automodule:: cudass
   :members:
   :imported-members:
   :exclude-members: __path__

.. automodule:: cudass.types
   :members:

.. automodule:: cudass.solver
   :members:
   :exclude-members: _StubBackend

Backends
--------

.. automodule:: cudass.backends.factory
   :members:

.. automodule:: cudass.backends.base
   :members:

.. automodule:: cudass.backends.cudss_backend
   :members:
   :exclude-members: _CudssApi, _coo_to_csr, _matrix_type_to_cudss_mtype, _dtype_to_value_type, _nvmath_matrix_create_csr, _nvmath_matrix_create_dn

.. automodule:: cudass.backends.cusolver_dn_backend
   :members:
   :exclude-members: _sparse_to_dense

.. automodule:: cudass.backends.cusolver_sp_backend
   :members:

Factories and utilities
-----------------------

.. automodule:: cudass.factorization.cache
   :members:

.. automodule:: cudass.factorization.refactorization
   :members:

Kernels
-------

.. automodule:: cudass.cuda.kernels
   :members:
