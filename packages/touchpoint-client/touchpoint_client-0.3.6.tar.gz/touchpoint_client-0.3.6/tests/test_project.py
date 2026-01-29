import pytest

pytest_plugins = ("pytest_asyncio",)

projects = [("705981142221725696",), ("705981455884361728",)]


# @pytest.mark.asyncio(loop_scope='session')
def test_projects(default_client):
    projects = default_client.projects()
    assert isinstance(projects, list)
    assert projects
    keys = ["id", "account_id", "name", "type", "project_settings"]
    for k in keys:
        for project in projects:
            assert k in project, f"{k} not in project"


@pytest.mark.asyncio(loop_scope="session")
async def test_projects_async(default_client_async):
    projects = await default_client_async.projects()
    assert isinstance(projects, list)
    assert projects
    keys = ["id", "account_id", "name", "type", "project_settings"]
    for k in keys:
        for project in projects:
            assert k in project, f"{k} not in project"


# @pytest.mark.parametrize("project", )
def test_project(default_client):
    profile = default_client.profile.profile()
    keys = [
        "id",
        "account_id",
        "username",
        "global_role",
        "created_on",
        "active",
        "is_confirmed",
        "two_factor",
        "modified_on",
        "personal_settings",
        "projects",
        "group_projects",
    ]
    for k in keys:
        assert k in profile, f"{k} not in profile"


@pytest.mark.asyncio(loop_scope="session")
async def test_project_async(default_client_async):
    profile = await default_client_async.profile.profile()
    keys = [
        "id",
        "account_id",
        "username",
        "global_role",
        "created_on",
        "active",
        "is_confirmed",
        "two_factor",
        "modified_on",
        "personal_settings",
        "projects",
        "group_projects",
    ]
    for k in keys:
        assert k in profile, f"{k} not in profile"


def test_account(default_client):
    account = default_client.profile.account()
    keys = [
        "id",
        "account_settings",
        "global_account",
        "created_on",
        "modified_on",
        "active",
        "name",
        "type",
        "limits",
    ]
    for k in keys:
        assert k in account, f"{k} not in account"


@pytest.mark.asyncio(loop_scope="session")
async def test_account_async(default_client_async):
    account = await default_client_async.profile.account()
    keys = [
        "id",
        "account_settings",
        "global_account",
        "created_on",
        "modified_on",
        "active",
        "name",
        "type",
        "limits",
    ]
    for k in keys:
        assert k in account, f"{k} not in account"


def test_delete_file(default_client):
    account = default_client.project("809272595567353856").remove_document("adbbe82a-abaf-4729-9d25-a832b3293272")
    assert account


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_file_async(default_client_async):
    account = await default_client_async.project("809272595567353856").remove_document(
        "f0029907-c10a-49b5-916f-801c8e33b1e6"
    )
    assert account
