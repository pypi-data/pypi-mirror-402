"""
Python package facade for OpenDHT.

This package re-exports the Cython-built core bindings from ``opendht._core``
to preserve the public API (e.g., ``opendht.DhtRunner``), and also exposes a
pure-Python asyncio-friendly wrapper under ``opendht.aio``.
"""


# start delvewheel patch
def _delvewheel_patch_1_12_0():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'opendht.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

from ._core import *  # re-export core Cython bindings

__version__ = version()
__all__ = [name for name in dir() if not name.startswith("_")]
