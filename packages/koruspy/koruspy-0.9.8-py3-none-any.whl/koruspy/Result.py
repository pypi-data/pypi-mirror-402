from .errors import ResultUnwrapError, KoruspyError
from typing import Generic, TypeVar, Callable, NoReturn, TypeAlias, Literal, overload, TypeGuard, Type, ParamSpec
from dataclasses import dataclass
import functools

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")
R = TypeVar("R")


@dataclass(slots=True, frozen=True)
class Okay(Generic[T_co]):
    value: T_co
    tag: Literal["ok"] = "ok"

    __match_args__ = ("value",)
    
    def __iter__(self):
        yield self.value

    def unwrap(self) -> T_co:
        return self.value

    def and_then(self, func: Callable[[T_co], "Result[U, E_co]"]) -> "Result[U, E_co]":
        return self.flat_map(func)

    def flat_map(self, func: Callable[[T_co], "Result[U, E_co]"]) -> "Result[U, E_co]":
        return func(self.value)

    def unwrap_or(self, default: U) -> T_co | U:
        return self.value

    def unwrap_or_else(self, func: Callable[[E_co], U]) -> T_co | U:
        return self.value

    def fold(self, on_okay: Callable[[T_co], R], on_err: Callable[[E_co], R]) -> R:
        return on_okay(self.value)

    def map_err(self, func: [[object], U]) -> "Okay[T_co]":
        return self 
    
    def map(self, func: Callable[[T_co], U]) -> "Okay[U]":
        return Okay(func(self.value))

    def __repr__(self):
        return f"Okay({self.value})"

    def is_okay(self) -> TypeGuard["Okay[T_co]"]:
        return True

    def is_err(self) -> TypeGuard["Err[E_co]"]:
        return False
    
    def unwrap_err(self) -> NoReturn:
        raise ResultUnwrapError(f"tried unwrap 'Okay({self.value})' using 'unwrap_err()' use 'unwrap()' when the instance is 'Okay'") 

    @overload
    def flatten(self: "Okay[T_co]") -> "Okay[T_co]":
        ...

    @overload
    def flatten(self: "Okay[Result[U, E_co]]") -> "Result[U, E_co]":
        ...

    def flatten(self):
        if isinstance(self.value, (Okay, Err)):
            return self.value
        return self    

    def expect(self, err: object) -> T_co:
        return self.value


@dataclass(slots=True, frozen=True)
class Err(Generic[E_co]):
    error: E_co
   
    __match_args__ = ("error",)

    def __iter__(self):
        yield from ()

    def fold(self, on_okay: Callable[[T_co], R], on_err: Callable[[E_co], R]) -> R:
        return on_err(self.error)

    def flatten(self):
        return self

    def expect(self, err) -> NoReturn:
        raise KoruspyError(err)

    def unwrap(self) -> NoReturn:
        raise ResultUnwrapError(f"tried to access Err: {self.error}")

    def unwrap_or(self, default: U) -> U:
        return default

    def unwrap_or_else(self, func: Callable[[E_co], U]) -> U:
        return func(self.error)

    def unwrap_err(self) -> E_co:
        return self.error

    def map_err(self, func: Callable[[object], U]) -> "Err[U]":
        return Err(func(self.error))
   
    def map(self, func: Callable[[object], U]) -> "Err[E_co]":
        return self

    def and_then(self, func: Callable[[object], "Result[U, E_co]"]) -> "Err[E_co]":
        return self

    def flat_map(self, func: Callable[[object], "Result[U, E_co]"]) -> "Err[E_co]":
        return self

    def __repr__(self):
        return f"Err({self.error})"

    def is_okay(self) -> TypeGuard["Okay[T_co]"]:
        return False

    def is_err(self) -> TypeGuard["Err[E_co]"]:
        return True

Result: TypeAlias = Okay[T_co] | Err[E_co]
E = TypeVar("E", bound=BaseException)
P = ParamSpec("P")

def result_of(func: Callable[P, U], *args: P.args, errors: tuple[Type[E], ...],**kwargs: P.kwargs) -> Okay[U] | Err[E]:
    try:
        return Okay(func(*args, **kwargs))
    except errors as e:
        return Err(e)

def Resultize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return Okay(func(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper
    