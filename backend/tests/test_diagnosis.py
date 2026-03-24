"""
活用可能性診断APIエンドポイントのテスト
POST /api/diagnosis/{property_id}
OpenAI APIはモックを使用し、実際のAPI呼び出しは行わない。
"""

import json
from unittest.mock import MagicMock, patch


# ===== モック用のAI診断レスポンス =====

MOCK_DIAGNOSIS = {
    "summary": "築50年以上の木造古民家で、広い土地と建物を活かした活用が期待できます。",
    "cafe": {
        "level": "high",
        "reason": "古民家の雰囲気を活かしたカフェ運営に適しています。",
        "tips": "古民家リノベーションの補助金を活用することで初期費用を抑えられます。"
    },
    "lodging": {
        "level": "medium",
        "reason": "宿泊施設としての活用も可能ですが、設備投資が必要です。",
        "tips": "農泊や民泊として小規模から始めることをおすすめします。"
    },
    "office": {
        "level": "low",
        "reason": "都市部から離れているためリモートオフィスとしては課題があります。",
        "tips": "サテライトオフィス誘致の補助金制度を確認してみてください。"
    },
    "farm": {
        "level": "high",
        "reason": "広い土地を活かした農業・体験農園に最適です。",
        "tips": "農業次世代人材投資資金などの支援制度が利用できます。"
    },
    "subsidies": [
        "空き家リノベーション補助金",
        "移住・定住促進補助金",
        "農泊推進対策補助金"
    ],
    "next_steps": [
        "市区町村の空き家担当窓口に相談する",
        "建物の耐震診断を依頼する",
        "活用方針を決めて事業計画を作成する"
    ]
}


def make_mock_llm():
    """ChatOpenAIのモックを作成する"""
    mock_response = MagicMock()
    mock_response.content = json.dumps(MOCK_DIAGNOSIS, ensure_ascii=False)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


def test_diagnosis_success(client, sample_property):
    """診断APIが正常に動作すること"""
    with patch("app.routers.diagnosis.ChatOpenAI", return_value=make_mock_llm()):
        response = client.post(f"/api/diagnosis/{sample_property.id}")

    assert response.status_code == 200
    data = response.json()

    # 基本フィールドの確認
    assert data["property_id"] == sample_property.id
    assert data["property_title"] == "テスト古民家"
    assert "summary" in data

    # 4用途スコアの確認
    assert data["cafe"]["level"] == "high"
    assert data["lodging"]["level"] == "medium"
    assert data["office"]["level"] == "low"
    assert data["farm"]["level"] == "high"

    # 各スコアにreason・tipsが含まれること
    for key in ["cafe", "lodging", "office", "farm"]:
        assert "reason" in data[key]
        assert "tips" in data[key]

    # 補助金・次のアクションが含まれること
    assert len(data["subsidies"]) == 3
    assert len(data["next_steps"]) == 3


def test_diagnosis_not_found(client):
    """存在しない物件IDで404が返ること"""
    with patch("app.routers.diagnosis.ChatOpenAI", return_value=make_mock_llm()):
        response = client.post("/api/diagnosis/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "物件が見つかりません"


def test_diagnosis_invalid_json(client, sample_property):
    """AIが不正なJSONを返したとき500が返ること"""
    mock_response = MagicMock()
    mock_response.content = "これはJSONではありません"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response

    with patch("app.routers.diagnosis.ChatOpenAI", return_value=mock_llm):
        response = client.post(f"/api/diagnosis/{sample_property.id}")

    assert response.status_code == 500