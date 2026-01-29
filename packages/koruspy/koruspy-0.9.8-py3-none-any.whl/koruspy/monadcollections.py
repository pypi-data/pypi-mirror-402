from __future__ import annotations
from typing import TypeVar, Generic, Callable
import collections
from itertools import dropwhile
from collections.abc import Sequence
from .Option import Some, nothing, _NoneOption


T = TypeVar("T")
U = TypeVar("U")


class SomeList(Generic[T], collections.abc.MutableSequence):
    __slots__ = ("value",)

    def __init__(self, value):
        if value is None or value is nothing:
            self.value = []
            return
        if isinstance(value, Some):
            self.value = [value]
            return
        if not hasattr(value, "__iter__") or isinstance(value, (str, bytes)):
            value = [value]
        self.value = [
            item if isinstance(item, (Some, _NoneOption)) 
            else (nothing if item is None else Some(item)) # Se for None puro, vira nothing
            for item in value
    ]
            
            
    @property
    def val(self):
        return self.value

    @classmethod
    def from_option(cls, opt):
        if opt is nothing:
            return cls()
        return cls([opt.unwrap()])    

    def match_all(self, on_some: Callable[[T], U], on_nothing: Callable[[], U]) -> list[U]:
         return [
          item.if_present(on_some) if item.is_present() else on_nothing()
          for item in self.value
    ]

    def partition(self):
        successes = []
        failures = []
        for item in self.value:
            if item.is_present():
                successes.append(item.value)
            else:
            # Aqui você poderia capturar o rastro do erro se fosse um Result
                failures.append(nothing) 
        return successes, failures

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, change):
        self.value[index] = change
        
    def __bool__(self):
        return bool(self.value)

    def __delitem__(self, index):
        del self.value[index]

    def map(self, fn: Callable[[T], U]) -> SomeList[U]:
        new_values = []
        for item in self.value:
            if item is nothing:
                new_values.append(nothing)
            else:
                res = fn(item.value)
            # Se a lambda já devolveu um Option (Some ou nothing), usamos ele.
            # Se devolveu um valor puro (string, int), embrulhamos.
                if isinstance(res, (Some, _NoneOption)):
                    new_values.append(res)
                else:
                    new_values.append(Some(res))
        return SomeList(new_values)


        
    @classmethod
    def to_somelist(cls, valor):
        return cls(valor)

    def to_integerlist(self):
        return SomeList([int(item) for item in self.value])

    def to_floatlist(self):
        return SomeList([float(item) for item in self.value])

    def unwrap_list(self) -> Some[T] | nothing:
        results = []
        for item in self.value:
            if item is nothing:
                return nothing
            results.append(item.value)   
        return Some(results)    

    def unwrap_list_or_else(self, func: Callable[[], T]) -> Some[T]:
        results = []
        for item in self.value:
            if item is nothing:
                return func()
            results.append(item.value)   
        return Some(results)     
                

    def unwrap_list_or(self, default: T) -> Some[T]:
        results = []
        for item in self.value:
            if item is nothing:
                return Some(default)
            results.append(item.value)
        return Some(results)                 

    def pop(self, index=-1):
        if not self.value:
            return nothing
        try:
            item = self.value.pop(index)
            return item
        except (IndexError, AttributeError):
            pass
        return nothing 
    
    def remove(self, val):
        item = self.value.remove(val)
        return self

    def insert(self, index, content):
        self.value.insert(index, content)
        return self

    def __iter__(self):
        yield from self.value  
    
    def sum(self):
        if self.value is nothing or self.value is None:
            return 0
        total = 0
        for item in self.value:
            if isinstance(item.value, (int, float)):
                total += item.value
        return total 

    def append(self, item):
        if item is not nothing and item is not None:
            self.value.append(Some(item))
        return self

    def head(self):
        if not self.value:
            return nothing
        first = self.value[0]  
        return first

    def last(self):
        if not self.value:
            return nothing
        last_item = self.value[-1] 
        return last_item 
    
    def tail(self):
        if not self.value:
            return nothing
        if len(self.value) <= 1:
            return nothing
        if isinstance(self.value, list):
            return SomeList(self.value[1:])
        return nothing    
        
    def filter_nothing(self):
        return SomeList([x for x in self.value if x is not nothing and x is not None])    

    def filter(self, cond):
        result = [item for item in self.value if cond(item.value)]
        return SomeList(result)

    def extend(self, items):
        to_add = [v if isinstance(v, (Some, _NoneOption)) else Some(v) for v in items if v is not None]
        self.value.extend(to_add)
        return self        
    
    def __contains__(self, other):
        return other in self.value

    def __eq__(self, other):
        if isinstance(other, SomeList):
            return other.value == self.value
        return NotImplemented   

    def __repr__(self):
        return f"SomeList({self.value})"    

    def clear(self):
        self.value.clear()
        return self  

    # Dentro da SomeList
    def for_each(self, fn: Callable[[T], None]):
        for item in self.value:
            fn(item)
        return self # Retorna self para permitir encadeamento

    def find(self, cond):
        if not isinstance(self.value, list):
            return nothing
        for v in self.value:
            valor_real = v.value 
            if cond(valor_real):
                return v 
        return nothing        

    def safe_reduce(self, func, initial = None):
        if not self.value:
            return nothing if initial is None else Some(initial)
        try:
            if initial is None:
                iterator = iter(self.value)
                try:
                    accumulator = next(iterator)
                    if isinstance(accumulator, Some): accumulator = accumulator.value
                    items_to_process = iterator
                except StopIteration:
                    return nothing
            else:
                accumulator = initial
                items_to_process = self.value
            for item in items_to_process:
                val = item.value
                accumulator = func(accumulator, val)
            return Some(accumulator)
        except Exception:
            return nothing

    def as_lazy(self):
        return LazyList(lambda: (item for item in self.value))

    def __len__(self):
        try:
            return len(self.value)   
        except TypeError:
            return 1 if self.value is not nothing else 0    


class LazyList(Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __iter__(self):
        return self.value()

    def __repr__(self):
        return f"LazyList({self.value})"

    def lazy_map(self, fn):
        gen = lambda: (fn(v) for v in self.value())
        return LazyList(gen)

    def as_SomeList(self):
        return SomeList(list(self.value()))

    def lazy_filter(self, cond):
        gen = lambda: (v for v in self.value() if cond(v))
        return LazyList(gen)
    def lazy_sum(self):
        total = 0
        for item in self.value():
            if isinstance(item, Some):
                val = item.value
            else:
                val = item
            if isinstance(val, (int, float)):
                total += val
        return total     
    
    # Dentro da classe LazyList
    def take(self, n: int):
        def gen():
            count = 0
            for item in self.value():
                if count >= n: break
                yield item
                count += 1
        return LazyList(gen)

    def drop(self, n: int):
        def gen():
            it = self.value()
            for _ in range(n):
                try:
                    next(it)
                except StopIteration:
                    return
            yield from it
        return LazyList(gen)    

    def drop_last(self, n: int):
        if n <= 0: return self
        def gen():
            it = self.value()
            queue = deque()
            for _ in range(n):
                try:
                    queue.append(next(it))
                except StopIteration:
                    return
            for item in it:
                yield queue.popleft()
                queue.append(item)
        return LazyList(gen)        
    def drop_while(self, cond):
        return LazyList(dropwhile(cond, self.value()))

    def for_each(self, fn: Callable[[T], None]):
        for item in self.value():
            fn(item)


class FrozenSomeList(Sequence):
    __slots__ = ("_data", "_hash")

    def __init__(self, iterable):
        self._data = tuple(
           item if isinstance(item, (Some, _NoneOption)) 
           else (nothing if item is None else Some(item))
           for item in iterable
        )
        self._hash = hash(self._data)

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, FrozenSomeList):
            return self._data == other._data
        return NotImplemented

    def __repr__(self):
        return f"FrozenSomeList({self._data})"
