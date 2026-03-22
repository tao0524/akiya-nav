# 空き家ナビ — Railway デプロイ手順

Phase 1〜4 完了版 → 本番デプロイ（Railway）

---

## 1. 今回修正するファイル

以下のファイルを変更・追加してから GitHub に push します。

```
akiya-nav/
├── docker-compose.yml          ← 修正（--reload 削除・volumes 削除）
├── frontend/
│   ├── Dockerfile              ← 新規追加
│   └── requirements.txt        ← 新規追加
└── backend/
    └── app/
        └── main.py             ← 修正（CORS を環境変数化）
```

修正内容の詳細はそれぞれのファイルを参照してください。

---

## 2. GitHub に push する

```bash
cd D:\akiya-nav
git add .
git commit -m "feat: Railway デプロイ準備（Dockerfile追加・CORS修正）"
git push origin main
```

---

## 3. Railway でプロジェクトを作成する

1. https://railway.app にアクセスしてログイン
2. `New Project` → `Deploy from GitHub repo`
3. `akiya-nav` リポジトリを選択
4. 最初のサービスは一旦スキップ（後で手動追加）

---

## 4. データベースサービスを追加する

pgvector が必要なため、Railway の標準 PostgreSQL ではなく  
**カスタム Docker イメージ**を使います。

1. `New Service` → `Docker Image`
2. イメージ名: `pgvector/pgvector:pg16`
3. サービス名: `db`
4. 以下の環境変数を設定する：

| 変数名 | 値 |
|---|---|
| `POSTGRES_USER` | `akiya` |
| `POSTGRES_PASSWORD` | （任意の強いパスワードに変更） |
| `POSTGRES_DB` | `akiya_nav` |

5. `Deploy` をクリック

> ⚠️ `POSTGRES_PASSWORD` はローカルの `akiya_pass` から必ず変更してください。

---

## 5. バックエンドサービスを追加する

1. `New Service` → `GitHub Repo` → `akiya-nav`
2. `Root Directory` に `backend` を指定
3. サービス名: `backend`
4. 以下の環境変数を設定する：

| 変数名 | 値 |
|---|---|
| `DATABASE_URL` | `postgresql://akiya:パスワード@db.railway.internal:5432/akiya_nav` |
| `OPENAI_API_KEY` | `sk-...（実際のキー）` |
| `CORS_ORIGINS` | （フロントエンドのURLが決まったら後で設定） |

> `db.railway.internal` は Railway 内部のサービス名です。  
> db サービスのダッシュボードに表示される `Internal Host` を確認して設定してください。

5. `Deploy` をクリック
6. ヘルスチェック確認: `https://バックエンドURL/health` にアクセスして `{"status":"ok"}` が返ればOK

---

## 6. フロントエンドサービスを追加する

1. `New Service` → `GitHub Repo` → `akiya-nav`
2. `Root Directory` に `frontend` を指定
3. サービス名: `frontend`
4. 以下の環境変数を設定する：

| 変数名 | 値 |
|---|---|
| `BACKEND_URL` | `https://バックエンドのRailwayURL` |

5. `Deploy` をクリック

---

## 7. CORS を本番URLで設定する

フロントエンドの Railway URL が確定したら、バックエンドの環境変数を更新します。

```
CORS_ORIGINS = https://frontend-xxxx.up.railway.app
```

バックエンドサービスを再デプロイして完了。

---

## 8. データを投入する

Railway のバックエンドサービスから Shell を開いて実行します。

```bash
# RAG サンプルデータ
python scripts/ingest.py --sample

# 物件ダミーデータ（21件）
python scripts/seed_properties.py

# 地域ダミーデータ（14件）
python scripts/seed_regions.py

# メンターダミーデータ（8件）
python scripts/seed_mentors.py
```

Railway ダッシュボード → バックエンドサービス → `Shell` タブから実行できます。

---

## 9. 動作確認チェックリスト

- [ ] `https://バックエンドURL/health` → `{"status":"ok"}`
- [ ] `https://バックエンドURL/docs` → Swagger UI が表示される
- [ ] `https://フロントエンドURL` → Streamlit UI が表示される
- [ ] RAGチャットで質問して回答が返ってくる
- [ ] 空き家マップにピンが表示される
- [ ] メンター一覧が表示される

---

## トラブルシューティング

**バックエンドが起動しない**
→ Railway のログを確認。`DATABASE_URL` の形式が正しいか確認する。

**`CREATE EXTENSION IF NOT EXISTS vector` でエラー**
→ db サービスが `pgvector/pgvector:pg16` イメージになっているか確認する。  
　標準の PostgreSQL プラグインでは pgvector が使えない。

**フロントエンドからバックエンドに繋がらない**
→ `BACKEND_URL` が `https://` で始まるフルURLになっているか確認する。  
　`localhost` のままになっていないか確認する。

**CORS エラー（ブラウザのコンソールに表示）**
→ バックエンドの `CORS_ORIGINS` にフロントエンドの URL が設定されているか確認する。

---

*空き家ナビ 引き継ぎテンプレート v3.0 — 本番デプロイ手順書*  
*作成: 2026年3月22日*
