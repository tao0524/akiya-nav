"""
メンターマッチングページ
frontend/pages/05_メンター.py
"""

import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

st.set_page_config(
    page_title="メンターマッチング — 空き家ナビ",
    page_icon="👥",
    layout="wide"
)

st.title("👥 メンターマッチング")
st.caption("移住経験者・地域専門家があなたの移住をサポートします")

tab1, tab2, tab3 = st.tabs(["🤖 AIマッチング", "👤 メンター一覧", "📩 相談リクエスト"])


# ===== タブ1: AIマッチング =====
with tab1:
    st.subheader("AIがあなたに合うメンターを選びます")
    st.markdown("あなたの状況を入力するだけで、AIが最適なメンターを3名ピックアップします。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        situation = st.text_area(
            "あなたの状況・相談したいことを教えてください",
            height=150,
            placeholder="例: 東京在住の40代夫婦。子供が独立したので地方移住を考えています。農業に興味があり、古民家を改修して住みたいです。予算は土地・建物合わせて500万円以内。",
        )
        pref_match = st.selectbox(
            "希望する移住先（任意）",
            ["指定なし", "北海道", "秋田県", "山形県", "長野県", "山梨県",
             "岐阜県", "兵庫県", "島根県", "岡山県", "高知県",
             "大分県", "宮崎県", "沖縄県"],
        )
        specialty_match = st.selectbox(
            "相談したい専門分野（任意）",
            ["指定なし", "農業", "古民家再生", "DIY", "飲食業", "民泊・宿泊業",
             "IT・テレワーク", "起業", "子育て", "定年移住", "補助金活用"],
        )
        match_btn = st.button("🤖 マッチングする", type="primary", use_container_width=True)

    with col_right:
        if match_btn:
            if not situation.strip():
                st.warning("状況・相談内容を入力してください。")
            else:
                with st.spinner("AIがあなたに合うメンターを探しています..."):
                    try:
                        payload = {"situation": situation}
                        if pref_match != "指定なし":
                            payload["prefecture"] = pref_match
                        if specialty_match != "指定なし":
                            payload["specialty"] = specialty_match

                        res = requests.post(
                            f"{BACKEND_URL}/api/mentors/match",
                            json=payload,
                            timeout=60
                        )
                        result = res.json()

                        if result.get("overall_advice"):
                            st.info(f"💡 **AIからのアドバイス:** {result['overall_advice']}")

                        st.markdown("### 🎯 おすすめメンター TOP3")

                        for i, rec in enumerate(result.get("recommendations", []), 1):
                            mentor = rec.get("mentor", {})
                            rank_emoji = ["🥇", "🥈", "🥉"][i - 1]

                            with st.expander(
                                f"{rank_emoji} {mentor.get('name', '')}（{mentor.get('age', '')}歳・{mentor.get('prefecture', '')}）",
                                expanded=(i == 1)
                            ):
                                m_col1, m_col2 = st.columns([2, 1])
                                with m_col1:
                                    st.markdown(f"**推薦理由:** {rec.get('reason', '')}")
                                    st.markdown("**マッチポイント:**")
                                    for point in rec.get("match_points", []):
                                        st.markdown(f"  ✅ {point}")
                                    if rec.get("first_question"):
                                        st.success(f"💬 **最初の質問のヒント:** {rec['first_question']}")
                                with m_col2:
                                    st.metric("評価", f"⭐ {mentor.get('rating', '')}")
                                    st.metric("相談実績", f"{mentor.get('consultation_count', 0)}件")
                                    st.caption(f"対応: {mentor.get('consultation_method', '')}")

                                if mentor.get("bio"):
                                    st.markdown(f"*{mentor['bio']}*")

                                # 相談リクエストボタン
                                if st.button(
                                    f"📩 {mentor.get('name', '')}に相談する",
                                    key=f"request_{mentor.get('id')}",
                                    use_container_width=True
                                ):
                                    st.session_state["selected_mentor_id"] = mentor.get("id")
                                    st.session_state["selected_mentor_name"] = mentor.get("name")
                                    st.info("「相談リクエスト」タブから送信してください。")

                    except requests.exceptions.ConnectionError:
                        st.error(f"バックエンドに接続できません（{BACKEND_URL}）。")
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
        else:
            st.markdown("#### 💡 こんな方におすすめ")
            st.markdown("""
- 移住したいけど、何から始めればいいかわからない
- 農業・カフェ・民泊など、やりたいことはあるけど不安
- 補助金の申請方法を教えてほしい
- 移住後のリアルな生活を知りたい
- 古民家購入・DIYについて専門家に聞きたい
            """)


# ===== タブ2: メンター一覧 =====
with tab2:
    st.subheader("メンター一覧")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        pref_filter = st.selectbox(
            "都道府県",
            ["すべて", "北海道", "秋田県", "山形県", "長野県", "山梨県",
             "岐阜県", "兵庫県", "島根県", "岡山県", "高知県",
             "大分県", "宮崎県", "沖縄県"],
            key="mentor_pref_filter"
        )
    with f_col2:
        specialty_filter = st.selectbox(
            "専門分野",
            ["すべて", "農業", "古民家再生", "DIY", "飲食業", "民泊・宿泊業",
             "IT・テレワーク", "起業", "子育て", "定年移住", "補助金活用"],
            key="mentor_specialty_filter"
        )
    with f_col3:
        available_only = st.checkbox("受付中のみ表示", value=True)

    try:
        params = {"available_only": str(available_only).lower()}
        if pref_filter != "すべて":
            params["prefecture"] = pref_filter
        if specialty_filter != "すべて":
            params["specialty"] = specialty_filter

        res = requests.get(f"{BACKEND_URL}/api/mentors", params=params, timeout=10)
        data = res.json()
        mentors = data.get("mentors", [])

        if not mentors:
            st.info("条件に合うメンターが見つかりませんでした。")
        else:
            st.markdown(f"**{len(mentors)}名** のメンターが見つかりました")

            for m in mentors:
                with st.expander(
                    f"{'🟢' if m['is_available'] else '🔴'} "
                    f"**{m['name']}**（{m['age']}歳）　"
                    f"{m['prefecture']} {m.get('city', '')}　"
                    f"⭐{m['rating']} / 相談{m['consultation_count']}件",
                    expanded=False
                ):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**出身:** {m.get('origin', '')} → **現在:** {m['prefecture']} {m.get('city', '')}")
                        st.markdown(f"**移住:** {m.get('migration_from', '')}から{m.get('migration_year', '')}年に移住")
                        st.markdown(f"**専門:** {' / '.join(m.get('specialties', []))}")
                        st.markdown(f"**相談対応:** {m.get('consultation_method', '')}")
                        if m.get("can_help_with"):
                            st.markdown(f"**対応できる相談:** {m['can_help_with']}")
                        if m.get("bio"):
                            st.info(f"💬 {m['bio']}")
                    with c2:
                        st.metric("評価", f"⭐ {m['rating']}")
                        st.metric("相談実績", f"{m['consultation_count']}件")
                        if m["is_available"]:
                            if st.button("📩 相談する", key=f"list_req_{m['id']}", use_container_width=True):
                                st.session_state["selected_mentor_id"] = m["id"]
                                st.session_state["selected_mentor_name"] = m["name"]
                                st.info("「相談リクエスト」タブへ")
                        else:
                            st.warning("受付停止中")

    except requests.exceptions.ConnectionError:
        st.error(f"バックエンドに接続できません（{BACKEND_URL}）。")
    except Exception as e:
        st.error(f"エラー: {e}")


# ===== タブ3: 相談リクエスト =====
with tab3:
    st.subheader("📩 相談リクエストを送る")

    # 選択済みメンターがあれば表示
    selected_id = st.session_state.get("selected_mentor_id")
    selected_name = st.session_state.get("selected_mentor_name")
    if selected_name:
        st.success(f"✅ 選択中のメンター: **{selected_name}**")

    req_col1, req_col2 = st.columns([1, 1])

    with req_col1:
        # メンター選択
        try:
            res = requests.get(f"{BACKEND_URL}/api/mentors", params={"available_only": "true"}, timeout=5)
            mentors_list = res.json().get("mentors", [])
            mentor_options = {f"{m['name']}（{m['prefecture']}・{'/'.join(m['specialties'][:2])}）": m["id"] for m in mentors_list}
        except Exception:
            mentor_options = {}

        if mentor_options:
            # 選択済みがあれば初期値にセット
            default_index = 0
            if selected_id:
                ids = list(mentor_options.values())
                if selected_id in ids:
                    default_index = ids.index(selected_id)

            selected_label = st.selectbox(
                "相談するメンターを選んでください",
                list(mentor_options.keys()),
                index=default_index
            )
            mentor_id = mentor_options[selected_label]
        else:
            st.error("メンターを取得できません。バックエンドを確認してください。")
            mentor_id = None

        requester_name = st.text_input("お名前", placeholder="山田 太郎")
        requester_email = st.text_input("メールアドレス", placeholder="yamada@example.com")
        message = st.text_area(
            "相談内容",
            height=150,
            placeholder="例: 長野県への移住を検討しています。農業を始めるにあたって、初期費用や必要な手続きについて教えていただけますか？現在は東京でサラリーマンをしており、来年春の移住を目指しています。"
        )

        send_btn = st.button("📩 リクエストを送信する", type="primary", use_container_width=True)

    with req_col2:
        st.markdown("#### 💡 相談のコツ")
        st.markdown("""
**メッセージに含めると回答がもらいやすい内容：**
- 現在の状況（職業・家族構成・居住地）
- 移住を考えている時期・予算
- やりたいこと・気になっていること
- 特に聞きたい具体的な質問

**相談の流れ：**
1. リクエスト送信
2. メンターから返信（2〜3営業日）
3. オンラインまたは対面で相談
        """)

        if send_btn:
            if not all([requester_name, requester_email, message, mentor_id]):
                st.warning("すべての項目を入力してください。")
            elif len(message) < 10:
                st.warning("相談内容をもう少し詳しく書いてください。")
            else:
                with st.spinner("送信中..."):
                    try:
                        res = requests.post(
                            f"{BACKEND_URL}/api/mentors/request",
                            json={
                                "mentor_id": mentor_id,
                                "requester_name": requester_name,
                                "requester_email": requester_email,
                                "message": message
                            },
                            timeout=10
                        )
                        result = res.json()
                        st.success(f"""
✅ **{result.get('mentor_name', '')}さんへのリクエストを送信しました！**

相談ID: `{result.get('consultation_id', '')}`

{result.get('note', '')}
                        """)
                        # セッション状態をリセット
                        st.session_state.pop("selected_mentor_id", None)
                        st.session_state.pop("selected_mentor_name", None)

                    except requests.exceptions.ConnectionError:
                        st.error(f"バックエンドに接続できません（{BACKEND_URL}）。")
                    except Exception as e:
                        st.error(f"エラー: {e}")
