import os
import re
import shutil
import subprocess
import sys

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist as _sdist

# Set by _resolve_cudss_cu_major() before setup(); used in _get_extensions and install_requires.
_CUDSS_CU_MAJOR = None


def _get_cuda_major_from_torch():
    """CUDA major from PyTorch (torch.version.cuda). 12.x -> "12", 13.x -> "13". Default "12"."""
    override = os.environ.get("CUDASS_CUDA_MAJOR")
    if override in ("12", "13"):
        return override
    try:
        import torch

        cuda = getattr(torch.version, "cuda", None)
        if cuda is None or not cuda:
            return "12"
        if cuda.startswith("12"):
            return "12"
        if cuda.startswith("13"):
            return "13"
    except Exception:
        pass
    return "12"


def _resolve_cudss_cu_major():
    """Set _CUDSS_CU_MAJOR from torch or CUDASS_CUDA_MAJOR. Does not require nvidia-cudss
    (deferred to _get_extensions) so sdist can be built in isolated envs without it."""
    global _CUDSS_CU_MAJOR
    _CUDSS_CU_MAJOR = _get_cuda_major_from_torch()


def _find_cuda_include_dir():
    """Find CUDA include (for library_types.h etc.). CUDA_HOME, nvcc -v, or system."""
    cuda = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    if cuda:
        inc = os.path.join(cuda, "include")
        if os.path.exists(inc):
            return inc
    try:
        out = subprocess.check_output(
            ["nvcc", "-v"], stderr=subprocess.STDOUT, text=True, timeout=5
        )
        for line in out.splitlines():
            if "InstalledDir" in line or "Install" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    d = parts[1].strip()
                    parent = os.path.dirname(os.path.dirname(d))
                    inc = os.path.join(parent, "include")
                    if os.path.exists(inc):
                        return inc
                    inc = os.path.join(os.path.dirname(d), "include")
                    if os.path.exists(inc):
                        return inc
    except Exception:
        pass
    for base in ["/usr/local/cuda", "/opt/cuda", "/usr/lib/cuda"]:
        inc = os.path.join(base, "include")
        if os.path.exists(inc):
            return inc
    for base in [sys.prefix]:
        for sub in (
            os.path.join(
                "lib",
                f"python{sys.version_info.major}.{sys.version_info.minor}",
                "site-packages",
            ),
            "site-packages",
        ):
            inc = os.path.join(base, sub, "triton", "backends", "nvidia", "include")
            if os.path.exists(os.path.join(inc, "library_types.h")):
                return inc
    return None


def _find_nvidia_cudss(cu_major):
    """Find nvidia-cudss-cu{cu_major} (nvidia/cu{cu_major}/lib and include) in site-packages.
    Returns (lib_dir, include_dir) or (None, None).
    """
    import site

    for p in site.getsitepackages():
        lib = os.path.join(p, "nvidia", f"cu{cu_major}", "lib")
        inc = os.path.join(p, "nvidia", f"cu{cu_major}", "include")
        if os.path.isfile(os.path.join(lib, "libcudss.so.0")) and os.path.isdir(inc):
            return lib, inc
    return None, None


def _ensure_nvidia_cudss(cu_major):
    """Ensure nvidia-cudss-cu{cu_major} is available: find or pip install. Raise if not."""
    nv_lib, nv_inc = _find_nvidia_cudss(cu_major)
    if nv_lib is not None and nv_inc is not None:
        return
    pkg = f"nvidia-cudss-cu{cu_major}"
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"{pkg}>=0.6"],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except Exception:
        pass
    nv_lib, nv_inc = _find_nvidia_cudss(cu_major)
    if nv_lib is None or nv_inc is None:
        raise RuntimeError(
            f"{pkg} not found. Install it: pip install {pkg}\n"
            f"The CUDA major (cu{cu_major}) was taken from PyTorch's torch.version.cuda; "
            f"override with CUDASS_CUDA_MAJOR=12 or 13 if needed."
        )


def _ensure_cudss_cpp(root):
    """Compile cudss_bindings.pyx to .cpp with a relative path so setuptools accepts it."""
    pyx = os.path.join(root, "cudass", "cuda", "bindings", "cudss_bindings.pyx")
    cpp = os.path.join(root, "cudass", "cuda", "bindings", "cudss_bindings.cpp")
    if not os.path.exists(pyx):
        return
    if os.path.exists(cpp) and os.path.getmtime(cpp) >= os.path.getmtime(pyx):
        return
    for cmd in [
        [sys.executable, "-m", "cython", "-3", "--cplus", pyx, "-o", cpp],
        [sys.executable, "-m", "Cython", "-3", "--cplus", pyx, "-o", cpp],
        ["cython", "-3", "--cplus", pyx, "-o", cpp],
    ]:
        try:
            subprocess.run(cmd, check=True, cwd=root)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    raise RuntimeError(
        "Cython not found or failed. Install Cython and run: "
        f"cython -3 --cplus {pyx} -o {cpp}"
    )


def _get_extensions():
    exts = []
    _root = os.path.dirname(os.path.abspath(__file__))
    cudss_pyx = os.path.join(_root, "cudass", "cuda", "bindings", "cudss_bindings.pyx")
    if not os.path.exists(cudss_pyx):
        return exts

    cu_major = _CUDSS_CU_MAJOR
    nv_lib, nv_inc = _find_nvidia_cudss(cu_major)
    if nv_lib is None or nv_inc is None:
        try:
            _ensure_nvidia_cudss(cu_major)
            nv_lib, nv_inc = _find_nvidia_cudss(cu_major)
        except Exception:
            pass
    if nv_lib is None or nv_inc is None:
        # Skip cudss when not available (e.g. sdist in isolated env). User install needs it.
        return exts

    bindings_dir = os.path.join(_root, "cudass", "cuda", "bindings")
    include_dirs = [bindings_dir, nv_inc]
    cuda_inc = _find_cuda_include_dir()
    if cuda_inc and cuda_inc not in include_dirs:
        include_dirs.append(cuda_inc)

    # nvidia-cudss-cu* has libcudss.so.0; link with -l:libcudss.so.0. RPATH to
    # nvidia/cu{cu_major}/lib so it is found at runtime.
    extra_link = ["-l:libcudss.so.0"]
    if os.name != "nt":
        extra_link.append(f"-Wl,-rpath,$ORIGIN/../../../nvidia/cu{cu_major}/lib")

    from setuptools import Extension

    _ensure_cudss_cpp(_root)
    exts.append(
        Extension(
            "cudass.cuda.bindings.cudss_bindings",
            sources=["cudass/cuda/bindings/cudss_bindings.cpp"],
            libraries=[],
            library_dirs=[nv_lib],
            include_dirs=include_dirs,
            extra_link_args=extra_link,
            language="c++",
        )
    )
    return exts


def _ensure_cuda_home_for_build():
    """Set CUDA_HOME if unset (CUDA_PATH, nvcc location, or nvcc -v). Helps module load."""
    if os.environ.get("CUDA_HOME"):
        return
    for key in ("CUDA_PATH", "CUDA_HOME"):
        base = os.environ.get(key)
        if base and os.path.isdir(os.path.join(base, "include")):
            os.environ["CUDA_HOME"] = base
            return
    nvcc = os.environ.get("NVCC") or "nvcc"
    try:
        out = subprocess.check_output(
            [nvcc, "-v"], stderr=subprocess.STDOUT, text=True, timeout=5
        )
        for line in out.splitlines():
            if "InstalledDir" in line or "Install" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    d = parts[1].strip()
                    for candidate in (
                        os.path.dirname(os.path.dirname(d)),
                        os.path.dirname(d),
                    ):
                        inc = os.path.join(candidate, "include")
                        if os.path.isdir(inc):
                            os.environ["CUDA_HOME"] = candidate
                            return
    except Exception:
        pass
    nvcc_path = shutil.which("nvcc")
    if nvcc_path and os.path.isfile(nvcc_path):
        candidate = os.path.dirname(os.path.dirname(nvcc_path))
        if os.path.isdir(os.path.join(candidate, "include")):
            os.environ["CUDA_HOME"] = candidate
            return


def _get_sparse_to_dense_ext():
    _root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(_root, "cudass", "cuda", "kernels", "sparse_to_dense.cu")
    if not os.path.exists(path):
        return None
    _ensure_cuda_home_for_build()
    # torch.utils.cpp_extension requires nvcc major == torch.version.cuda major.
    # If they differ (e.g. nvcc 13 + torch cu12), skip to avoid RuntimeError at build.
    try:
        out = subprocess.check_output(
            ["nvcc", "--version"], stderr=subprocess.STDOUT, text=True, timeout=5
        )
        m = re.search(r"release\s+(\d+)\.\d+", out)
        nvcc_major = m.group(1) if m else None
        import torch

        tc = getattr(torch.version, "cuda", None) or ""
        torch_major = tc.split(".")[0] if tc else None
        if nvcc_major and torch_major and nvcc_major != torch_major:
            return None
    except Exception:
        pass
    try:
        from torch.utils.cpp_extension import CUDAExtension

        return CUDAExtension(
            name="cudass.cuda.kernels._sparse_to_dense",
            sources=["cudass/cuda/kernels/sparse_to_dense.cu"],
        )
    except Exception:
        return None


def _build_ext():
    _root = os.path.dirname(os.path.abspath(__file__))
    exts = _get_extensions()
    out = list(exts)
    s2d = _get_sparse_to_dense_ext()
    if s2d is not None:
        out.append(s2d)
    return out


class _sdist_exclude_deps(_sdist):
    """Exclude dependencies.txt from sdist; it is generated by setup.py at install time."""

    def make_distribution(self):
        if hasattr(self, "filelist") and hasattr(self.filelist, "files"):
            self.filelist.files = [f for f in self.filelist.files if f != "dependencies.txt"]
        super().make_distribution()


def _get_cmdclass():
    out = {"sdist": _sdist_exclude_deps}
    try:
        from torch.utils.cpp_extension import BuildExtension

        out["build_ext"] = BuildExtension
    except Exception:
        pass
    return out


_resolve_cudss_cu_major()

# Write dependencies.txt for [tool.setuptools.dynamic] dependencies = { file = "dependencies.txt" }.
# Keeps distribution CUDA-agnostic: nvidia-cudss-cu12 or cu13 chosen from torch / CUDASS_CUDA_MAJOR.
_root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_root, "dependencies.txt"), "w") as f:
    f.write("torch>=2.0\n")
    f.write(f"nvidia-cudss-cu{_CUDSS_CU_MAJOR}>=0.6\n")

setup(
    packages=find_packages(),
    ext_modules=_build_ext(),
    cmdclass=_get_cmdclass(),
)
