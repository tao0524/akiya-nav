"""
テスト共通設定・fixture
SQLiteインメモリDBを使用し、PostgreSQL・pgvectorなしでテストを実行できるようにする。
"""

import pytest
import sys
from unittest.mock import MagicMock
from sqlalchemy import create_engine, Text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# ===== pgvectorをモックに差し替え（importより前に実行する必要がある） =====
mock_vector = MagicMock(return_value=Text())
mock_pgvector = MagicMock()
mock_pgvector.sqlalchemy.Vector = mock_vector
sys.modules["pgvector"] = mock_pgvector
sys.modules["pgvector.sqlalchemy"] = mock_pgvector.sqlalchemy

# ===== アプリのimport（pgvectorモック後でないとエラーになる） =====
from app.database import Base, get_db
from app.main import app
from app.models import Property


# ===== テスト用SQLiteエンジン =====
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """本番DBの代わりにSQLiteを使うDependency Override"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """セッション開始時にテーブルを作成し、終了時に削除する"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """各テスト用のDBセッション（テスト後にロールバック）"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """テスト用FastAPIクライアント（DBをSQLiteにオーバーライド）"""
    def _override():
        yield db
    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_property(db):
    """テスト用の物件データを1件作成し、テスト後に削除する"""
    prop = Property(
        title="テスト古民家",
        description="テスト用の物件です",
        prefecture="長野県",
        city="松本市",
        address="松本市test1-1",
        latitude="36.2381",
        longitude="137.9719",
        property_type="house",
        structure="木造",
        area_m2="120",
        land_area_m2="300",
        built_year=1970,
        price=500,
        price_type="sale",
        rent=0,
        status="available",
        potential_cafe="high",
        potential_lodging="medium",
        potential_office="low",
        potential_farm="high",
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    yield prop
    db.delete(prop)
    db.commit()