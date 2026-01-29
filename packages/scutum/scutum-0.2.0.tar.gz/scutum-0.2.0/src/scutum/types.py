from typing import Protocol, Union, Awaitable, Any
from scutum.response import Response

ReturnType = Union[Response, bool]

class Rule(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Union[ReturnType, Awaitable[ReturnType]]:
        ...
