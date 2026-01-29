import inspect
from asyncio import Lock
from threading import RLock
from abc import ABC
from typing import Dict, Optional, Union
from scutum.types import Rule, Response
from scutum.exceptions import RuleNotFoundException, ScopeNotFoundException
from scutum.cache import get_cache

class BaseScope(ABC):
    def __init__(self, name: str):
        self.name = name
        self._rules: Dict[str, Rule] = {}
        self._children: Dict[str, "BaseScope"] = {}
        self._parent: Optional["BaseScope"] = None

class ScopeResolverMixin:
    def _resolve_scope(self, path: str):
        cache = get_cache()
        cache_key = (id(self), path)
        if cache_key in cache.scopes:
            return cache.scopes[cache_key]
        
        scope = self._resolve_scope_uncached(path)
        cache.scopes[cache_key] = scope
        return scope

    def _resolve_scope_uncached(self, path: str):
        if not path or "::" in path or any(part == "" for part in path.split(":")):
            raise ValueError(f"Invalid path: '{path}'")
        
        scopes = path.split(":")
        current = self
        for name in scopes:
            if name not in current._children:
                raise ScopeNotFoundException(f"Scope '{name}' not found")
            current = current._children[name]
        return current

    def _resolve_rule(self, path: str) -> Rule:
        cache = get_cache()
        cache_key = (id(self), path)
        if cache_key in cache.rules:
            return cache.rules[cache_key]

        rule = self._resolve_rule_uncached(path)
        cache.rules[cache_key] = rule
        return rule

    def _resolve_rule_uncached(self, path: str) -> Rule:
        scope, rule_name = self._resolve_path(path)
        if rule_name not in scope._rules:
            raise RuleNotFoundException(f"Rule '{rule_name}' not found")
        return scope._rules[rule_name]

    def _resolve_path(self, path: str):
        if not path or "::" in path or any(part == "" for part in path.split(":")):
            raise ValueError(f"Invalid path: '{path}'")
        
        parts = path.split(":")
        if len(parts) == 1:
            return self, parts[0]
        scope_path = ":".join(parts[:-1])
        return self._resolve_scope(scope_path), parts[-1]

    def debug(self, indent: int = 0) -> str:
        prefix = "  " * indent
        lines = [f"{prefix}Scope: {self.name}"]
        for rule_name in self._rules:
            lines.append(f"{prefix}  Rule: {rule_name}")
        for child in self._children.values():
            lines.append(child.debug(indent + 1))
        return "\n".join(lines)

class Scope(BaseScope, ScopeResolverMixin):
    def __init__(self, name: str, lock: Optional[RLock] = None):
        super().__init__(name)
        self._lock: RLock = lock or RLock()

    def has_rule(self, name: str) -> bool:
        with self._lock:
            try:
                self._resolve_rule(name)
                return True
            except RuleNotFoundException:
                return False
    
    def get_rule(self, name: str) -> Rule:
        with self._lock:
            return self._resolve_rule(name)

    def add_rule(self, name: str, rule: Rule):
        with self._lock:
            scope, rule_name = self._resolve_path(name)
            scope._rules[rule_name] = rule

    def remove_rule(self, name: str):
        with self._lock:
            scope, rule_name = self._resolve_path(name)
            if rule_name not in scope._rules:
                raise RuleNotFoundException(f"Rule '{rule_name}' not found")
            del scope._rules[rule_name]

    def has_scope(self, name: str) -> bool:
        with self._lock:
            try:
                self._resolve_scope(name)
                return True
            except ScopeNotFoundException:
                return False

    def get_scope(self, name: str) -> "Scope":
        with self._lock:
            return self._resolve_scope(name)

    def add_scope(self, name: str, scope: "Scope"):
        with self._lock:
            parent_scope, child_name = self._resolve_path(name)
            parent_scope._children[child_name] = scope
            scope._parent = parent_scope

    def remove_scope(self, name: str):
        with self._lock:
            parent_scope, child_name = self._resolve_path(name)
            if child_name not in parent_scope._children:
                raise ScopeNotFoundException(f"Scope '{child_name}' not found")
            child_scope = parent_scope._children[child_name]
            child_scope._parent = None
            del parent_scope._children[child_name]

    def call(self, name: str, *args, **kwargs) -> Union[Response, bool]:
        with self._lock:
            rule = self._resolve_rule(name)
            return rule(*args, **kwargs)

class AsyncScope(BaseScope, ScopeResolverMixin):
    def __init__(self, name: str, lock: Optional[Lock] = None):
        super().__init__(name)
        self._lock: Lock = lock or Lock()

    async def has_rule(self, name: str) -> bool:
        async with self._lock:
            try:
                self._resolve_rule(name)
                return True
            except RuleNotFoundException:
                return False

    async def get_rule(self, name: str) -> Rule:
        async with self._lock:
            return self._resolve_rule(name)

    async def add_rule(self, name: str, rule: Rule):
        async with self._lock:
            scope, rule_name = self._resolve_path(name)
            scope._rules[rule_name] = rule

    async def remove_rule(self, name: str):
        async with self._lock:
            scope, rule_name = self._resolve_path(name)
            if rule_name not in scope._rules:
                raise RuleNotFoundException(f"Rule '{rule_name}' not found")
            del scope._rules[rule_name]

    async def has_scope(self, name: str) -> bool:
        async with self._lock:
            try:
                self._resolve_scope(name)
                return True
            except ScopeNotFoundException:
                return False

    async def get_scope(self, name: str) -> "AsyncScope":
        async with self._lock:
            return self._resolve_scope(name)

    async def add_scope(self, name: str, scope: "AsyncScope"):
        async with self._lock:
            parent_scope, child_name = self._resolve_path(name)
            parent_scope._children[child_name] = scope
            scope._parent = parent_scope

    async def remove_scope(self, name: str):
        async with self._lock:
            parent_scope, child_name = self._resolve_path(name)
            if child_name not in parent_scope._children:
                raise ScopeNotFoundException(f"Scope '{child_name}' not found")
            child_scope = parent_scope._children[child_name]
            child_scope._parent = None
            del parent_scope._children[child_name]

    async def call(self, name: str, *args, **kwargs) -> Union[Response, bool]:
        async with self._lock:
            rule = self._resolve_rule(name)
            result = rule(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result
