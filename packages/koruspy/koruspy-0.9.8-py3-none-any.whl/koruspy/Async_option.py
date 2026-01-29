from .Option import Some, _NoneOption, nothing
from typing import Awaitable, Callable, Generic, TypeVar, TypeAlias, NoReturn
import asyncio
import functools
from .errors import OptionUnwrapError

T = TypeVar("T")
U = TypeVar("U")
Option: TypeAlias = Some[T] | _NoneOption
   
class AsyncOption(Generic[T]):
    __slots__ = ("future",)
    def __init__(self, future: Awaitable[Option]):
        self.future = future

    def __repr__(self):
        return f"AsyncOption[<{self.future.__class__.__name__}>]"

    def __await__(self):
        return self.future.__await__()
    
    def map_async(self, fn: Callable[[T], U]) -> "AsyncOption[U]":
        async def _inner():
            opt = await self
            return opt.map(fn)
        return AsyncOption(_inner())

    def and_then_async(self, fn):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                res = fn(opt.value)
                if isinstance(res, Some) or res is nothing or isinstance(res, _NoneOption):
                    return res
                if isinstance(res, AsyncOption):	
                    return await res
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    res = await res
                return Some(res)
            return nothing 
        return AsyncOption(_inner())

    def filter_async(self, cond):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                res = cond(opt.value)
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    res = await res
                return opt if res else nothing  
            return nothing    
        return  AsyncOption(_inner())

    def unwrap_or_else_async(self, fn: Callable[[], U]) -> Awaitable[U]:
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                return opt.value
            res = fn()    
            if isinstance(opt, _NoneOption):
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    res = await res
            return res        
        return _inner()        

    def on_nothing_async(self, fn):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                return opt
            res = fn() if callable(fn) else fn
            if isinstance(opt, _NoneOption):
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    await res
            return opt
        return AsyncOption(_inner())    

    def if_present_async(self, fn):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                res = fn(opt.value) if callable(fn) else fn
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    res = await res
                return Some(res)
            return opt
        return AsyncOption(_inner())

    def unwrap_or_async(self, defaultValue: U | Callable[[], U]) -> Awaitable[U]:
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                return opt.value
            if callable(defaultValue):
                dz = defaultValue()
            else:
                dz = defaultValue   
            return await dz if asyncio.iscoroutine(dz) else dz
        return _inner()

    def unwrap(self) -> Awaitable[U] | NoReturn:
        self.finalize()     
    
    def finalize(self) -> Awaitable[U] | NoReturn:
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                return opt.value
            if isinstance(opt, _NoneOption):
                raise OptionUnwrapError("Option doesn`t have a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value")
        return _inner()        


def async_option(coro):
    async def _inner():
        return await coro
    return AsyncOption(_inner()) 
    
def AsyncOptionize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        async def _inner():
            result = await func(*args, **kwargs)
            if result is None or result is nothing:
                return nothing
            elif isinstance(result, Some):
                return result
            else:
                return Some(result)
        return AsyncOption(_inner())
    return wrapper    
              