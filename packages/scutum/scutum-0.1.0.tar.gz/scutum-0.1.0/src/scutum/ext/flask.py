from flask import Response, g
from functools import wraps
from scutum.exceptions import AuthorizationException
from scutum.cache import reset_scoped_cache

class Scutum:
    def __init__(self, app=None, user_resolver=None):
        self._gate = Gate()
        self._user_resolver = user_resolver or self._default_resolver

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.extensions["scutum"] = self

        @app.before_request
        def _before():
            reset_scoped_cache()

        @app.errorhandler(AuthorizationException)
        def _auth_error(err):
            return Response(err.message, status=err.status_code)

    @property
    def gate(self):
        return self._gate

    def user_resolver(self, func):
        self._user_resolver = func
        return func

    def _default_resolver(self):
        raise RuntimeError("User resolver not configured")

    def authorized(self, rule: str):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                user = self._user_resolver()
                self._gate.authorize(rule, user)
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    def authorized_rules(self, rules: list[str]):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                user = self._user_resolver()
                if self._gate.none(rules, user):
                    raise AuthorizationException()
                return fn(*args, **kwargs)
            return wrapper
        return decorator
