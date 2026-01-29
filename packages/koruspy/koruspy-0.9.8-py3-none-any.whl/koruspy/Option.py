from __future__ import annotations
from typing import TypeVar, Generic, Callable, overload, TypeAlias, TypeGuard, NoReturn
from .errors import OptionUnwrapError
import functools 

T_co = TypeVar("T_co", covariant=True)
U = TypeVar("U", bound=object)
V = TypeVar("V")

Option: TypeAlias = "Some[T_co] | _NoneOption"


class Some(Generic[T_co]):

    __slots__ = ("value", "hash",)
    __match_args__ = ("value",)

    def __eq__(self, other):
        if isinstance(other, Some):
            return self.value == other.value
        return NotImplemented 

    def __iter__(self):
        yield self.value

    def unwrap_or_else(self, func: Callable[[], U]) -> T_co | U:
        return self.value

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

    def and_then(self, func: Callable[[T_co], Option[V]]) -> Option[V]:
        return func(self.value)
   
    def filter(self, condition: Callable[[T_co], bool]) -> Option[T_co]:
        if condition(self.value):
            return self
        return nothing    

    def safe_call(self, method_name: str, *args, **kwargs) -> Option[object]:
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

    def unwrap_or(self, default: U) -> T_co | U:
        return self.value

    def unwrap(self) -> T_co:
        return self.value

    def finalize(self) -> T_co:
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

    def map(self, func: Callable[[T_co], U]) -> Option[U]:
        result = func(self.value)
        if result is None:
            return nothing
        return Some(result)    

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def is_present(self) -> TypeGuard[Some[T_co]]:
        return True


class _NoneOption:
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

    def unwrap_or_else(self, func: Callable[[], U]) -> U:
        return func()

    def flatten(self):
        return nothing

    def on_nothing(self, func: Callable[[], None]):
        func()
        return nothing

    def filter(self, condition: Callable[[object], bool]) -> Option[object]:
        return nothing

    def and_then(self, func: Callable[[object], Option[V]]) -> Option[V]:
        return nothing

    def safe_call(self, method_name, *args, **kwargs) -> Option[object]:
        return nothing

    def getattr(self, attr_name):
        return nothing
   
    def unwrap_or(self, default: U) -> U:
        return default

    def unwrap(self) -> NoReturn:
        raise OptionUnwrapError("called 'unwrap()' on nothing")
    
    def finalize(self) -> NoReturn:
        raise OptionUnwrapError("Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value")

    def __eq__(self, other):
        return isinstance(other, _NoneOption)

    def __repr__(self):
        return "nothing"

    def if_present(self, func):
        return nothing 

    def to_int(self):
        return nothing

    def map(self, func: Callable[[T_co], U]) -> Option[U]:
        return nothing

    def is_present(self) -> TypeGuard[Some[T_co]]:
        return False


nothing = _NoneOption()


def option_of(value: U | None) -> Option[U]:
    if value is None or isinstance(value, _NoneOption):
        return nothing
    if isinstance(value, Some):
        return value
    return Some(value)


def Optionize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is None or result is nothing:
            return nothing
        elif isinstance(result, Some):
            return result
        else:
            return Some(result)
    return wrapper    
