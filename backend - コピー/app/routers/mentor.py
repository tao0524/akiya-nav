"""
メンターマッチングAPIエンドポイント
GET  /api/mentors           : メンター一覧（絞り込み対応）
GET  /api/mentors/{id}      : メンター詳細
POST /api/mentors/match     : AIによるメンターマッチング
POST /api/mentors/request   : 相談リクエスト送信
GET  /api/mentors/stats     : メンター統計
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from app.database import get_db
from app.models import Mentor, ConsultationRequest
from app.config import get_settings

router = APIRouter(prefix="/api/mentors", tags=["mentors"])
settings = get_settings()


# ===== スキーマ =====

class MatchRequest(BaseModel):
    situation: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="あなたの状況・相談したいこと",
        examples=["東京から長野県に移住して農業を始めたい。40代夫婦。予算は500万円。"]
    )
    prefecture: Optional[str] = Field(None, description="希望する移住先の都道府県")
    specialty: Optional[str] = Field(None, description="相談したい専門分野")

    class Config:
        json_schema_extra = {
            "example": {
                "situation": "大阪から島根県に移住してカフェを開きたい。30代単身。古民家を活用したい。",
                "prefecture": "島根県",
                "specialty": "古民家再生"
            }
        }


class ConsultationRequestSchema(BaseModel):
    mentor_id: int
    requester_name: str = Field(..., min_length=1, max_length=50)
    requester_email: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=10, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "mentor_id": 1,
                "requester_name": "山田太郎",
                "requester_email": "yamada@example.com",
                "message": "長野県への移住を検討しています。農業の始め方について相談させてください。"
            }
        }


# ===== マッチングプロンプト =====

MATCH_SYSTEM_PROMPT = """あなたは移住・地域創生のメンターマッチング専門AIです。
ユーザーの状況と、提供されたメンター一覧をもとに、最適なメンターを3名選んで推薦してください。

必ず以下のJSON構造で回答してください（他のテキストは一切含めないこと）:
{
  "recommendations": [
    {
      "mentor_id": メンターのID（整数）,
      "reason": "このメンターを推薦する理由（2〜3文）",
      "match_points": ["マッチポイント1", "マッチポイント2", "マッチポイント3"],
      "first_question": "このメンターへの最初の質問としておすすめの内容"
    }
  ],
  "overall_advice": "ユーザーの状況への全体的なアドバイス（2〜3文）"
}"""


# ===== エンドポイント =====

@router.get("", summary="メンター一覧")
async def get_mentors(
    prefecture: Optional[str] = Query(None, description="都道府県で絞り込み"),
    specialty: Optional[str] = Query(None, description="専門分野で絞り込み（部分一致）"),
    available_only: bool = Query(True, description="受付中のみ表示"),
    db: Session = Depends(get_db)
):
    """
    登録されているメンターの一覧を返す。
    """
    query = db.query(Mentor)

    if prefecture:
        query = query.filter(Mentor.prefecture == prefecture)
    if specialty:
        query = query.filter(Mentor.specialties.contains(specialty))
    if available_only:
        query = query.filter(Mentor.is_available == "true")

    mentors = query.order_by(Mentor.consultation_count.desc()).all()

    return {
        "mentors": [
            {
                "id": m.id,
                "name": m.name,
                "age": m.age,
                "prefecture": m.prefecture,
                "city": m.city,
                "origin": m.origin,
                "specialties": m.specialties.split(",") if m.specialties else [],
                "migration_year": m.migration_year,
                "migration_from": m.migration_from,
                "can_help_with": m.can_help_with,
                "consultation_method": m.consultation_method,
                "rating": m.rating,
                "consultation_count": m.consultation_count,
                "is_available": m.is_available == "true",
                "bio": m.bio,
            }
            for m in mentors
        ],
        "total": len(mentors)
    }


@router.get("/stats", summary="メンター統計")
async def get_mentor_stats(db: Session = Depends(get_db)):
    total = db.query(Mentor).count()
    available = db.query(Mentor).filter(Mentor.is_available == "true").count()

    return {
        "total_mentors": total,
        "available_mentors": available,
    }


@router.get("/{mentor_id}", summary="メンター詳細")
async def get_mentor(mentor_id: int, db: Session = Depends(get_db)):
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="メンターが見つかりません")

    return {
        "id": mentor.id,
        "name": mentor.name,
        "age": mentor.age,
        "gender": mentor.gender,
        "prefecture": mentor.prefecture,
        "city": mentor.city,
        "origin": mentor.origin,
        "specialties": mentor.specialties.split(",") if mentor.specialties else [],
        "migration_year": mentor.migration_year,
        "migration_from": mentor.migration_from,
        "migration_story": mentor.migration_story,
        "can_help_with": mentor.can_help_with,
        "consultation_method": mentor.consultation_method,
        "rating": mentor.rating,
        "consultation_count": mentor.consultation_count,
        "is_available": mentor.is_available == "true",
        "bio": mentor.bio,
    }


@router.post("/match", summary="AIメンターマッチング")
async def match_mentor(request: MatchRequest, db: Session = Depends(get_db)):
    """
    ユーザーの状況をもとにAIが最適なメンターを3名推薦する。
    """
    # メンター一覧を取得
    query = db.query(Mentor).filter(Mentor.is_available == "true")
    if request.prefecture:
        query = query.filter(Mentor.prefecture == request.prefecture)
    if request.specialty:
        query = query.filter(Mentor.specialties.contains(request.specialty))

    mentors = query.all()

    if not mentors:
        # 条件を緩めて再取得
        mentors = db.query(Mentor).filter(Mentor.is_available == "true").all()

    if not mentors:
        raise HTTPException(status_code=404, detail="現在登録されているメンターがいません")

    # メンター情報をテキスト化
    mentor_list_text = ""
    for m in mentors:
        mentor_list_text += f"""
ID: {m.id}
名前: {m.name}（{m.age}歳・{m.origin}出身）
居住地: {m.prefecture} {m.city or ''}
専門: {m.specialties}
移住年: {m.migration_year}年（{m.migration_from}から移住）
対応可能: {m.can_help_with}
相談方法: {m.consultation_method}
---"""

    user_message = f"""
【ユーザーの状況】
{request.situation}
希望移住先: {request.prefecture or '未定'}
相談したい専門分野: {request.specialty or '特になし'}

【登録メンター一覧】
{mentor_list_text}

上記のユーザーの状況に最も合うメンターを3名選んでJSON形式で推薦してください。
"""

    try:
        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )

        messages = [
            SystemMessage(content=MATCH_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        result = json.loads(raw)

        # メンター詳細情報を付加
        mentor_map = {m.id: m for m in mentors}
        for rec in result.get("recommendations", []):
            mid = rec.get("mentor_id")
            if mid and mid in mentor_map:
                m = mentor_map[mid]
                rec["mentor"] = {
                    "id": m.id,
                    "name": m.name,
                    "age": m.age,
                    "prefecture": m.prefecture,
                    "city": m.city,
                    "specialties": m.specialties.split(",") if m.specialties else [],
                    "migration_from": m.migration_from,
                    "migration_year": m.migration_year,
                    "consultation_method": m.consultation_method,
                    "rating": m.rating,
                    "consultation_count": m.consultation_count,
                    "bio": m.bio,
                }

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="マッチング結果の解析に失敗しました。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"マッチング中にエラーが発生しました: {str(e)}")


@router.post("/request", summary="相談リクエスト送信")
async def send_consultation_request(
    request: ConsultationRequestSchema,
    db: Session = Depends(get_db)
):
    """
    メンターへの相談リクエストを送信する。
    """
    mentor = db.query(Mentor).filter(Mentor.id == request.mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="メンターが見つかりません")
    if mentor.is_available != "true":
        raise HTTPException(status_code=400, detail="このメンターは現在受付停止中です")

    consultation = ConsultationRequest(
        mentor_id=request.mentor_id,
        requester_name=request.requester_name,
        requester_email=request.requester_email,
        message=request.message,
        status="pending"
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return {
        "message": "相談リクエストを送信しました",
        "consultation_id": consultation.id,
        "mentor_name": mentor.name,
        "status": "pending",
        "note": "メンターからの返信をお待ちください（通常2〜3営業日以内）"
    }
