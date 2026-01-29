import ctypes
import ctypes.util
from typing import Type, Any, Dict, get_origin, get_args, ClassVar, Annotated, get_type_hints
from pydantic import BaseModel

# Map Pydantic/Python types to default ctypes
TYPE_MAP = {
    int: ctypes.c_int,
    float: ctypes.c_double,
    bool: ctypes.c_bool,
    str: ctypes.c_char_p,
    bytes: ctypes.c_void_p,
    ctypes.c_void_p: ctypes.c_void_p,
}

# --- Exceptions ---
class CdanticError(Exception):
    """Base exception for all C-Dantic errors."""
    pass

class ValidationBoundaryError(CdanticError):
    """Raised when data fails to cross the Python-C boundary safely."""
    pass

class LibraryNotBoundError(CdanticError):
    """Raised when a native function is called before bind_library()."""
    pass

class SymbolNotFoundError(CdanticError):
    """Raised when a native function name cannot be found in the library."""
    pass

class CallbackLifetimeError(CdanticError):
    """Raised when a callback is potentially at risk of being garbage collected."""
    pass

# --- Global Registry for Callback Pinning ---
_CALLBACK_REGISTRY: Dict[int, Any] = {}

def pin_callback(obj: Any):
    """Adds a reference to the callback object to prevent GC while in flight."""
    _CALLBACK_REGISTRY[id(obj)] = obj

class CStruct(BaseModel):
    """
    A Pydantic Model that can automagically convert itself to a ctypes.Structure.
    Supports ABI control via __pack__ / _pack_ and __align__ / _align_.
    """
    _c_struct_cls: ClassVar[Type[ctypes.Structure]] = None

    @classmethod
    def sizeof(cls) -> int:
        """Returns the size of the C structure in bytes."""
        if not cls._c_struct_cls:
            cls._compile_c_struct()
        return ctypes.sizeof(cls._c_struct_cls)

    @classmethod
    def offsetof(cls, field_name: str) -> int:
        """Returns the offset of a field within the structure."""
        if not cls._c_struct_cls:
            cls._compile_c_struct()
        return getattr(cls._c_struct_cls, field_name).offset

    def to_c(self) -> ctypes.Structure:
        """Converts the Pydantic instance into a populated ctypes Structure."""
        cls = self.__class__
        if not cls._c_struct_cls:
            cls._compile_c_struct()
        
        c_instance = cls._c_struct_cls()
        for name, field in cls.model_fields.items():
            value = getattr(self, name)
            if isinstance(value, CStruct):
                setattr(c_instance, name, value.to_c())
            else:
                c_type = cls._c_struct_cls._fields_map[name]
                if c_type == ctypes.c_char_p and isinstance(value, str):
                    value = value.encode('utf-8')
                setattr(c_instance, name, value)
        return c_instance

    @classmethod
    def from_c_pointer(cls, ptr: ctypes.c_void_p):
        """Hydrates a Pydantic model from a raw memory pointer."""
        if not cls._c_struct_cls:
            cls._compile_c_struct()
        c_instance = ctypes.cast(ptr, ctypes.POINTER(cls._c_struct_cls)).contents
        return cls.from_c(c_instance)

    @classmethod
    def from_c(cls, c_instance: ctypes.Structure):
        """Hydrates a Pydantic model from a raw ctypes Structure."""
        data = {}
        for name, field in cls.model_fields.items():
            val = getattr(c_instance, name)
            # Use raw annotations or get_type_hints to avoid Pydantic V2 stripping metadata
            hints = get_type_hints(cls, include_extras=True)
            field_type = hints.get(name, field.annotation)
            
            if hasattr(field_type, "__metadata__"):
                 field_type = get_args(field_type)[0]

            if isinstance(field_type, type) and issubclass(field_type, CStruct):
                 val = field_type.from_c(val)
            elif isinstance(val, bytes) and field_type == str:
                 val = val.decode('utf-8')
            data[name] = val
        return cls(**data)

    @classmethod
    def _resolve_c_type(cls, name, field, hints):
        """Helper to resolve c_type from a Pydantic field and raw type hints."""
        c_type = None
        # Pydantic V2 strips metadata from field.annotation, so we use get_type_hints
        ann = hints.get(name, field.annotation)
        
        # 1. Annotated metadata (ctypes types are classes)
        if get_origin(ann) is not None:
            if hasattr(ann, "__metadata__"):
                for m in ann.__metadata__:
                    if isinstance(m, type) and issubclass(m, (ctypes._SimpleCData, ctypes.Structure, ctypes.Array)):
                        c_type = m
                        break
                    if m == ctypes.c_void_p:
                        c_type = ctypes.c_void_p
                        break
                    if hasattr(m, "_type_"):
                        c_type = m
                        break

        # 2. json_schema_extra fallback
        if not c_type and field.json_schema_extra:
            c_type = field.json_schema_extra.get('c_type')
        
        # 3. Fallback to TYPE_MAP or recursion
        if not c_type:
            real_type = ann
            if get_origin(ann) is not None:
                real_type = get_args(ann)[0]

            if isinstance(real_type, type) and issubclass(real_type, CStruct):
                if not real_type._c_struct_cls:
                    real_type._compile_c_struct()
                c_type = real_type._c_struct_cls
            else:
                c_type = TYPE_MAP.get(real_type, ctypes.c_int)
        
        return c_type

    @classmethod
    def _compile_c_struct(cls):
        """
        Dynamically generates the internal ctypes.Structure class.
        Forces _pack_ to be processed BEFORE _fields_ triggers layout calculation.
        Uses get_type_hints to recover metadata Pydantic V2 might strip.
        """
        # 1. Extract raw configuration bypassing Pydantic shadowing
        def get_layout_attr(underscore_name, dunder_name):
            val = cls.__dict__.get(underscore_name) or cls.__dict__.get(dunder_name)
            if val is None:
                private_attrs = getattr(cls, "__private_attributes__", {})
                if underscore_name in private_attrs:
                    val = private_attrs[underscore_name].default
                elif dunder_name in private_attrs:
                    val = private_attrs[dunder_name].default
            if val is None:
                val = getattr(cls, underscore_name, None) or getattr(cls, dunder_name, None)
            return val

        raw_pack = get_layout_attr("_pack_", "__pack__")
        raw_align = get_layout_attr("_align_", "__align__")

        # 2. Resolve fields using rich type hints (Pydantic V2 strips metadata from field.annotation)
        hints = get_type_hints(cls, include_extras=True)
        fields = []
        fields_map = {}
        for name, field in cls.model_fields.items():
            c_type = cls._resolve_c_type(name, field, hints)
            fields.append((name, c_type))
            fields_map[name] = c_type
            
        # 3. Create Shadow Class with Strict ABI Order
        DynamicStructure = type(f"c_{cls.__name__}", (ctypes.Structure,), {})
        
        if raw_pack is not None:
            DynamicStructure._pack_ = raw_pack
        if raw_align is not None:
            DynamicStructure._align_ = raw_align

        # Finalizing _fields_ triggers offset calculation
        DynamicStructure._fields_ = fields
        DynamicStructure._fields_map = fields_map
        
        cls._c_struct_cls = DynamicStructure
        return DynamicStructure

def bind_library(instance: Any, lib_path: str):
    """Binds a native library to a class instance."""
    for name in dir(instance):
        attr = getattr(instance, name)
        if hasattr(attr, "_cdantic_func"):
            attr._cdantic_func.lib_name = lib_path
    setattr(instance, "__cdantic_bound__", True)
    return instance

class CFunction:
    """Decorator for native C functions with validation and binding enforcement."""
    def __init__(self, func_name: str, lib_name: str = None, argtypes: list = None, restype=None):
        self.lib_name = lib_name
        self.func_name = func_name
        self._lib = None
        self._func = None
        self._f = None # The decorated function

    def __call__(self, f):
        self._f = f
        def wrapper(instance_or_arg, *args, **kwargs):
            # Detect self vs static call
            is_self = hasattr(instance_or_arg, "__cdantic_bound__") or (self.lib_name is None)
            
            if is_self:
                if not getattr(instance_or_arg, "__cdantic_bound__", False):
                     raise LibraryNotBoundError(f"Native function {self.func_name} called on unbound instance. Call bind_library() first.")
                target_args = list(args)
            else:
                target_args = [instance_or_arg] + list(args)

            if not self.lib_name:
                 raise LibraryNotBoundError(f"CFunction '{self.func_name}' has no library path assigned.")

            if not self._lib:
                try:
                    target_lib = self.lib_name
                    if target_lib == 'user32':
                        if hasattr(ctypes, 'windll'):
                            self._lib = ctypes.windll.user32
                        else:
                            raise CdanticError("user32 is only available on Windows.")
                    elif target_lib == 'kernel32':
                        if hasattr(ctypes, 'windll'):
                            self._lib = ctypes.windll.kernel32
                        else:
                            raise CdanticError("kernel32 is only available on Windows.")
                    elif target_lib == 'libc':
                        path = ctypes.util.find_library('c')
                        self._lib = ctypes.CDLL(path)
                    else:
                        self._lib = ctypes.CDLL(target_lib)
                except Exception as e:
                    raise CdanticError(f"Failed to load library '{target_lib}': {e}")
                    
            if not self._func:
                try: 
                    self._func = getattr(self._lib, self.func_name)
                    self._compile(is_method=is_self)
                except AttributeError: raise SymbolNotFoundError(f"Function '{self.func_name}' not found in {self.lib_name}.")
            
            c_args = []
            for arg in target_args:
                if isinstance(arg, CStruct): c_args.append(arg.to_c())
                elif isinstance(arg, CCallback):
                    pin_callback(arg.c_callback)
                    c_args.append(arg.c_callback)
                else: c_args.append(arg)
            
            try: 
                return self._func(*c_args)
            except Exception as e: 
                raise CdanticError(f"Native call error in {self.func_name}: {e}")
        
        wrapper._cdantic_func = self
        return wrapper

    def _compile(self, is_method=False):
        """Resolves argtypes and restype from the decorated function signature."""
        import inspect
        sig = inspect.signature(self._f)
        
        # 1. Resolve Return Type
        res_type = None
        if sig.return_annotation is not inspect.Signature.empty:
            ann = sig.return_annotation
            if hasattr(ann, "__metadata__"): ann = ann.__metadata__[0]
            res_type = TYPE_MAP.get(ann, ann)
        
        if res_type:
            self._func.restype = res_type

        # 2. Resolve Arg Types
        hints = get_type_hints(self._f, include_extras=True)
        arg_types = []
        params = list(sig.parameters.values())
        
        # Skip 'self' if it's a method
        start_idx = 1 if is_method else 0
        
        for param in params[start_idx:]:
            name = param.name
            ann = hints.get(name, param.annotation)
            c_type = ctypes.c_int
            
            if ann is not inspect.Signature.empty:
                if hasattr(ann, "__metadata__"):
                     meta = ann.__metadata__
                     for m in meta:
                         if hasattr(m, "_type_") or m == ctypes.c_void_p:
                             c_type = m
                             break
                else: c_type = TYPE_MAP.get(ann, ann)
            arg_types.append(c_type)
        
        if arg_types:
            self._func.argtypes = arg_types

class CCallback:
    """Decorator for ctypes callbacks with automatic lifetime pinning."""
    def __init__(self, f):
        self.f = f
        self._c_callback = None
        
    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    @property
    def c_callback(self):
        if not self._c_callback: self._compile()
        return self._c_callback
        
    def _compile(self):
        import inspect
        sig = inspect.signature(self.f)
        res_type = ctypes.c_int
        if sig.return_annotation is not inspect.Signature.empty:
            ann = sig.return_annotation
            if hasattr(ann, "__metadata__"): ann = ann.__metadata__[0]
            res_type = TYPE_MAP.get(ann, ann)
            
        hints = get_type_hints(self.f, include_extras=True)
        arg_types = []
        for name, param in sig.parameters.items():
            ann = hints.get(name, param.annotation)
            c_type = ctypes.c_int
            if ann is not inspect.Signature.empty:
                if hasattr(ann, "__metadata__"):
                     meta = ann.__metadata__
                     for m in meta:
                         if hasattr(m, "_type_") or m == ctypes.c_void_p:
                             c_type = m
                             break
                else: c_type = TYPE_MAP.get(ann, ann)
            arg_types.append(c_type)
            
        self._c_callback = ctypes.CFUNCTYPE(res_type, *arg_types)(self.f)
        pin_callback(self._c_callback)

def is_null(handle: Any) -> bool:
    if handle is None: return True
    if isinstance(handle, int): return handle == 0
    return not bool(handle)

def assert_not_null(handle: Any, context: str = "Handle"):
    if is_null(handle):
        raise ValidationBoundaryError(f"Access Violation: {context} is NULL.")
