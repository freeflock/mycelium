import os

import pytest
from starlette.testclient import TestClient

from symbiosis.entrypoint import app, NutrientRequest

MYCELIUM_API_KEY = os.getenv("MYCELIUM_API_KEY")


@pytest.mark.asyncio
async def test_provide_nutrient():
    with TestClient(app) as client:
        headers = {"x-api-key": MYCELIUM_API_KEY}
        nutrient_request = NutrientRequest(
            research_topic="How do Mycelial networks use electrical signaling?",
            category="research",
            context="",
            tag="test")
        response = client.post("/provide_nutrient", json=nutrient_request.model_dump(), headers=headers)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_visualize():
    with TestClient(app) as client:
        headers = {"x-api-key": MYCELIUM_API_KEY}
        response = client.post("/visualize", headers=headers)
        assert response.status_code == 200
