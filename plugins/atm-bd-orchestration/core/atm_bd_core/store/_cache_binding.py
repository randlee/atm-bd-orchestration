"""Typed boundary to the native cache wheel, which does not ship stubs."""
from importlib import import_module
from typing import Any, Protocol, cast


class CacheModule(Protocol):
    CacheError: type[Exception]

    def Cache(self, root: str, **kwargs: Any) -> Any: ...


cache_module = cast(CacheModule, import_module("bd_cache_rs"))
