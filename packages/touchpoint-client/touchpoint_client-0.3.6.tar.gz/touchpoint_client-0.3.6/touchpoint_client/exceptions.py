from __future__ import annotations

"""
Custom exceptions raised by touchpoint-client.
"""

__all__ = [
    "Error",
    "AuthError",
    "RequestError",
    "ProjectNotFoundError",
    "AccessDeniedError",
]


class Error(Exception):
    """Base class for all exceptions raised by the touchpoint-client library"""


class RequestError(Error):
    """Base class for all request error raised by the touchpoint-client library"""

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


class ServerError(RequestError):
    """Server error raised by the touchpoint-client library"""


class AuthError(RequestError):
    """Authentication error"""


class AccessDeniedError(RequestError):
    """Access denied error"""


class ProjectNotFoundError(RequestError):
    """Project not found error"""
