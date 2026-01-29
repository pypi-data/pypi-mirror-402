from scutum.exceptions import AuthorizationException

class Response:
    def __init__(self, allowed=False, message="Permission denied", status_code=403, json=False):
        super().__init__()
        self.allowed = allowed
        self.message = message
        self.status_code = status_code

    @classmethod
    def allow(cls, message="Permission granted", status_code=200):
        return cls(True, message, status_code)

    @classmethod
    def deny(cls, message="Permission denied", status_code=403):
        return cls(False, message, status_code)
    
    def authorize(self):
        if not self.allowed:
            raise AuthorizationException(self.message, self.status_code)
