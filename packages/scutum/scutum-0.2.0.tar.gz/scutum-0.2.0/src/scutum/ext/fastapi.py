from typing import Any, Callable, Awaitable
from fastapi import Request, Depends, HTTPException
from scutum import AsyncGate, AuthorizationException

def fastapi_adapter(gate: AsyncGate, default_user_resolver: Callable[..., Awaitable[Any]]):
    def can(
        rule: str, 
        user_resolver: Callable[..., Awaitable[Any]] | None = None, 
        resource_resolver: Callable | None = None,
        exception: Exception | None = None
    ):
        async def dependency(
            request: Request, 
            user = Depends(user_resolver or default_user_resolver),
            resource = Depends(resource_resolver) if resource_resolver else None
        ):
            args = [resource] if resource_resolver else []
            try:
                await gate.authorize(rule, user, *args, request=request)
                return user
            except AuthorizationException as e:
                raise exception or HTTPException(status_code=403, detail=str(e))
        return dependency

    gate.can = can
    return gate