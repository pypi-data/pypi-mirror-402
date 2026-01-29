# koruspy/__init__.py

__all__ = [
    "Some", "nothing", "_NoneOption", "Option","SomeList", "println", "Okay", "Err",
    "option_of", "result_of", "Result", "AsyncOption", "async_option",
    "ResultUnwrapError", "KoruspyError", "OptionUnwrapError", "LazyList", "FrozenSomeList"
]

from .Option import Some, nothing, Option, option_of, _NoneOption
from .Result import Err, Okay, result_of, Result
from .monadcollections import FrozenSomeList, LazyList, SomeList
from .Async_option import AsyncOption, async_option
from .errors import ResultUnwrapError, OptionUnwrapError, KoruspyError

# Tenta importar a versão Cython já compilada
try:
    from .printlnUtils.cythonprintln import println
except ImportError:
    # Fallback em Python puro
    def println(*args, **kwargs):
        print(*args, **kwargs)