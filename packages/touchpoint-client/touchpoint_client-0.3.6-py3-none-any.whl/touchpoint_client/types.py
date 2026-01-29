from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum

__all__ = [
    "ConnectorBase",
    "AsyncConnectorBase",
    "ProjectPermissions",
    "AccountPermissions",
    "ProjectGetDocumentBodyHighlight",
    "ProjectGetDocumentBody",
    "ProjectQueryBody",
    "ProjectSearchBody",
    "ProjectAggregateBody",
]


class ConnectorBase(ABC):
    @abstractmethod
    def head(self, uri: str, **kwargs): ...

    @abstractmethod
    def get(self, uri: str, **kwargs): ...

    @abstractmethod
    def post(self, uri: str, **kwargs): ...

    @abstractmethod
    def put(self, uri: str, **kwargs): ...

    @abstractmethod
    def patch(self, uri: str, **kwargs): ...

    @abstractmethod
    def delete(self, uri: str, **kwargs): ...


class AsyncConnectorBase(ABC):
    @abstractmethod
    async def head(self, uri: str, **kwargs): ...

    @abstractmethod
    async def get(self, uri: str, **kwargs): ...

    @abstractmethod
    async def post(self, uri: str, **kwargs): ...

    @abstractmethod
    async def put(self, uri: str, **kwargs): ...

    @abstractmethod
    async def patch(self, uri: str, **kwargs): ...

    @abstractmethod
    async def delete(self, uri: str, **kwargs): ...


class ProjectPermissions(str, Enum):
    project = "project"
    users = "users"
    dpp = "dpp"
    doc_update = "doc_update"
    doc_delete = "doc_delete"
    external_source = "external_source"
    async_search = "async_search"


class AccountPermissions(str, Enum):
    account = "account"
    alerts = "alerts"
    categories = "categories"
    categories_read = "categories_read"
    charts = "charts"
    charts_read = "charts_read"
    charts_shared = "charts_shared"
    dashboards = "dashboards"
    dashboards_read = "dashboards_read"
    dashboards_shared = "dashboards_shared"
    debug = "debug"
    entity_types = "entity_types"
    label_view = "label_view"
    monitoring = "monitoring"
    push = "push"
    queries = "queries"
    queries_read = "queries_read"
    queries_shared = "queries_shared"
    reports = "reports"
    reports_read = "reports_read"
    reports_shared = "reports_shared"
    roles = "roles"
    root_projects = "root_projects"
    s2t_tuning = "s2t_tuning"
    search = "search"
    statistics = "statistics"
    tapes = "tapes"
    tapes_read = "tapes_read"
    tapes_shared = "tapes_shared"
    users = "users"


@dataclass()
class ProjectGetDocumentBodyHighlight:
    """
    Вспомогательный класс для генерации json документа передаваемого в поле highlight объекта ProjectGetDocumentBody
    :param pre_tags: Открывающиеся теги для подсветки
    :param post_tags: Закрывающиеся теги для подсветки
    :param fetch_fields: Поля документа, которые необходимо подсветить. Можно запросить только такие поля, которые определены в fileds_description и у которых operations.highlight == true
    :param query: Запрос для подсветки (если не указан, то используется основной запрос query). Формат строки определён в документации
        https://www.elastic.co/guide/en/elasticsearch/reference/7.9/query-dsl-query-string-query.html
    :param query_fetch_fields: Поля документа, в которых необходимо искать и подсвечивать найденный текст. Если не задать, то данное поле равно highlight.fetch_fields

    """

    pre_tags: typing.List[str] = field(default_factory=lambda: ["<highlight>"])
    post_tags: typing.List[str] = field(default_factory=lambda: ["</highlight>"])
    fetch_fields: typing.List[str] = field(
        default_factory=lambda: [
            "mono.transcript",
            "client.transcript",
            "operator.transcript",
        ]
    )
    query: str = ""
    query_fetch_fields: typing.List[str] = field(default_factory=lambda: [])

    def dict(self):
        return asdict(self)


@dataclass()
class ProjectGetDocumentBody:
    r"""Вспомогательный класс для генерации json документа передаваемого в запросе при поиске документа в проекте
    по его идентификатору

    :param fetch_fields: Список запрашиваемых полей. Данные поля вернутся в документе в мапе fields. Можно запросить
        только такие поля, которые определены в fileds_description и у которых operations.fetch == true
    :type with_title: List[str]
    :param highlight_info_fields: Массив полей, по которым нужно получить информацию из подсветки (где в тексте
        размечены категории и сущности). Можно запросить только такие поля, которые определены в fileds_description
        и у которых operations.highlight == true
    :param with_title: Нужно ли выводить заголовок документа
    :type with_title: bool
    :param with_snippet: Нужно ли выводить сниппет документа
    :type with_snippet: bool
    :param with_url: Нужно ли выводить ссылку на документ
    :type with_url: bool
    :param with_image: Нужно ли выводить изображение документа
    :type with_image: bool
    :param with_rank: Нужно ли выводить релевантность документов
    :type with_rank: bool
    :param highlight_title: Нужно ли подсвечивать заголовок документа
    :type highlight_title: bool
    :param highlight: Запрос на подсветку
    :type highlight: ProjectGetDocumentBodyHighlight dict Optional

    """

    fetch_fields: typing.List[str] = field(
        default_factory=lambda: [
            "created_date",
            "language",
            "file.properties",
            "categories",
        ]
    )
    highlight_info_fields: typing.Optional[typing.List[str]] = None
    with_title: bool = True
    with_snippet: bool = False
    with_url: bool = True
    with_image: bool = False
    with_rank: bool = False
    highlight_title: bool = False
    highlight: typing.Union[ProjectGetDocumentBodyHighlight, None, dict] = None

    def dict(self):
        return asdict(self)


@dataclass()
class ProjectQueryBody:
    r"""
    :param query: Полнотекстовый поисковой запрос в elasticsearch. Формат строки определён в документации
    :param filters: Массив фильтров для поиска. Все фильтры в массиве объединяются через логическое "И".
    :param error: Искать документы в ошибочных индексах
    :param with_additional_account_filters: Добавить к фильтрам в массиве filters дополнительные фильтры,
        определённые в настройках аккаунта account_settings.authority_filters. Данные фильтры добавляются через "ИЛИ"
    """

    query: str = "*"
    filters: typing.Optional[typing.List[dict]] = None
    error: bool = False
    with_additional_account_filters: bool = True


@dataclass()
class ProjectSearchBody(ProjectGetDocumentBody, ProjectQueryBody):
    r"""
    :param sort: Сортировка результатов. Сортировать можно в порядке возрастания значения asc или в порядке убывания desc.
        Сначала документы сортируются по первой сортировке в массиве, если документы по этому полю равны,
        то они сортируются по второй сортировке и т.д. Если они равны по всем полям для сортировок, то документы
        сортируются лексикографически по идентификаторам документов.
        Можно сортировать только такие поля, которые определены в fields_description и у которых operations.sort == true
    :param offset: Смещение от первого результата. offset + limit не может быть больше 10000
    :param limit: Количество документов в результате. offset + limit не может быть больше 10000
    :param scroll: ttl scroll-а (значение можно записать в секундах или в минутах в формате эластика;
        максимальное значение 5 минут)
    """

    sort: typing.Optional[typing.List[dict]] = None
    offset: int = 0
    limit: int = 1000
    scroll: typing.Optional[str] = None

    def dict(self):
        return asdict(self)


@dataclass()
class ProjectAggregateBody(ProjectQueryBody):
    r"""Агрегации бывают bucket-агрегациями (документы группируются по определённым критериям и для каждого критерия
    возвращается количество документов) и metrics-агрегациями (для поля документа вычисляется определённая метрика
    и возвращается в виде числа). По каждому бакету в bucket-агрегациях можно строить подагрегации.
    https://www.elastic.co/guide/en/elasticsearch/reference/7.9/search-aggregations.html

    :param aggs: Запрос агрегаций (формат как в документации).
    """

    aggs: typing.Optional[typing.List[dict]] = None

    def dict(self):
        return asdict(self)
