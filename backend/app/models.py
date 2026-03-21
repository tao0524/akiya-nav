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
