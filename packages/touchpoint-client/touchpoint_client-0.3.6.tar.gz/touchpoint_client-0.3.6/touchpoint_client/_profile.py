from __future__ import annotations

from ._decorators import use_error_details
from .exceptions import RequestError
from .types import AsyncConnectorBase, ConnectorBase

__all__ = ("_Profile", "_ProfileAsync")


class _Profile:
    """
    Доступ к личной информации
    """

    def __init__(self, client: ConnectorBase):
        self._client: ConnectorBase = client

    @use_error_details
    def account(self, error_details: bool = False, **kwargs):
        """
        Получить информацию о текущем аккаунте

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    def profile(self, error_details: bool = False, **kwargs):
        r"""
        Получить информацию о текущем пользователе.

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("profile", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)


class _ProfileAsync:
    """
    Доступ к личной информации
    """

    def __init__(self, client: AsyncConnectorBase):
        self._client: AsyncConnectorBase = client

    @use_error_details
    async def account(self, error_details: bool = False, **kwargs):
        """
        Получить информацию о текущем аккаунте

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = await self._client.get("", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    async def profile(self, error_details: bool = False, **kwargs):
        r"""
        Получить информацию о текущем пользователе.

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = await self._client.get("profile", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)
