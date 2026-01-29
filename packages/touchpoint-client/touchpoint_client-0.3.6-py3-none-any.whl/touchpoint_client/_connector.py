from __future__ import annotations

import typing
from urllib.parse import urljoin

import httpx

from ._auth import TouchpointClientAuthBase
from .exceptions import AccessDeniedError, AuthError, RequestError, ServerError
from .types import AsyncConnectorBase, ConnectorBase

DEFAULT_TIMEOUT = 300

__all__ = ["Connector", "AsyncConnector"]


class Connector(ConnectorBase):

    _auth: typing.Optional[TouchpointClientAuthBase]
    _authorization: typing.Optional[str] = None
    _authorization_params: typing.Optional[dict] = None

    def __init__(
        self,
        api_url,
        auth: typing.Optional[TouchpointClientAuthBase] = None,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.api_url = api_url
        self._timeout = timeout
        self._auth = auth
        self.session = httpx.Client(verify=False, timeout=timeout)
        self.session.auth = auth

    def url(self, part):
        return urljoin(self.api_url, part)

    def head(self, uri: str, **kwargs):
        return self.request("HEAD", uri, **kwargs)

    def get(self, uri: str, **kwargs):
        return self.request("GET", uri, **kwargs)

    def post(self, uri: str, **kwargs):
        return self.request("POST", uri, **kwargs)

    def put(self, uri: str, **kwargs):
        return self.request("PUT", uri, **kwargs)

    def patch(self, uri: str, **kwargs):
        return self.request("PATCH", uri, **kwargs)

    def delete(self, uri: str, **kwargs):
        return self.request("DELETE", uri, **kwargs)

    def request(self, method: str, uri: str, **kwargs):
        url = self.url(uri)
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            self.invalidate()
            response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            raise AuthError(response.status_code, response.text)
        if response.status_code == 403:
            raise AccessDeniedError(response.status_code, response.text)
        if 300 <= response.status_code <= 400:
            raise RequestError(response.status_code, response.text)
        if 500 <= response.status_code < 600:
            raise ServerError(response.status_code, response.text)
        return response

    def invalidate(self):
        if self._auth:
            self._auth.invalidate()


class AsyncConnector(AsyncConnectorBase):

    _auth: typing.Optional[TouchpointClientAuthBase]
    _authorization: typing.Optional[str] = None
    _authorization_params: typing.Optional[dict] = None

    def __init__(
        self,
        api_url,
        auth: typing.Optional[TouchpointClientAuthBase] = None,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.api_url = api_url
        self._timeout = timeout
        self._auth = auth
        self.session = httpx.AsyncClient(verify=False, timeout=timeout)
        self.session.auth = auth

    def url(self, part):
        return urljoin(self.api_url, part)

    async def head(self, uri: str, **kwargs):
        return await self.request("HEAD", uri, **kwargs)

    async def get(self, uri: str, **kwargs):
        return await self.request("GET", uri, **kwargs)

    async def post(self, uri: str, **kwargs):
        return await self.request("POST", uri, **kwargs)

    async def put(self, uri: str, **kwargs):
        return await self.request("PUT", uri, **kwargs)

    async def patch(self, uri: str, **kwargs):
        return await self.request("PATCH", uri, **kwargs)

    async def delete(self, uri: str, **kwargs):
        return await self.request("DELETE", uri, **kwargs)

    async def request(self, method: str, uri: str, **kwargs):
        url = self.url(uri)
        response = await self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            await self.invalidate()
            response = await self.session.request(method, url, **kwargs)
            if response.status_code == 401:
                raise AuthError(response.status_code, response.text)
        if response.status_code == 403:
            raise AccessDeniedError(response.status_code, response.text)
        if 300 <= response.status_code <= 400:
            raise RequestError(response.status_code, response.text)
        if 500 <= response.status_code < 600:
            raise ServerError(response.status_code, response.text)
        await response.aread()
        return response

    async def invalidate(self):
        if self._auth:
            await self._auth.async_invalidate()
