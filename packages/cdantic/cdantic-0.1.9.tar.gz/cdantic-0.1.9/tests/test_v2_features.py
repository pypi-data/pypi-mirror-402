from cdantic import CStruct
from cdantic.types import CField
import ctypes
from typing import Annotated

# --- Annotated Syntax Test ---
class RectAnnotated(CStruct):
    left: Annotated[int, ctypes.c_int]
    top: Annotated[int, ctypes.c_int]
    right: Annotated[int, ctypes.c_int]
    bottom: Annotated[int, ctypes.c_int]

def test_annotated_syntax():
    r = RectAnnotated(left=10, top=10, right=100, bottom=100)
    c_r = r.to_c()
    assert isinstance(c_r, ctypes.Structure)
    assert c_r.left == 10
    
    # Check memory size (4 ints * 4 bytes = 16)
    assert ctypes.sizeof(c_r) == 16 

# --- legacy CField Syntax Test ---
class RectLegacy(CStruct):
    left: int = CField(ctypes.c_int)
    top: int = CField(ctypes.c_int)
    right: int = CField(ctypes.c_int)
    bottom: int = CField(ctypes.c_int)

def test_legacy_syntax():
    r = RectLegacy(left=10, top=10, right=100, bottom=100)
    c_r = r.to_c()
    assert ctypes.sizeof(c_r) == 16

# --- Validation Test ---
def test_validation():
    try:
        # Pydantic built-in validation
        r = RectAnnotated(left="invalid", top=0, right=0, bottom=0)
        assert False, "Should have raised ValidationError"
    except Exception as e:
        assert "validation error" in str(e).lower()

# --- From C Pointer Test ---
def test_from_c_pointer():
    r = RectAnnotated(left=99, top=88, right=77, bottom=66)
    c_r = r.to_c()
    
    # Create a pointer to this real memory
    ptr = ctypes.pointer(c_r)
    ptr_addr = ctypes.cast(ptr, ctypes.c_void_p)
    
    # Hydrate back
    r2 = RectAnnotated.from_c_pointer(ptr_addr)
    
    assert r2.left == 99
    assert r2.bottom == 66
