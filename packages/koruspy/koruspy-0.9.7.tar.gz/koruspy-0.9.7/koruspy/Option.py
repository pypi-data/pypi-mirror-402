from __future__ import annotations
from typing import TypeVar, Generic, Callable, overload, TypeAlias
from .errors import OptionUnwrapError
import collections
from collections import deque
from itertools import dropwhile

T_co = TypeVar("T_co", covariant=True)
U = TypeVar("U")

Option: TypeAlias = "Some[T_co] | _NoneOption"
class Some(Generic[T_co]):

    __slots__ = ("value", "hash",)
    __match_args__ = ("value",)

    def __eq__(self, other):
        if isinstance(other, Some):
            return self.value == other.value
        return NotImplemented 
    
    def to_list(self):
        return SomeList([self.value])

    def __iter__(self):
        yield self.value

    def unwrap_or_else(self, func: Callable[[], U]):
        return self.value
        
    # No final da classe Some:
    def __getattr__(self, name):
    # Se o método/atributo não existe no Some, tenta no valor interno de forma segura
        return  self.safe_call(name)

    def __hash__(self):
        if self.hash is None:
            raise TypeError("unhashable Some")
        return self.hash
   
    def flatten(self):
        if isinstance(self.value, (Some, _NoneOption)):
            return self.value
        return self    

    def on_nothing(self, func):
        return self

    def and_then(self, func: Callable[[T], Some[U] | _NoneOption]):
        return func(self.value)
   
    def filter(self, condition: Callable[[T], bool]):
        if condition(self.value):
            return self
        return nothing    

    def safe_call(self, method_name: str, *args, **kwargs):
        try:
            method = getattr(self.value, method_name)
            return Some(method(*args, **kwargs))
        except (AttributeError, TypeError):
            return nothing

    def getattr(self, attr_name):
        try:
            val = getattr(self.value, attr_name)
            return Some(val)
        except AttributeError:
            return nothing

    def __init__(self, value: U):
        self.value = value
        try:
            self.hash = hash(self.value)
        except TypeError:
            self.hash = None

    def unwrap_or(self, default):
        return self.value

    def finalize(self):
        return self.value

    def __repr__(self):
        return f"Some({self.value})"

    def if_present(self, func):
        return func(self.value)

    def to_int(self):
        try:
            return Some(int(self.value))
        except ValueError:
            return nothing

    def to_float(self):
           try:
               return Some(float(self.value))  
           except (ValueError, TypeError):
               return nothing   

    @overload
    def map(self, func: Callable[[T_co], U]) -> Some[U]:
        ...

    def map(self, func: Callable[[T_co], U]) -> Some[U] | _NoneOption:
        result = func(self.value)
        if result is None:
            return nothing
        return Some(result)    

    @overload
    def get_value(self) -> Some[T_co]:
        ...

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def get_value(self) -> Some[T_co] | _NoneOption:
        return Some(self.value)

    def is_present(self):
        return True


class _NoneOption(Generic[T_co]):
    _instance = None
    __match_args__ = ()
    __slots__ = ()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def value(self):
        return None

    def __hash__(self):
        return hash(None)

    def __getattr__(self, name):
        return nothing

    def to_list(self):
        return nothing

    def __iter__(self):
        yield from ()

    def to_float(self):
        return nothing

    def __float__(self):
        raise TypeError("Cannot convert 'nothing' to float")

    def __int__(self):
        raise TypeError("Cannot convert 'nothing' to integer")

    def unwrap_or_else(self, func: Callable[[], U]):
        return func()

    def flatten(self):
        return nothing

    def on_nothing(self, func: Callable[[], None]):
        func()
        return nothing

    def filter(self, condition: Callable[[U], bool]):
        return nothing

    def and_then(self, func: Callable[[U], nothing]):
        return nothing

    def safe_call(self, method_name, *args, **kwargs):
        return nothing

    def getattr(self, attr_name):
        return nothing
   
    def unwrap_or(self, default):
        return default

    def finalize(self):
        raise OptionUnwrapError("Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value")

    def __eq__(self, other):
        return isinstance(other, _NoneOption)

    def __repr__(self):
        return "nothing"

    def if_present(self, func):
        return nothing 

    def to_int(self):
        return nothing

    def map(self, func):
        return nothing

    def get_value(self):
        return nothing

    def is_present(self):
        return False


nothing = _NoneOption()
Option: TypeAlias = Some[T_co] | _NoneOption

def option_of(value, default):
    if value is None or isinstance(value, _NoneOption):
        if default is not None and default is not nothing:
            return Some(default)
    if isinstance(value, Some):
        return value
    return Some(value)
