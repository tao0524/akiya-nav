"""
DIYサポートAPIエンドポイント
POST /api/diy/advice     : DIYアドバイスAI
GET  /api/diy/categories : DIYカテゴリ一覧
POST /api/diy/checklist  : DIYチェックリスト生成
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from app.database import get_db
from app.config import get_settings

router = APIRouter(prefix="/api/diy", tags=["diy"])
settings = get_settings()


# ===== スキーマ =====

class DIYAdviceRequest(BaseModel):
    category: str = Field(
        ...,
        description="DIYカテゴリ",
        examples=["屋根修繕", "壁紙張り替え", "床のリノベーション"]
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="作業の詳細・状況説明",
        examples=["築40年の木造住宅。屋根の一部が雨漏りしている。面積は約20㎡。"]
    )
    budget: Optional[int] = Field(
        None,
        description="予算（万円）",
        examples=[50]
    )
    experience_level: str = Field(
        default="beginner",
        description="経験レベル: beginner / intermediate / advanced",
        examples=["beginner"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "category": "壁紙張り替え",
                "description": "和室6畳の壁紙（クロス）を自分で張り替えたい。古い壁紙を剥がす作業から。",
                "budget": 5,
                "experience_level": "beginner"
            }
        }


class ChecklistRequest(BaseModel):
    category: str = Field(..., description="作業カテゴリ")
    description: str = Field(..., description="作業の詳細")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "フローリング張り替え",
                "description": "リビング12畳のフローリングを無垢材に張り替える"
            }
        }


# ===== システムプロンプト =====

DIY_SYSTEM_PROMPT = """あなたは空き家・古民家のDIY・リノベーション専門アドバイザーAIです。
ユーザーの作業内容を分析し、実践的なアドバイスをJSON形式で返してください。

必ず以下のJSON構造で回答してください（他のテキストは含めないこと）:
{
  "difficulty": "初心者向け / 中級者向け / 上級者向け / 専門業者推奨",
  "difficulty_reason": "難易度の理由",
  "estimated_cost": "費用目安（例: 3〜8万円）",
  "estimated_time": "所要時間（例: 1〜2日）",
  "permit_required": true/false,
  "permit_detail": "建築確認申請が必要な場合の詳細（不要なら空文字）",
  "safety_warnings": ["注意点1", "注意点2"],
  "tools_needed": ["工具1", "工具2"],
  "materials_needed": ["材料1（数量目安）", "材料2（数量目安）"],
  "steps": [
    {"step": 1, "title": "作業名", "detail": "詳細説明", "tips": "コツ・注意点"},
    {"step": 2, "title": "作業名", "detail": "詳細説明", "tips": "コツ・注意点"}
  ],
  "professional_recommendation": "業者に依頼すべき場合の条件・理由",
  "budget_tips": "予算を抑えるためのコツ",
  "subsidy_info": "活用できる補助金・支援制度があれば記載"
}"""

DIY_CHECKLIST_PROMPT = """あなたはDIY作業の安全管理アドバイザーです。
指定された作業の事前チェックリストをJSON形式で返してください。

必ず以下のJSON構造で回答してください:
{
  "pre_work_checks": [
    {"item": "確認項目", "importance": "必須/推奨", "detail": "確認方法・理由"}
  ],
  "safety_equipment": [
    {"item": "安全装備", "required": true/false}
  ],
  "legal_checks": [
    {"item": "法的確認事項", "detail": "確認先・方法"}
  ],
  "completion_checks": [
    {"item": "完了確認項目", "detail": "確認内容"}
  ]
}"""


# ===== カテゴリマスタ =====

DIY_CATEGORIES = [
    {
        "id": "roofing",
        "name": "屋根・雨漏り",
        "description": "屋根修繕、雨漏り補修、防水工事",
        "difficulty": "上級者向け / 専門業者推奨",
        "icon": "🏠"
    },
    {
        "id": "flooring",
        "name": "床・フローリング",
        "description": "フローリング張り替え、畳交換、床下補修",
        "difficulty": "中級者向け",
        "icon": "🪵"
    },
    {
        "id": "wallpaper",
        "name": "壁紙・クロス",
        "description": "クロス張り替え、塗装、漆喰塗り",
        "difficulty": "初心者向け〜中級者向け",
        "icon": "🎨"
    },
    {
        "id": "window_door",
        "name": "窓・ドア・建具",
        "description": "サッシ交換、断熱窓取り付け、引き戸修繕",
        "difficulty": "中級者向け",
        "icon": "🚪"
    },
    {
        "id": "insulation",
        "name": "断熱・気密",
        "description": "断熱材施工、窓の断熱、隙間塞ぎ",
        "difficulty": "中級者向け",
        "icon": "🌡️"
    },
    {
        "id": "plumbing",
        "name": "水回り",
        "description": "キッチン・浴室・トイレのリフォーム、配管補修",
        "difficulty": "上級者向け / 専門業者推奨",
        "icon": "🚿"
    },
    {
        "id": "electrical",
        "name": "電気工事",
        "description": "照明交換、コンセント増設（要資格）",
        "difficulty": "専門業者推奨（第2種電気工事士資格必要）",
        "icon": "⚡"
    },
    {
        "id": "garden",
        "name": "庭・外構",
        "description": "庭の整備、フェンス設置、ウッドデッキ作成",
        "difficulty": "初心者向け〜中級者向け",
        "icon": "🌿"
    },
    {
        "id": "pest_control",
        "name": "害獣・シロアリ対策",
        "description": "シロアリ防除、ネズミ・害虫対策",
        "difficulty": "中級者向け（重症は専門業者推奨）",
        "icon": "🐛"
    },
    {
        "id": "structural",
        "name": "構造補強",
        "description": "耐震補強、基礎補修、柱・梁の修繕",
        "difficulty": "専門業者推奨",
        "icon": "🏗️"
    }
]


# ===== エンドポイント =====

@router.get("/categories", summary="DIYカテゴリ一覧")
async def get_categories():
    """
    対応しているDIYカテゴリの一覧を返す。
    """
    return {
        "categories": DIY_CATEGORIES,
        "total": len(DIY_CATEGORIES),
        "note": "専門業者推奨のカテゴリは、DIYでの作業が法律・安全上の理由で困難な場合があります"
    }


@router.post("/advice", summary="DIYアドバイスAI")
async def get_diy_advice(request: DIYAdviceRequest):
    """
    作業内容を入力するとAIが詳細なアドバイスを返す。

    - **category**: 作業カテゴリ
    - **description**: 作業の詳細・現状説明
    - **budget**: 予算（万円、任意）
    - **experience_level**: 経験レベル（beginner/intermediate/advanced）
    """
    level_map = {
        "beginner": "初心者（DIY経験なし〜1年）",
        "intermediate": "中級者（DIY経験2〜5年、基本工具を使える）",
        "advanced": "上級者（DIY経験5年以上、幅広い工具を使える）"
    }
    level_label = level_map.get(request.experience_level, "初心者")

    budget_text = f"予算: 約{request.budget}万円" if request.budget else "予算: 未定"

    user_message = f"""
以下の作業についてアドバイスをお願いします。

【作業カテゴリ】{request.category}
【状況・詳細】{request.description}
【{budget_text}】
【作業者のレベル】{level_label}

上記の条件を考慮して、具体的かつ実践的なアドバイスをJSON形式で回答してください。
"""

    try:
        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )

        messages = [
            SystemMessage(content=DIY_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        # JSON部分を抽出
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        advice = json.loads(raw)

        return {
            "category": request.category,
            "experience_level": request.experience_level,
            "advice": advice
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AIの回答の解析に失敗しました。もう一度お試しください。"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"アドバイス生成中にエラーが発生しました: {str(e)}"
        )


@router.post("/checklist", summary="DIYチェックリスト生成")
async def generate_checklist(request: ChecklistRequest):
    """
    作業開始前の安全チェックリストをAIが生成する。
    """
    user_message = f"""
以下のDIY作業の事前チェックリストを作成してください。

【作業カテゴリ】{request.category}
【作業内容】{request.description}
"""

    try:
        llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0.2,
            openai_api_key=settings.openai_api_key
        )

        messages = [
            SystemMessage(content=DIY_CHECKLIST_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        checklist = json.loads(raw)

        return {
            "category": request.category,
            "checklist": checklist
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="チェックリストの解析に失敗しました。"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"チェックリスト生成中にエラーが発生しました: {str(e)}"
        )
