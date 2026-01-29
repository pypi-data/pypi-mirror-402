from .errors import ResultUnwrapError, KoruspyError
from typing import Generic, TypeVar, Callable, NoReturn, TypeAlias

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")

class Okay(Generic[T_co]):
    __match_args__ = ("value",)
    __slots__ = ("value",)
    
    def __iter__(self):
        yield self.value

    def __init__(self, value: T_co):
        self.value = value

    def unwrap(self):
        return self.value

    def and_then(self, func):
        return self.flat_map(func)

    def flat_map(self, func: Callable[[T_co], "Result[U, E_co]"]) -> "Result[U, E_co]":
        return func(self.value)

    def unwrap_or(self, default):
        return self.value

    def unwrap_or_else(self, func):
        return self.value

    def fold(self, on_okay, on_err):
        return on_okay(self.value)

    def map(self, func: Callable[[T_co], U]) -> "Okay[U]":
        return Okay(func(self.value))

    def __repr__(self):
        return f"Okay({self.value})"

    def is_okay(self):
        return True

    def is_err(self):
        return False
    
    def unwrap_err(self):
        raise ResultUnwrapError(f"tried unwrap 'Okay({self.value})' using 'unwrap_err()' use 'unwrap()' when the instance is 'Okay'") 

    def flatten(self):
        if isinstance(self.value, (Okay, Err)):
            return self.value
        return self    

    def expect(self, err):
        return self.value


class Err(Generic[E_co]):
    __match_args__ = ("error",)
    __slots__ = ("error",)

    def __init__(self, error: E_co):
        self.error = error

    def __iter__(self):
        yield from ()

    def fold(self, on_okay, on_err):
        return on_err(self.error)

    def flatten(self):
        return self

    def expect(self, err) -> NoReturn:
        raise KoruspyError(err)

    def unwrap(self) -> NoReturn:
        raise ResultUnwrapError(f"tried to access Err: {self.error}")

    def unwrap_or(self, default):
        return default

    def unwrap_or_else(self, func):
        return func(self.error)

    def unwrap_err(self) -> E_co:
        return self.error

    def map(self, func):
        return self

    def and_then(self, func):
        return self

    def flat_map(self, func):
        return self

    def __repr__(self):
        return f"Err({self.error})"

    def is_okay(self):
        return False

    def is_err(self):
        return True

def result_of(func: Callable[..., T_co], *args, **kwargs) -> Okay[T_co] | Err[E_co]:
    try:
        return Okay(func(*args, **kwargs))
    except Exception as e:
        return Err(e)


Result: TypeAlias = Okay[T_co] | Err[E_co]