import json

import pytest

from touchpoint_client import TouchpointClient, TouchpointClientAsync

with open(".tests/credentials.json", encoding="utf-8", mode="r") as f:
    TOUCHPOINT_CONFIG = json.load(f)


@pytest.fixture(scope="session")
def default_client():
    yield TouchpointClient(**TOUCHPOINT_CONFIG)


@pytest.fixture(scope="session")
def default_client_async():
    yield TouchpointClientAsync(**TOUCHPOINT_CONFIG)
