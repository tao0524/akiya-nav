"""
活用可能性診断 — Phase 2後半
frontend/pages/02_活用診断.py に配置してください。
"""

import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

st.set_page_config(
    page_title="活用可能性診断 — 空き家ナビ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .diag-header { font-size: 1.6rem; font-weight: 800; color: #1a3c5e; letter-spacing: -0.5px; }
    .diag-sub { font-size: 0.9rem; color: #6b7280; margin-top: 2px; }
    .score-card {
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
        border: 1.5px solid #e5e7eb;
    }
    .score-high { background: #f0fdf4; border-color: #86efac; }
    .score-medium { background: #fffbeb; border-color: #fcd34d; }
    .score-low { background: #f9fafb; border-color: #d1d5db; }
    .score-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }
    .score-reason { font-size: 0.85rem; color: #374151; margin-bottom: 6px; }
    .score-tips {
        font-size: 0.83rem; color: #1e40af;
        background: #eff6ff; border-radius: 8px;
        padding: 7px 10px; margin-top: 4px;
    }
    .level-badge {
        display: inline-block;
        padding: 2px 12px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 700;
        margin-left: 8px;
    }
    .level-high { background: #dcfce7; color: #166534; }
    .level-medium { background: #fef3c7; color: #92400e; }
    .level-low { background: #f3f4f6; color: #6b7280; }
    .summary-box {
        background: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        padding: 14px 18px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 20px;
        font-size: 0.95rem; color: #0c4a6e;
    }
    .subsidy-item {
        background: #f0fdf4; border-radius: 8px;
        padding: 7px 12px; margin-bottom: 6px;
        font-size: 0.85rem; color: #166534;
    }
    .step-item {
        background: #faf5ff; border-radius: 8px;
        padding: 7px 12px; margin-bottom: 6px;
        font-size: 0.85rem; color: #6b21a8;
    }
    .prop-info {
        background: #f8fafc; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 20px;
        font-size: 0.88rem; color: #374151;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# ===== ヘルパー =====

def level_badge(level):
    label = {"high": "◎ おすすめ", "medium": "○ 条件次第", "low": "△ 課題あり"}.get(level, level)
    cls = f"level-{level}"
    return f'<span class="level-badge {cls}">{label}</span>'

def score_card_class(level):
    return f"score-card score-{level}"

def fetch_properties():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/properties", params={"limit": 100}, timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def run_diagnosis(property_id: int):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/diagnosis/{property_id}",
            timeout=60
        )
        if resp.status_code == 200:
            return resp.json(), None
        return None, resp.json().get("detail", "エラーが発生しました")
    except requests.exceptions.Timeout:
        return None, "タイムアウトしました。再度お試しください。"
    except Exception as e:
        return None, str(e)


# ===== メイン =====

st.markdown('<p class="diag-header">🔍 活用可能性診断</p>', unsafe_allow_html=True)
st.markdown('<p class="diag-sub">物件を選ぶとAIがカフェ・宿泊・オフィス・農業の4用途を診断します</p>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 物件一覧を取得
properties = fetch_properties()

if not properties:
    st.error("⚠️ 物件データが取得できません。バックエンドが起動しているか確認してください。")
    st.stop()

# 物件選択
available = [p for p in properties if p.get("status") != "contracted"]
options = {f"{p['prefecture']} {p['city']} — {p['title']}": p["id"] for p in available}

col_select, col_btn = st.columns([4, 1])
with col_select:
    selected_label = st.selectbox(
        "診断する物件を選択",
        list(options.keys()),
        label_visibility="collapsed",
    )
with col_btn:
    diagnose_btn = st.button("🔍 診断する", type="primary", use_container_width=True)

selected_id = options[selected_label]

# 選択中の物件情報を表示
selected_prop = next((p for p in available if p["id"] == selected_id), None)
if selected_prop:
    price_map = {"free": "無償譲渡", "sale": f"売却 {selected_prop['price']}万円",
                 "rent": f"賃料 {selected_prop.get('rent', 0)}万円/月", "negotiable": "価格応相談"}
    price_info = price_map.get(selected_prop.get("price_type", ""), "")
    type_map = {"house": "🏠 住宅", "land": "🌾 土地", "commercial": "🏪 商業"}
    type_label = type_map.get(selected_prop.get("property_type", ""), "")
    st.markdown(f"""
    <div class="prop-info">
        <strong>{selected_prop['title']}</strong><br>
        📍 {selected_prop['prefecture']} {selected_prop['city']} &nbsp;|&nbsp;
        {type_label} &nbsp;|&nbsp; 建物 {selected_prop.get('area_m2', '-')}㎡ &nbsp;|&nbsp;
        {price_info}
    </div>
    """, unsafe_allow_html=True)

# 診断実行
if diagnose_btn:
    with st.spinner("🤖 AIが物件を分析中です... （10〜20秒かかります）"):
        result, error = run_diagnosis(selected_id)

    if error:
        st.error(f"⚠️ {error}")
    elif result:
        st.session_state["last_result"] = result

# 診断結果の表示
if "last_result" in st.session_state:
    result = st.session_state["last_result"]

    st.divider()
    st.markdown(f"### 📊 診断結果：{result['property_title']}")

    # 総合コメント
    st.markdown(f'<div class="summary-box">💡 {result["summary"]}</div>', unsafe_allow_html=True)

    # 4用途スコア（2x2グリッド）
    uses = [
        ("cafe",    "☕ カフェ・飲食"),
        ("lodging", "🏨 宿泊・民泊"),
        ("office",  "💻 オフィス・コワーキング"),
        ("farm",    "🌾 農業・農園"),
    ]

    col1, col2 = st.columns(2)
    for i, (key, label) in enumerate(uses):
        score = result[key]
        level = score["level"]
        card_cls = score_card_class(level)
        badge = level_badge(level)
        col = col1 if i % 2 == 0 else col2
        with col:
            st.markdown(f"""
            <div class="{card_cls}">
                <div class="score-title">{label}{badge}</div>
                <div class="score-reason">📌 {score['reason']}</div>
                <div class="score-tips">💡 {score['tips']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    bottom_col1, bottom_col2 = st.columns(2)

    # 活用できる補助金
    with bottom_col1:
        st.markdown("#### 💰 活用できる補助金・支援制度")
        for s in result.get("subsidies", []):
            st.markdown(f'<div class="subsidy-item">✅ {s}</div>', unsafe_allow_html=True)
        if not result.get("subsidies"):
            st.caption("該当する補助金情報がありません")

    # 次のアクション
    with bottom_col2:
        st.markdown("#### 📋 次にすべきアクション")
        for i, step in enumerate(result.get("next_steps", []), 1):
            st.markdown(f'<div class="step-item">{i}. {step}</div>', unsafe_allow_html=True)
        if not result.get("next_steps"):
            st.caption("アクション情報がありません")

    # RAGチャットへの誘導
    st.divider()
    st.markdown("💬 **補助金の詳細や法律について詳しく知りたい場合は、AIチャットに相談できます**")
    if st.button("🤖 RAGチャットで詳しく調べる →", type="secondary"):
        st.switch_page("app.py")
