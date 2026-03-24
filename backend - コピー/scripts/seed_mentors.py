"""
メンターのダミーデータを投入するスクリプト。
Phase 4: メンターマッチング機能で使用。

使用方法:
    docker-compose exec backend python scripts/seed_mentors.py
"""

import sys
sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import Mentor

MENTOR_DATA = [
    {
        "name": "田中 誠",
        "age": 45,
        "gender": "男性",
        "prefecture": "長野県",
        "city": "松本市",
        "origin": "東京都",
        "specialties": "農業,古民家再生,地域コミュニティ",
        "migration_year": 2015,
        "migration_from": "東京都",
        "migration_story": "広告代理店を退職し、妻と二人で長野県松本市に移住。最初の2年は農業の失敗続きでしたが、地元農家のサポートで軌道に乗りました。今は無農薬野菜の直売と民泊を経営しています。",
        "can_help_with": "農業の始め方・失敗談、古民家のリノベーション費用、地域コミュニティへの溶け込み方、東京からの移住手続き全般",
        "consultation_method": "オンライン・対面（長野県内）",
        "rating": "4.9",
        "consultation_count": 47,
        "is_available": "true",
        "bio": "元広告マン。農業×民泊で年商800万円を達成。失敗から学んだリアルな移住ノウハウをお伝えします。",
    },
    {
        "name": "佐藤 美咲",
        "age": 36,
        "gender": "女性",
        "prefecture": "島根県",
        "city": "邑南町",
        "origin": "大阪府",
        "specialties": "飲食業,古民家カフェ,補助金活用",
        "migration_year": 2019,
        "migration_from": "大阪府",
        "migration_story": "大阪でOLをしながら「いつかカフェを開きたい」という夢を持ち続け、島根県邑南町の「A級グルメのまち」プロジェクトに惹かれて移住。古民家をDIYでリノベーションし、地元食材を使ったカフェをオープン。移住支援金と補助金を最大限活用しました。",
        "can_help_with": "古民家カフェの開業手順、補助金の申請方法、島根県移住の実態、女性一人での地方移住の不安解消",
        "consultation_method": "オンライン",
        "rating": "5.0",
        "consultation_count": 38,
        "is_available": "true",
        "bio": "補助金総額350万円を活用してカフェを開業。移住前の不安から開業までの全ステップをリアルにお話しします。",
    },
    {
        "name": "鈴木 健太",
        "age": 52,
        "gender": "男性",
        "prefecture": "北海道",
        "city": "ニセコ町",
        "origin": "神奈川県",
        "specialties": "民泊・宿泊業,インバウンド,不動産",
        "migration_year": 2010,
        "migration_from": "神奈川県",
        "migration_story": "不動産会社勤務を経てニセコに移住。外国人観光客向けの民泊を3軒経営。インバウンド需要の波に乗り、現在は年商2000万円超。空き家を購入・リノベーションして民泊にする方法を熟知しています。",
        "can_help_with": "民泊の開業・許認可手続き、外国人観光客対応、空き家の不動産取得、ニセコの物価・生活費の実態",
        "consultation_method": "オンライン・対面（北海道内）",
        "rating": "4.8",
        "consultation_count": 62,
        "is_available": "true",
        "bio": "ニセコで民泊3軒経営。インバウンド向け宿泊業の立ち上げから運営まで、なんでも相談してください。",
    },
    {
        "name": "山本 花子",
        "age": 41,
        "gender": "女性",
        "prefecture": "高知県",
        "city": "四万十市",
        "origin": "愛知県",
        "specialties": "農業,子育て,移住支援制度",
        "migration_year": 2017,
        "migration_from": "愛知県",
        "migration_story": "夫の転勤をきっかけに高知県四万十市へ。子育てしながら週3日だけ農業パートをしています。子育て環境の充実に驚き、もう都会には戻れないと感じています。移住前の不安だった医療・教育の実態もリアルにお話しできます。",
        "can_help_with": "子育て世代の移住、農業パートの探し方、四万十市の生活費・医療・学校の実態、家族を説得するコツ",
        "consultation_method": "オンライン",
        "rating": "4.9",
        "consultation_count": 29,
        "is_available": "true",
        "bio": "子育て中の移住者。家族での移住に必要な情報を全部お伝えします。特に奥様・お子様連れの方はぜひ。",
    },
    {
        "name": "中村 拓也",
        "age": 38,
        "gender": "男性",
        "prefecture": "岡山県",
        "city": "真庭市",
        "origin": "東京都",
        "specialties": "IT・テレワーク,林業,起業",
        "migration_year": 2020,
        "migration_from": "東京都",
        "migration_story": "IT企業でエンジニアをしながらフルリモートワークを実現し、岡山県真庭市に移住。週4日テレワーク、週1日は地元の林業組合でアルバイト。都会の収入を保ちながら自然の中で暮らすデュアルライフを実践中。",
        "can_help_with": "テレワーク移住の進め方、IT系副業・フリーランスの移住、林業への参入方法、岡山県移住のコスパ",
        "consultation_method": "オンライン",
        "rating": "4.7",
        "consultation_count": 41,
        "is_available": "true",
        "bio": "東京の年収を維持しながら地方移住を実現。テレワーク×地方暮らしのリアルな両立術を公開します。",
    },
    {
        "name": "伊藤 幸子",
        "age": 60,
        "gender": "女性",
        "prefecture": "山梨県",
        "city": "北杜市",
        "origin": "東京都",
        "specialties": "定年移住,農業,コミュニティ形成",
        "migration_year": 2012,
        "migration_from": "東京都",
        "migration_story": "定年を機に夫婦で山梨県北杜市へ移住。八ヶ岳の麓で家庭菜園と陶芸を楽しんでいます。移住者コミュニティの世話役として、これまで100人以上の移住相談に乗ってきました。シニア移住の先輩として、年金・医療・介護のリアルもお伝えできます。",
        "can_help_with": "定年後の移住計画、夫婦での移住、年金生活での地方暮らしの費用、シニアのコミュニティ参加",
        "consultation_method": "オンライン・対面（山梨県内）",
        "rating": "5.0",
        "consultation_count": 103,
        "is_available": "true",
        "bio": "相談実績100件超のベテランメンター。定年移住から10年。シニアのリアルな田舎暮らしをお話しします。",
    },
    {
        "name": "渡辺 大輔",
        "age": 44,
        "gender": "男性",
        "prefecture": "宮崎県",
        "city": "日南市",
        "origin": "福岡県",
        "specialties": "起業,地域ブランディング,観光",
        "migration_year": 2016,
        "migration_from": "福岡県",
        "migration_story": "福岡のベンチャー企業を退職後、日南市の「テレワーク移住」プロジェクトに共感して移住。地域おこし協力隊を経て、地域特産品のECサイトを立ち上げ。現在は年商1500万円の社長として日南市のブランディングにも携わっています。",
        "can_help_with": "地域おこし協力隊の実態、地方での起業・EC事業、宮崎県移住の生活費、地域ブランディングのノウハウ",
        "consultation_method": "オンライン",
        "rating": "4.8",
        "consultation_count": 35,
        "is_available": "true",
        "bio": "地域おこし協力隊→起業家。地方で稼ぐ仕組みの作り方、協力隊制度の活用法を詳しくお話しします。",
    },
    {
        "name": "小林 純",
        "age": 49,
        "gender": "男性",
        "prefecture": "岐阜県",
        "city": "飛騨市",
        "origin": "大阪府",
        "specialties": "古民家再生,DIY,建築",
        "migration_year": 2014,
        "migration_from": "大阪府",
        "migration_story": "建築士として大阪で働いていたが、飛騨の古民家の美しさに魅せられて移住。古民家再生の専門家として、これまで20棟以上の改修に携わってきました。DIYで自分でできる工事と専門家に任せるべき工事の見極め方を熟知しています。",
        "can_help_with": "古民家購入の注意点、DIYリノベーションの範囲と費用、建築確認申請の要否、飛騨の工務店・大工の探し方",
        "consultation_method": "オンライン・対面（岐阜県内）",
        "rating": "4.9",
        "consultation_count": 55,
        "is_available": "true",
        "bio": "一級建築士×古民家再生スペシャリスト。購入前の物件診断から改修計画まで、専門家目線でアドバイスします。",
    },
]


def seed_mentors():
    db = SessionLocal()
    try:
        existing = db.query(Mentor).count()
        if existing > 0:
            print(f"⚠️  既存のメンターデータ {existing}件 を削除して再投入します")
            db.query(Mentor).delete()
            db.commit()

        mentors = [Mentor(**data) for data in MENTOR_DATA]
        db.add_all(mentors)
        db.commit()

        print(f"✅ メンターデータを {len(mentors)}件 投入しました")
        for m in db.query(Mentor).order_by(Mentor.prefecture).all():
            print(f"   👤 {m.name}（{m.age}歳）{m.prefecture} {m.city} — 専門: {m.specialties}")

    except Exception as e:
        db.rollback()
        print(f"❌ エラー: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("👥 メンターダミーデータを投入中...")
    seed_mentors()
