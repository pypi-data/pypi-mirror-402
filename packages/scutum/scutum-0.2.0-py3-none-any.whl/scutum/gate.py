import asyncio
from typing import Union, List, Any, Tuple
from scutum.types import Rule
from scutum.scope import Scope, AsyncScope
from scutum.policy import Policy, AsyncPolicy
from scutum.response import Response
from scutum.exceptions import AuthorizationException

class Gate:
    def __init__(self):
        self._root = Scope("root")

    def has_rule(self, name: str):
        return self._root.has_rule(name)

    def has_scope(self, name: str):
        return self._root.has_scope(name)
    
    def clear(self):
        self._root = Scope("root")
    
    def rules(self):
        return dict(self._root._rules)
    
    def scopes(self):
        return self._root._children
    
    def _register_rule(self, name: str, rule: Rule):
        if not callable(rule):
            raise TypeError("Rule must be a callable")
        self._root.add_rule(name, rule)
            
    def _register_policy(self, name: str, policy: Policy):
        if not isinstance(policy, type) or not issubclass(policy, Policy):
            raise TypeError("policy must be a Policy class (not an instance)")
        self._ensure_policy_registration(name, policy)

    def _ensure_policy_registration(self, name: str, policy: Policy):
        if self._root.has_scope(name):
            raise KeyError(f"A scope named {name} already exists")
        scope = policy._to_scope(name)
        self._root.add_scope(name, scope)

    def _call_rule(self, name: str, *args, **kwargs):
        return self._root.call(name, *args, **kwargs)

    def scope(self, name: str):
        def decorator(scope: Scope):
            self.add_scope(name, scope)
            return scope
        return decorator
        
    def add_scope(self, name: str, scope: Scope):
        if self._root.has_scope(name):
            raise KeyError(f"A scope named {name} already exists")
        self._root.add_scope(name, scope)

    def rule(self, name: str):
        def decorator(rule: Rule):
            self._register_rule(name, rule)
            return rule
        return decorator
    
    def add_rule(self, name: str, rule: Rule):
        if self._root.has_rule(name):
            raise KeyError(f"A rule named {name} already exists")
        self._register_rule(name, rule)
    
    def policy(self, name):
        def decorator(policy: Policy):
            self._register_policy(name, policy)
            return policy
        return decorator
    
    def add_policy(self, name, policy):
        self._register_policy(name, policy)
    
    def remove_rule(self, name: str):
        self._root.remove_rule(name)

    def remove_scope(self, name: str):
        self._root.remove_scope(name)

    def check(self, rule: str, user: Any, *args, **kwargs) -> Union[Response, bool]:
        result = self._call_rule(rule, user, *args, **kwargs)
        if isinstance(result, Response):
            return result
        return bool(result)

    def allowed(self, rule: str, user: Any, *args, **kwargs) -> bool:
        response = self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            return response.allowed
        return response

    def denied(self, rule: str, user: Any, *args, **kwargs) -> bool:
        response = self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            return not response.allowed
        return not response
    
    def authorize(self, rule: str, user: Any, *args, **kwargs) -> None:
        response = self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            response.authorize()

        if isinstance(response, bool) and not response:
            raise AuthorizationException()
    
    def any(self, rules: List[str], user: Any, *args, **kwargs):
        return any([self.allowed(rule, user, *args, **kwargs) for rule in rules])

    def none(self, rules: List[str], user: Any, *args, **kwargs):
        return not self.any(rules, user, *args, **kwargs)

class AsyncGate:
    def __init__(self):
        self._root = AsyncScope("root")
        self._pending_rules: List[Tuple[str, Rule]] = []
        self._pending_scopes: List[Tuple[str, AsyncScope]] = []
        self._pending_policies: List[Tuple[str, AsyncPolicy]] = []
        self._lock = asyncio.Lock()
        self._setup_completed = False

    async def setup(self):
        async with self._lock:
            for name, rule in self._pending_rules:
                await self._register_rule(name, rule)
            self._pending_rules.clear()

            for name, scope in self._pending_scopes:
                await self.add_scope(name, scope)
            self._pending_scopes.clear()

            for name, policy in self._pending_policies:
                await self._register_policy(name, policy)
            self._pending_policies.clear()

    async def has_rule(self, name: str):
        return await self._root.has_rule(name)

    async def has_scope(self, name: str):
        return await self._root.has_scope(name)

    def clear(self):
        self._root = AsyncScope("root")

    def rules(self):
        return dict(self._root._rules)

    def scopes(self):
        return self._root._children

    async def _register_rule(self, name: str, rule: Rule):
        if not callable(rule):
            raise TypeError("Rule must be a callable")
        await self._root.add_rule(name, rule)

    async def _register_policy(self, name: str, policy: AsyncPolicy):
        if not isinstance(policy, type) or not issubclass(policy, AsyncPolicy):
            raise TypeError("policy must be a AsyncPolicy class (not an instance)")
        await self._ensure_policy_registration(name, policy)

    async def _ensure_policy_registration(self, name: str, policy: AsyncPolicy):
        if await self._root.has_scope(name):
            raise KeyError(f"A scope named {name} already exists")
        scope = policy._to_scope(name)
        await self._root.add_scope(name, await scope)

    async def _call_rule(self, name: str, *args, **kwargs):
        return await self._root.call(name, *args, **kwargs)
    
    def scope(self, name: str):
        def decorator(scope: AsyncScope):
            self._pending_scopes.append((name, scope))
            return scope
        return decorator

    async def add_scope(self, name: str, scope: AsyncScope):
        if await self._root.has_scope(name):
            raise KeyError(f"A scope named {name} already exists")
        await self._root.add_scope(name, scope)

    def rule(self, name: str):
        def decorator(rule: Rule):
            self._pending_rules.append((name, rule))
            return rule
        return decorator

    async def add_rule(self, name: str, rule: Rule):
        if await self._root.has_rule(name):
            raise KeyError(f"A rule named {name} already exists")
        await self._register_rule(name, rule)

    def policy(self, name: str):
        def decorator(policy: AsyncPolicy):
            self._pending_policies.append((name, policy))
            return policy
        return decorator

    async def add_policy(self, name: str, policy: AsyncPolicy):
        await self._register_policy(name, policy)

    async def remove_rule(self, name: str):
        await self._root.remove_rule(name)

    async def remove_scope(self, name: str):
        await self._root.remove_scope(name)

    async def check(self, rule: str, user: Any, *args, **kwargs) -> Union[Response, bool]:
        if not self._setup_completed:
            await self.setup()
            self._setup_completed = True

        result = await self._call_rule(rule, user, *args, **kwargs)
        if isinstance(result, Response):
            return result
        return bool(result)

    async def allowed(self, rule: str, user: Any, *args, **kwargs) -> bool:
        response = await self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            return response.allowed
        return response

    async def denied(self, rule: str, user: Any, *args, **kwargs) -> bool:
        response = await self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            return not response.allowed
        return not response

    async def authorize(self, rule: str, user: Any, *args, **kwargs) -> None:
        response = await self.check(rule, user, *args, **kwargs)
        if isinstance(response, Response):
            response.authorize()
        elif isinstance(response, bool) and not response:
            raise AuthorizationException()

    async def any(self, rules: List[str], user: Any, *args, **kwargs):
        results = await asyncio.gather(
            *[self.allowed(rule, user, *args, **kwargs) for rule in rules]
        )
        return any(results)

    async def none(self, rules: List[str], user: Any, *args, **kwargs):
        return not await self.any(rules, user, *args, **kwargs)
