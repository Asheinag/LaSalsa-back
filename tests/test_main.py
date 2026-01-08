import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_main_answer(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to LaSalsa API!"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
