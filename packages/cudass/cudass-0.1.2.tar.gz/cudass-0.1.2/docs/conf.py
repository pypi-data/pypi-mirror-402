# Sphinx configuration for cudass
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock C/CUDA extensions so docs build without nvcc or built binaries
autodoc_mock_imports = [
    "cudass.cuda.bindings.cudss_bindings",
    "cudass.cuda.kernels._sparse_to_dense",
]

project = "cudass"
copyright = "2025 cudass contributors"
author = "cudass contributors"
version = "0.1.0"
release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

exclude_patterns = ["_build"]

# Furo theme
html_theme = "furo"
html_title = "cudass"
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2962ff",
        "color-brand-content": "#2962ff",
    },
    "dark_css_variables": {
        "color-brand-primary": "#5b8def",
        "color-brand-content": "#5b8def",
    },
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
}

# Intersphinx: Python, PyTorch
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "torch": ("https://pytorch.org/docs/stable", None),
}

# Napoleon for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# Autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
