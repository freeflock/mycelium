import os

import requests

BASE_URL = "http://0.0.0.0:33933"
SYMBIOSIS_API_KEY = os.getenv("SYMBIOSIS_API_KEY")


def test_no_api_key():
    response = requests.post(f"{BASE_URL}/provide_nutrient", json={})
    assert response.status_code == 403


def test_wrong_api_key():
    headers = {"x-api-key": "nonsense"}
    response = requests.post(f"{BASE_URL}/provide_nutrient", headers=headers, json={})
    assert response.status_code == 403


def test_provide_nutrient():
    headers = {"x-api-key": SYMBIOSIS_API_KEY}
    payload = {
        "research_topic": "Mycelium sensitivity to light",
        "category": "research",
        "context": ""
    }
    response = requests.post(f"{BASE_URL}/provide_nutrient", headers=headers, json=payload)
    assert response.status_code == 200


def test_clear():
    headers = {"x-api-key": SYMBIOSIS_API_KEY}
    response = requests.post(f"{BASE_URL}/clear", headers=headers)
    assert response.status_code == 200


def test_fruit():
    headers = {"x-api-key": SYMBIOSIS_API_KEY}
    response = requests.post(f"{BASE_URL}/fruit", headers=headers)
    assert response.status_code == 200
    collation = response.json().get("collation")
    print(collation)
