# Touchpoint Client

[![PyPI - Version](https://img.shields.io/pypi/v/touchpoint-client.svg)](https://pypi.org/project/touchpoint-client)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/touchpoint-client.svg)](https://pypi.org/project/touchpoint-client)

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install touchpoint-client
```

## Usage
```pycon
>>> from touchpoint_client import *
>>> credentials = dict(
...     api_url = "https://api.v15.touchpoint-analytics.xyz/v1/",
...     auth_url = "https://oauth.v15.touchpoint-analytics.xyz/token/",
...     client_id = "1234567890",
...     username = r"demo@username",
...     password = r"demousernamepassword",
... }
>>> client = TouchpointClient(**credentials)
>>> client.profile.profile()    
{'id': '973495689374985', 'account_id': '354878293746', 'username': 'demo@username'
, 'global_role': 'ACCOUNT_ADMIN', 'created_on': '2022-09-09T09:19:47.208Z', 'active': True
, 'is_confirmed': False, 'two_factor': False, 'modified_on': '2022-09-09T12:50:13.092Z'
, 'personal_settings': {'show_lag': True}, 'projects': [{'id': '702134155655258112', 'name': 'Видео'}
, {'id': '705981455884361728', 'name': 'Видео_РТК'}, {'id': '702134218578206720', 'name': 'Тест видео'}
, {'id': '695777230432772096', 'name': 'Аудио'}, {'id': '695778026528448512', 'name': 'Тест голосовой галереи'}
, {'id': '705981142221725696', 'name': 'video_rtc-cc'}], 'group_projects': []}
>>> projects = client.projects()
>>> fields = client.project('3089479827348976').get_fields()
>>>

```
Загрука в файловое хранилище и добавление файла в коллекцию
```pycon
>>> data = b"some binary data or path to file"
>>> name = "file_name in staorage"
>>> metadata = {"record_start_time": "2023-12-04T13:00:20Z", "operator": "Operator 1"}
>>> tags = "test_call"
>>> file_info = client.storage.upload(data, name, metadata, tags)
>>> client.project('3089479827348976').append_file(file_info["id"], language="ru")
```

Поиск документов в проекте
```pycon
>>> search_query = ProjectSearchBody(query=r'file.properties.operator:"Operator 1"', limit=10)      
>>> search_query.dict()
{'query': 'file.properties.operator:"Operator 1"', 'filters': None, 'error': False, 'with_additional_account_filters': True
, 'fetch_fields': ['created_date', 'language', 'file.properties', 'categories'], 'highlight_info_fields': None
, 'with_title': True, 'with_snippet': False, 'with_url': True, 'with_image': False, 'with_rank': False
, 'highlight_title': False, 'highlight': None, 'sort': None, 'offset': 0, 'limit': 10, 'scroll': None}
>>> first_10_results = client.project('3089479827348976').search(search_query)
>>> all_results = list(client.project('3089479827348976').iterate_search(search_query))
```

## License

`touchpoint-client` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

