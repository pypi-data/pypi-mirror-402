import ctypes
from typing import Annotated
from pydantic import Field

# Type Aliases for nicer Pydantic definitions
def c_field(c_type, **kwargs):
    """
    Helper to define a Field with a specific ctypes type.
    usage:
       my_int: int = c_field(ctypes.c_uint32)
    """
    if "json_schema_extra" not in kwargs:
        kwargs["json_schema_extra"] = {}
    kwargs["json_schema_extra"]["c_type"] = c_type
    return Field(**kwargs)

# Alias for modern syntax recommendation
CField = c_field

# Common Windows Types
HWND = ctypes.c_void_p
LPARAM = ctypes.c_void_p
WPARAM = ctypes.c_void_p
UINT = ctypes.c_uint
BOOL = ctypes.c_int
