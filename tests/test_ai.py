async def test_get_active_review(client, create_task_factory, create_review_factory):
    task = await create_task_factory()
    task_id = task.json()["id"]
    create_review_factory(task_id)  # синхронно, через db_session

    response = await client.get(f"/ai-reviews/tasks/{task_id}/active")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert "comment" in data
