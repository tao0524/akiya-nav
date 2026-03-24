"""
活用可能性診断APIエンドポイント
POST /api/diagnosis/{property_id} : 物件の活用可能性をAIが診断
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from app.database import get_db
from app.models import Property
from app.config import get_settings

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])
settings = get_settings()


# ===== スキーマ =====

class PotentialScore(BaseModel):
    level: str          # high / medium / low
    reason: str         # AIによる理由説明
    tips: str           # 具体的なアドバイス


class DiagnosisResult(BaseModel):
    property_id: int
    property_title: str
    summary: str                        # 総合コメント
    cafe: PotentialScore
    lodging: PotentialScore
    office: PotentialScore
    farm: PotentialScore
    subsidies: list[str]                # 活用できる補助金・支援制度
    next_steps: list[str]               # 次にすべきアクション


# ===== システムプロンプト =====

DIAGNOSIS_SYSTEM_PROMPT = """あなたは空き家・古民家の活用コンサルタントAIです。
物件情報をもとに、以下の4つの活用用途それぞれについて診断し、
必ずJSON形式のみで回答してください。前置きや説明文は不要です。

回答フォーマット（JSONのみ）:
{
  "summary": "物件全体の総合コメント（2〜3文）",
  "cafe": {
    "level": "high/medium/low のいずれか",
    "reason": "この評価の理由（1〜2文）",
    "tips": "具体的な活用アドバイス（1〜2文）"
  },
  "lodging": {
    "level": "high/medium/low のいずれか",
    "reason": "この評価の理由（1〜2文）",
    "tips": "具体的な活用アドバイス（1〜2文）"
  },
  "office": {
    "level": "high/medium/low のいずれか",
    "reason": "この評価の理由（1〜2文）",
    "tips": "具体的な活用アドバイス（1〜2文）"
  },
  "farm": {
    "level": "high/medium/low のいずれか",
    "reason": "この評価の理由（1〜2文）",
    "tips": "具体的な活用アドバイス（1〜2文）"
  },
  "subsidies": ["活用できる補助金・支援制度を最大3つ"],
  "next_steps": ["次にすべき具体的なアクションを最大3つ"]
}

評価基準:
- high: 強くおすすめ。収益化・活用の可能性が高い
- medium: 条件次第で可能。工夫や投資が必要
- low: 課題が多い。他の用途を優先すべき

地域性（都市部・観光地・農村・山間部など）、建物の特徴、面積、
築年数を総合的に考慮して現実的な診断をしてください。"""


def build_property_prompt(prop: Property) -> str:
    price_info = {
        "free": "無償譲渡",
        "sale": f"売却価格 {prop.price}万円",
        "rent": f"賃料 {prop.rent}万円/月",
        "negotiable": "価格応相談",
    }.get(prop.price_type, "不明")

    return f"""以下の物件を診断してください。

【物件情報】
名称: {prop.title}
所在地: {prop.prefecture} {prop.city}
住所: {prop.address or '詳細住所不明'}
種別: {prop.property_type}（{prop.structure or '構造不明'}）
建物面積: {prop.area_m2 or '不明'}㎡
土地面積: {prop.land_area_m2 or '不明'}㎡
築年数: {f'{prop.built_year}年築' if prop.built_year else '不明'}
取引条件: {price_info}
物件説明: {prop.description or '説明なし'}"""


# ===== エンドポイント =====

@router.post("/{property_id}", response_model=DiagnosisResult, summary="活用可能性診断")
async def diagnose_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    物件IDを指定してAIによる活用可能性診断を実行する。
    カフェ・宿泊・オフィス・農業の4用途について評価と理由を返す。
    """
    # 物件取得
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="物件が見つかりません")

    # GPT呼び出し
    try:
        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )

        messages = [
            SystemMessage(content=DIAGNOSIS_SYSTEM_PROMPT),
            HumanMessage(content=build_property_prompt(prop))
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        # JSON部分を抽出（```json ... ``` で囲まれている場合も対応）
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI診断結果のパースに失敗しました")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"診断中にエラーが発生しました: {str(e)}")

    return DiagnosisResult(
        property_id=prop.id,
        property_title=prop.title,
        summary=data.get("summary", ""),
        cafe=PotentialScore(**data["cafe"]),
        lodging=PotentialScore(**data["lodging"]),
        office=PotentialScore(**data["office"]),
        farm=PotentialScore(**data["farm"]),
        subsidies=data.get("subsidies", []),
        next_steps=data.get("next_steps", []),
    )
