import pytest
from httpx import AsyncClient


def create_project_function(client: AsyncClient, project_name: str = "Test Project"):
    return client.post(
        "/projects/",
        json={
            "name": project_name,
        },
    )


def create_task_function(client: AsyncClient, task_data=None):
    if task_data is None:
        task_data = {
            "name": "Test Task",
            "description": "Created via test",
            "status": "TODO",
        }
    return client.post(
        "/tasks/",
        json=task_data,
    )


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    """
    Test successful creation of a new project.
    """
    response = await create_project_function(client)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "INACTIVE"
    assert data["owner_uid"] == "test_user_123"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient):
    """
    Test getting a list of projects.
    """
    # First create a project to ensure there is at least one project to retrieve
    await create_project_function(client)
    # Now get the projects
    response = await client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "name" in data[0]
    assert "status" in data[0]


@pytest.mark.asyncio
async def test_get_projects_empty(client: AsyncClient):
    """Return empty list when no projects exist."""
    response = await client.get("/projects/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient):
    """
    Test getting a project by its ID.
    """
    # First create a project
    response = await create_project_function(client)
    assert response.status_code == 201
    data = response.json()

    project_id = data["id"]
    # Now get the project by ID
    full_response = await client.get(f"/projects/{project_id}")
    assert full_response.status_code == 200
    project_data = full_response.json()
    assert project_data["id"] == project_id
    assert project_data["name"] == "Test Project"
    assert "created_at" in project_data


@pytest.mark.asyncio
async def test_create_project_with_all_fields(client: AsyncClient):
    """
    Test successful creation of a new project with all fields.
    """
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            # Optional field, can be omitted
            "description": "Created via test",
            "type": "LIST",
            "status": "INACTIVE",
            "deadline": "2023-12-31T23:59:59z",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "INACTIVE"
    assert "id" in data

    full_response = await client.get(f"/projects/{data['id']}")
    full_data = full_response.json()
    assert full_data["name"] == "Test Project"
    assert full_data["description"] == "Created via test"
    assert full_data["type"] == "LIST"
    assert full_data["status"] == "INACTIVE"
    assert full_data["deadline"] == "2023-12-31T23:59:59Z"
    assert full_data["owner_uid"] == "test_user_123"


@pytest.mark.asyncio
async def test_unsuccessful_create_project_with_invalid_status(client: AsyncClient):
    """
    Test unsuccessful creation of a project with wrong value of status
    """
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created via test",
            "type": "LIST",
            "status": "INVALID_STATUS",  # Invalid status value
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unsuccessful_create_project_with_invalid_type(client: AsyncClient):
    """
    Test unsuccessful creation of a project with wrong value of type
    """
    response = await client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created via test",
            "type": "INVALID_TYPE",  # Invalid type value
            "status": "INACTIVE",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_tasks_by_project(client: AsyncClient):
    project_response = await create_project_function(client, "Project With Tasks")
    project_id = project_response.json()["id"]
    await create_task_function(
        client,
        {
            "name": "Task 1",
            "description": "Task 1 description",
            "status": "TODO",
            "project_id": project_id,
        },
    )
    await create_task_function(
        client,
        {
            "name": "Task 2",
            "description": "Task 2 description",
            "status": "TODO",
            "project_id": project_id,
        },
    )

    response = await client.get(f"/projects/{project_id}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["project_id"] == project_id for task in data)


@pytest.mark.asyncio
async def test_get_tasks_by_project_not_found(client: AsyncClient):
    project_response = await create_project_function(client, "Empty Project")
    project_id = project_response.json()["id"]
    response = await client.get(f"/projects/{project_id}/tasks")
    assert response.status_code == 200
    assert response.json() == []
