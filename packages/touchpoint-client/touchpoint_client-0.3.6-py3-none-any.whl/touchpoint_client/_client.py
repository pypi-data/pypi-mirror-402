from __future__ import annotations

from typing import List, Optional

from ._auth import TouchpointClientAuth, TouchpointClientAuthBase, TouchpointClientTokenAuth
from ._connector import AsyncConnector, Connector
from ._decorators import use_error_details
from ._profile import _Profile, _ProfileAsync
from ._project import _Project, _ProjectAsync
from ._storage import _Storage, _StorageAsync
from ._users import _Users, _UsersAsync
from .exceptions import *
from .types import AsyncConnectorBase, ConnectorBase

DEFAULT_TIMEOUT = 300

__all__ = ["TouchpointClient", "TouchpointClientAsync"]


class TouchpointClient:
    """
    https://api.v15.touchpoint-analytics.ru/swagger/
    """

    _connector: ConnectorBase

    def __init__(
        self,
        api_url: str,
        *,
        connector: Optional[ConnectorBase] = None,
        auth: Optional[TouchpointClientAuthBase] = None,
        client_id: Optional[str] = None,
        auth_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        token_type: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Инициализация клиента

        При передаче access_token следующие записи эквиваленты:
        TouchpointClient(api_url, access_token="12423523")
        TouchpointClient(api_url, access_token="12423523", token_type="Bearer")
        TouchpointClient(api_url, access_token="Bearer 12423523", token_type="")

        :param api_url: Базовый URL для выполнения запросов
        :param connector: Объект для выполнения HTTP запросов. Если не передан используются следующие параметры для его создания.
        :param auth: Объект для выполнения авторизация. Используется если не передан connector. Если не передан, используются следующие параметры для его создания.
        :param client_id: Идентификатор приложения.
        :param client_secret: Секретный ключ приложения.
        :param auth_url: URL для аутентификации по протоколу OAuth 2
        :param username: Имя пользователя, для аутентификации
        :param password: Пароль
        :param access_token: token используемый при передаче запросов, если не передан auth и параметры авторизации
        :param token_type: Тип токена. Если не передан  используется значение по умолчанию. Если переданы пустая строка - полное значение пареметра заголовка Authorization указано в access_token
        :param timeout: Время ожидания ответа на запрос
        """
        if connector is None:
            if auth:
                self._auth = auth
            elif username and password and client_id and auth_url:
                self._auth = TouchpointClientAuth(
                    client_id,
                    auth_url,
                    username=username,
                    password=password,
                    client_secret=client_secret,
                    timeout=timeout,
                )
            elif access_token:
                if token_type is not None:
                    self._auth = TouchpointClientTokenAuth(access_token, token_type=token_type)
                else:
                    self._auth = TouchpointClientTokenAuth(access_token)
            else:
                raise AuthError(403, "Some authentication params missing")
            connector = Connector(api_url, auth=self._auth, timeout=timeout)
        self._connector = connector
        self._storage = _Storage(self._connector)
        self._profile = _Profile(self._connector)
        self._users = _Users(self._connector)

    @property
    def profile(self) -> _Profile:
        """
        Возвращает объект для выполнения API запросов к личной информации пользователя

        :return: Объект :class:`_Profile <_Profile>`
        :rtype: TouchpointClient._Profile
        """
        return self._profile

    @property
    def storage(self) -> _Storage:
        """
        Возвращает объект для выполнения API запросов к файловому хранилищу Touchpoint

        :return: Объект :class:`TouchpointClient._Storage`
        :rtype: TouchpointClient._Storage
        """
        return self._storage

    @property
    def users(self) -> _Users:
        """
        Возвращает объект для выполнения API запросов управления пользователями Touchpoint

        :return: Объект :class:`TouchpointClient._Users`
        :rtype: TouchpointClient._Users
        """
        return self._users

    def project(self, project_id: str) -> _Project:
        """
        Возвращает объект для выполнения API запросов к указанному проекту Touchpoint

        :param project_id: Идентификатор проекта

        :return: Объект :class:`TouchpointClient._Project`
        :rtype: TouchpointClient._Project
        """
        return _Project(self._connector, project_id)

    @use_error_details
    def projects(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""
        Получить список проектов, в которых участвует пользователь

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список проектов
        :rtype: List[dict]
        """
        res = self._connector.get(f"projects", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)


class TouchpointClientAsync:
    """
    https://api.v15.touchpoint-analytics.ru/swagger/
    """

    _connector: AsyncConnectorBase
    _auth: TouchpointClientAuthBase

    def __init__(
        self,
        api_url: str,
        *,
        connector: Optional[AsyncConnectorBase] = None,
        auth: Optional[TouchpointClientAuth] = None,
        client_id: Optional[str] = None,
        auth_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        token_type: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Инициализация клиента

        При передаче access_token следующие записи эквиваленты:
        TouchpointClientAsync(api_url, access_token="12423523")
        TouchpointClientAsync(api_url, access_token="12423523", token_type="Bearer")
        TouchpointClientAsync(api_url, access_token="Bearer 12423523", token_type="")

        :param api_url: Базовый URL для выполнения запросов
        :param connector: Объект для выполнения HTTP запросов. Если не передан используются следующие параметры для его создания.
        :param auth: Объект для выполнения авторизация. Используется если не передан connector. Если не передан, используются следующие параметры для его создания.
        :param client_id: Идентификатор приложения.
        :param client_secret: Секретный ключ приложения.
        :param auth_url: URL для аутентификации по протоколу OAuth 2
        :param username: Имя пользователя, для аутентификации
        :param password: Пароль
        :param access_token: token используемый при передаче запросов, если не передан auth и параметры авторизации
        :param token_type: Тип токена. Если не передан  используется значение по умолчанию. Если переданы пустая строка - полное значение пареметра заголовка Authorization указано в access_token
        :param timeout: Время ожидания ответа на запрос
        """
        if connector is None:
            if auth:
                self._auth = auth
            elif username and password and client_id and auth_url:
                self._auth = TouchpointClientAuth(
                    client_id,
                    auth_url,
                    username=username,
                    password=password,
                    client_secret=client_secret,
                    timeout=timeout,
                )
            elif access_token:
                if token_type is not None:
                    self._auth = TouchpointClientTokenAuth(access_token, token_type=token_type)
                else:
                    self._auth = TouchpointClientTokenAuth(access_token)
            else:
                raise AuthError(403, "Some authentication params missing")
            connector = AsyncConnector(api_url, auth=self._auth, timeout=timeout)
        self._connector = connector
        self._storage = _StorageAsync(self._connector)
        self._profile = _ProfileAsync(self._connector)
        self._users = _UsersAsync(self._connector)

    @property
    def profile(self) -> _ProfileAsync:
        """
        Возвращает объект для выполнения API запросов к личной информации пользователя

        :return: Объект :class:`_Profile <_Profile>`
        :rtype: TouchpointClient._Profile
        """
        return self._profile

    @property
    def storage(self) -> _StorageAsync:
        """
        Возвращает объект для выполнения API запросов к файловому хранилищу Touchpoint

        :return: Объект :class:`TouchpointClient._Storage`
        :rtype: TouchpointClient._Storage
        """
        return self._storage

    @property
    def users(self) -> _UsersAsync:
        """
        Возвращает объект для выполнения API запросов управления пользователями Touchpoint

        :return: Объект :class:`TouchpointClient._Users`
        :rtype: TouchpointClient._Users
        """
        return self._users

    def project(self, project_id: str) -> _ProjectAsync:
        """
        Возвращает объект для выполнения API запросов к указанному проекту Touchpoint

        :param project_id: Идентификатор проекта

        :return: Объект :class:`TouchpointClient._Project`
        :rtype: TouchpointClient._Project
        """
        return _ProjectAsync(self._connector, project_id)

    @use_error_details
    async def projects(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""
        Получить список проектов, в которых участвует пользователь

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список проектов
        :rtype: List[dict]
        """
        res = await self._connector.get(f"projects", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)
