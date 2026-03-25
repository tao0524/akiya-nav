"""
空き家マップ
frontend/pages/01_空き家マップ.py
"""

import streamlit as st
import json
from datetime import datetime
from services.api import get_properties, get_property_stats

# ===== ページ設定 =====
st.set_page_config(
    page_title="空き家マップ — 空き家ナビ",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== スタイル =====
st.markdown("""
<style>
    .map-header {
        font-size: 1.6rem; font-weight: 800;
        color: #1a3c5e; margin-bottom: 0;
        letter-spacing: -0.5px;
    }
    .map-sub { font-size: 0.9rem; color: #6b7280; margin-top: 2px; }
    .prop-card {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .prop-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .prop-title { font-weight: 700; font-size: 0.95rem; color: #1a3c5e; }
    .prop-meta { font-size: 0.8rem; color: #6b7280; margin-top: 2px; }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .badge-free { background: #d1fae5; color: #065f46; }
    .badge-sale { background: #dbeafe; color: #1e40af; }
    .badge-rent { background: #fef3c7; color: #92400e; }
    .badge-negotiable { background: #f3e8ff; color: #6b21a8; }
    .badge-high { background: #d1fae5; color: #065f46; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #f3f4f6; color: #6b7280; }
    .stat-box {
        background: #f0f9ff;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .stat-num { font-size: 1.8rem; font-weight: 800; color: #0369a1; }
    .stat-label { font-size: 0.78rem; color: #6b7280; margin-top: 2px; }
    .filter-section { margin-bottom: 16px; }
    .potential-row { margin-top: 6px; }
</style>
""", unsafe_allow_html=True)


# ===== ヘルパー関数 =====

def price_label(prop):
    pt = prop.get("price_type", "")
    price = prop.get("price", 0)
    rent = prop.get("rent", 0)
    if pt == "free":
        return "無償譲渡"
    elif pt == "rent":
        return f"月額 {rent}万円"
    elif pt == "sale":
        return f"売却 {price}万円" if price else "価格応相談"
    else:
        return "応相談"

def price_badge_class(price_type):
    return {
        "free": "badge-free",
        "sale": "badge-sale",
        "rent": "badge-rent",
        "negotiable": "badge-negotiable",
    }.get(price_type, "badge-sale")

def type_label(t):
    return {"house": "🏠 住宅", "land": "🌾 土地", "commercial": "🏪 商業"}.get(t, t)

def potential_badge(level, label):
    cls = f"badge-{level}" if level in ("high", "medium", "low") else "badge-low"
    emoji_map = {"high": "◎", "medium": "○", "low": "△"}
    emoji = emoji_map.get(level, "-")
    return f'<span class="badge {cls}">{label}: {emoji}</span>'


def fetch_properties(filters: dict) -> list:
    try:
        return get_properties({k: v for k, v in filters.items() if v is not None})
    except Exception as e:
        st.error(f"物件データの取得に失敗しました: {e}")
        return []

def build_folium_map(properties: list) -> str:
    """Foliumマップを構築してHTMLを返す"""
    try:
        import folium
        from folium.plugins import MarkerCluster

        # 中心座標（物件の平均、なければ日本の中心）
        if properties:
            lats = [float(p["latitude"]) for p in properties if p.get("latitude")]
            lons = [float(p["longitude"]) for p in properties if p.get("longitude")]
            center = [sum(lats) / len(lats), sum(lons) / len(lons)] if lats else [36.0, 136.0]
            zoom = 6
        else:
            center = [36.0, 136.0]
            zoom = 5

        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="CartoDB positron",
            prefer_canvas=True,
        )

        # クラスタリング
        cluster = MarkerCluster(
            options={
                "maxClusterRadius": 60,
                "spiderfyOnMaxZoom": True,
            }
        ).add_to(m)

        # カラーマッピング
        color_map = {
            "free": "green",
            "rent": "orange",
            "sale": "blue",
            "negotiable": "purple",
            "contracted": "gray",
            "negotiating": "red",
        }
        icon_map = {
            "house": "home",
            "land": "leaf",
            "commercial": "shopping-cart",
        }

        for prop in properties:
            try:
                lat = float(prop["latitude"])
                lon = float(prop["longitude"])
            except (TypeError, ValueError):
                continue

            # ステータスで色分け
            if prop.get("status") == "contracted":
                color = "gray"
            elif prop.get("status") == "negotiating":
                color = "red"
            else:
                color = color_map.get(prop.get("price_type", "sale"), "blue")

            icon = icon_map.get(prop.get("property_type", "house"), "home")

            # ポップアップHTML
            potential_html = ""
            for key, label in [("potential_cafe", "カフェ"), ("potential_lodging", "宿泊"), ("potential_office", "オフィス"), ("potential_farm", "農業")]:
                level = prop.get(key, "low")
                emoji = {"high": "◎", "medium": "○", "low": "△"}.get(level, "-")
                potential_html += f'<span style="margin-right:6px;font-size:0.8em">{label}:{emoji}</span>'

            status_label = {"available": "募集中", "negotiating": "商談中", "contracted": "成約済み"}.get(prop.get("status"), "")
            price_info = price_label(prop)

            popup_html = f"""
            <div style="min-width:220px; font-family: sans-serif;">
                <div style="font-weight:700;font-size:0.95em;color:#1a3c5e;margin-bottom:4px">
                    {prop.get('title','物件名不明')}
                </div>
                <div style="font-size:0.8em;color:#6b7280;margin-bottom:6px">
                    📍 {prop.get('prefecture','')} {prop.get('city','')}
                </div>
                <div style="margin-bottom:6px">
                    <span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:600">
                        {status_label}
                    </span>
                    <span style="background:#f3f4f6;color:#374151;padding:2px 8px;border-radius:12px;font-size:0.75em;margin-left:4px">
                        {type_label(prop.get('property_type',''))}
                    </span>
                </div>
                <div style="font-size:0.85em;font-weight:700;color:#0369a1;margin-bottom:6px">
                    {price_info}
                </div>
                <div style="font-size:0.78em;color:#374151;margin-bottom:4px">
                    建物: {prop.get('area_m2','-')}㎡ / 土地: {prop.get('land_area_m2','-')}㎡
                </div>
                <div style="font-size:0.78em;color:#374151;margin-bottom:6px">{potential_html}</div>
            </div>
            """

            tooltip = f"{prop.get('city','')} | {price_info}"

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=tooltip,
                icon=folium.Icon(color=color, icon=icon, prefix="fa"),
            ).add_to(cluster)

        # 凡例
        legend_html = """
        <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                    background:white;padding:12px 16px;border-radius:10px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.15);font-size:0.78em;font-family:sans-serif">
            <div style="font-weight:700;margin-bottom:6px;color:#374151">🗺️ 凡例</div>
            <div>🟢 無償譲渡</div>
            <div>🔵 売却物件</div>
            <div>🟠 賃貸物件</div>
            <div>🟣 価格応相談</div>
            <div>🔴 商談中</div>
            <div>⚫ 成約済み</div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        return m._repr_html_()

    except ImportError:
        return "<div style='padding:20px;color:#dc2626'>⚠️ foliumがインストールされていません。<br><code>pip install folium</code> を実行してください。</div>"


# ===== サイドバー: フィルター =====
with st.sidebar:
    st.markdown("## 🗺️ 空き家マップ")
    st.markdown("*全国物件検索*")
    st.divider()

    st.markdown("### 🔍 絞り込み")

    pref_options = ["すべての都道府県", "北海道", "秋田県", "長野県", "京都府",
                    "兵庫県", "岡山県", "島根県", "高知県", "大分県", "沖縄県"]
    selected_pref = st.selectbox("都道府県", pref_options)
    prefecture_filter = None if selected_pref == "すべての都道府県" else selected_pref

    type_options = {"すべての種別": None, "🏠 住宅": "house", "🌾 土地": "land", "🏪 商業施設": "commercial"}
    selected_type_label = st.selectbox("物件種別", list(type_options.keys()))
    type_filter = type_options[selected_type_label]

    price_type_options = {
        "すべて": None, "💚 無償譲渡": "free",
        "🔵 売却": "sale", "🟠 賃貸": "rent", "🟣 応相談": "negotiable"
    }
    selected_pt_label = st.selectbox("取引種別", list(price_type_options.keys()))
    price_type_filter = price_type_options[selected_pt_label]

    st.markdown("##### 活用ポテンシャル（高のみ表示）")
    potential_filter = None
    p_cafe = st.checkbox("☕ カフェ向き")
    p_lodge = st.checkbox("🏨 宿泊向き")
    p_office = st.checkbox("💻 オフィス向き")
    p_farm = st.checkbox("🌾 農業向き")
    if p_cafe: potential_filter = "cafe"
    elif p_lodge: potential_filter = "lodging"
    elif p_office: potential_filter = "office"
    elif p_farm: potential_filter = "farm"

    show_contracted = st.checkbox("成約済み・商談中も表示", value=False)
    status_filter = None if show_contracted else "available"

    st.divider()
    st.markdown("### 📊 エリア別統計")
    try:
        stats = get_property_stats()
        for s in stats[:8]:
            st.caption(f"・{s['prefecture']}: {s['count']}件")
    except Exception:
        st.caption("⚠️ バックエンド未接続")

# ===== メインエリア =====
st.markdown('<p class="map-header">🗺️ 空き家マップ</p>', unsafe_allow_html=True)
st.markdown('<p class="map-sub">全国の空き家・空き地を地図で探す</p>', unsafe_allow_html=True)

# フィルターを適用して物件取得
filters = {
    "prefecture": prefecture_filter,
    "property_type": type_filter,
    "price_type": price_type_filter,
    "potential": potential_filter,
    "status": status_filter,
    "limit": 100,
}
properties = fetch_properties(filters)

# KPIバー
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num">{len(properties)}</div>
        <div class="stat-label">件の物件</div>
    </div>""", unsafe_allow_html=True)
with col2:
    free_count = sum(1 for p in properties if p.get("price_type") == "free")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num" style="color:#065f46">{free_count}</div>
        <div class="stat-label">無償譲渡</div>
    </div>""", unsafe_allow_html=True)
with col3:
    high_cafe = sum(1 for p in properties if p.get("potential_cafe") == "high")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num" style="color:#92400e">{high_cafe}</div>
        <div class="stat-label">カフェ向き ◎</div>
    </div>""", unsafe_allow_html=True)
with col4:
    high_lodge = sum(1 for p in properties if p.get("potential_lodging") == "high")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num" style="color:#6b21a8">{high_lodge}</div>
        <div class="stat-label">宿泊向き ◎</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 地図 + 物件リストの2カラムレイアウト
map_col, list_col = st.columns([3, 1])

with map_col:
    if not properties:
        st.info("📭 条件に合う物件が見つかりませんでした。フィルターを変更してみてください。")
    else:
        with st.spinner("🗺️ 地図を生成中..."):
            map_html = build_folium_map(properties)
        st.components.v1.html(map_html, height=560, scrolling=False)

with list_col:
    st.markdown(f"#### 物件一覧 ({len(properties)}件)")
    if not properties:
        st.caption("物件がありません")
    else:
        for prop in properties[:20]:  # リストは最大20件表示
            pt = prop.get("price_type", "sale")
            badge_cls = price_badge_class(pt)
            status = prop.get("status", "available")
            status_emoji = {"available": "🟢", "negotiating": "🔴", "contracted": "⚫"}.get(status, "🟢")

            potential_row = ""
            for k, label in [("potential_cafe", "☕"), ("potential_lodging", "🏨"), ("potential_office", "💻"), ("potential_farm", "🌾")]:
                lvl = prop.get(k, "low")
                if lvl == "high":
                    potential_row += f'<span style="font-size:0.8em">{label}◎ </span>'

            st.markdown(f"""
            <div class="prop-card">
                <div class="prop-title">{status_emoji} {prop.get('title','')}</div>
                <div class="prop-meta">📍 {prop.get('prefecture','')} {prop.get('city','')}</div>
                <div style="margin-top:4px">
                    <span class="badge {badge_cls}">{price_label(prop)}</span>
                    <span class="badge" style="background:#f3f4f6;color:#374151">{type_label(prop.get('property_type',''))}</span>
                </div>
                <div class="potential-row">{potential_row}</div>
            </div>
            """, unsafe_allow_html=True)

        if len(properties) > 20:
            st.caption(f"他 {len(properties) - 20}件（フィルターで絞り込んでください）")

# 凡例・注意事項
with st.expander("ℹ️ このマップについて"):
    st.markdown("""
    - **データソース**: 現在はサンプルデータ（実在する代表エリアのダミー物件）を表示しています
    - **今後の拡張**: 国土交通省「不動産情報ライブラリ」APIや各自治体の空き家バンクデータと連携予定
    - **地図の色分け**: 緑=無償、青=売却、橙=賃貸、紫=応相談、赤=商談中、灰=成約済み
    - **活用ポテンシャル**: AI診断による物件の活用可能性スコアです（「活用診断」ページで詳しく確認できます）
    - **ご注意**: 実際の物件取引には必ず現地確認・専門家への相談を行ってください
    """)

# RAGチャットへの誘導
st.markdown("---")
col_chat1, col_chat2 = st.columns([2, 1])
with col_chat1:
    st.markdown("💬 **気になる物件の法律・補助金について相談したい？**")
    st.caption("AIチャットで空き家法・移住支援金・活用事例を質問できます")
with col_chat2:
    if st.button("🤖 AIに相談する →", type="primary", use_container_width=True):
        st.switch_page("app.py")


