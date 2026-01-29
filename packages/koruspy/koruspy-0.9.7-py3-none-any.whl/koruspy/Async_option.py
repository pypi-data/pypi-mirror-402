from .Option import Some, _NoneOption, nothing
from typing import Awaitable, Callable, Generic, TypeVar
import asyncio
from .errors import OptionUnwrapError

T = TypeVar("T")
U = TypeVar("U")
Option: "TypeAlias" = Some[T] | _NoneOption
   
class AsyncOption(Generic[T]):
    __slots__ = ("future",)
    def __init__(self, future: Awaitable[Option]):
        self.future = future

    def __repr__(self):
        status = "done" if asyncio.create_task(self.future).done() else "pending"
        return f"\033[95mAsyncOption[{status}]\033[0m"

    def __await__(self):
        return self.future.__await__()
    
    def map_async(self, fn):
        async def _inner():
            opt = await self
            return opt.map(fn)
        return AsyncOption(_inner())

    def and_then_async(self, fn):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                res = fn(opt.value)
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    return await res
                return res
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

    def unwrap_or_else_async(self, fn):
        async def _inner():
            opt = await self
            if isinstance(opt, Some):
                return opt.value
            res = fn()    
            if isinstance(opt, _NoneOption):
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    return await res
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
                    await res 
            return opt
        return AsyncOption(_inner())            

    def unwrap_or_async(self, defaultValue):
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

    def finalize(self):
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