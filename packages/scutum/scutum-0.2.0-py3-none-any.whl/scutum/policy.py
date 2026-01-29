import inspect
from functools import wraps
from scutum.scope import Scope, AsyncScope

def _get_method(obj, method):
    @wraps(method)
    def get_method(*args, **kwargs):
        return method(obj, *args, **kwargs)
    return get_method

def _get_async_method(obj, method):
    @wraps(method)
    async def get_method(*args, **kwargs):
        return await method(obj, *args, **kwargs)
    return get_method

def _get_scope(name, rules):
    scope = Scope(name)
    for rule_name, rule in rules.items():
        scope.add_rule(rule_name, rule)
    return scope

async def _get_async_scope(name, rules):
    scope = AsyncScope(name)
    for rule_name, rule in rules.items():
        await scope.add_rule(rule_name, rule)
    return scope

class BasePolicy:
    _method_wrapper = staticmethod(_get_method)
    _scope_wrapper = staticmethod(_get_scope)

    @classmethod
    def _to_rules(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        actions = {
            name: cls._method_wrapper(obj, method)
            for name, method in inspect.getmembers(cls, predicate=callable)
            if not name.startswith("_") and method.__qualname__.startswith(cls.__name__)
        }
        return actions
    
    @classmethod
    def _to_scope(cls, name):
        rules = cls._to_rules()
        return cls._scope_wrapper(name, rules)
    
class Policy(BasePolicy):
    _method_wrapper = staticmethod(_get_method)
    _scope_wrapper = staticmethod(_get_scope)

class AsyncPolicy(BasePolicy):
    _method_wrapper = staticmethod(_get_async_method)
    _scope_wrapper = staticmethod(_get_async_scope)
    