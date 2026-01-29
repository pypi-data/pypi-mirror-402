# Changelog


## 0.3.2 (01 октября 2024)
### Добавлено
- Передача `access_token` и `token_type` в конструктор клиентов
- class `TouchpointClientTokenAuth` 

## 0.3.1 (28 августа 2024)
### Исправлено
- `storage.get_files` возвращает `dict` вместо `list`
- типы в некоторых методах


## 0.3.0 (27 августа 2024)
### Изменено
- Переход на использование библиотеки `HTTPX`

### Добавлено
- Асинхронный клиент `TouchpointClientAsync`
- Метод удалление документа из проекта remove_document


## 0.2.1 (1 августа 2024)
### Изменено
- Название класса TouchPointClient изменено на TouchpointClient
- Проверка типов с помощью mypy

### Добавлено
- Поддержка `client_secret` при авторизации в Touchpoint
- Тесты `TouchpointClient.profile`

## 0.1.1 (31 июля 2024)
### Добавлено
- Поддержка `client_secret` при авторизации в Touchpoint
- Тесты `TouchpointClient.profile`

## 0.0.1 (25 июля 2024)
- Первая версия
