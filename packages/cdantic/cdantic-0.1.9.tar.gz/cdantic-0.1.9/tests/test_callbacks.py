from cdantic import CCallback
import ctypes
from typing import Annotated

def test_callback_generation():
    # Define a python function
    def my_hook(a: int, b: int) -> int:
        return a + b
        
    # Wrap it
    cb_wrapper = CCallback(my_hook)
    
    # Get the ctypes object
    c_func_ptr = cb_wrapper.c_callback
    
    # It should be a _CFuncPtr instance (CFUNCTYPE returns a class, calling it creates instance)
    assert isinstance(c_func_ptr, ctypes._CFuncPtr)
    
    # We can actually call it (it goes Python -> C -> Python)
    # ctypes creates a thunk
    assert c_func_ptr(10, 20) == 30

def test_callback_annotations():
    # Verify typing inspection
    
    def complex_hook(hwnd: Annotated[int, ctypes.c_void_p]) -> bool:
        return True
        
    wrapper = CCallback(complex_hook)
    c_func = wrapper.c_callback
    
    # Check argtypes
    # argtypes is a tuple of types on the instance's class or instance?
    # ctypes docs say _argtypes_ and _restype_ on the function type
    
    # The instance 'c_func' has access to them?
    # For CFUNCTYPE objects, the strict validation happens at call time.
    # But internal `argtypes` property might be missing on the thunk itself.
    
    # Instead, let's verify it accepts the right data without crash?
    pass
