import pytest
import json
from demo_service.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_get_user_existing(client):
    resp = client.get("/api/user", json={"user_id": "1"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Alice"
    assert data["age"] == 30


def test_get_user_missing_key(client):
    resp = client.get("/api/user", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_get_user_nonexistent(client):
    resp = client.get("/api/user", json={"user_id": "999"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data


def test_calculate_normal(client):
    resp = client.post("/api/calculate", json={"a": 10, "b": 2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["result"] == "Result: 5.0"


def test_calculate_zero_division(client):
    resp = client.post("/api/calculate", json={"a": 10, "b": 0})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_calculate_string_input(client):
    resp = client.post("/api/calculate", json={"a": "10", "b": 2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "result" in data


def test_calculate_invalid_input(client):
    resp = client.post("/api/calculate", json={"a": "abc", "b": 2})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_discount_normal(client):
    resp = client.post("/api/discount", json={"price": 100, "discount": 20})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["final_price"] == 80


def test_discount_missing_price(client):
    resp = client.post("/api/discount", json={"discount": 20})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "final_price" in data


def test_greet_with_name(client):
    resp = client.get("/api/greet", json={"name": "world"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["greeting"] == "WORLD"


def test_greet_without_name(client):
    resp = client.get("/api/greet", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "greeting" in data
