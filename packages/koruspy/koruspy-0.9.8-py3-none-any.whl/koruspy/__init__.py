# koruspy/__init__.py

__all__ = [
    "Some", "nothing", "_NoneOption", "Option", "Optionize", "SomeList", "println", "Okay", "Err",
    "option_of", "result_of", "Result", "Resultize", "AsyncOption", "async_option", "AsyncOptionize",
    "ResultUnwrapError", "KoruspyError", "OptionUnwrapError", "LazyList", "FrozenSomeList"
]

from .Option import Some, nothing, Option, option_of, _NoneOption, Optionize
from .Result import Err, Okay, result_of, Result, Resultize
from .monadcollections import FrozenSomeList, LazyList, SomeList
from .Async_option import AsyncOption, async_option, AsyncOptionize
from .errors import ResultUnwrapError, OptionUnwrapError, KoruspyError

# Tenta importar a versão Cython já compilada
try:
    from .printlnUtils.cythonprintln import println
except ImportError:
    # Fallback em Python puro
    def println(*args, **kwargs):
        print(*args, **kwargs)