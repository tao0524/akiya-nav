"""
地域創生AIプラットフォーム — バックエンドAPI
FastAPI アプリケーションのエントリーポイント
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routers import chat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時・終了時の処理"""
    print("🚀 サーバー起動中...")
    init_db()
    print("✅ 起動完了")
    yield
    print("👋 サーバー終了")


app = FastAPI(
    title=settings.app_name,
    description="""
## 地域創生AIプラットフォーム API

空き家問題・移住支援・地域産業創出を、RAG技術でサポートするAPIです。

### 主な機能
- **RAGチャット**: 法律・補助金・事例をAIが回答
- **空き家マップ**: 全国の空き家データを可視化（Phase 2で実装）
- **活用診断**: 物件の活用可能性をAIが提案（Phase 2で実装）
- **メンターマッチング**: 熟練専門家とのマッチング（Phase 4で実装）

### 使い方
1. `POST /api/chat` に質問を送信
2. ドメインを指定するとより精度の高い回答が得られます
    """,
    version="0.1.0",
    lifespan=lifespan
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(chat.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "message": "地域創生AIプラットフォーム API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
