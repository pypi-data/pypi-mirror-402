class AuthorizationException(Exception):
    def __init__(self, message="Permission denied", status_code=403, *args):
        super().__init__(message, *args)
        self.status_code = status_code

class RuleNotFoundException(Exception):
    def __init__(self, message="Rule not found", *args):
        super().__init__(message, *args)

class ScopeNotFoundException(Exception):
    def __init__(self, message="Scope not found", *args):
        super().__init__(message, *args)