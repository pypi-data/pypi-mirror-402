from __future__ import annotations

import typing

import httpx

from .exceptions import AuthError

DEFAULT_TIMEOUT = 300

__all__ = ["TouchpointClientAuth", "TouchpointClientTokenAuth", "TouchpointClientAuthBase"]


class TouchpointClientAuthBase(httpx.Auth):
    pass


class TouchpointClientAuth(TouchpointClientAuthBase):

    _authorization: typing.Optional[str] = None
    _authorization_params: typing.Optional[dict] = None
    _auth_url: str
    _scope: set

    def __init__(
        self,
        client_id,
        auth_url,
        *,
        username=None,
        password=None,
        client_secret=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        self._auth_url = auth_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout = timeout
        self._authorization_params = {
            "username": username,
            "password": password,
            "client_id": self._client_id,
            "grant_type": "password",
            "error_details": True,
            "client_secret": self._client_secret,
        }

    def sync_auth_flow(self, request: httpx.Request) -> typing.Generator[httpx.Request, httpx.Response, None]:
        if not self._authorization:
            self.invalidate()
        if self._authorization:
            request.headers["Authorization"] = self._authorization
        yield request

    async def async_auth_flow(self, request: httpx.Request) -> typing.AsyncGenerator[httpx.Request, httpx.Response]:

        if not self._authorization:
            await self.async_invalidate()
        if self._authorization:
            request.headers["Authorization"] = self._authorization
        yield request

    def invalidate(self):
        self._authorization = None
        self.authenticate()

    async def async_invalidate(self):
        self._authorization = None
        await self.async_authenticate()

    def authenticate(self):
        res = httpx.post(
            self._auth_url,
            params=self._authorization_params,
            verify=False,
            timeout=self._timeout,
        )
        if res.status_code == 200:
            js = res.json()
            self._authorization = f"""{js["token_type"].capitalize()} {js["access_token"]}"""
            self._scope = set(js["scope"].split(" "))
        else:
            raise AuthError(res.status_code, res.text)

    async def async_authenticate(self):
        async with httpx.AsyncClient(verify=False, timeout=self._timeout) as client:
            res = await client.post(
                self._auth_url,
                params=self._authorization_params,
            )
            if res.status_code == 200:
                await res.aread()
                js = res.json()
                self._authorization = f"""{js["token_type"].capitalize()} {js["access_token"]}"""
                self._scope = set(js["scope"].split(" "))
            else:
                raise AuthError(res.status_code, res.text)

    @property
    def scope(self):
        return self._scope


class TouchpointClientTokenAuth(TouchpointClientAuthBase):

    _authorization: str

    def __init__(self, access_token: str, token_type: str = "Bearer"):
        if token_type:
            self._authorization = f"""{token_type} {access_token}"""
        else:
            self._authorization = access_token

    def auth_flow(self, request: httpx.Request) -> typing.Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = self._authorization
        yield request

    def invalidate(self):
        raise AuthError(403, f"{self._authorization} is not a valid authorization token")

    async def async_invalidate(self):
        raise AuthError(403, f"{self._authorization} is not a valid authorization token")

    @property
    def scope(self) -> set:
        return set()
