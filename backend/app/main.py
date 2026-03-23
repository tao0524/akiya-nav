"""
地域創生AIプラットフォーム — バックエンドAPI
FastAPI アプリケーションのエントリーポイント
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database import init_db
from app.routers import chat
from app.routers import properties  # Phase 2
from app.routers import diagnosis   # Phase 2後半
from app.routers import migration   # Phase 3
from app.routers import diy         # Phase 3
from app.routers import mentor      # Phase 4

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
- **空き家マップ**: 全国の空き家データを可視化（Phase 2 ✅）
- **活用診断**: 物件の活用可能性をAIが提案（Phase 2後半で実装）
- **メンターマッチング**: 熟練専門家とのマッチング（Phase 4で実装）

### 使い方
1. `POST /api/chat` に質問を送信
2. `GET /api/properties` で物件一覧を取得
    """,
    version="0.4.0",
    lifespan=lifespan
)

# CORS設定
# 環境変数 CORS_ORIGINS にカンマ区切りでURLを指定する
# 例: "https://akiya-frontend.up.railway.app,https://example.com"
# 未設定の場合は開発用に全許可（本番では必ず設定すること）
_cors_origins_env = os.getenv("CORS_ORIGINS", "*")
if _cors_origins_env == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in _cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(chat.router)
app.include_router(properties.router)
app.include_router(diagnosis.router)
app.include_router(migration.router)  # Phase 3
app.include_router(diy.router)        # Phase 3
app.include_router(mentor.router)     # Phase 4


@app.get("/", tags=["health"])
async def root():
    return {
        "message": "地域創生AIプラットフォーム API",
        "version": "0.4.0",
        "docs": "/docs",
        "status": "running",
        "features": {
            "phase1": "RAGチャット ✅",
            "phase2": "空き家マップ ✅",
            "phase3": "移住サポート・DIY ✅",
            "phase4": "メンターマッチング ✅",
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

@app.post("/api/seed", tags=["admin"])
async def seed_all():
    """一時的なデータ投入エンドポイント（使用後は削除すること）"""
    import subprocess
    results = {}
    for script in ["scripts/seed_properties.py", "scripts/seed_regions.py", "scripts/seed_mentors.py"]:
        result = subprocess.run(["python", script], capture_output=True, text=True)
        results[script] = "✅ 成功" if result.returncode == 0 else f"❌ 失敗: {result.stderr}"
    return results