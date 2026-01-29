# -*- coding: utf-8 -*-
from __future__ import annotations

__version__ = "3.0.0"

import functools
import hashlib
import inspect
import logging
import uuid
from typing import Any

from django.core.cache import cache as default_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


def force_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


class Memoizer:
    def __init__(self, cache=None):
        self.cache = cache or default_cache

    # NOTE: internal helpers
    def _func_namespace(self, func):
        return f"{func.__module__}.{func.__qualname__}"

    def _make_cache_key(self, func, args, kwargs, version):
        raw = (
            self._func_namespace(func),
            args,
            tuple(sorted(kwargs.items())),
            version,
        )
        digest = hashlib.md5(force_bytes(raw)).hexdigest()
        return f"memoize:{digest}"

    def _verhash_key(self, func):
        return f"memoize:verhash:{self._func_namespace(func)}"

    def _get_verhash(self, func):
        key = self._verhash_key(func)
        ver = self.cache.get(key)
        if ver is None:
            ver = uuid.uuid4().hex
            self.cache.set(key, ver, None)
        return ver

    def _bump_verhash(self, func):
        key = self._verhash_key(func)
        self.cache.set(key, uuid.uuid4().hex, None)

    # NOTE: public API
    def memoize(self, timeout=DEFAULT_TIMEOUT):
        def decorator(func):
            sig = inspect.signature(func)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                bound = sig.bind_partial(*args, **kwargs)
                bound.apply_defaults()

                version = self._get_verhash(func)
                cache_key = self._make_cache_key(
                    func,
                    tuple(bound.args),
                    bound.kwargs,
                    version,
                )

                result = self.cache.get(cache_key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                self.cache.set(cache_key, result, timeout)
                return result

            return wrapper

        return decorator

    def delete_memoized(self, func, *args, **kwargs):
        if not args and not kwargs:
            self._bump_verhash(func)
            return

        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        version = self._get_verhash(func)
        cache_key = self._make_cache_key(
            func,
            tuple(bound.args),
            bound.kwargs,
            version,
        )
        self.cache.delete(cache_key)

    def delete_memoized_verhash(self, func):
        self._bump_verhash(func)


_memoizer = Memoizer()

memoize = _memoizer.memoize
delete_memoized = _memoizer.delete_memoized
delete_memoized_verhash = _memoizer.delete_memoized_verhash
