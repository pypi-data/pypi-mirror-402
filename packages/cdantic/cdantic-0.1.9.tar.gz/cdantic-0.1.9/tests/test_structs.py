from cdantic import CStruct
from cdantic.types import c_field
import ctypes

class Point(CStruct):
    x: int = c_field(ctypes.c_int)
    y: int = c_field(ctypes.c_int)

class Rect(CStruct):
    left: int = c_field(ctypes.c_int)
    top: int = c_field(ctypes.c_int)
    right: int = c_field(ctypes.c_int)
    bottom: int = c_field(ctypes.c_int)

def test_basic_struct():
    p = Point(x=10, y=20)
    c_p = p.to_c()
    
    assert isinstance(c_p, ctypes.Structure)
    assert c_p.x == 10
    assert c_p.y == 20
    assert ctypes.sizeof(c_p) == 8 # 2 * 4 bytes (int)
    # c_int is consistently 4 bytes on Windows and Linux x64.

def test_round_trip():
    p = Point(x=55, y=99)
    c_p = p.to_c()
    
    p2 = Point.from_c(c_p)
    assert p2.x == 55
    assert p2.y == 99

def test_nested_struct():
    # If we supported nesting (logic in core.py handles it)
    pass
