from __future__ import annotations

import json
from typing import BinaryIO, List, Optional, Union

from ._decorators import use_error_details
from .exceptions import Error, RequestError
from .types import AsyncConnectorBase, ConnectorBase

__all__ = ("_Storage", "_StorageAsync")


class _Storage:
    """
    Доступ к файловому хранилищу
    """

    def __init__(self, client: ConnectorBase):
        self._client: ConnectorBase = client

    @use_error_details
    def info(self, error_details: bool = False, **kwargs) -> dict:
        """
        Получить информацию о хранилище файлов

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о хранилище файлов.
        """
        res = self._client.get("storage", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    def upload(
        self,
        data: Union[bytes, BinaryIO],
        name: str,
        parameters: Optional[dict] = None,
        tags: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить файл в хранилище

        :param data: Содержимое загружаемого файла.
        :param name: Название файла.
        :param parameters: JSON с метаданными файла.
        :param tags: Тэги, которые будут добавлены в файл. Перечисляются через запятую или передаются в виде списка.
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о загруженном файле.
        """
        if tags:
            kwargs["params"]["tags"] = tags
        parameters = parameters or {}
        res = self._client.post(
            "storage/files",
            files=(
                (
                    "parameters",
                    (
                        None,
                        json.dumps(parameters, ensure_ascii=False),
                        "application/json",
                    ),
                ),
                ("file", (name, data)),
            ),
            **kwargs,
        )
        if res.status_code in (200, 201):
            return res.json()
        raise RequestError(res.status_code, res.text)

    def iterate_files(
        self,
        offset: int = 0,
        limit: int = 1000,
        sort: Union[str, List[str]] = "-created_date",
        **kwargs,
    ):
        """
        Генератор, возвращающий все файлы удовлетворящие заданному запросу

        :param offset: Смещение первого элемента в массиве ответа
        :param limit: Количество элементов в массиве ответа одного запроса
        :param sort: По каким полям сортировать. Поля перечисляются через запятую или передаются в виде списка. Если перед полем присутствует '-', то сортируется по убыванию, иначе по возрастанию. Пример: `-created_date,name`
        :param kwargs: Дополнительные параметры, которые принимает ``_Storage.get_files``.
        :return: Генерирует JSON документы с метаданныами найденных файлов
        """
        files = set()
        while True:
            data = self.get_files(offset, limit, sort=sort, **kwargs)
            if not data or not data.get("data"):
                break
            for file in data["data"]:
                if file["id"] not in files:
                    files.add(file["id"])
                    yield file
            if len(data["data"]) < limit:
                break
            offset += limit

    @use_error_details
    def get_files(
        self,
        offset: int = 0,
        limit: int = 1000,
        *,
        sort: Union[str, List[str]] = "-created_date",
        name: Optional[str] = None,
        size_gte: Optional[int] = None,
        size_lte: Optional[int] = None,
        created_date_gte: Optional[str] = None,
        created_date_lte: Optional[str] = None,
        md5_match: Optional[str] = None,
        tag_like: Optional[str] = None,
        error_details: bool = False,
        **kwargs,
    ):
        """
        Получить список файлов

        :param offset: Смещение первого элемента в массиве ответа
        :param limit: Количество элементов в массиве ответа
        :param sort: По каким полям сортировать. Поля перечисляются через запятую или передаются в виде списка. Если перед полем присутствует '-', то сортируется по убыванию, иначе по возрастанию. Пример: `-created_date,name`
        :param name: Фильтр по началу имени файла
        :param size_gte: Фильтр по размеру файла. Размер файла больше либо равен заданному
        :param size_lte: Фильтр по размеру файла. Размер файла меньше либо равен заданному
        :param created_date_gte: Фильтр по дате добавления файла (дата в формате UTC). Дата добавления больше либо равна заданной
        :param created_date_lte: Фильтр по дате добавления файла (дата в формате UTC). Дата добавления меньше либо равна заданной
        :param md5_match: Фильтр по md5
        :param tag_like: Фильтр по фрагмену тега
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return:
        """
        params = kwargs["params"]
        if name is not None:
            params["name_like"] = name
        if size_gte is not None:
            params["size_gte"] = size_gte
        if size_lte is not None:
            params["size_lte"] = size_lte
        if created_date_gte is not None:
            params["created_date_gte"] = created_date_gte
        if created_date_lte is not None:
            params["created_date_lte"] = created_date_lte
        if md5_match is not None:
            params["md5_match"] = md5_match
        if tag_like is not None:
            params["tag_like"] = tag_like
        if isinstance(sort, list):
            sort = ",".join(sort)
        params["sort"] = sort
        params["offset"] = offset
        params["limit"] = limit
        res = self._client.get("storage/files", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    def exists(self, file_id: str, error_details: bool = False, **kwargs) -> bool:
        """
        Проверяет существует ли файл с указанным идентификатором

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True если файл найден, иначе False
        """
        res = self._client.get(f"storage/files/{file_id}", **kwargs)
        return res.status_code in (200,)

    @use_error_details
    def get_file(self, file_id: str, error_details: bool = False, **kwargs) -> Optional[dict]:
        """
        Получить файл по идентификатору

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: JSON с информацие о найденном файле или None
        """
        res = self._client.get(f"storage/files/{file_id}", **kwargs)
        if res.status_code in (200,):
            return res.json()
        return None

    @use_error_details
    def remove_file(self, file_id: str, error_details: bool = False, **kwargs) -> bool:
        """
        Удалить файл

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True если файл удален, иначе False
        """
        res = self._client.delete(f"storage/files/{file_id}", **kwargs)
        return res.status_code == 204

    @use_error_details
    def update_file(
        self,
        file_id: str,
        properties: Optional[dict] = None,
        tags: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ):
        """
        Обновить метаданные файла

        :param file_id: Идентификатор файла
        :param parameters: JSON с метаданными файла.
        :param tags: Тэги, которые будут добавлены в файл. Перечисляются через запятую или передаются в виде списка.
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о загруженном файле.
        """
        data: dict = {}
        if properties:
            data["properties"] = properties
        if tags is not None:
            if isinstance(tags, str):
                tags = tags.split(",")
            data["tags"] = tags
        if data and file_id:
            res = self._client.patch(f"storage/files/{file_id}", json=data, **kwargs)
            if res.status_code in (200, 201):
                return res.json()
            raise RequestError(res.status_code, res.text)
        if not data:
            raise Error()


class _StorageAsync:
    """
    Доступ к файловому хранилищу
    """

    def __init__(self, client: AsyncConnectorBase):
        self._client: AsyncConnectorBase = client

    @use_error_details
    async def info(self, error_details: bool = False, **kwargs) -> dict:
        """
        Получить информацию о хранилище файлов

        :param error_details: Выводить подробную информацию об ошибке.
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о хранилище файлов.
        """
        res = await self._client.get("storage", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    async def upload(
        self,
        data: Union[bytes, BinaryIO],
        name: str,
        parameters: Optional[dict] = None,
        tags: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Добавить файл в хранилище

        :param data: Содержимое загружаемого файла.
        :param name: Название файла.
        :param parameters: JSON с метаданными файла.
        :param tags: Тэги, которые будут добавлены в файл. Перечисляются через запятую или передаются в виде списка.
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о загруженном файле.
        """
        if tags:
            kwargs["params"]["tags"] = tags
        parameters = parameters or {}
        res = await self._client.post(
            "storage/files",
            files=(
                (
                    "parameters",
                    (
                        None,
                        json.dumps(parameters, ensure_ascii=False),
                        "application/json",
                    ),
                ),
                ("file", (name, data)),
            ),
            **kwargs,
        )
        if res.status_code in (200, 201):
            return res.json()
        raise RequestError(res.status_code, res.text)

    async def iterate_files(
        self,
        offset: int = 0,
        limit: int = 1000,
        sort: Union[str, List[str]] = "-created_date",
        **kwargs,
    ):
        """
        Генератор, возвращающий все файлы удовлетворящие заданному запросу

        :param offset: Смещение первого элемента в массиве ответа
        :param limit: Количество элементов в массиве ответа одного запроса
        :param sort: По каким полям сортировать. Поля перечисляются через запятую или передаются в виде списка. Если перед полем присутствует '-', то сортируется по убыванию, иначе по возрастанию. Пример: `-created_date,name`
        :param kwargs: Дополнительные параметры, которые принимает ``_Storage.get_files``.
        :return: Генерирует JSON документы с метаданныами найденных файлов
        """
        files = set()
        while True:
            data = await self.get_files(offset, limit, sort=sort, **kwargs)
            if not data or not data.get("data"):
                break
            for file in data["data"]:
                if file["id"] not in files:
                    files.add(file["id"])
                    yield file
            if len(data["data"]) < limit:
                break
            offset += limit

    @use_error_details
    async def get_files(
        self,
        offset: int = 0,
        limit: int = 1000,
        *,
        sort: Union[str, List[str]] = "-created_date",
        name: Optional[str] = None,
        size_gte: Optional[int] = None,
        size_lte: Optional[int] = None,
        created_date_gte: Optional[str] = None,
        created_date_lte: Optional[str] = None,
        md5_match: Optional[str] = None,
        tag_like: Optional[str] = None,
        error_details: bool = False,
        **kwargs,
    ) -> dict:
        """
        Получить список файлов

        :param offset: Смещение первого элемента в массиве ответа
        :param limit: Количество элементов в массиве ответа
        :param sort: По каким полям сортировать. Поля перечисляются через запятую или передаются в виде списка. Если перед полем присутствует '-', то сортируется по убыванию, иначе по возрастанию. Пример: `-created_date,name`
        :param name: Фильтр по началу имени файла
        :param size_gte: Фильтр по размеру файла. Размер файла больше либо равен заданному
        :param size_lte: Фильтр по размеру файла. Размер файла меньше либо равен заданному
        :param created_date_gte: Фильтр по дате добавления файла (дата в формате UTC). Дата добавления больше либо равна заданной
        :param created_date_lte: Фильтр по дате добавления файла (дата в формате UTC). Дата добавления меньше либо равна заданной
        :param md5_match: Фильтр по md5
        :param tag_like: Фильтр по фрагмену тега
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return:
        """
        params = kwargs["params"]
        if name is not None:
            params["name_like"] = name
        if size_gte is not None:
            params["size_gte"] = size_gte
        if size_lte is not None:
            params["size_lte"] = size_lte
        if created_date_gte is not None:
            params["created_date_gte"] = created_date_gte
        if created_date_lte is not None:
            params["created_date_lte"] = created_date_lte
        if md5_match is not None:
            params["md5_match"] = md5_match
        if tag_like is not None:
            params["tag_like"] = tag_like
        if isinstance(sort, list):
            sort = ",".join(sort)
        params["sort"] = sort
        params["offset"] = offset
        params["limit"] = limit
        res = await self._client.get("storage/files", **kwargs)
        if res.status_code in (200,):
            return res.json()
        raise RequestError(res.status_code, res.text)

    @use_error_details
    async def exists(self, file_id: str, error_details: bool = False, **kwargs) -> bool:
        """
        Проверяет существует ли файл с указанным идентификатором

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True если файл найден, иначе False
        """
        res = await self._client.get(f"storage/files/{file_id}", **kwargs)
        return res.status_code in (200,)

    @use_error_details
    async def get_file(self, file_id: str, error_details: bool = False, **kwargs) -> Optional[dict]:
        """
        Получить файл по идентификатору

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: JSON с информацие о найденном файле или None
        """
        res = await self._client.get(f"storage/files/{file_id}", **kwargs)
        if res.status_code in (200,):
            return res.json()
        return None

    @use_error_details
    async def remove_file(self, file_id: str, error_details: bool = False, **kwargs) -> bool:
        """
        Удалить файл

        :param file_id: Идентификатор файла
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.get``.
        :return: True если файл удален, иначе False
        """
        res = await self._client.delete(f"storage/files/{file_id}", **kwargs)
        return res.status_code == 204

    @use_error_details
    async def update_file(
        self,
        file_id: str,
        properties: Optional[dict] = None,
        tags: Union[List[str], str, None] = None,
        error_details: bool = False,
        **kwargs,
    ):
        """
        Обновить метаданные файла

        :param file_id: Идентификатор файла
        :param parameters: JSON с метаданными файла.
        :param tags: Тэги, которые будут добавлены в файл. Перечисляются через запятую или передаются в виде списка.
        :param error_details: Выводить подробную информацию об ошибке
        :param kwargs: Дополнительные параметры, которые принимает ``requests.post``.
        :raises touchpoint_client.exceptions.RequestError: Если REST возвращает код ответа отличный от 200, 201.
        :return: JSON содержащий информацию о загруженном файле.
        """
        data: dict = {}
        if properties:
            data["properties"] = properties
        if tags is not None:
            if isinstance(tags, str):
                tags = tags.split(",")
            data["tags"] = tags
        if data and file_id:
            res = await self._client.patch(f"storage/files/{file_id}", json=data, **kwargs)
            if res.status_code in (200, 201):
                return res.json()
            raise RequestError(res.status_code, res.text)
        if not data:
            raise Error()
