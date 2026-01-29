from typing import Any, Callable, Awaitable
from fastapi import Depends, HTTPException
from scutum import AsyncGate, Response

class Can:
    def __init__(
        self,
        rule: str,
        resolver: Callable[..., Awaitable[Any]] | None = None,
    ):
        self.rule = rule
        self.resolver = resolver

    async def __call__(
        self,
        user: Any = Depends(),
        resource: Any = Depends(lambda: None),
    ):
        gate: AsyncGate = self.gate

        args = []
        if self.resolver:
            resource = await self.resolver()
            args.append(resource)

        try:
            await gate.authorize(self.rule, user, *args)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=403, detail=str(e))

        return user

def create_api_gate(user_resolver: Callable[..., Awaitable[Any]]):
    gate = AsyncGate()

    async def setup_once():
        if not getattr(gate, "_ready", False):
            await gate.setup()
            gate._ready = True

    def CanFactory(rule: str, resolver: Callable | None = None):
        dep = Can(rule, resolver)
        dep.gate = gate
        dep.__call__.__defaults__ = (Depends(user_resolver),)
        return dep

    gate.can = CanFactory
    gate._setup = setup_once
    return gate