from contextvars import ContextVar

_scoped_cache = ContextVar("scutum_cache", default=None)

class ScopedCache:
    __slots__ = ("scopes", "rules")
    
    def __init__(self):
        self.scopes = {}
        self.rules = {}

def get_cache() -> ScopedCache:
    cache = _scoped_cache.get()
    if cache is None:
        cache = ScopedCache()
        _scoped_cache.set(cache)
    return cache

def reset_scoped_cache():
    _scoped_cache.set(None)