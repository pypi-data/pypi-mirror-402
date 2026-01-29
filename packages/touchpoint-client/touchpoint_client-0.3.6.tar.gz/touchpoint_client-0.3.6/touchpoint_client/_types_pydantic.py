from __future__ import annotations
import typing
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProjectPermissionType(str, Enum):
    project = "project"
    users = "users"
    dpp = "dpp"
    doc_update = "doc_update"
    doc_delete = "doc_delete"
    external_source = "external_source"
    async_search = "async_search"


class SortType(str, Enum):
    asc = "asc"
    desc = "desc"


class ProjectSettingsSearchDefaultType(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    # Количество документов по-умолчанию
    limit: int
    # Натсройки подсветки по-умолчанию
    highlight: typing.Any
    # Список запрашиваемых полей
    fetch_fields: list[str]
    # Сортировка результатов.
    # Сначала результат сортируется по первому элементу, если первые элементы совпадают, то по второму и т.д.
    sort: dict[str, SortType]
    # Нужно ли выводить идентификатор документа
    with_id: bool
    # Нужно ли выводить заголовок документа
    with_title: bool
    # Нужно ли выводить сниппет документа
    with_snippet: bool
    # Нужно ли выводить ссылку на документ
    with_url: bool
    # Нужно ли выводить релевантность документов
    with_rank: bool
    # Нужно ли выводить изображение документа
    with_image: bool
    # Нужно ли подсвечивать заголовок документа
    highlight_title: bool


class ProjectSettingsDocumentDefaultType:
    # Список запрашиваемых полей
    fetch_fields: list[str]
    # Нужно ли выводить заголовок документа
    with_title: bool
    # Нужно ли выводить ссылку на документ
    with_url: bool


class ProjectSettingsDefaultsType(BaseModel):
    # Дефолтные данные для поискового запроса
    search: ProjectSettingsSearchDefaultType
    # Дефолтные данные для поискового запроса
    report: ProjectSettingsSearchDefaultType
    # Дефолтные данные для запроса детального просмотра
    document: ProjectSettingsDocumentDefaultType


class ProjectSettingsSelectedType(BaseModel):
    # Список полей для сортировки
    sort_fields: list[str]
    # Список полей для расширенного поиска
    search_fields: list[str]
    # Поле для быстрого фильтра по дате
    date_quick_filter_field: str


class ProjectSettingsSelectedEntitiesType(BaseModel):
    # Топ сущностей каждого типа, которые будут отображаться в статистике
    count: int
    # Типы сущностей, которые будут выводиться в статистике
    entities: list[str]


class ProjectSettingsSystemLatestDocumentDateType(BaseModel):
    # Поле документа, по которому будет определяться дата документа;
    # поле нужно писать в dot-нотации, как оно указано в полях документа
    field: str
    # Порог индикации
    threshold: int


class ProjectSettingsSystemType(BaseModel):
    # Индикация даты последнего зашедшего в проект документа
    latest_document_date: ProjectSettingsSystemLatestDocumentDateType


class ProjectSettingsType(BaseModel):
    # Дефолтные поисковые запросы для страниц поиска, детального просмотра и для отчётов.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    defaults: ProjectSettingsDefaultsType
    # Выбранные поля для сортировки, поиска, быстрого фильтра по дате.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    selected: ProjectSettingsSelectedType
    # Настройка статистики сущностей на странице поиска.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    selected_entities: ProjectSettingsSelectedEntitiesType
    # Настройки отображения. Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов
    # и информации о конкретном проекте данная настройка перетерается.
    view: dict
    # Идентификатор дефолтной роли на проект. Данную настройку можно задать только для рутового проекта.
    # Все дочерние проекты наследуют эту настройку. Если пользователь добавлен в проект с ролью,
    # для которой не определены свои настройки, то будут использоваться настройки дефолтной роли.
    default_role_id: str
    # Системные настройки проекта. Данную настройку можно задать только для рутового проекта
    system: ProjectSettingsSystemType


class ProjectModuleS2tThresholdsType(BaseModel):
    # Порог символьной достоверности фразы (значение от 0 до 1)
    greedy: float = Field(..., ge=0.0, le=1.0, alias="greedy")
    # Порог акустической достоверности слова (значение от 0 до 1)
    am: float = Field(..., ge=0.0, le=1.0, alias="am")


class ProjectModuleS2tIdentificationType(BaseModel):
    # Список фильтров, по которым будут отобраны дикторы для идентификации
    speakers: list[dict]
    # Порог определения дикторов по умолчанию (значение от 0 до 1)
    threshold: float = Field(..., ge=0.0, le=1.0, alias="threshold")
    # Максимальное количество альтернатив
    max_alternatives: int
    # Максимальное количество языков для мультиязычных документов
    languages_limit: int


class ProjectModuleS2tGenderType(BaseModel):
    # Порог определения пола (значение от 0 до 1)
    threshold: float = Field(..., ge=0.0, le=1.0, alias="threshold")


class ProjectModuleS2tChannelRoleType(BaseModel):
    # Роль канала
    role: str
    # Каналы записи (0 - моно, -1 - левый, 1 - правый) TODO: Enum
    channel: int


class ProjectModuleS2tLangIdType(BaseModel):
    # Идентификатор модели определения языков
    model_id: str
    # Порог автоопределения языка по умолчанию (значение от 0 до 1);
    # если в настройках lang_models не указан собственный порог, то берётся этот
    threshold: float = Field(..., ge=0.0, le=1.0, alias="threshold")
    # Понижающий коэффициент для определения мультиязычности (значение от 0 до 1)
    mixed_language_ratio: float = Field(..., ge=0.0, le=1.0, alias="mixed_language_ratio")


class ProjectModuleS2tLangModelType(BaseModel):
    # Идентификатор модели распознавания
    model_id: str
    # Порог определения языка (значение от 0 до 1);
    # если язык имеет вероятность ниже данного порога, то считается что данного языка нет в записи
    threshold: float = Field(..., ge=0.0, le=1.0, alias="threshold")


class ProjectModuleS2tType(BaseModel):
    # Настройки моделей распознавания и порогов для языков; ключом является код языка
    lang_models: dict[str, ProjectModuleS2tLangModelType]
    # Настройки модуля определения языка
    lang_id: ProjectModuleS2tLangIdType
    # Список соответствий между ролями и каналами
    channel_roles: list[ProjectModuleS2tChannelRoleType]
    # Настройки определения пола
    gender: ProjectModuleS2tGenderType
    # Настройки определения дикторов
    identification: ProjectModuleS2tIdentificationType
    async_speaker: dict
    # Идентификатор модели распознавания
    model_id: str
    # Включить диаризацию
    diarization: bool
    # Пороги для модуля распознавания
    thresholds: ProjectModuleS2tThresholdsType
    # Порог перебивания, миллисекунд
    interruption_duration_threshold: int
    # Порог перебивания, слов
    interruption_word_threshold: int
    # Обрабатывать документы с неопределенным языком
    transform_unk_files: bool


class ProjectModuleEntityType(BaseModel):
    # Список полей, на которых необходимо размечать сущности
    fields: list[str]
    # Типы сущностей, которые будут размечаться на проекте
    entity_types: dict[str, dict]
    # Не учитывать регистр при извлечении сущностей
    force_any_case_entities: bool


class ProjectModuleAudioCategorySettingsType(BaseModel):
    # Нужно ли размечать категории в диалогах
    audio: bool
    # Идентификатор активного чек-листа; настройка доступна для обычного (несоставного) проекта
    checklist_id: str
    # Присваивать только одну категорию для документа
    max_extent_counter_filter: bool


class ProjectModuleTextCategorySettingsType(BaseModel):
    # Список полей, на которых необходимо размечать категории
    # Поле документа; поле нужно писать в dot-нотации, как оно указано в полях документа
    text_fields: list[str]


class ProjectModuleSilenceType(BaseModel):
    # Порог длительности паузы (миллисекунды)
    duration_threshold: int
    # Граница конца разговора, доля от длительности
    place_end_threshold: float = Field(..., ge=0.0, le=1.0, alias="place_end_threshold")
    # Граница начала разговора, доля от длительности
    place_begin_threshold: float = Field(..., ge=0.0, le=1.0, alias="place_begin_threshold")


class ProjectModuleSpellCorrectionType(BaseModel):
    # Список идентификаторов орфографических словарей
    dictionaries: list[str]
    # Поля данных, на которых будет происходить разметка;
    # поля нужно писать в dot-нотации, как они указаны в полях документа
    fields_to_process: list[str]
    # Поля данных, из которых будут браться слова-исключения (например, ФИО оператора);
    # поля нужно писать в dot-нотации, как они указаны в полях документа
    expanded_dictionary_paths: list[str]


class ProjectModuleFcrType(BaseModel):
    # Поле даты; поле нужно писать в dot-нотации, как оно указано в полях документа
    date_path: str
    # Поля данных; поля нужно писать в dot-нотации, как они указаны в полях документа
    data_paths: list[str]
    # Максимальный временной интервал между соседними звонками в миллисекундах
    max_window_millis: int


class ProjectModuleSimpleChainType(BaseModel):
    # Поле данных; поле нужно писать в dot-нотации, как оно указано в полях документа
    date_path: str
    # Идентификатор проекта, по которому будет построена упрощённая цепочка (фильтрация по одному полю).
    # Обычно используется составной проект. По-умолчанию используется текущий проект.
    project_id: str


class ProjectModulesType(BaseModel):
    # Настройки s2t; доступны для рутового проекта
    s2t: ProjectModuleS2tType
    # Настройки извлечения сущностей; доступны для рутового проекта
    entity: ProjectModuleEntityType
    # Настройки извлечения категорий; доступны как для рутового так и для обычного (несоставного) проекта
    category: ProjectModuleTextCategorySettingsType | ProjectModuleAudioCategorySettingsType
    # Настройки извлечения пауз; доступны для обычного (несоставного) проекта
    silence: ProjectModuleSilenceType
    # Настройки извлечения орфографических ошибок; доступны для обычного (несоставного) проекта
    spell_correction: ProjectModuleSpellCorrectionType
    # Настройки извлечения цепочек звонков; доступны для обычного (несоставного) проекта
    fcr: ProjectModuleFcrType
    # Настройки упрощенных цепочек звонков; доступны для обычного (несоставного) проекта
    simple_chain: ProjectModuleSimpleChainType


class ProjectDataType(BaseModel):
    # Фильр по проекту (используется только в нерутовых проектах)
    query: str
    # Модули проекта
    modules: ProjectModulesType


class ProjectStatusType(str, Enum):
    stopped = "stopped"
    started = "started"
    stopping = "stopping"
    starting = "starting"
    failed = "failed"


class ProjectStatisticModuleStatsType(BaseModel):
    # Размеры входных очередений
    in_queues_size: list[int]
    # Размеры выходных очередей
    out_queues_size: list[int]
    # Количество документов, ожидающих обработку
    pending: int
    # Количество документов, зашедших в модуль
    received: int
    # Количество обработанных документов
    sent: int


class ProjectStatisticModuleType(BaseModel):
    # Идентификатор модуля
    module_id: str
    # Название модуля
    name: str
    # Статстика по модулю обработки
    stats: ProjectStatisticModuleStatsType


class ProjectStatisticType(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    # Количество документов, ожидающих обработку
    pending_messages: int
    # Количество документов в обработке
    queue_size: int
    # Статус обработки
    status: ProjectStatusType
    # Общее количество обработанных документов
    total_processed_messages: int
    # Статистика обработки по модулям
    modules: list[ProjectStatisticModuleType]


class RoleSettingsType(BaseModel):
    # Дефолтные поисковые запросы для страниц поиска, детального просмотра и для отчётов.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    defaults: ProjectSettingsDefaultsType
    # Выбранные поля для сортировки, поиска, быстрого фильтра по дате.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    selected: ProjectSettingsSelectedType
    # Настройка статистики сущностей на странице поиска.
    # Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов и информации
    # о конкретном проекте данная настройка перетерается.
    selected_entities: ProjectSettingsSelectedEntitiesType
    # Настройки отображения. Данную настройку можно задать только для рутового проекта.
    # Если для проекта существуют настройки на роли, то при получении списка проектов
    # и информации о конкретном проекте данная настройка перетерается.
    view: dict
    # Идентификатор дефолтной роли на проект. Данную настройку можно задать только для рутового проекта.
    # Все дочерние проекты наследуют эту настройку. Если пользователь добавлен в проект с ролью,
    # для которой не определены свои настройки, то будут использоваться настройки дефолтной роли.


class ChecklistStatisticType(BaseModel):
    # Количестов категорий
    categories_count: int


class ProjectType(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    # Идентификатор проекта
    id: str = Field(pattern=r"^\d+$")
    # Идентификатор аккаунта, которому принадлежит проект
    account_id: str
    # Название проекта
    name: str
    # Описание проекта
    description: str
    # Тип проекта
    type: str
    # Дата и время создания проекта
    created_on: datetime
    # Дата и время изменения проекта
    modified_on: datetime
    # Идентификатор рутового проекта (коллекции)
    root_id: str
    # Настройки проекта, относящиеся к фильтрации и обработке
    data: ProjectDataType
    # Настройки проекта, относящиеся к отображению
    project_settings: ProjectSettingsType
    # Является ли проект составным
    is_compound: bool = False
    # Статистика realtime-обработки
    realtime_statistic: ProjectStatisticType
    # Статистика reindex-обработки
    reindex_statistic: ProjectStatisticType
    # Количество документов
    documents_count: int
    # Дата последнего документа
    latest_document_date: datetime
    # Количестов категорий
    categories_count: int
    # Список разрешений на проект (данный список есть только у пользователей с глобальной ролью ACCOUNT_USER)
    permissions: list[ProjectPermissionType]
    # Настройки на роль, который используются в этом проекте
    role_settings: RoleSettingsType
    # Идентификатор роли на проект
    role_id: str = Field(pattern=r"^\d+$")
    # Статистика по активному чек-листу
    checklist: ChecklistStatisticType
