# pdflinkcheck_rust/__init__.py
import os
import sys
import ctypes

_package_dir = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    # Mandatory for Windows
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(_package_dir)
    else:
        os.environ["PATH"] = _package_dir + os.pathsep + os.environ.get("PATH", "")
else:
    # Linux/macOS: Pre-load libpdfium.so into the global symbol table
    # This makes the library visible to the Rust extension when it loads.
    _lib_name = "libpdfium.so" if sys.platform == "linux" else "libpdfium.dylib"
    _lib_path = os.path.join(_package_dir, _lib_name)
        
    if os.path.exists(_lib_path):
        try:
            # RTLD_GLOBAL is key: it makes the symbols available to other libs (like our Rust one)
            ctypes.CDLL(_lib_path, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            # Fallback if manual loading fails; RPATH might still work
            pass
# We import the rust binary here. 
# Because of RPATH (Linux) and add_dll_directory (Win), it will find libpdfium.
from .pdflinkcheck_rust import analyze_pdf

__all__ = ["analyze_pdf"]
