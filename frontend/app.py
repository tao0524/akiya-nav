"""
地域創生AIプラットフォーム — フロントエンド
Streamlit を使ったチャットUI
"""

import streamlit as st
import requests
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# ===== ページ設定 =====
st.set_page_config(
    page_title="空き家ナビ — 地域創生AIプラットフォーム",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== スタイル =====
st.markdown("""
<style>
    .main-title { font-size: 1.8rem; font-weight: bold; color: #1F5C8B; margin-bottom: 0; }
    .sub-title  { font-size: 1rem; color: #666; margin-top: 0; }
    .answer-box {
        background: #f0f7ff;
        border-left: 4px solid #1F5C8B;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .source-tag {
        display: inline-block;
        background: #e8f5e9;
        color: #2E7D32;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .user-msg {
        background: #fff3e0;
        border-left: 4px solid #ff8f00;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ===== サイドバー =====
with st.sidebar:
    st.markdown("## 🏡 空き家ナビ")
    st.markdown("*地域創生AIプラットフォーム*")
    st.divider()

    # ドメイン選択
    st.markdown("### 相談カテゴリ")
    domain_options = {
        "🔍 すべてから検索": None,
        "⚖️ 空き家・法律相談": "law_akiya",
        "🏗️ 建築・許認可": "law_construction",
        "🌾 農業・農地相談": "law_agriculture",
        "💰 補助金・助成金": "subsidy_national",
        "🌿 事例から学ぶ": "case_study",
    }
    selected_label = st.selectbox(
        "どのカテゴリについて相談しますか？",
        list(domain_options.keys()),
        help="カテゴリを指定すると、より精度の高い回答が得られます"
    )
    selected_domain = domain_options[selected_label]

    st.divider()

    # DB統計
    st.markdown("### 📊 データベース情報")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/chat/stats", timeout=5)
        if resp.status_code == 200:
            stats = resp.json()
            st.metric("登録文書数", f"{stats['total_documents']:,} チャンク")
            if stats.get("by_domain"):
                for domain, count in stats["by_domain"].items():
                    st.caption(f"・{domain}: {count}件")
        else:
            st.warning("バックエンドに接続できません")
    except Exception:
        st.error("⚠️ バックエンド未起動\n`docker-compose up` を実行してください")

    st.divider()

    # よくある質問（クイック入力）
    st.markdown("### 💡 よくある質問")
    quick_questions = [
        "特定空き家に指定されたらどうなる？",
        "相続した空き家の税金について教えて",
        "移住支援金はいくらもらえる？",
        "古民家でカフェを開くには何が必要？",
        "農地を借りて農業を始めるには？",
        "空き家をDIYリノベするときの注意点は？",
    ]
    for q in quick_questions:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.session_state["pending_question"] = q


# ===== メインエリア =====
st.markdown('<p class="main-title">🏡 空き家ナビ — 地域創生AIプラットフォーム</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">「AIが情報をつなぎ、人が知恵をつなぐ」 | Phase 1: RAGチャット</p>', unsafe_allow_html=True)
st.divider()

# セッション初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 会話履歴の表示
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="answer-box">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("sources"):
            st.markdown("**参照文書:** " + " ".join([
                f'<span class="source-tag">📄 {s}</span>' for s in msg["sources"]
            ]), unsafe_allow_html=True)

# クイック質問の処理
if "pending_question" in st.session_state:
    pending = st.session_state.pop("pending_question")
    st.session_state["prefill"] = pending

# 入力フォーム
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        default_val = st.session_state.pop("prefill", "")
        user_input = st.text_input(
            "質問を入力してください",
            value=default_val,
            placeholder="例：相続した空き家の固定資産税について教えてください",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("送信 →", use_container_width=True, type="primary")

if submitted and user_input.strip():
    # ユーザーメッセージを履歴に追加
    st.session_state.messages.append({"role": "user", "content": user_input})

    # バックエンドにリクエスト
    with st.spinner("🔍 関連文書を検索・回答生成中..."):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={"question": user_input, "domain": selected_domain},
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])
                context_used = data.get("context_used", 0)

                # アシスタントの回答を履歴に追加
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "context_used": context_used
                })

                # 統計情報をサイドバーに表示
                if context_used == 0:
                    st.info("💡 関連文書が見つかりませんでした。ingest.py で文書を登録すると精度が上がります。")
            else:
                st.error(f"エラー: {resp.text}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ バックエンドに接続できません。`docker-compose up` を実行してください。")
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    st.rerun()

# 会話クリアボタン
if st.session_state.messages:
    if st.button("🗑️ 会話をクリア", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# 初期メッセージ
if not st.session_state.messages:
    st.markdown("""
    ---
    ### 👋 ようこそ！

    このAIアシスタントは、空き家・移住・地方起業に関する質問にお答えします。

    **こんなことが聞けます：**
    - ⚖️ 空き家の法律・相続・税金について
    - 🏘️ 移住支援金・補助金の情報
    - 🌾 農業・林業で起業する方法
    - 🏡 古民家のリノベ・活用アイデア
    - 📋 キャンプ場・民泊の許認可手続き

    左のサイドバーからカテゴリを選ぶか、質問を直接入力してください。

    > **Note**: サンプルデータで動作確認する場合は  
    > `cd backend && python scripts/ingest.py --sample` を実行してください。
    """)
