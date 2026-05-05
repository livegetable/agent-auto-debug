from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_get_user_1_success():
    """测试正常用户1的请求，应该返回200和正确的用户信息"""
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Alice"
    assert data["age"] == 20


def test_get_user_2_fixed():
    """测试用户2的请求，修复后应该返回200，并为缺失age提供默认值"""
    response = client.get("/users/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["name"] == "Bob"
    assert data["age"] == 0
