from __future__ import annotations
"""Domain-level exceptions mapped to HTTP errors in the API layer."""


class ServiceError(Exception):
    status_code = 400
    msg_key = "common.bad_request"

    def __init__(self, msg_key: str | None = None, status_code: int | None = None):
        if msg_key:
            self.msg_key = msg_key
        if status_code:
            self.status_code = status_code
        super().__init__(self.msg_key)


class NotFoundError(ServiceError):
    status_code = 404
    msg_key = "common.not_found"


class ConflictError(ServiceError):
    status_code = 409
    msg_key = "common.already_exists"


class AuthError(ServiceError):
    status_code = 401
    msg_key = "auth.invalid_credentials"
