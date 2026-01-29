from .Result import Result, Okay, Err
from typing import Awaitable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")
class AsyncResult(Generic[T, E]):
    __slots__ = ("future",)
    
    def __init__(self, future: Awaitable)