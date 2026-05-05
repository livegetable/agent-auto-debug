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


def test_get_user_not_found():
    """测试不存在的用户ID，应该返回404"""
    response = client.get("/users/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"


def test_get_user_response_schema():
    """测试用户接口返回的字段完整性"""
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "age" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["age"], int)
