import os

import pytest
from starlette.testclient import TestClient

from symbiosis.entrypoint import app

SYMBIOSIS_API_KEY = os.getenv("SYMBIOSIS_API_KEY")


@pytest.mark.asyncio
async def test_visualize():
    with TestClient(app) as client:
        headers = {"x-api-key": SYMBIOSIS_API_KEY}
        response = client.post("/visualize", headers=headers)
        assert response.status_code == 200
