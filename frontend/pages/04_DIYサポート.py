"""
DIYサポートページ
frontend/pages/04_DIYサポート.py
"""

import streamlit as st
from services.api import get_diy_categories, get_diy_advice, get_diy_checklist

st.set_page_config(
    page_title="DIYサポート — 空き家ナビ",
    page_icon="🔨",
    layout="wide"
)

st.title("🔨 DIYサポート")
st.caption("空き家・古民家のDIYリノベーションをAIがサポート")

# タブ構成
tab1, tab2 = st.tabs(["🛠️ DIYアドバイスを得る", "📋 作業チェックリスト"])


# ===== タブ1: DIYアドバイス =====
with tab1:
    st.subheader("DIYアドバイスを得る")

    # カテゴリ一覧を取得
    try:
        cat_res = get_diy_categories()
        categories_data = cat_res.get("categories", [])
        category_map = {f"{c['icon']} {c['name']}": c["id"] for c in categories_data}
        category_display_map = {f"{c['icon']} {c['name']}": c for c in categories_data}
    except Exception as e:
        st.error(f"DIYカテゴリの取得に失敗しました: {e}")
        categories_data = []
        category_map = {}
        category_display_map = {}

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### 作業内容を入力")

        category_label = st.selectbox(
            "作業カテゴリ",
            list(category_map.keys()) if category_map else ["カテゴリを取得できません"],
            key="diy_category"
        )

        # 選択カテゴリの難易度目安を表示
        if category_label in category_display_map:
            cat_info = category_display_map[category_label]
            st.caption(f"目安難易度: {cat_info.get('difficulty', '')}")

        description = st.text_area(
            "状況・詳細説明",
            height=120,
            placeholder="例: 築45年の木造住宅の和室6畳。壁紙が黄ばんで剥がれている。押し入れも同様に張り替えたい。初めてのDIYです。",
            key="diy_description"
        )

        budget = st.number_input("予算（万円）", min_value=0, max_value=1000, value=0, step=5)
        budget_val = budget if budget > 0 else None

        experience = st.radio(
            "あなたの経験レベル",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {"beginner": "🌱 初心者", "intermediate": "🔧 中級者", "advanced": "⚡ 上級者"}[x],
            horizontal=True
        )

        advice_btn = st.button("🤖 AIアドバイスを取得", type="primary", use_container_width=True)

    with col_right:
        if advice_btn:
            if not description.strip():
                st.warning("作業の詳細を入力してください。")
            elif not category_map:
                st.error("カテゴリデータを取得できませんでした。バックエンドを確認してください。")
            else:
                category_id_text = category_label.split(" ", 1)[1] if " " in category_label else category_label

                with st.spinner("AIが分析中... 少々お待ちください"):
                    try:
                        payload = {
                            "category": category_id_text,
                            "description": description,
                            "experience_level": experience
                        }
                        if budget_val:
                            payload["budget"] = budget_val

                        result = get_diy_advice(payload)
                        advice = result.get("advice", {})

                        # 難易度バナー
                        difficulty = advice.get("difficulty", "")
                        if "専門業者" in difficulty:
                            st.error(f"⚠️ **{difficulty}**\n\n{advice.get('difficulty_reason', '')}")
                        elif "上級" in difficulty:
                            st.warning(f"🔧 **{difficulty}**\n\n{advice.get('difficulty_reason', '')}")
                        else:
                            st.success(f"✅ **{difficulty}**\n\n{advice.get('difficulty_reason', '')}")

                        # 基本情報
                        info_col1, info_col2, info_col3 = st.columns(3)
                        with info_col1:
                            st.metric("💰 費用目安", advice.get("estimated_cost", "—"))
                        with info_col2:
                            st.metric("⏱️ 所要時間", advice.get("estimated_time", "—"))
                        with info_col3:
                            permit = advice.get("permit_required", False)
                            st.metric("📋 建築確認申請", "必要 ⚠️" if permit else "不要 ✅")

                        if permit and advice.get("permit_detail"):
                            st.error(f"⚠️ **申請が必要:** {advice['permit_detail']}")

                        # 安全警告
                        if advice.get("safety_warnings"):
                            st.markdown("#### ⚠️ 安全注意事項")
                            for warning in advice["safety_warnings"]:
                                st.warning(f"• {warning}")

                        # 必要なもの
                        tools_col, materials_col = st.columns(2)
                        with tools_col:
                            if advice.get("tools_needed"):
                                st.markdown("#### 🔧 必要な工具")
                                for tool in advice["tools_needed"]:
                                    st.markdown(f"- {tool}")
                        with materials_col:
                            if advice.get("materials_needed"):
                                st.markdown("#### 📦 必要な材料")
                                for mat in advice["materials_needed"]:
                                    st.markdown(f"- {mat}")

                        # 作業手順
                        if advice.get("steps"):
                            st.markdown("#### 📝 作業手順")
                            for step in advice["steps"]:
                                with st.expander(f"Step {step['step']}: {step['title']}"):
                                    st.markdown(step["detail"])
                                    if step.get("tips"):
                                        st.info(f"💡 **コツ:** {step['tips']}")

                        # 追加情報
                        if advice.get("budget_tips"):
                            st.info(f"💰 **予算を抑えるコツ:** {advice['budget_tips']}")
                        if advice.get("subsidy_info"):
                            st.success(f"🎁 **活用できる補助金:** {advice['subsidy_info']}")
                        if advice.get("professional_recommendation"):
                            st.markdown(f"🏢 **業者依頼を推奨するケース:** {advice['professional_recommendation']}")

                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

        else:
            st.markdown("#### 📚 DIYカテゴリ一覧")
            if categories_data:
                for cat in categories_data:
                    st.markdown(
                        f"**{cat['icon']} {cat['name']}** — {cat['description']}  \n"
                        f"　難易度目安: `{cat['difficulty']}`"
                    )
            else:
                st.info("バックエンドを起動するとカテゴリが表示されます。")


# ===== タブ2: チェックリスト =====
with tab2:
    st.subheader("📋 作業前チェックリスト")
    st.markdown("作業開始前に安全確認チェックリストをAIが生成します。")

    check_col1, check_col2 = st.columns([1, 1])
    with check_col1:
        check_category = st.text_input(
            "作業カテゴリ",
            placeholder="例: 屋根修繕、壁紙張り替え",
            key="check_cat"
        )
        check_description = st.text_area(
            "作業の詳細",
            height=100,
            placeholder="例: 築50年の木造住宅の屋根の部分補修。瓦が数枚ずれている。",
            key="check_desc"
        )
        checklist_btn = st.button("📋 チェックリストを生成", type="primary", use_container_width=True)

    with check_col2:
        if checklist_btn and check_category and check_description:
            with st.spinner("チェックリストを生成中..."):
                try:
                    data = get_diy_checklist({"category": check_category, "description": check_description})
                    checklist = data.get("checklist", {})

                    if checklist.get("pre_work_checks"):
                        st.markdown("#### 🔍 事前確認")
                        for item in checklist["pre_work_checks"]:
                            importance = item.get("importance", "")
                            icon = "🔴" if importance == "必須" else "🟡"
                            with st.expander(f"{icon} {item['item']} ({importance})"):
                                st.markdown(item.get("detail", ""))

                    if checklist.get("safety_equipment"):
                        st.markdown("#### 🦺 安全装備")
                        for item in checklist["safety_equipment"]:
                            required = item.get("required", False)
                            icon = "✅" if required else "💡"
                            st.markdown(f"{icon} {item['item']}")

                    if checklist.get("legal_checks"):
                        st.markdown("#### ⚖️ 法的確認")
                        for item in checklist["legal_checks"]:
                            with st.expander(f"📋 {item['item']}"):
                                st.markdown(item.get("detail", ""))

                    if checklist.get("completion_checks"):
                        st.markdown("#### ✔️ 完了確認")
                        for item in checklist["completion_checks"]:
                            st.markdown(f"☐ **{item['item']}** — {item.get('detail', '')}")

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

        elif checklist_btn:
            st.warning("カテゴリと作業詳細を入力してください。")
        else:
            st.info("左側でカテゴリと作業詳細を入力し、「チェックリストを生成」を押してください。")


