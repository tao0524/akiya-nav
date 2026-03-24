"""
物件情報APIエンドポイント
GET  /api/properties        : 物件一覧（フィルター対応）
GET  /api/properties/{id}   : 物件詳細
GET  /api/properties/stats  : 都道府県別統計
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.database import get_db
from app.models import Property

router = APIRouter(prefix="/api/properties", tags=["properties"])


# ===== スキーマ =====

class PropertySummary(BaseModel):
    id: int
    title: str
    prefecture: str
    city: str
    latitude: str
    longitude: str
    property_type: str
    price: int
    price_type: str
    area_m2: Optional[str]
    status: str
    potential_cafe: Optional[str]
    potential_lodging: Optional[str]

    class Config:
        from_attributes = True


class PropertyDetail(PropertySummary):
    description: Optional[str]
    address: Optional[str]
    structure: Optional[str]
    land_area_m2: Optional[str]
    built_year: Optional[int]
    rent: int
    potential_office: Optional[str]
    potential_farm: Optional[str]
    source: str


class PropertyStats(BaseModel):
    prefecture: str
    count: int


# ===== エンドポイント =====

@router.get("", response_model=list[PropertySummary], summary="物件一覧取得")
async def get_properties(
    prefecture: Optional[str] = Query(None, description="都道府県で絞り込み"),
    property_type: Optional[str] = Query(None, description="物件種別: house/land/commercial"),
    price_type: Optional[str] = Query(None, description="取引種別: sale/rent/free/negotiable"),
    max_price: Optional[int] = Query(None, description="上限価格（万円）"),
    status: Optional[str] = Query(None, description="ステータス: available/negotiating"),
    potential: Optional[str] = Query(None, description="活用可能性: cafe/lodging/office/farm"),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    物件一覧を取得。地図表示用にlatitude/longitudeを含む。
    フィルター条件を複数組み合わせ可能。
    """
    query = db.query(Property)

    if prefecture:
        query = query.filter(Property.prefecture == prefecture)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if price_type:
        query = query.filter(Property.price_type == price_type)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if status:
        query = query.filter(Property.status == status)
    if potential == "cafe":
        query = query.filter(Property.potential_cafe == "high")
    elif potential == "lodging":
        query = query.filter(Property.potential_lodging == "high")
    elif potential == "office":
        query = query.filter(Property.potential_office == "high")
    elif potential == "farm":
        query = query.filter(Property.potential_farm == "high")

    return query.limit(limit).all()


@router.get("/stats", response_model=list[PropertyStats], summary="都道府県別物件数")
async def get_stats(db: Session = Depends(get_db)):
    """都道府県ごとの物件数を返す（ヒートマップ用）。"""
    result = db.execute(text("""
        SELECT prefecture, COUNT(*) as count
        FROM properties
        WHERE status = 'available'
        GROUP BY prefecture
        ORDER BY count DESC
    """))
    return [{"prefecture": row.prefecture, "count": row.count} for row in result.fetchall()]


@router.get("/{property_id}", response_model=PropertyDetail, summary="物件詳細取得")
async def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="物件が見つかりません")
    return prop
