# 🏡 空き家ナビ — 地域創生AIプラットフォーム

> 「AIが情報をつなぎ、人が知恵をつなぐ」

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-purple)](https://langchain.com)
[![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-blue?logo=postgresql)](https://github.com/pgvector/pgvector)

---

## 概要

日本全国で約900万戸に達した空き家問題を「入口」として、移住・地域産業創出・DIY・メンターマッチングまでを一気通貫でサポートする**地域創生AIナビゲーター**です。

RAG（Retrieval-Augmented Generation）技術を核に、法律文書・補助金情報・成功事例を検索して根拠付きで回答します。

---

## システム構成

```
akiya-nav/
├── backend/               # FastAPI + RAGエンジン
│   ├── app/
│   │   ├── main.py        # FastAPIアプリ
│   │   ├── config.py      # 設定管理（pydantic-settings）
│   │   ├── database.py    # PostgreSQL + pgvector接続
│   │   ├── models.py      # SQLAlchemyモデル
│   │   ├── rag/
│   │   │   ├── pipeline.py  # RAGパイプライン（コア）
│   │   │   └── prompts.py   # ドメイン別プロンプト
│   │   └── routers/
│   │       └── chat.py    # チャットAPIエンドポイント
│   └── scripts/
│       └── ingest.py      # 文書取り込みスクリプト
├── frontend/
│   └── app.py             # Streamlit UI
├── data/raw/              # 取り込む文書を置く場所
├── docker-compose.yml
└── .env.example
```

### RAGパイプライン

```
① インデックス構築（一度だけ実行）
文書PDF → チャンク分割 → ベクトル化 → pgvectorに保存

② 検索 & 回答生成（毎回実行）
質問 → クエリ埋め込み → コサイン類似度検索 → プロンプト構築 → LLM回答生成
```

---

## クイックスタート

### 必要なもの
- Docker & Docker Compose
- OpenAI API Key（[取得はこちら](https://platform.openai.com/api-keys)）

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourname/akiya-nav.git
cd akiya-nav
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# .envファイルを開いてOPENAI_API_KEYを設定
```

### 3. Docker で起動

```bash
docker-compose up -d
```

起動確認：
- バックエンドAPI: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

### 4. サンプルデータを投入

```bash
docker-compose exec backend python scripts/ingest.py --sample
```

### 5. チャットを試す

ブラウザで http://localhost:8501 を開いて質問してみてください。

---

## ローカル開発（Docker不使用）

```bash
# PostgreSQL（pgvector付き）を別途起動しておく必要があります

# バックエンド
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env  # .envを編集
uvicorn app.main:app --reload

# 別ターミナルで文書取り込み
python scripts/ingest.py --sample

# 別ターミナルでフロントエンド
cd frontend
pip install streamlit requests
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

---

## 文書の追加方法

```bash
# PDFを取り込む（空き家法）
python scripts/ingest.py --file data/raw/空き家対策特別措置法.pdf --domain law_akiya

# フォルダごと取り込む
python scripts/ingest.py --dir data/raw/laws --domain law_akiya

# 対応ドメイン
# law_akiya        : 空き家関連法律
# law_construction : 建築基準法・消防法・旅館業法
# law_agriculture  : 農地法・農業経営基盤強化促進法
# subsidy_national : 国の補助金・助成金
# subsidy_local    : 自治体の補助金
# case_study       : 全国活用事例
# migration        : 移住体験談・地域情報
```

---

## APIエンドポイント

| メソッド | エンドポイント | 説明 |
|---|---|---|
| `POST` | `/api/chat` | RAGチャット（メイン機能） |
| `GET` | `/api/chat/domains` | 利用可能ドメイン一覧 |
| `GET` | `/api/chat/stats` | DB統計情報 |
| `GET` | `/docs` | Swagger UI |

### チャットAPIの例

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "特定空き家に指定されたらどうなりますか？", "domain": "law_akiya"}'
```

---

## 工夫した点

### 1. ドメイン分離設計
法律・補助金・事例など、文書の種類ごとにドメインタグを付与。ドメインを指定することで検索精度が向上し、プロンプトも自動で切り替わります。

### 2. コンテキスト不使用時の透明性
関連文書が見つからない場合、「提供された文書には情報がありません」と明示した上で一般知識で補足します。ハルシネーションのリスクを低減する設計です。

### 3. 差し替え可能なアーキテクチャ
LLMモデル・埋め込みモデルは設定ファイルで変更可能。GPT-4o → Claude APIへの切り替えも`.env`の編集だけで対応できます。

---

## 今後の拡張（ロードマップ）

- **Phase 2**: 空き家マップ（Folium + 国交省オープンデータ）・活用診断機能
- **Phase 3**: 移住サポート・産業創出プランナー
- **Phase 4**: メンターマッチング・React移行・本番デプロイ

---

## 使用技術・データソース

**技術スタック**: Python / FastAPI / LangChain / pgvector / OpenAI API / Streamlit

**データソース**:
- e-Gov 法令データベース（法律XML）
- 国土交通省 住宅・土地統計調査
- 農林水産省・林野庁 各種補助金要綱
- 内閣府 移住支援ポータルサイト
