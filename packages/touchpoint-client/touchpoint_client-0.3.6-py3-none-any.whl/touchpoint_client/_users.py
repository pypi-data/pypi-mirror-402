from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union, cast

from ._decorators import use_error_details
from .exceptions import ProjectNotFoundError, RequestError
from .types import AccountPermissions, AsyncConnectorBase, ConnectorBase, ProjectPermissions

__all__ = ("_Users", "_UsersAsync")


def _parse_result(
    response: Any,
    codes: Tuple[int, ...],
    error_on_404: bool = False,
    error_code: Optional[int] = None,
) -> Union[bool, dict, list, None]:

    if response.status_code in codes:
        return response.json() if response.status_code != 204 else True
    try:
        if response.status_code in (404,) and (not error_code or response.json()["code"] == error_code):
            if error_on_404:
                raise ProjectNotFoundError(response.status_code, response.text)
            return None
    except:
        pass
    raise RequestError(response.status_code, response.text)


class _Users:
    """
    Доступ к личной информации
    """

    def __init__(self, client: ConnectorBase):
        self._client: ConnectorBase = client

    @use_error_details
    def permissions(self, *, error_details: bool = False, **kwargs):
        """
        Получить все разрешения на аккаунт

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("permissions", **kwargs)
        return _parse_result(res, (200,))

    @use_error_details
    def projects_permissions(self, *, error_details: bool = False, **kwargs) -> List[str]:
        """
        Получить все разрешения на проект

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("projects/permissions", **kwargs)
        return cast(List[str], _parse_result(res, (200,)))

    @use_error_details
    def users(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список пользователей

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("users", **kwargs)
        return cast(List[dict], _parse_result(res, (200,)))

    @use_error_details
    def create_user(
        self,
        username: str,
        password: str,
        account_role_id: str,
        personal_settings: Optional[dict] = None,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> List[dict]:
        r"""Получить список пользователей

        :param username: Имя пользователя, которое является его электронной почтой
        :param password: Пароль пользователя
        :param account_role_id: Идентификатор роли на аккаунт
        :param personal_settings: Персональные настройки пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert username, "username cannot be empty"
        assert password, "password cannot be empty"
        assert account_role_id, "account_role cannot be empty"
        body: dict = {
            "username": username,
            "password": password,
            "account_role_id": account_role_id,
        }
        if personal_settings:
            body["personal_settings"] = personal_settings
        res = self._client.post("users", json=body, **kwargs)
        return cast(List[dict], _parse_result(res, (200, 201)))

    @use_error_details
    def user(self, user_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить пользователья по идентификатору

        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert user_id, "user_id is required"
        resp = self._client.get(f"users/{user_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def update_user(
        self,
        user_id: str,
        *,
        account_role_id: Optional[str] = None,
        personal_settings: Optional[dict] = None,
        error_details: bool = False,
        **kwargs,
    ) -> Optional[dict]:
        r"""Получить пользователья по идентификатору

        :param user_id: Идентификатор пользователя
        :param user_data: Данные пользователя для обновления
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert user_id, "user_id is required"
        assert account_role_id or personal_settings is not None, "account_role or personal_settings must not be empty"

        body: dict = {}
        if account_role_id:
            body["account_role_id"] = (account_role_id,)
        if personal_settings is not None:
            body["personal_settings"] = (personal_settings,)
        resp = self._client.patch(f"users/{user_id}", json=body, **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def groups(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список групп

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = self._client.get("groups", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    def create_group(self, name: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Получить список пользователей

        :param name: Имя группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert name, "name cannot be empty"
        body = {
            "name": name,
        }
        resp = self._client.post("groups", json=body, **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def group(self, group_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить группу по идентификатору

        :param group_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        resp = self._client.get(f"groups/{group_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def update_group(self, group_id: str, *, name: str, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Обновить данный группы

        :param group_id: Идентификатор группы
        :param name: Имя группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        assert name, "account_role or personal_settings must not be empty"

        body = {
            "name": name,
        }
        resp = self._client.patch(f"groups/{group_id}", json=body, **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def group_users(self, group_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить пользователей группы

        :param group_id: Идентификатор группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        resp = self._client.get(f"groups/{group_id}/users", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def create_group_user(
        self, group_id: str, user_id: str, *, error_details: bool = False, **kwargs
    ) -> Optional[dict]:
        r"""Добавить пользователя в группу

        :param group_id: Идентификатор группы
        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        assert user_id, "user_id is required"
        resp = self._client.put(f"groups/{group_id}/users/{user_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    def remove_group_user(self, group_id: str, user_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить пользователя из группы

        :param group_id: Идентификатор группы
        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 204.
        """
        assert group_id, "group_id is required"
        assert user_id, "user_id is required"
        resp = self._client.delete(f"groups/{group_id}/users/{user_id}", **kwargs)
        _parse_result(resp, (204,))

    @use_error_details
    def subjects(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить субъекты

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = self._client.get("subjects", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def roles(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на аккаунт

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = self._client.get("roles", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def create_role(
        self,
        name: str,
        permissions: List[Union[str, AccountPermissions]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить роль на аккаунт

        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert name, "name is required"
        body = {"name": name, "permissions": list(map(str, permissions))}
        resp = self._client.post("roles", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    def role(self, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id, "role_id is required"
        resp = self._client.get(f"roles/{role_id}", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def update_role(
        self,
        role_id: str,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[Union[str, AccountPermissions]]] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Обновить роль на аккаунт

        :param role_id: Идентификатор роли
        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id, "role_id is required"
        assert name or permissions is not None, "name or permissions is required"
        body: dict = {}
        if name:
            body["name"] = name
        if permissions is not None:
            body["permissions"] = list(map(str, permissions))
        resp = self._client.patch(f"roles/{role_id}", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    def remove_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> None:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 204.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        resp = self._client.delete(f"roles/{role_id}", **kwargs)
        _parse_result(resp, (204,))

    @use_error_details
    def projects_roles(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на проект

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = self._client.get("projects/roles", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def create_projects_role(
        self,
        name: str,
        permissions: List[Union[str, ProjectPermissions]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить роль на проект

        :param name: Название роли
        :param permissions: Ограничения пользователя на проект
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        body = {"name": name, "permissions": list(map(str, permissions))}
        resp = self._client.post("projects/roles", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    def projects_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на проект
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        resp = self._client.get(f"projects/roles/{role_id}", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    def update_projects_role(
        self,
        role_id: str,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[Union[str, AccountPermissions]]] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Обновить роль на аккаунт

        :param role_id: Идентификатор роли
        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        assert name or permissions is not None, "name or permissions is required"

        body: dict = {}
        if name:
            body["name"] = name
        if permissions is not None:
            body["permissions"] = list(map(str, permissions))
        resp = self._client.patch(f"projects/roles/{role_id}", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    def remove_projects_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> None:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """

        resp = self._client.delete(f"projects/roles/{role_id}", **kwargs)
        _parse_result(resp, (204,))


class _UsersAsync:
    """
    Доступ к личной информации
    """

    def __init__(self, client: AsyncConnectorBase):
        self._client: AsyncConnectorBase = client

    @use_error_details
    async def permissions(self, *, error_details: bool = False, **kwargs):
        """
        Получить все разрешения на аккаунт

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = self._client.get("permissions", **kwargs)
        return _parse_result(res, (200,))

    @use_error_details
    async def projects_permissions(self, *, error_details: bool = False, **kwargs) -> List[str]:
        """
        Получить все разрешения на проект

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = await self._client.get("projects/permissions", **kwargs)
        return cast(List[str], _parse_result(res, (200,)))

    @use_error_details
    async def users(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список пользователей

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        res = await self._client.get("users", **kwargs)
        return cast(List[dict], _parse_result(res, (200,)))

    @use_error_details
    async def create_user(
        self,
        username: str,
        password: str,
        account_role_id: str,
        personal_settings: Optional[dict] = None,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> List[dict]:
        r"""Получить список пользователей

        :param username: Имя пользователя, которое является его электронной почтой
        :param password: Пароль пользователя
        :param account_role_id: Идентификатор роли на аккаунт
        :param personal_settings: Персональные настройки пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert username, "username cannot be empty"
        assert password, "password cannot be empty"
        assert account_role_id, "account_role cannot be empty"
        body: dict = {
            "username": username,
            "password": password,
            "account_role_id": account_role_id,
        }
        if personal_settings:
            body["personal_settings"] = personal_settings
        res = await self._client.post("users", json=body, **kwargs)
        return cast(List[dict], _parse_result(res, (200, 201)))

    @use_error_details
    async def user(self, user_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить пользователья по идентификатору

        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert user_id, "user_id is required"
        resp = await self._client.get(f"users/{user_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def update_user(
        self,
        user_id: str,
        *,
        account_role_id: Optional[str] = None,
        personal_settings: Optional[dict] = None,
        error_details: bool = False,
        **kwargs,
    ) -> Optional[dict]:
        r"""Получить пользователья по идентификатору

        :param user_id: Идентификатор пользователя
        :param user_data: Данные пользователя для обновления
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert user_id, "user_id is required"
        assert account_role_id or personal_settings is not None, "account_role or personal_settings must not be empty"

        body: dict = {}
        if account_role_id:
            body["account_role_id"] = (account_role_id,)
        if personal_settings is not None:
            body["personal_settings"] = (personal_settings,)
        resp = await self._client.patch(f"users/{user_id}", json=body, **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def groups(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список групп

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = await self._client.get("groups", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    async def create_group(self, name: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Получить список пользователей

        :param name: Имя группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert name, "name cannot be empty"
        body = {
            "name": name,
        }
        resp = await self._client.post("groups", json=body, **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def group(self, group_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить группу по идентификатору

        :param group_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        resp = await self._client.get(f"groups/{group_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def update_group(self, group_id: str, *, name: str, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Обновить данный группы

        :param group_id: Идентификатор группы
        :param name: Имя группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        assert name, "account_role or personal_settings must not be empty"

        body = {
            "name": name,
        }
        resp = await self._client.patch(f"groups/{group_id}", json=body, **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def group_users(self, group_id: str, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        r"""Получить пользователей группы

        :param group_id: Идентификатор группы
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        resp = await self._client.get(f"groups/{group_id}/users", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def create_group_user(
        self, group_id: str, user_id: str, *, error_details: bool = False, **kwargs
    ) -> Optional[dict]:
        r"""Добавить пользователя в группу

        :param group_id: Идентификатор группы
        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert group_id, "group_id is required"
        assert user_id, "user_id is required"
        resp = await self._client.put(f"groups/{group_id}/users/{user_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False, 3))

    @use_error_details
    async def remove_group_user(self, group_id: str, user_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить пользователя из группы

        :param group_id: Идентификатор группы
        :param user_id: Идентификатор пользователя
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 204.
        """
        assert group_id, "group_id is required"
        assert user_id, "user_id is required"
        resp = await self._client.delete(f"groups/{group_id}/users/{user_id}", **kwargs)
        _parse_result(resp, (204,))

    @use_error_details
    async def subjects(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить субъекты

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = await self._client.get("subjects", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def roles(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на аккаунт

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = await self._client.get("roles", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def create_role(
        self,
        name: str,
        permissions: List[Union[str, AccountPermissions]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить роль на аккаунт

        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert name, "name is required"
        body = {"name": name, "permissions": list(map(str, permissions))}
        resp = await self._client.post("roles", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    async def role(self, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id, "role_id is required"
        resp = await self._client.get(f"roles/{role_id}", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def update_role(
        self,
        role_id: str,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[Union[str, AccountPermissions]]] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Обновить роль на аккаунт

        :param role_id: Идентификатор роли
        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id, "role_id is required"
        assert name or permissions is not None, "name or permissions is required"
        body: dict = {}
        if name:
            body["name"] = name
        if permissions is not None:
            body["permissions"] = list(map(str, permissions))
        resp = await self._client.patch(f"roles/{role_id}", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    async def remove_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> None:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 204.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        resp = await self._client.delete(f"roles/{role_id}", **kwargs)
        _parse_result(resp, (204,))

    @use_error_details
    async def projects_roles(self, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на проект

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        resp = await self._client.get("projects/roles", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def create_projects_role(
        self,
        name: str,
        permissions: List[Union[str, ProjectPermissions]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить роль на проект

        :param name: Название роли
        :param permissions: Ограничения пользователя на проект
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        body = {"name": name, "permissions": list(map(str, permissions))}
        resp = await self._client.post("projects/roles", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    async def projects_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        """
        Получить список ролей на проект
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        resp = await self._client.get(f"projects/roles/{role_id}", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,)))

    @use_error_details
    async def update_projects_role(
        self,
        role_id: str,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[Union[str, AccountPermissions]]] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Обновить роль на аккаунт

        :param role_id: Идентификатор роли
        :param name: Название роли
        :param permissions: Ограничения пользователя на аккаунт
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """
        assert role_id and role_id.strip(), "role_id is required"
        assert "/" not in role_id, "'/' is not allowed"
        assert name or permissions is not None, "name or permissions is required"

        body: dict = {}
        if name:
            body["name"] = name
        if permissions is not None:
            body["permissions"] = list(map(str, permissions))
        resp = await self._client.patch(f"projects/roles/{role_id}", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201)))

    @use_error_details
    async def remove_projects_role(self, role_id: str, *, error_details: bool = False, **kwargs) -> None:
        """
        Получить список ролей на аккаунт
        :param role_id: Идентификатор роли
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        """

        resp = await self._client.delete(f"projects/roles/{role_id}", **kwargs)
        _parse_result(resp, (204,))
