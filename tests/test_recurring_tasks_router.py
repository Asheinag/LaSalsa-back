import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.crud.recurring_task import process_recurring_tasks
from app.models import RecurringFrequency, RecurringTask, Task

REC_ROUTE = "/recurring-tasks"


class TestRecurringTask:
    @pytest.mark.asyncio
    async def test_create_rec_task(
        self, client: AsyncClient, create_task_factory, create_recurring_task_factory
    ):
        await create_task_factory()
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
            "task_id": 1,
        }
        response = await create_recurring_task_factory(recurring_task_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Recurring Task by Test"
        assert data["description"] == "Created via test"
        assert data["frequency"] == "daily"
        assert data["next_run_at"] is not None
        assert data["last_run_at"] is None
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_daily_rec_task(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "daily"

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # Ожидаем завтра в 09:00 по Екб
        now_local = datetime.now(tz)
        expected = (now_local + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        assert next_run == expected

    @pytest.mark.asyncio
    async def test_create_interval_rec_task(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.INTERVAL,
            "days": [3],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "interval"
        assert data["days"] == [3]

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # Ожидаем через 1 день в 09:00 по Екб
        now_local = datetime.now(tz)
        expected = (now_local + timedelta(days=3)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        assert next_run == expected

    @pytest.mark.asyncio
    async def test_create_weekly_rec_task(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.WEEKLY,
            "days": [0, 4],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "weekly"
        assert data["days"] == [0, 4]

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # день недели должен быть из списка [0, 4]
        assert next_run.weekday() in [0, 4]

        # и это должно быть в будущем
        assert next_run > datetime.now(tz)

        # и время должно быть 09:00
        assert next_run.hour == 9
        assert next_run.minute == 0

    @pytest.mark.asyncio
    async def test_create_monthly_rec_task(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.MONTHLY,
            "days": [1],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "monthly"
        assert data["days"] == [1]

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # день месяца должен быть 1
        assert next_run.day == 1

        # и время должно быть 09:00
        assert next_run.hour == 9
        assert next_run.minute == 0

    @pytest.mark.asyncio
    async def test_create_rec_interval_task_normalize(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.INTERVAL,
            "days": [1],
            "timezone": "Asia/Yekaterinburg",
        }

        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "daily"
        assert data["days"] == []

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # Ожидаем завтра в 09:00 по Екб
        now_local = datetime.now(tz)
        expected = (now_local + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        assert next_run == expected

    @pytest.mark.asyncio
    async def test_create_rec_task_weekly_normalize(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.WEEKLY,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "daily"
        assert data["days"] == []

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # Ожидаем завтра в 09:00 по Екб
        now_local = datetime.now(tz)
        expected = (now_local + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        assert next_run == expected

    @pytest.mark.asyncio
    async def test_create_monthly_rec_task_normalize(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.MONTHLY,
            "days": [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
            ],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "daily"
        assert data["days"] == []

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # Ожидаем завтра в 09:00 по Екб
        now_local = datetime.now(tz)
        expected = (now_local + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        assert next_run == expected

    @pytest.mark.asyncio
    async def test_create_monthly_rec_task_with_last_day(
        self, client: AsyncClient, create_recurring_task_factory
    ):
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.MONTHLY,
            "days": [31],
            "timezone": "Asia/Yekaterinburg",
        }
        response = await create_recurring_task_factory(recurring_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["frequency"] == "monthly"

        # Проверяем next_run_at
        tz = ZoneInfo("Asia/Yekaterinburg")
        next_run = datetime.fromisoformat(data["next_run_at"]).astimezone(tz)

        # время должно быть 09:00
        assert next_run.hour == 9
        assert next_run.minute == 0

        # дата в будущем
        assert next_run > datetime.now(tz)
        max_day = calendar.monthrange(next_run.year, next_run.month)[1]
        expected_day = min(31, max_day)
        assert next_run.day == expected_day

    @pytest.mark.asyncio
    async def test_get_rec_tasks(
        self, client: AsyncClient, create_task_factory, create_recurring_task_factory
    ):
        task1 = {
            "name": "Test Task 1",
            "description": "Created via test",
        }
        task2 = {
            "name": "Test Task 2",
            "description": "Created via test",
        }
        await create_task_factory(task1)
        await create_task_factory(task2)
        recurring_task_data1 = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
            "task_id": 1,
        }
        recurring_task_data2 = {
            "name": "Test Recurring Task 2 by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
            "task_id": 2,
        }
        await create_recurring_task_factory(recurring_task_data1)
        await create_recurring_task_factory(recurring_task_data2)
        response = await client.get("/recurring-tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_rec_task(
        self, client: AsyncClient, create_task_factory, create_recurring_task_factory
    ):
        task1 = {
            "name": "Test Task 1",
            "description": "Created via test",
        }
        task2 = {
            "name": "Test Task 2",
            "description": "Created via test",
        }
        await create_task_factory(task1)

        await create_task_factory(task2)

        recurring_task_data1 = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
            "task_id": 1,
        }
        recurring_task_data2 = {
            "name": "Test Recurring Task 2 by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
            "task_id": 2,
        }
        await create_recurring_task_factory(recurring_task_data1)
        await create_recurring_task_factory(recurring_task_data2)

        response = await client.get(f"{REC_ROUTE}/1")
        print(response)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Recurring Task by Test"
        assert data["description"] == "Created via test"

    @pytest.mark.asyncio
    async def test_get_rec_task_not_found(self, client: AsyncClient):
        response = await client.get(f"{REC_ROUTE}/1")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_rec_task(
        self, client: AsyncClient, create_recurring_task_factory, create_task_factory
    ):
        task_data = {
            "name": "Test Task",
            "description": "Created via test",
        }
        await create_task_factory(task_data)
        recurring_task_data = {
            "name": "Test Recurring Task by Test",
            "description": "Created via test",
            "frequency": RecurringFrequency.DAILY,
            "days": [],
            "timezone": "UTC",
        }
        response = await create_recurring_task_factory(recurring_task_data)

        data = response.json()
        assert data["name"] == "Test Recurring Task by Test"
        assert data["description"] == "Created via test"
        assert data["frequency"] == "daily"
        assert data["days"] == []
        assert data["timezone"] == "UTC"

        await client.patch(
            f"{REC_ROUTE}/1", json={"name": "Test Recurring Task by Test 2"}
        )
        response = await client.get(f"{REC_ROUTE}/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Recurring Task by Test 2"
        assert data["description"] == "Created via test"
        assert data["frequency"] == "daily"
        assert data["days"] == []
        assert data["timezone"] == "UTC"

    @pytest.mark.asyncio
    async def test_delete_rec_task(
        self, client: AsyncClient, create_recurring_task_factory, create_task_factory
    ):
        await create_task_factory()

        response = await create_recurring_task_factory()
        data = response.json()
        print(data)

        assert data["name"] == "Test Recurring Task"
        await client.delete(f"{REC_ROUTE}/1")

        response = await client.get(f"{REC_ROUTE}/1")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_recurring_tasks_creates_task(
        self, client: AsyncClient, db_session, mock_celery_session
    ):
        # 1. Создать шаблон через API
        response = await client.post(
            "/recurring-tasks/",
            json={
                "name": "Авто задача",
                "frequency": "daily",
                "days": [],
                "timezone": "UTC",
            },
        )
        assert response.status_code == 201
        template_id = response.json()["id"]

        # 2. Двигаем next_run_at в прошлое напрямую в БД
        from datetime import UTC, timedelta

        template = db_session.scalar(
            select(RecurringTask).where(RecurringTask.id == template_id)
        )
        template.next_run_at = datetime.now(UTC) - timedelta(minutes=1)
        db_session.commit()

        # 3. Запускаем таску синхронно (celery_eager включён через autouse)
        process_recurring_tasks()

        # 4. Проверяем что задача создалась
        tasks = (
            db_session.query(Task).filter(Task.recurring_task_id == template_id).all()
        )
        assert len(tasks) == 1
        assert tasks[0].name == "Авто задача"
        assert tasks[0].recurring_task_id == template_id

        # 5. Проверяем что next_run_at пересчитался вперёд
        updated_template = db_session.scalar(
            select(RecurringTask).where(RecurringTask.id == template_id)
        )
        assert updated_template.next_run_at > datetime.now(UTC)
