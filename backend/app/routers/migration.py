"""
移住サポートAPIエンドポイント
GET  /api/migration/regions  : 都道府県別移住情報一覧
GET  /api/migration/compare  : 地域比較（複数県）
POST /api/migration/chat     : 移住相談RAGチャット
GET  /api/migration/stats    : 移住データ統計
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models import RegionInfo
from app.rag.pipeline import get_rag_pipeline

router = APIRouter(prefix="/api/migration", tags=["migration"])


# ===== スキーマ =====

class MigrationChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="移住に関する質問",
        examples=["長野県に移住したい。補助金はありますか？"]
    )
    prefecture: Optional[str] = Field(
        None,
        description="絞り込む都道府県（任意）",
        examples=["長野県"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "子育て支援が充実している地域を教えてください",
                "prefecture": None
            }
        }


class RegionResponse(BaseModel):
    id: int
    prefecture: str
    city: Optional[str]
    population: Optional[int]
    area_km2: Optional[str]
    climate: Optional[str]
    subsidy_max: int
    subsidy_detail: Optional[str]
    job_support: Optional[str]
    industry: Optional[str]
    attraction: Optional[str]
    challenge: Optional[str]
    score_nature: int
    score_convenience: int
    score_subsidy: int
    score_community: int

    class Config:
        from_attributes = True


# ===== エンドポイント =====

@router.get("/regions", summary="都道府県別移住情報一覧")
async def get_regions(
    prefecture: Optional[str] = Query(None, description="都道府県名で絞り込み"),
    min_subsidy: Optional[int] = Query(None, description="移住支援金の最低額（万円）"),
    db: Session = Depends(get_db)
):
    """
    登録されている都道府県・市区町村の移住情報を返す。

    - **prefecture**: 都道府県名（例: 「長野県」）
    - **min_subsidy**: 移住支援金の最低額（万円）でフィルター
    """
    query = db.query(RegionInfo)

    if prefecture:
        query = query.filter(RegionInfo.prefecture == prefecture)
    if min_subsidy is not None:
        query = query.filter(RegionInfo.subsidy_max >= min_subsidy)

    regions = query.order_by(RegionInfo.prefecture).all()

    return {
        "regions": [RegionResponse.model_validate(r).model_dump() for r in regions],
        "total": len(regions)
    }


@router.get("/compare", summary="地域比較")
async def compare_regions(
    prefectures: str = Query(..., description="カンマ区切りの都道府県名（例: 長野県,岡山県,島根県）"),
    db: Session = Depends(get_db)
):
    """
    複数の都道府県を並べて比較する。

    - **prefectures**: カンマ区切りの都道府県名（最大5件推奨）
    """
    pref_list = [p.strip() for p in prefectures.split(",") if p.strip()]

    if len(pref_list) < 2:
        raise HTTPException(status_code=400, detail="比較には2つ以上の都道府県を指定してください")
    if len(pref_list) > 6:
        raise HTTPException(status_code=400, detail="比較は最大6都道府県まで対応しています")

    regions = db.query(RegionInfo).filter(
        RegionInfo.prefecture.in_(pref_list)
    ).all()

    if not regions:
        raise HTTPException(status_code=404, detail="指定された都道府県のデータが見つかりません")

    # スコア比較用のサマリーを作成
    comparison_data = []
    for r in regions:
        comparison_data.append({
            "prefecture": r.prefecture,
            "city": r.city,
            "population": r.population,
            "subsidy_max": r.subsidy_max,
            "subsidy_detail": r.subsidy_detail,
            "industry": r.industry,
            "attraction": r.attraction,
            "challenge": r.challenge,
            "scores": {
                "nature": r.score_nature,
                "convenience": r.score_convenience,
                "subsidy": r.score_subsidy,
                "community": r.score_community,
                "total": r.score_nature + r.score_convenience + r.score_subsidy + r.score_community
            }
        })

    # 総合スコア順にソート
    comparison_data.sort(key=lambda x: x["scores"]["total"], reverse=True)

    return {
        "comparison": comparison_data,
        "count": len(comparison_data),
        "note": "スコアは1〜5の5段階評価（5が最高）"
    }


@router.post("/chat", summary="移住相談RAGチャット")
async def migration_chat(
    request: MigrationChatRequest,
    db: Session = Depends(get_db)
):
    """
    移住に関する質問をRAGで回答する。

    - **question**: 質問テキスト
    - **prefecture**: 都道府県を指定すると、その地域の情報を優先して回答
    """
    try:
        pipeline = get_rag_pipeline()

        # 都道府県が指定されている場合は質問に追記してコンテキストを強化
        question = request.question
        if request.prefecture:
            question = f"【地域: {request.prefecture}】{request.question}"

        result = pipeline.chat(
            db=db,
            question=question,
            domain="migration"
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "context_used": result["context_used"],
            "prefecture": request.prefecture,
            "domain": "migration"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"回答生成中にエラーが発生しました: {str(e)}"
        )


@router.get("/stats", summary="移住データ統計")
async def get_migration_stats(db: Session = Depends(get_db)):
    """
    登録されている地域情報の統計を返す。
    """
    total = db.query(RegionInfo).count()

    # 補助金上位5地域
    top_subsidy = db.query(RegionInfo).order_by(
        RegionInfo.subsidy_max.desc()
    ).limit(5).all()

    # 都道府県別件数
    result = db.execute(text("""
        SELECT prefecture, COUNT(*) as count, MAX(subsidy_max) as max_subsidy
        FROM region_info
        GROUP BY prefecture
        ORDER BY max_subsidy DESC
    """))
    by_prefecture = [
        {"prefecture": row.prefecture, "count": row.count, "max_subsidy": row.max_subsidy}
        for row in result.fetchall()
    ]

    return {
        "total_regions": total,
        "top_subsidy_regions": [
            {"prefecture": r.prefecture, "city": r.city, "subsidy_max": r.subsidy_max}
            for r in top_subsidy
        ],
        "by_prefecture": by_prefecture
    }
