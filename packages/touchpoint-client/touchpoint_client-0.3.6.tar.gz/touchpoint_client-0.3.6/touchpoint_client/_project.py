from __future__ import annotations

import datetime
from typing import Any, AsyncGenerator, Generator, List, Optional, Tuple, Union, cast

from ._decorators import use_error_details
from .exceptions import ProjectNotFoundError, RequestError
from .types import AsyncConnectorBase, ConnectorBase, ProjectAggregateBody, ProjectGetDocumentBody, ProjectSearchBody

__all__ = ("_Project", "_ProjectAsync")


def _parse_result(response: Any, codes: Tuple[int, ...], error_on_404: bool = True) -> Union[bool, dict, list, None]:
    if response.status_code in codes:
        return response.json() if response.status_code != 204 else True
    try:
        if response.status_code in (404,) and response.json()["code"] == 2:
            if error_on_404:
                raise ProjectNotFoundError(response.status_code, response.text)
            return None
    except:
        pass
    raise RequestError(response.status_code, response.text)


class _Project:
    r"""
    Управление проектами
    """

    def __init__(self, client: ConnectorBase, project_id: str):
        """
        :param client: Коннектор к Touchpoint
        :param project_id: Идентификатор проекта
        """

        self._client: ConnectorBase = client
        self.project_id: str = project_id

    @use_error_details
    def info(self, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        """
        Получить информацию о проекте

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о проекте или None.
        """
        resp = self._client.get(f"projects/{self.project_id}", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False))

    def append(
        self,
        item_id: str,
        data: Optional[dict] = None,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""

        :param item_id:
        :param data:
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return:
        """
        if data:
            return self.append_document(item_id, data, error_details=error_details, **kwargs)
        else:
            return self.append_file(item_id, error_details=error_details, **kwargs)

    def append_file(
        self,
        file_id: str,
        *,
        language: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""Добавить файл в коллекцию. Информация о файле обогатиться информацией из файлового сервиса

        :param file_id: Идентификатор файла
        :param language: Языки файла
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: True если файл добавблен. Иначе будет выброшено исключение
        """
        results = self.append_files([file_id], language=language, error_details=error_details, **kwargs)
        return results[0]["success"]

    @use_error_details
    def append_files(
        self,
        file_ids: List[Union[str, dict]],
        *,
        language: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> list:
        r"""Добавить файлы в коллекцию. Информация о файле обогатиться информацией из файлового сервиса

        :param file_ids: Список добавляемых файлов. В списке или строка с идентификатором файла, или словарь
        :param language: Список языков, передаваемых вместе с файлами, которые перечислены в file_ids в виде строки
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список, содержащий результаты добавбления файлов в коллекцию
        """
        data: list = []
        if language is not None:
            if isinstance(language, str):
                language = [language]
        for file_id in file_ids:
            if isinstance(file_id, str):
                file: dict = {"id": file_id}
                if language is not None:
                    file["language"] = language
                data.append(file)
            elif isinstance(file_id, dict):
                data.append(file_id)

        resp = self._client.post(f"projects/{self.project_id}/files", json=data, **kwargs)
        return cast(list, _parse_result(resp, (200, 201), True))

    def append_document(
        self,
        document_id: str,
        document_data: dict,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""Добавить документ в коллекцию

        :param document_id: Идетификатор документа
        :param document_data: Содержимое документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Статус
        """
        results = self.append_documents({document_id: document_data}, error_details=error_details, **kwargs)
        return results.get(str(document_id), True)

    @use_error_details
    def append_documents(self, documents_dict: dict, *, error_details: bool = False, **kwargs) -> dict:
        r"""Добавить документы в коллекцию

        :param documents_dict: Словарь документов. Ключ - идентификатор, значение - тело документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список статусов
        """
        documents = [{"id": id_, "data": data_} for id_, data_ in documents_dict.items()]
        body = {"documents": documents}
        resp = self._client.post(f"projects/{self.project_id}/documents", json=body, **kwargs)
        result = _parse_result(resp, (200, 201), True)
        # DPP не поддерживает передачу статусов добавления документов
        # results = {document["id"]: result["status"] for document, result in zip(documents, result["documents"])}
        results = {document["id"]: True for document in documents}
        return results

    def update_document(
        self,
        document_id: str,
        document_data: dict,
        *,
        error_details: bool = False,
        **kwargs,
    ):
        r"""Обновить документ

        :param document_id: Идетификатор документа
        :param document_data: Содержимое документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        :return:
        """
        results = self.update_documents({document_id: document_data}, error_details=error_details, **kwargs)
        return results[str(document_id)]

    @use_error_details
    def update_documents(self, documents_dict: dict, *, error_details: bool = False, **kwargs) -> dict:
        r"""
        :param documents_dict: Словарь документов. Ключ - идентификатор, значение - тело документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return:
        """
        documents = [{"id": id_, "op_type": "patch", "data": data_} for id_, data_ in documents_dict.items()]
        body = {"documents": documents}
        resp = self._client.post(f"projects/{self.project_id}/documents", json=body, **kwargs)
        result = cast(dict, _parse_result(resp, (200, 201), True))
        # results = {document["id"]: result["status"] for document, result in zip(documents, result["documents"])}
        results = {document["id"]: True for document in documents}
        return results

    @use_error_details
    def get_fields(self, *, error_details: bool = False, **kwargs) -> dict:
        """

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        :return:
        """
        resp = self._client.get(f"projects/{self.project_id}/realtime/fields", **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def get_document(
        self,
        document_id: str,
        body: Union[ProjectGetDocumentBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param document_id:
        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        if isinstance(body, ProjectGetDocumentBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectGetDocumentBody object"
        resp = self._client.post(
            f"projects/{self.project_id}/realtime/documents/{document_id}",
            json=body,
            **kwargs,
        )
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def remove_document(
        self,
        document_id: str,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        """

        :param document_id: Идентификатор удаляемого документа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return:
        """

        resp = self._client.delete(
            f"projects/{self.project_id}/realtime/documents/{document_id}",
            **kwargs,
        )
        return cast(bool, _parse_result(resp, (200,), True))

    @use_error_details
    def search(
        self,
        body: Union[ProjectSearchBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        if isinstance(body, ProjectSearchBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectSearchBody object"
        resp = self._client.post(f"projects/{self.project_id}/realtime/search", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def scroll(
        self,
        scroll_id: str,
        scroll: str = "5m",
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param scroll_id:
        :param scroll:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        body = {
            "scroll_id": scroll_id,
            "scroll": scroll,
        }
        resp = self._client.post(f"projects/search/scroll", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def delete_scrolls(self, *, error_details: bool = False, **kwargs) -> None:
        """

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return:
        """
        resp = self._client.delete(f"projects/search/scroll", **kwargs)
        _parse_result(resp, (204,), True)

    def iterate_search(
        self,
        search_body: Union[ProjectSearchBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> Generator[dict]:
        """

        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        result = self.search(search_body, error_details=error_details, **kwargs)
        if isinstance(search_body, ProjectSearchBody):
            body = search_body.dict()
        else:
            body = cast(dict, search_body)
        while result and result.get("documents"):
            for document in result["documents"]:
                yield document
            if not result.get("scroll_id"):
                break
            result = self.scroll(
                result["scroll_id"],
                scroll=body.get("scroll"),
                error_details=error_details,
                **kwargs,
            )

    @use_error_details
    def aggregate(
        self,
        body: Union[ProjectAggregateBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        r"""Агрегировать документы в проекте. Агрегирование суммирует ваши данные в виде показателей, статистики или другой аналитики

        :param body: Данные для агрегации по проекту
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает `requests.post`.
        :return: Ответ агрегации по проекту, включающий общее количество документов и идентификатор проекта.
        :rtype: dict
        """
        if isinstance(body, ProjectAggregateBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectAggregateBody object"
        resp = self._client.post(f"projects/{self.project_id}/realtime/aggregate", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def users(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить пользователей проекта вместе с ролями

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Пользователи, принадлежащие проекту
        """
        resp = self._client.get(f"projects/{self.project_id}/users", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    def append_user(self, user_id: str, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Добавить пользователя в проект с определённой ролью или обновить роль у добавленного пользователя

        :param user_id: Идентификатор пользователя
        :param role_id: Идентификатор роли на проект
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.patch``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        """
        results = self.append_users([(user_id, role_id)], error_details=error_details, **kwargs)
        return results

    @use_error_details
    def append_users(
        self,
        users: List[Union[dict, tuple, list]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> List[dict]:
        r"""Добавить пользователей в проект с определённой ролью или обновить роль у добавленного пользователя

        :param users: Список пользователей с ролями в проекте
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.patch``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        """
        assert users
        data = [a if isinstance(a, dict) else {"id": a[0], "role_id": a[1]} for a in users]
        resp = self._client.patch(f"projects/{self.project_id}/users", json=data, **kwargs)
        return cast(List[dict], _parse_result(resp, (200,), True))

    @use_error_details
    def remove_users(self, users: Union[List[str], str], *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Удалить пользователей из проекта по фильтру

        :param users: Список идентификаторов пользователей
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        :rtype: List[dict]
        """
        assert users
        if isinstance(users, str):
            users = [users]
        kwargs["params"]["ids"] = ",".join(map(str, users))
        resp = self._client.delete(f"projects/{self.project_id}/users", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,), True))

    @use_error_details
    def subjects(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить субъекты проекта

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Список субъектов в проекте
        """
        resp = self._client.get(f"projects/{self.project_id}/subjects", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    def append_subject(self, subject_id: str, role_id: str, *, error_details: bool = False, **kwargs) -> dict:
        r"""Добавить субъект в проект

        :param subject_id: Идентификатор субъекта (группы или пользователя)
        :type subject_id: str
        :param role_id: Идентификатор роли на проект
        :type role_id: str
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.put``.
        :return: Субъект добавленный в проект
        :rtype: dict
        """
        data = {
            "role_id": role_id,
        }
        resp = self._client.put(f"projects/{self.project_id}/subjects/{subject_id}", json=data, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201), True))

    @use_error_details
    def remove_subject(self, subject_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить субъект из проекта

        :param subject_id: Идентификатор субъекта (группы или пользователя)
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        """
        resp = self._client.delete(f"projects/{self.project_id}/subjects/{subject_id}", **kwargs)
        _parse_result(resp, (204,), True)

    @use_error_details
    def checklists(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить чек-листы проекта

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Список чек-листов
        """
        resp = self._client.get(f"projects/{self.project_id}/checklists", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    def append_checklist(
        self,
        name: str,
        begin_date: Union[str, datetime.datetime],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        r"""Добавить чек-лист в проект; чек-лист создаётся на основе последнего чек-листа в проекте. Чек-листы сравниваются по дате применения begin_date, если эти даты равны, то по дате создания created_date.

        :param name: Название чек-листа
        :param begin_date: Дата начала применения чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.put``.
        :return: Субъект добавленный в проект
        :rtype: dict
        """
        if isinstance(begin_date, datetime.datetime):
            begin_date = begin_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        data = {
            "name": name,
            "begin_date": begin_date,
        }
        resp = self._client.post(f"projects/{self.project_id}/checklists", json=data, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    def checklist(self, checklist_id: str, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Чек-лист
        """

        resp = self._client.get(f"projects/{self.project_id}/checklists/{checklist_id}", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    def update_checklist(
        self,
        checklist_id: str,
        *,
        name: Optional[str] = None,
        begin_date: Union[None, str, datetime.datetime] = None,
        error_details: bool = False,
        **kwargs,
    ) -> Optional[List[dict]]:
        r"""Обновить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param name: Название чек-листа
        :param begin_date: Дата начала применения чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Чек-лист
        """

        data = {}
        if name:
            data["name"] = name
        if begin_date is not None:
            if isinstance(begin_date, datetime.datetime):
                begin_date = begin_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            data["begin_date"] = begin_date
        resp = self._client.patch(f"projects/{self.project_id}/checklists/{checklist_id}", json=data, **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    def remove_checklist(self, checklist_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True Если чек-лист успешно удалён
        """
        resp = self._client.delete(f"projects/{self.project_id}/checklists/{checklist_id}", **kwargs)
        _parse_result(resp, (204,), True)


class _ProjectAsync:
    r"""
    Управление проектами
    """

    def __init__(self, client: AsyncConnectorBase, project_id: str):
        """
        :param client: Коннектор к Touchpoint
        :param project_id: Идентификатор проекта
        """

        self._client: AsyncConnectorBase = client
        self.project_id: str = project_id

    @use_error_details
    async def info(self, *, error_details: bool = False, **kwargs) -> Optional[dict]:
        """
        Получить информацию о проекте

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о проекте или None.
        """
        resp = await self._client.get("storage", **kwargs)
        return cast(Optional[dict], _parse_result(resp, (200,), False))

    async def append(
        self,
        item_id: str,
        data: Optional[dict] = None,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""

        :param item_id:
        :param data:
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return:
        """
        if data:
            return await self.append_document(item_id, data, error_details=error_details, **kwargs)
        else:
            return await self.append_file(item_id, error_details=error_details, **kwargs)

    async def append_file(
        self,
        file_id: str,
        *,
        language: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""Добавить файл в коллекцию. Информация о файле обогатиться информацией из файлового сервиса

        :param file_id: Идентификатор файла
        :param language: Языки файла
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: True если файл доавблен. Иначе будет выброшено исключение
        """
        results = await self.append_files([file_id], language=language, error_details=error_details, **kwargs)
        return results[0]["success"]

    @use_error_details
    async def append_files(
        self,
        file_ids: List[Union[str, dict]],
        *,
        language: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> list:
        r"""Добавить файлы в коллекцию. Информация о файле обогатиться информацией из файлового сервиса

        :param file_ids: Список добавляемых файлов. В списке или строка с идентификатором файла, или словарь
        :param language: Список языков, передаваемых вместе с файлами, которые перечислены в file_ids в виде строки
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список, содержащий результаты добавбления файлов в коллекцию
        """
        data: list = []
        if language is not None:
            if isinstance(language, str):
                language = [language]
        for file_id in file_ids:
            if isinstance(file_id, str):
                file: dict = {"id": file_id}
                if language is not None:
                    file["language"] = language
                data.append(file)
            elif isinstance(file_id, dict):
                data.append(file_id)

        resp = await self._client.post(f"projects/{self.project_id}/files", json=data, **kwargs)
        return cast(list, _parse_result(resp, (200, 201), True))

    async def append_document(
        self,
        document_id: str,
        document_data: dict,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        r"""Добавить документ в коллекцию

        :param document_id: Идетификатор документа
        :param document_data: Содержимое документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Статус
        """
        results = await self.append_documents({document_id: document_data}, error_details=error_details, **kwargs)
        return results[str(document_id)]

    @use_error_details
    async def append_documents(self, documents_dict: dict, *, error_details: bool = False, **kwargs) -> dict:
        r"""Добавить документы в коллекцию

        :param documents_dict: Словарь документов. Ключ - идентификатор, значение - тело документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return: Список статусов
        """
        documents = [{"id": id_, "data": data_} for id_, data_ in documents_dict.items()]
        body = {"documents": documents}
        resp = await self._client.post(f"projects/{self.project_id}/documents", json=body, **kwargs)
        result = cast(list, _parse_result(resp, (200, 201), True))
        # results = {document["id"]: result["status"] for document, result in zip(documents, result["documents"])}
        results = {document["id"]: True for document in documents}
        return results

    async def update_document(
        self,
        document_id: str,
        document_data: dict,
        *,
        error_details: bool = False,
        **kwargs,
    ):
        r"""Обновить документ

        :param document_id: Идетификатор документа
        :param document_data: Содержимое документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        :return:
        """
        results = await self.update_documents({document_id: document_data}, error_details=error_details, **kwargs)
        return results[str(document_id)]

    @use_error_details
    async def update_documents(self, documents_dict: dict, *, error_details: bool = False, **kwargs) -> dict:
        r"""
        :param documents_dict: Словарь документов. Ключ - идентификатор, значение - тело документа
        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.

        :return:
        """
        documents = [{"id": id_, "op_type": "patch", "data": data_} for id_, data_ in documents_dict.items()]
        body = {"documents": documents}
        resp = await self._client.post(f"projects/{self.project_id}/documents", json=body, **kwargs)
        result = cast(dict, _parse_result(resp, (200, 201), True))
        # results = {document["id"]: result["status"] for document, result in zip(documents, result["documents"])}
        results = {document["id"]: True for document in documents}
        return results

    @use_error_details
    async def get_fields(self, *, error_details: bool = False, **kwargs) -> dict:
        """

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200.
        :return:
        """
        resp = await self._client.get(f"projects/{self.project_id}/realtime/fields", **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def get_document(
        self,
        document_id: str,
        body: Union[ProjectGetDocumentBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param document_id:
        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        if isinstance(body, ProjectGetDocumentBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectGetDocumentBody object"
        resp = await self._client.post(
            f"projects/{self.project_id}/realtime/documents/{document_id}",
            json=body,
            **kwargs,
        )
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def remove_document(
        self,
        document_id: str,
        *,
        error_details: bool = False,
        **kwargs,
    ) -> bool:
        """

        :param document_id: Идентификатор удаляемого документа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return:
        """

        resp = await self._client.delete(
            f"projects/{self.project_id}/realtime/documents/{document_id}",
            **kwargs,
        )
        return cast(bool, _parse_result(resp, (200,), True))

    @use_error_details
    async def search(
        self,
        body: Union[ProjectSearchBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        if isinstance(body, ProjectSearchBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectSearchBody object"
        resp = await self._client.post(f"projects/{self.project_id}/realtime/search", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def scroll(
        self,
        scroll_id: str,
        scroll: str = "5m",
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """

        :param scroll_id:
        :param scroll:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        body = {
            "scroll_id": scroll_id,
            "scroll": scroll,
        }
        resp = await self._client.post(f"projects/search/scroll", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def delete_scrolls(self, *, error_details: bool = False, **kwargs) -> None:
        """

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return:
        """
        resp = await self._client.delete(f"projects/search/scroll", **kwargs)
        _parse_result(resp, (204,), True)

    async def iterate_search(
        self,
        search_body: Union[ProjectSearchBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> AsyncGenerator[dict]:
        """

        :param body:
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :return:
        """
        result = await self.search(search_body, error_details=error_details, **kwargs)
        if isinstance(search_body, ProjectSearchBody):
            body = search_body.dict()
        else:
            body = cast(dict, search_body)
        while result and result.get("documents"):
            for document in result["documents"]:
                yield document
            if not result.get("scroll_id"):
                break
            result = self.scroll(
                result["scroll_id"],
                scroll=body.get("scroll"),
                error_details=error_details,
                **kwargs,
            )

    @use_error_details
    async def aggregate(
        self,
        body: Union[ProjectAggregateBody, dict],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        r"""Агрегировать документы в проекте. Агрегирование суммирует ваши данные в виде показателей, статистики или другой аналитики

        :param body: Данные для агрегации по проекту
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает `requests.post`.
        :return: Ответ агрегации по проекту, включающий общее количество документов и идентификатор проекта.
        :rtype: dict
        """
        if isinstance(body, ProjectAggregateBody):
            body = body.dict()
        assert isinstance(body, dict), "Body must be dict or ProjectAggregateBody object"
        resp = await self._client.post(f"projects/{self.project_id}/realtime/aggregate", json=body, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def users(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить пользователей проекта вместе с ролями

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Пользователи, принадлежащие проекту
        """
        resp = await self._client.get(f"projects/{self.project_id}/users", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    async def append_user(self, user_id: str, role_id: str, *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Добавить пользователя в проект с определённой ролью или обновить роль у добавленного пользователя

        :param user_id: Идентификатор пользователя
        :param role_id: Идентификатор роли на проект
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.patch``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        """
        results = await self.append_users([(user_id, role_id)], error_details=error_details, **kwargs)
        return results

    @use_error_details
    async def append_users(
        self,
        users: List[Union[dict, tuple, list]],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> List[dict]:
        r"""Добавить пользователей в проект с определённой ролью или обновить роль у добавленного пользователя

        :param users: Список пользователей с ролями в проекте
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.patch``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        """
        assert users
        data = [a if isinstance(a, dict) else {"id": a[0], "role_id": a[1]} for a in users]
        resp = await self._client.patch(f"projects/{self.project_id}/users", json=data, **kwargs)
        return cast(List[dict], _parse_result(resp, (200,), True))

    @use_error_details
    async def remove_users(self, users: Union[List[str], str], *, error_details: bool = False, **kwargs) -> List[dict]:
        r"""Удалить пользователей из проекта по фильтру

        :param users: Список идентификаторов пользователей
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        :return: Обновляённый список пользователей, принадлежащих проекту
        :rtype: List[dict]
        """
        assert users
        if isinstance(users, str):
            users = [users]
        kwargs["params"]["ids"] = ",".join(map(str, users))
        resp = await self._client.delete(f"projects/{self.project_id}/users", **kwargs)
        return cast(List[dict], _parse_result(resp, (200,), True))

    @use_error_details
    async def subjects(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить субъекты проекта

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Список субъектов в проекте
        """
        resp = await self._client.get(f"projects/{self.project_id}/subjects", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    async def append_subject(self, subject_id: str, role_id: str, *, error_details: bool = False, **kwargs) -> dict:
        r"""Добавить субъект в проект

        :param subject_id: Идентификатор субъекта (группы или пользователя)
        :type subject_id: str
        :param role_id: Идентификатор роли на проект
        :type role_id: str
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.put``.
        :return: Субъект добавленный в проект
        :rtype: dict
        """
        data = {
            "role_id": role_id,
        }
        resp = await self._client.put(f"projects/{self.project_id}/subjects/{subject_id}", json=data, **kwargs)
        return cast(dict, _parse_result(resp, (200, 201), True))

    @use_error_details
    async def remove_subject(self, subject_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить субъект из проекта

        :param subject_id: Идентификатор субъекта (группы или пользователя)
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.delete``.
        """
        resp = await self._client.delete(f"projects/{self.project_id}/subjects/{subject_id}", **kwargs)
        _parse_result(resp, (204,), True)

    @use_error_details
    async def checklists(self, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить чек-листы проекта

        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Список чек-листов
        """
        resp = await self._client.get(f"projects/{self.project_id}/checklists", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    async def append_checklist(
        self,
        name: str,
        begin_date: Union[str, datetime.datetime],
        *,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        r"""Добавить чек-лист в проект; чек-лист создаётся на основе последнего чек-листа в проекте. Чек-листы сравниваются по дате применения begin_date, если эти даты равны, то по дате создания created_date.

        :param name: Название чек-листа
        :param begin_date: Дата начала применения чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.put``.
        :return: Субъект добавленный в проект
        :rtype: dict
        """
        if isinstance(begin_date, datetime.datetime):
            begin_date = begin_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        data = {
            "name": name,
            "begin_date": begin_date,
        }
        resp = await self._client.post(f"projects/{self.project_id}/checklists", json=data, **kwargs)
        return cast(dict, _parse_result(resp, (200,), True))

    @use_error_details
    async def checklist(self, checklist_id: str, *, error_details: bool = False, **kwargs) -> Optional[List[dict]]:
        r"""Получить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Чек-лист
        """

        resp = await self._client.get(f"projects/{self.project_id}/checklists/{checklist_id}", **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    async def update_checklist(
        self,
        checklist_id: str,
        *,
        name: Optional[str] = None,
        begin_date: Union[None, str, datetime.datetime] = None,
        error_details: bool = False,
        **kwargs,
    ) -> Optional[List[dict]]:
        r"""Обновить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param name: Название чек-листа
        :param begin_date: Дата начала применения чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: Чек-лист
        """

        data = {}
        if name:
            data["name"] = name
        if begin_date is not None:
            if isinstance(begin_date, datetime.datetime):
                begin_date = begin_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            data["begin_date"] = begin_date
        resp = await self._client.patch(f"projects/{self.project_id}/checklists/{checklist_id}", json=data, **kwargs)
        return cast(Optional[List[dict]], _parse_result(resp, (200,), True))

    @use_error_details
    async def remove_checklist(self, checklist_id: str, *, error_details: bool = False, **kwargs) -> None:
        r"""Удалить чек-лист

        :param checklist_id: Идентификатор чек-листа
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True Если чек-лист успешно удалён
        """
        resp = await self._client.delete(f"projects/{self.project_id}/checklists/{checklist_id}", **kwargs)
        _parse_result(resp, (204,), True)
