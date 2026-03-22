from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from app.database import Base


class Document(Base):
    """
    RAGに使用する文書チャンクを格納するテーブル。
    各チャンクにはベクトル埋め込みとドメインタグが付与される。
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # 文書の内容
    content = Column(Text, nullable=False)

    # ベクトル埋め込み（text-embedding-3-smallは1536次元）
    embedding = Column(Vector(1536))

    # メタデータ
    domain = Column(String(50), index=True)     # 例: "law_akiya", "subsidy_national"
    source = Column(String(200))                # 例: "空き家対策特別措置法.pdf"
    source_page = Column(Integer, default=0)    # 元文書のページ番号

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Document id={self.id} domain={self.domain} source={self.source}>"


class ChatHistory(Base):
    """
    ユーザーのチャット履歴を保存するテーブル（将来の拡張用）。
    """
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    role = Column(String(20))       # "user" or "assistant"
    content = Column(Text)
    domain = Column(String(50))     # どの機能で使われたか
    created_at = Column(DateTime, server_default=func.now())


class Property(Base):
    """
    空き家・空き地の物件情報を格納するテーブル。
    Phase 2: 空き家マップ機能で使用。
    """
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    # 基本情報
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 位置情報
    prefecture = Column(String(10), index=True)
    city = Column(String(50), index=True)
    address = Column(String(200))
    latitude = Column(String(20))
    longitude = Column(String(20))

    # 物件情報
    property_type = Column(String(20))      # house / land / commercial
    structure = Column(String(20))          # 木造 / RC / 鉄骨
    area_m2 = Column(String(10))            # 建物面積（㎡）
    land_area_m2 = Column(String(10))       # 土地面積（㎡）
    built_year = Column(Integer)

    # 取引条件
    price = Column(Integer, default=0)      # 価格（万円）
    price_type = Column(String(20), default="sale")  # sale / rent / free / negotiable
    rent = Column(Integer, default=0)       # 賃料（万円/月）

    # ステータス
    status = Column(String(20), default="available", index=True)
    # available / negotiating / contracted

    # 活用ポテンシャル
    potential_cafe = Column(String(10))     # high / medium / low
    potential_lodging = Column(String(10))
    potential_office = Column(String(10))
    potential_farm = Column(String(10))

    # ソース情報
    source = Column(String(50), default="sample")  # sample / mlit / local_bank

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Property id={self.id} title={self.title} city={self.city}>"
