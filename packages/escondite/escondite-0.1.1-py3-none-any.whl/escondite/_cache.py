from typing import Any, overload, override


class Cache:
    def __init__(self) -> None:
        self._bag: dict[str, set[Any]] = {}

    @overload
    def get(self, key: str, /, *, raises: bool = True) -> set[Any]: ...
    @overload
    def get[InstanceT](self, key: str, /, *, hint: type[InstanceT], raises: bool = True) -> set[InstanceT]: ...
    def get(
        self,
        key: str,
        /,
        *,
        hint: Any | None = None,
        raises: bool = True,
    ) -> set[Any]:
        if key not in self:
            if raises:
                raise KeyError(key)
            return set()
        return self._bag[key]

    def delete(self, key: str) -> None:
        if key not in self:
            raise KeyError(key)
        del self._bag[key]

    def init(self, key: str) -> None:
        self._bag[key] = set()

    def add(self, key: str, value: Any) -> None:
        if key not in self:
            self.init(key)
        self._bag[key].add(value)

    def remove(self, key: str, value: Any) -> None:
        if key not in self:
            raise KeyError(key)
        if value not in self._bag[key]:
            raise KeyError(key, value)
        self._bag[key].remove(value)
        if len(self._bag[key]) == 0:
            self.delete(key)

    def clear(self) -> None:
        self._bag.clear()

    @staticmethod
    def _merge(c1: "Cache", c2: "Cache") -> "Cache":
        c3 = Cache()
        for key, values in c1._bag.items():
            for value in values:
                c3.add(key, value)
        for key, values in c2._bag.items():
            for value in values:
                c3.add(key, value)
        return c3

    def __contains__(self, key: str) -> bool:
        return key in self._bag

    def __len__(self) -> int:
        return len(self._bag)

    def __or__(self, other: "Cache", /) -> "Cache":
        return self._merge(self, other)

    @override
    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, Cache):
            return NotImplemented
        if len(self._bag) != len(other._bag):
            return False
        for key, self_bag in self._bag.items():
            if key not in other._bag:
                return False
            other_bag = other._bag[key]
            for self_value, other_value in zip(self_bag, other_bag, strict=True):
                if self_value != other_value:
                    return False
        return True

    @staticmethod
    def with_fallback(cache: "Cache | None") -> "Cache":
        return __user_cache__ if cache is None else cache


__user_cache__ = Cache()
