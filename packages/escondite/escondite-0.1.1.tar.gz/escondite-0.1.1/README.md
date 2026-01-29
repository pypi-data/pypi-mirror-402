# Escondite

Escondite is a simple caching library for Python that allows you to store and retrieve data with string keys.
Escondite is used by the [Bolinette project](https://github.com/bolinette) to cache classes at script load time.

## Installation

```shell
$ pip install escondite  # or use your preferred package manager
```

## Usage

Escondite provides a `Cache` class that can be used as a singleton or instantiated as needed.
You can also use the default user cache instance `__user_cache__` to store everything in a single global cache.

```python
from collections.abc import Callable
from escondite import Cache, __user_cache__

def cache_class[**P, T](cls: Callable[P, T], *, cache: Cache | None = None) -> Callable[P, T]:
    Cache.with_fallback(cache).add('stored_classes', cls)
    return cls

@cache_class
class MyClass:
    pass

assert 'stored_classes' in __user_cache__
assert __user_cache__.get('stored_classes') == {MyClass}
```

In this example, the `cache_class` decorator adds the decorated class to the cache under the key `'stored_classes'`.
If the cache funtion is called without a specific cache, it uses the global `__user_cache__` instance with the `with_fallback` method.
