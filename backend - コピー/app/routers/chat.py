"""
チャットAPIエンドポイント
POST /api/chat  : RAGチャット
GET  /api/chat/domains : 利用可能ドメイン一覧
GET  /api/chat/stats   : DB統計情報
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.rag.pipeline import get_rag_pipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ===== リクエスト / レスポンス スキーマ =====

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="ユーザーの質問テキスト",
        examples=["特定空き家に指定されたらどうなりますか？"]
    )
    domain: Optional[str] = Field(
        None,
        description="検索対象ドメイン。指定しない場合は全ドメインから検索",
        examples=["law_akiya", "subsidy_national", "case_study"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "相続した空き家の固定資産税について教えてください",
                "domain": "law_akiya"
            }
        }


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AIが生成した回答")
    sources: list[str] = Field(default=[], description="参照した文書のソース一覧")
    context_used: int = Field(..., description="検索で取得した文書数")
    domain: Optional[str] = Field(None, description="使用したドメイン")


class DomainInfo(BaseModel):
    id: str
    name: str
    description: str
    document_count: int


# ===== エンドポイント =====

@router.post("", response_model=ChatResponse, summary="RAGチャット")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    質問を受け取り、RAGを使って回答を返す。

    - **question**: ユーザーの質問（1〜1000文字）
    - **domain**: 検索対象ドメイン（省略可）

    ドメイン一覧:
    - `law_akiya`: 空き家関連法律
    - `law_construction`: 建築基準法・許認可
    - `law_agriculture`: 農地法・農業関連
    - `subsidy_national`: 国の補助金・助成金
    - `case_study`: 全国の活用事例
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.chat(
            db=db,
            question=request.question,
            domain=request.domain
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            context_used=result["context_used"],
            domain=request.domain
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"回答生成中にエラーが発生しました: {str(e)}"
        )


@router.get("/domains", response_model=list[DomainInfo], summary="利用可能ドメイン一覧")
async def get_domains(db: Session = Depends(get_db)):
    """
    DBに登録されているドメインとその文書数を返す。
    """
    result = db.execute(text("""
        SELECT domain, COUNT(*) as count
        FROM documents
        GROUP BY domain
        ORDER BY domain
    """))
    rows = result.fetchall()

    domain_meta = {
        "law_akiya":        ("空き家関連法律",      "空き家対策特別措置法・民法・相続法"),
        "law_construction": ("建築・許認可法律",    "建築基準法・消防法・旅館業法"),
        "law_agriculture":  ("農業関連法律",        "農地法・農業経営基盤強化促進法"),
        "subsidy_national": ("国の補助金",          "農水省・林野庁・国交省の助成金"),
        "subsidy_local":    ("自治体の補助金",      "各都道府県・市区町村の移住支援金"),
        "case_study":       ("全国活用事例",        "成功事例・失敗事例・取り組みレポート"),
        "migration":        ("移住情報",            "移住体験談・地域比較データ"),
    }

    return [
        DomainInfo(
            id=row.domain,
            name=domain_meta.get(row.domain, (row.domain, ""))[0],
            description=domain_meta.get(row.domain, ("", row.domain))[1],
            document_count=row.count
        )
        for row in rows
    ]


@router.get("/stats", summary="DB統計情報")
async def get_stats(db: Session = Depends(get_db)):
    """
    登録文書の統計情報を返す（ヘルスチェック用）。
    """
    result = db.execute(text("SELECT COUNT(*) FROM documents"))
    total = result.scalar()

    result2 = db.execute(text("""
        SELECT domain, COUNT(*) as count
        FROM documents
        GROUP BY domain
        ORDER BY count DESC
    """))
    by_domain = {row.domain: row.count for row in result2.fetchall()}

    return {
        "total_documents": total,
        "by_domain": by_domain,
        "status": "ready" if total > 0 else "empty - run ingest.py to add documents"
    }
