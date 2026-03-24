"""
ヘルスチェックエンドポイントのテスト
GET /
GET /health
"""


def test_root(client):
    """ルートエンドポイントが200を返すこと"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health(client):
    """ヘルスチェックエンドポイントが200を返すこと"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"