import pytest
from httpx import AsyncClient

from app.models.pomodoro import Pomodoro


@pytest.mark.asyncio
async def test_create_pomodoro(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка создания сеанса Помодоро через API.
    """
    # Создаем сеанс Помодоро
    response = await create_pomodoro_factory()

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()
    assert data["duration_minutes"] == 25
    assert data["owner_uid"] == "test_user_123"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_pomodoro_with_previous(
    client: AsyncClient, create_pomodoro_factory
):
    """
    Проверка создания сеанса Помодоро с предыдущим сеансом через API.
    """
    # Сначала создаем первый сеанс Помодоро
    first_response = await create_pomodoro_factory()
    print(first_response.json())
    first_pomodoro_id = first_response.json()["id"]
    print(f"First Pomodoro ID: {first_pomodoro_id}")

    # Затем создаем второй сеанс Помодоро, ссылаясь на первый
    second_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Second Pomodoro",
            "duration_minutes": 30,
            "owner_uid": "test_user_123",
            "previous_pomodoro_id": first_pomodoro_id,
        }
    )

    # Проверяем ответ второго сеанса
    assert second_response.status_code == 201
    data = second_response.json()
    assert data["previous_pomodoro_id"] == first_pomodoro_id
    assert data["owner_uid"] == "test_user_123"


@pytest.mark.asyncio
async def test_create_pomodoro_without_note(
    client: AsyncClient, create_pomodoro_factory
):
    """
    Проверка создания сеанса Помодоро без заметки через API.
    """
    # Создаем сеанс Помодоро без заметки
    response = await create_pomodoro_factory(
        pomodoro_data={
            "duration_minutes": 20,
            "owner_uid": "test_user_123",
        }
    )

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()
    assert data["note"] is None
    assert data["duration_minutes"] == 20
    assert data["owner_uid"] == "test_user_123"


@pytest.mark.asyncio
async def test_create_pomodoro_custom_duration(
    client: AsyncClient, create_pomodoro_factory
):
    """
    Проверка создания сеанса Помодоро с пользовательской длительностью через API.
    """
    # Создаем сеанс Помодоро с длительностью 45 минут
    response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Long Pomodoro",
            "duration_minutes": 45,
            "owner_uid": "test_user_123",
        }
    )

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()
    assert data["duration_minutes"] == 45
    assert data["owner_uid"] == "test_user_123"


@pytest.mark.asyncio
async def test_create_pomodoro_without_user_session(
    unauthenticated_client: AsyncClient,
):
    """
    Проверка создания сеанса Помодоро без пользовательской сессии через API.
    """
    # Пытаемся создать сеанс Помодоро без аутентификации
    response = await unauthenticated_client.post(
        "/pomodoros/",
        json={
            "note": "Unauthorized Pomodoro",
            "duration_minutes": 25,
        },
    )

    # Проверяем ответ
    assert response.status_code == 403  # Ожидаем ошибку аутентификации


@pytest.mark.asyncio
async def test_get_pomodoro(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка получения сеанса Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory()
    pomodoro_id = create_response.json()["id"]

    # Получаем сеанс Помодоро
    response = await client.get(f"/pomodoros/{pomodoro_id}")

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pomodoro_id
    assert data["owner_uid"] == "test_user_123"


@pytest.mark.asyncio
async def test_get_pomodoro_tasks(
    client: AsyncClient, create_pomodoro_factory, create_task_factory
):
    """
    Проверка получения задач, связанных с сеансом Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory()
    print(create_response.json())
    pomodoro_id = create_response.json()["id"]
    print(f"Pomodoro ID for tasks: {pomodoro_id}")

    # Затем создаем задачи, связанные с этим сеансом Помодоро
    task1_response = await create_task_factory()
    print(task1_response.json())
    task2_response = await create_task_factory()
    print(task2_response.json())

    task1_id = task1_response.json()["id"]
    task2_id = task2_response.json()["id"]

    # Обновляем задачи, чтобы связать их с сеансом Помодоро
    await client.patch(f"/tasks/{task1_id}", json={"pomodoro_id": pomodoro_id})

    await client.patch(f"/tasks/{task2_id}", json={"pomodoro_id": pomodoro_id})
    # Получаем задачи, связанные с сеансом Помодоро
    response = await client.get(f"/pomodoros/{pomodoro_id}/tasks")
    print(response.json())
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    task_names = [task["name"] for task in data]
    assert task1_response.json()["name"] in task_names
    assert task2_response.json()["name"] in task_names


@pytest.mark.asyncio
async def test_delete_pomodoro(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка удаления сеанса Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory()
    pomodoro_id = create_response.json()["id"]

    # Удаляем сеанс Помодоро
    response = await client.delete(f"/pomodoros/{pomodoro_id}")

    # Проверяем ответ
    assert response.status_code == 204

    # Пытаемся получить удаленный сеанс Помодоро
    get_response = await client.get(f"/pomodoros/{pomodoro_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_update_pomodoro_note(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка обновления заметки сеанса Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Initial Note",
            "duration_minutes": 25,
        }
    )
    pomodoro_id = create_response.json()["id"]
    print(f"Pomodoro ID for update: {pomodoro_id}")

    # Обновляем заметку сеанса Помодоро
    new_note = "Updated Note"
    response = await client.patch(
        f"/pomodoros/{pomodoro_id}",
        json={"note": new_note},
    )

    print(response.json())

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["note"] == new_note

    # Получаем сеанс Помодоро, чтобы проверить обновление
    get_response = await client.get(f"/pomodoros/{pomodoro_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["note"] == new_note


@pytest.mark.asyncio
async def test_update_pomodoro_duration(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка обновления длительности сеанса Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Duration Update Test",
            "duration_minutes": 25,
        }
    )
    pomodoro_id = create_response.json()["id"]
    print(f"Pomodoro ID for duration update: {pomodoro_id}")

    # Обновляем длительность сеанса Помодоро
    new_duration = 40
    response = await client.patch(
        f"/pomodoros/{pomodoro_id}",
        json={"duration_minutes": new_duration},
    )

    print(response.json())

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["duration_minutes"] == new_duration

    # Получаем сеанс Помодоро, чтобы проверить обновление
    get_response = await client.get(f"/pomodoros/{pomodoro_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["duration_minutes"] == new_duration


@pytest.mark.asyncio
async def test_update_pomodoro_note_and_duration(
    client: AsyncClient, create_pomodoro_factory
):
    """
    Проверка обновления заметки и длительности сеанса Помодоро через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Initial Note and Duration",
            "duration_minutes": 25,
        }
    )
    pomodoro_id = create_response.json()["id"]
    print(f"Pomodoro ID for note and duration update: {pomodoro_id}")

    # Обновляем заметку и длительность сеанса Помодоро
    new_note = "Updated Note"
    new_duration = 35
    response = await client.patch(
        f"/pomodoros/{pomodoro_id}",
        json={"note": new_note, "duration_minutes": new_duration},
    )

    print(response.json())

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["note"] == new_note
    assert data["duration_minutes"] == new_duration

    # Получаем сеанс Помодоро, чтобы проверить обновление
    get_response = await client.get(f"/pomodoros/{pomodoro_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["note"] == new_note
    assert get_data["duration_minutes"] == new_duration


@pytest.mark.asyncio
async def test_update_pomodoro_no_fields(client: AsyncClient, create_pomodoro_factory):
    """
    Проверка обновления сеанса Помодоро без указания полей через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "No Update Test",
            "duration_minutes": 25,
        }
    )
    pomodoro_id = create_response.json()["id"]
    original_data = create_response.json()
    print(f"Pomodoro ID for no fields update: {pomodoro_id}")

    # Пытаемся обновить сеанс Помодоро без указания полей
    response = await client.patch(f"/pomodoros/{pomodoro_id}", json={})

    print(response.json())

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data == original_data  # Данные не должны измениться


@pytest.mark.asyncio
async def test_update_pomodoro_invalid_field(
    client: AsyncClient, create_pomodoro_factory
):
    """
    Проверка обновления сеанса Помодоро с недопустимым полем через API.
    """
    # Сначала создаем сеанс Помодоро
    create_response = await create_pomodoro_factory(
        pomodoro_data={
            "note": "Invalid Field Test",
            "duration_minutes": 25,
        }
    )
    pomodoro_id = create_response.json()["id"]
    print(f"Pomodoro ID for invalid field update: {pomodoro_id}")

    # Пытаемся обновить сеанс Помодоро с недопустимым полем
    response = await client.patch(
        f"/pomodoros/{pomodoro_id}",
        json={"invalid_field": "Some Value"},
    )

    print(response.json())

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    # Убедимся, что недопустимое поле не было добавлено
    assert "invalid_field" not in data


@pytest.mark.asyncio
async def test_update_another_users_pomodoro(client: AsyncClient, db_session):
    """
    Проверка обновления сеанса Помодоро другого пользователя через API.
    """
    # Создаем помидорку от имени другого пользователя напрямую в БД
    another_user_pomodoro = Pomodoro(
        note="Other User's Pomodoro", duration_minutes=25, owner_uid="other_user_456"
    )
    db_session.add(another_user_pomodoro)
    db_session.commit()

    pomodoro_id = another_user_pomodoro.id

    # Пытаемся обновить сеанс Помодоро от имени другого пользователя
    response = await client.patch(
        f"/pomodoros/{pomodoro_id}",
        json={"note": "Hacked Note"},
    )

    print(response.json())

    # Проверяем ответ
    assert (
        response.status_code == 404
    )  # Ожидаем, что сеанс не найден для другого пользователя


@pytest.mark.asyncio
async def test_delete_another_users_pomodoro(client: AsyncClient, db_session):
    """
    Проверка удаления сеанса Помодоро другого пользователя через API.
    """
    # Создаем помидорку от имени другого пользователя напрямую в БД
    another_user_pomodoro = Pomodoro(
        note="Other User's Pomodoro to Delete",
        duration_minutes=25,
        owner_uid="other_user_456",
    )
    db_session.add(another_user_pomodoro)
    db_session.commit()

    pomodoro_id = another_user_pomodoro.id

    # Пытаемся удалить сеанс Помодоро от имени другого пользователя
    response = await client.delete(f"/pomodoros/{pomodoro_id}")

    print(response.status_code)

    # Проверяем ответ
    assert (
        response.status_code == 404
    )  # Ожидаем, что сеанс не найден для другого пользователя
