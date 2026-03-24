"""
移住サポートページ
frontend/pages/03_移住サポート.py
"""

import streamlit as st
from services.api import get_regions, compare_regions, migration_chat

st.set_page_config(
    page_title="移住サポート — 空き家ナビ",
    page_icon="🏡",
    layout="wide"
)

st.title("🏡 移住サポート")
st.caption("AIが移住の不安を解消。補助金ナビ・地域比較・移住相談")

# タブ構成
tab1, tab2, tab3 = st.tabs(["🗺️ 地域を探す", "⚖️ 地域を比較する", "💬 移住相談チャット"])


# ===== タブ1: 地域を探す =====
with tab1:
    st.subheader("移住候補地を探す")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 絞り込み条件")
        prefecture_filter = st.selectbox(
            "都道府県",
            ["すべて", "北海道", "秋田県", "山形県", "長野県", "山梨県",
             "岐阜県", "兵庫県", "島根県", "岡山県", "高知県",
             "大分県", "宮崎県", "沖縄県"],
            key="region_pref"
        )
        min_subsidy = st.slider("移住支援金の下限（万円）", 0, 200, 0, step=10)

        search_btn = st.button("🔍 検索", use_container_width=True, type="primary")

    with col2:
        if search_btn or True:
            params = {}
            if prefecture_filter != "すべて":
                params["prefecture"] = prefecture_filter
            if min_subsidy > 0:
                params["min_subsidy"] = min_subsidy

            try:
                data = get_regions(params)
                regions = data.get("regions", [])

                if not regions:
                    st.info("条件に合う地域が見つかりませんでした。条件を変えてお試しください。")
                else:
                    st.markdown(f"**{len(regions)}件** の地域が見つかりました")

                    for r in regions:
                        with st.expander(
                            f"📍 {r['prefecture']} {r.get('city', '')}  　"
                            f"支援金: 最大 **{r['subsidy_max']}万円**",
                            expanded=False
                        ):
                            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                            with score_col1:
                                st.metric("🌿 自然環境", f"{'★' * r['score_nature']}{'☆' * (5 - r['score_nature'])}")
                            with score_col2:
                                st.metric("🏪 利便性", f"{'★' * r['score_convenience']}{'☆' * (5 - r['score_convenience'])}")
                            with score_col3:
                                st.metric("💰 補助金", f"{'★' * r['score_subsidy']}{'☆' * (5 - r['score_subsidy'])}")
                            with score_col4:
                                st.metric("🤝 コミュニティ", f"{'★' * r['score_community']}{'☆' * (5 - r['score_community'])}")

                            info_col1, info_col2 = st.columns(2)
                            with info_col1:
                                if r.get("climate"):
                                    st.markdown(f"**気候:** {r['climate']}")
                                if r.get("industry"):
                                    st.markdown(f"**主要産業:** {r['industry']}")
                                if r.get("job_support"):
                                    st.markdown(f"**就業支援:** {r['job_support']}")
                            with info_col2:
                                if r.get("subsidy_detail"):
                                    st.markdown(f"**補助金詳細:** {r['subsidy_detail']}")

                            if r.get("attraction"):
                                st.success(f"✨ **魅力:** {r['attraction']}")
                            if r.get("challenge"):
                                st.warning(f"⚠️ **注意点:** {r['challenge']}")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")


# ===== タブ2: 地域比較 =====
with tab2:
    st.subheader("地域を比較する")
    st.markdown("複数の地域を並べてスコアや補助金を比較できます。")

    all_prefectures = [
        "北海道（ニセコ町）", "秋田県（横手市）", "山形県（鶴岡市）",
        "長野県（松本市）", "長野県（飯山市）", "山梨県（北杜市）",
        "岐阜県（飛騨市）", "兵庫県（養父市）", "島根県（邑南町）",
        "岡山県（真庭市）", "高知県（四万十市）", "大分県（由布市）",
        "宮崎県（日南市）", "沖縄県（うるま市）"
    ]

    selected = st.multiselect(
        "比較したい地域を選んでください（2〜6件）",
        all_prefectures,
        default=["長野県（松本市）", "島根県（邑南町）", "宮崎県（日南市）"]
    )

    if st.button("⚖️ 比較する", type="primary") and selected:
        # 「県名（市名）」から県名だけ抽出
        pref_names = [s.split("（")[0] for s in selected]
        compare_query = ",".join(pref_names)

        try:
            data = compare_regions(compare_query)
            regions = data.get("comparison", [])

            if not regions:
                st.warning("データが見つかりませんでした。")
            else:
                st.markdown("### 📊 スコア比較")

                # スコアテーブル
                score_data = []
                for r in regions:
                    score_data.append({
                        "地域": f"{r['prefecture']} {r.get('city', '')}",
                        "🌿 自然": r["scores"]["nature"],
                        "🏪 利便性": r["scores"]["convenience"],
                        "💰 補助金": r["scores"]["subsidy"],
                        "🤝 コミュニティ": r["scores"]["community"],
                        "合計": r["scores"]["total"],
                        "支援金上限(万円)": r.get("subsidy_max", "-")
                    })

                st.dataframe(score_data, use_container_width=True, hide_index=True)

                # 詳細カード
                st.markdown("### 📋 詳細比較")
                cols = st.columns(len(regions))
                for i, (col, r) in enumerate(zip(cols, regions)):
                    with col:
                        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"][i]
                        st.markdown(f"#### {rank_emoji} {r['prefecture']}")
                        if r.get("city"):
                            st.caption(r["city"])
                        st.metric("移住支援金", f"最大{r.get('subsidy_max', 0)}万円")
                        if r.get("attraction"):
                            st.success(f"✨ {r['attraction'][:80]}...")
                        if r.get("challenge"):
                            st.warning(f"⚠️ {r['challenge'][:60]}...")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    elif len(selected) < 2:
        st.info("2件以上の地域を選んでください。")


# ===== タブ3: 移住相談チャット =====
with tab3:
    st.subheader("💬 移住相談 AIチャット")
    st.markdown("移住に関するあらゆる疑問にAIが回答します。")

    # サンプル質問
    sample_questions = [
        "子育て支援が充実している地方はどこですか？",
        "農業を始めたい場合、どの地域がおすすめですか？",
        "テレワーカーが移住しやすい地域は？",
        "移住支援金をもらうための条件を教えてください",
        "島根県への移住で注意することは何ですか？",
    ]

    st.markdown("**💡 よくある質問:**")
    cols = st.columns(3)
    for i, q in enumerate(sample_questions):
        if cols[i % 3].button(q, key=f"sample_{i}", use_container_width=True):
            st.session_state["migration_question"] = q

    st.divider()

    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        question = st.text_area(
            "質問を入力してください",
            value=st.session_state.get("migration_question", ""),
            height=80,
            placeholder="例: 長野県に移住したい。農業を始めるための補助金はありますか？",
            key="migration_input"
        )
    with col_q2:
        pref_chat = st.selectbox(
            "都道府県を絞る（任意）",
            ["指定なし", "北海道", "秋田県", "山形県", "長野県", "山梨県",
             "岐阜県", "兵庫県", "島根県", "岡山県", "高知県",
             "大分県", "宮崎県", "沖縄県"],
            key="chat_pref"
        )
        send_btn = st.button("送信 ✈️", type="primary", use_container_width=True)

    if send_btn and question.strip():
        with st.spinner("AIが回答を生成中..."):
            try:
                prefecture = pref_chat if pref_chat != "指定なし" else None
                result = migration_chat(question, prefecture)

                st.markdown("### 🤖 AIの回答")
                st.markdown(result.get("answer", "回答を取得できませんでした。"))

                if result.get("sources"):
                    with st.expander("📚 参照した文書"):
                        for src in result["sources"]:
                            st.markdown(f"- {src}")

                context_used = result.get("context_used", 0)
                if context_used == 0:
                    st.info("💡 関連する登録文書が見つからなかったため、一般的な知識で回答しました。`scripts/ingest.py` で移住関連文書を追加すると回答精度が向上します。")

            except requests.exceptions.ConnectionError:
                st.error(f"バックエンドに接続できません（{BACKEND_URL}）。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    elif send_btn:
        st.warning("質問を入力してください。")
