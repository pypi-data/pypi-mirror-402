"""FFI bindings for the KeraDB native library."""

import ctypes
import os
import platform
import sys
from pathlib import Path
from typing import Optional


class KeraDBFFI:
    """Wrapper for KeraDB native library functions."""

    def __init__(self):
        """Initialize FFI bindings by loading the native library."""
        self._lib = self._load_library()
        self._setup_functions()

    def _load_library(self) -> ctypes.CDLL:
        """Load the appropriate native library for the current platform."""
        system = platform.system()
        
        # Determine library name based on platform
        if system == "Windows":
            lib_name = "keradb.dll"
        elif system == "Darwin":
            lib_name = "libkeradb.dylib"
        else:
            lib_name = "libkeradb.so"
        
        # Search paths for the library
        search_paths = [
            # Current directory
            Path.cwd() / lib_name,
            # SDK directory
            Path(__file__).parent / lib_name,
            # Project root target/release
            Path(__file__).parent.parent.parent.parent / "target" / "release" / lib_name,
            # System library paths (will be searched automatically by ctypes)
        ]
        
        # Try to load from search paths
        for path in search_paths:
            if path.exists():
                try:
                    return ctypes.CDLL(str(path))
                except OSError:
                    continue
        
        # Try system paths as last resort
        try:
            return ctypes.CDLL(lib_name)
        except OSError as e:
            raise RuntimeError(
                f"Failed to load KeraDB library ({lib_name}). "
                f"Make sure it's built and in your library path. Error: {e}"
            )

    def _setup_functions(self):
        """Setup function signatures for all FFI functions."""
        # Type definitions
        KeraDBHandle = ctypes.c_void_p
        
        # Database operations
        self._lib.keradb_create.argtypes = [ctypes.c_char_p]
        self._lib.keradb_create.restype = KeraDBHandle
        
        self._lib.keradb_open.argtypes = [ctypes.c_char_p]
        self._lib.keradb_open.restype = KeraDBHandle
        
        self._lib.keradb_close.argtypes = [KeraDBHandle]
        self._lib.keradb_close.restype = None
        
        # Document operations
        self._lib.keradb_insert.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p]
        self._lib.keradb_insert.restype = ctypes.c_char_p
        
        self._lib.keradb_find_by_id.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p]
        self._lib.keradb_find_by_id.restype = ctypes.c_char_p
        
        self._lib.keradb_update.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self._lib.keradb_update.restype = ctypes.c_char_p
        
        self._lib.keradb_delete.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p]
        self._lib.keradb_delete.restype = ctypes.c_int
        
        self._lib.keradb_find_all.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self._lib.keradb_find_all.restype = ctypes.c_char_p
        
        self._lib.keradb_count.argtypes = [KeraDBHandle, ctypes.c_char_p]
        self._lib.keradb_count.restype = ctypes.c_int
        
        self._lib.keradb_list_collections.argtypes = [KeraDBHandle]
        self._lib.keradb_list_collections.restype = ctypes.c_char_p
        
        self._lib.keradb_sync.argtypes = [KeraDBHandle]
        self._lib.keradb_sync.restype = ctypes.c_int
        
        # Error handling
        self._lib.keradb_last_error.argtypes = []
        self._lib.keradb_last_error.restype = ctypes.c_char_p
        
        self._lib.keradb_free_string.argtypes = [ctypes.c_char_p]
        self._lib.keradb_free_string.restype = None
        
        # Vector operations (optional - only if available in library)
        try:
            self._lib.keradb_create_vector_collection.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p]
            self._lib.keradb_create_vector_collection.restype = ctypes.c_char_p
            
            self._lib.keradb_list_vector_collections.argtypes = [KeraDBHandle]
            self._lib.keradb_list_vector_collections.restype = ctypes.c_char_p
            
            self._lib.keradb_drop_vector_collection.argtypes = [KeraDBHandle, ctypes.c_char_p]
            self._lib.keradb_drop_vector_collection.restype = ctypes.c_int
            
            self._lib.keradb_insert_vector.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
            self._lib.keradb_insert_vector.restype = ctypes.c_char_p
            
            self._lib.keradb_insert_text.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
            self._lib.keradb_insert_text.restype = ctypes.c_char_p
            
            self._lib.keradb_vector_search.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
            self._lib.keradb_vector_search.restype = ctypes.c_char_p
            
            self._lib.keradb_vector_search_text.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
            self._lib.keradb_vector_search_text.restype = ctypes.c_char_p
            
            self._lib.keradb_vector_search_filtered.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
            self._lib.keradb_vector_search_filtered.restype = ctypes.c_char_p
            
            self._lib.keradb_get_vector.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_ulonglong]
            self._lib.keradb_get_vector.restype = ctypes.c_char_p
            
            self._lib.keradb_delete_vector.argtypes = [KeraDBHandle, ctypes.c_char_p, ctypes.c_ulonglong]
            self._lib.keradb_delete_vector.restype = ctypes.c_int
            
            self._lib.keradb_vector_stats.argtypes = [KeraDBHandle, ctypes.c_char_p]
            self._lib.keradb_vector_stats.restype = ctypes.c_char_p
            
            self._has_vector_support = True
        except AttributeError:
            # Vector functions not available in this version of the library
            self._has_vector_support = False

    def get_last_error(self) -> str:
        """Get the last error message from the native library."""
        result = self._lib.keradb_last_error()
        if result:
            error = result.decode('utf-8')
            return error
        return "Unknown error"

    def free_string(self, ptr: ctypes.c_char_p):
        """Free a string allocated by the native library."""
        if ptr:
            self._lib.keradb_free_string(ptr)

    @property
    def lib(self) -> ctypes.CDLL:
        """Get the underlying ctypes library object."""
        return self._lib


# Global FFI instance
_ffi: Optional[KeraDBFFI] = None


def get_ffi() -> KeraDBFFI:
    """Get or create the global FFI instance."""
    global _ffi
    if _ffi is None:
        _ffi = KeraDBFFI()
    return _ffi
