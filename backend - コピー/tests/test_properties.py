"""
物件APIエンドポイントのテスト
GET /api/properties
GET /api/properties/{id}
GET /api/properties/stats
"""


def test_get_properties_empty(client):
    """物件が0件のとき空リストを返すこと"""
    response = client.get("/api/properties")
    assert response.status_code == 200
    assert response.json() == []


def test_get_properties(client, sample_property):
    """物件が1件あるとき正しく返すこと"""
    response = client.get("/api/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "テスト古民家"
    assert data[0]["prefecture"] == "長野県"
    assert data[0]["city"] == "松本市"


def test_get_property_detail(client, sample_property):
    """物件詳細が正しく返ること"""
    response = client.get(f"/api/properties/{sample_property.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "テスト古民家"
    assert data["structure"] == "木造"
    assert data["built_year"] == 1970
    assert data["price"] == 500


def test_get_property_not_found(client):
    """存在しない物件IDで404が返ること"""
    response = client.get("/api/properties/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "物件が見つかりません"


def test_filter_by_prefecture(client, sample_property):
    """都道府県フィルターが正しく動作すること"""
    # 存在する都道府県
    response = client.get("/api/properties", params={"prefecture": "長野県"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 存在しない都道府県
    response = client.get("/api/properties", params={"prefecture": "沖縄県"})
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_filter_by_price_type(client, sample_property):
    """取引種別フィルターが正しく動作すること"""
    response = client.get("/api/properties", params={"price_type": "sale"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/properties", params={"price_type": "free"})
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_filter_by_potential(client, sample_property):
    """活用ポテンシャルフィルターが正しく動作すること"""
    # potential_cafe = "high" なのでヒットする
    response = client.get("/api/properties", params={"potential": "cafe"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    # potential_office = "low" なのでヒットしない
    response = client.get("/api/properties", params={"potential": "office"})
    assert response.status_code == 200
    assert len(response.json()) == 0