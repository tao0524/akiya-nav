from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPIのDependency Injection用"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    起動時にDBを初期化する。
    pgvector拡張を有効化し、必要なテーブルを作成する。
    """
    with engine.connect() as conn:
        # pgvector拡張を有効化（初回のみ実行される）
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # 全モデルのテーブルを作成
    Base.metadata.create_all(bind=engine)
    print("✅ データベース初期化完了")
