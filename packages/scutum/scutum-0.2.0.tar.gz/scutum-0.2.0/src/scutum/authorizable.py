from scutum.gate import Gate, AsyncGate

def authorizable(gate: Gate | AsyncGate):
    if not isinstance(gate, (Gate, AsyncGate)):
        raise ValueError("Gate or AsyncGate instance expected")

    def decorator(cls):
        def create_permission_method(method_type: str):
            async def async_method(self, action: str, *args, **kwargs):
                if method_type == 'can':
                    return await gate.allowed(action, self, *args, **kwargs)
                return await gate.denied(action, self, *args, **kwargs)

            def sync_method(self, action: str, *args, **kwargs):
                if method_type == 'can':
                    return gate.allowed(action, self, *args, **kwargs)
                return gate.denied(action, self, *args, **kwargs)

            return async_method if isinstance(gate, AsyncGate) else sync_method
        
        cls.can = create_permission_method('can')
        cls.cannot = create_permission_method('cannot')
        return cls

    return decorator
