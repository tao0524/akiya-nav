"""
地域情報のダミーデータを投入するスクリプト。
Phase 3: 移住サポート機能で使用。

使用方法:
    docker-compose exec backend python scripts/seed_regions.py
"""

import sys
import os
sys.path.insert(0, "/app")

from app.database import SessionLocal, engine
from app.models import Base, RegionInfo

REGION_DATA = [
    # ===== 北海道・東北 =====
    {
        "prefecture": "北海道",
        "city": "ニセコ町",
        "population": 5200,
        "area_km2": "197.13",
        "climate": "冷涼。夏は涼しく快適。冬は豪雪地帯（積雪2〜3m）。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（単身50万円）、家賃補助月3万円×2年、空き家改修補助上限200万円",
        "job_support": "スキーリゾート・観光業・農業の求人多数。テレワーク移住歓迎。",
        "industry": "観光（スキーリゾート）・農業・酪農",
        "attraction": "世界有数のパウダースノー。豊かな自然。インバウンド需要による経済活性化。移住者コミュニティが活発。",
        "challenge": "冬季の除雪・暖房費負担。医療機関が少ない。公共交通が限定的。",
        "score_nature": 5,
        "score_convenience": 2,
        "score_subsidy": 4,
        "score_community": 4,
    },
    {
        "prefecture": "秋田県",
        "city": "横手市",
        "population": 88000,
        "area_km2": "692.81",
        "climate": "内陸型。夏は高温多湿、冬は豪雪（かまくらで有名）。",
        "subsidy_max": 150,
        "subsidy_detail": "移住支援金150万円（世帯）、子育て支援金50万円（18歳未満の子1人につき）、テレワーク移住補助あり",
        "job_support": "農業・製造業への就農・就職支援。マッチングイベント年4回開催。",
        "industry": "農業（お米・きりたんぽ）・製造業・医療福祉",
        "attraction": "全国有数の米どころ。食文化が豊か。横手焼きそば・比内地鶏など。地域のつながりが強い。",
        "challenge": "豪雪による生活コスト増。人口減少が進む。若者の雇用が限られる。",
        "score_nature": 4,
        "score_convenience": 3,
        "score_subsidy": 5,
        "score_community": 4,
    },
    {
        "prefecture": "山形県",
        "city": "鶴岡市",
        "population": 120000,
        "area_km2": "1311.54",
        "climate": "日本海側。冬は雪が多いが、内陸ほどではない。夏は庄内平野に暖かい風が吹く。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、空き家バンク活用補助上限100万円、子育て世代向け定住補助あり",
        "job_support": "農業・水産業・ものづくり産業への転職支援。慶應大学先端研究所が立地。",
        "industry": "農業（庄内米・だだちゃ豆）・水産業・ものづくり",
        "attraction": "ユネスコ食文化創造都市認定。自然豊か（出羽三山・最上川）。東北の中では比較的アクセス良好。",
        "challenge": "東京まで新幹線＋在来線で約3時間。冬季の移動が大変。",
        "score_nature": 4,
        "score_convenience": 3,
        "score_subsidy": 4,
        "score_community": 3,
    },

    # ===== 関東・甲信越 =====
    {
        "prefecture": "長野県",
        "city": "松本市",
        "population": 240000,
        "area_km2": "978.77",
        "climate": "内陸型高原気候。夏は涼しく冬は寒い。年間晴天日数が多い。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、テレワーク移住補助50万円、空き家改修最大200万円、子育て支援充実",
        "job_support": "IT・製造業・観光業の求人。テレワーカー向けコワーキングスペースあり。",
        "industry": "製造業・観光・農業（果樹・野菜）",
        "attraction": "北アルプスなど山岳観光の拠点。都市機能が充実した地方都市。東京まで約2時間。移住者が多く溶け込みやすい。",
        "challenge": "家賃・地価が長野県内では高め。冬の凍結路面・除雪が必要。",
        "score_nature": 5,
        "score_convenience": 4,
        "score_subsidy": 4,
        "score_community": 4,
    },
    {
        "prefecture": "長野県",
        "city": "飯山市",
        "population": 19000,
        "area_km2": "202.44",
        "climate": "日本有数の豪雪地帯。夏は涼しく快適。",
        "subsidy_max": 200,
        "subsidy_detail": "移住支援金200万円（世帯・条件あり）、テレワーク移住特別補助、農業参入支援、空き家改修補助300万円",
        "job_support": "農業（特産品：花き・野菜）への就農支援。テレワーク移住を積極誘致。",
        "industry": "農業・観光（スキーリゾート）・木工・仏壇製造",
        "attraction": "北陸新幹線（飯山駅）で金沢1時間・東京1.5時間。豊かな雪国文化。補助金が県内最高水準。",
        "challenge": "豪雪による暮らしの負担大。商業施設が少ない。",
        "score_nature": 5,
        "score_convenience": 2,
        "score_subsidy": 5,
        "score_community": 3,
    },
    {
        "prefecture": "山梨県",
        "city": "北杜市",
        "population": 44000,
        "area_km2": "602.93",
        "climate": "高原性気候。年間晴天日数が日本有数。夏涼しく冬寒い。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、空き家活用補助最大150万円、農業参入支援制度あり",
        "job_support": "農業・ワイナリー・アウトドア関連の就業支援。東京からの週末移住も人気。",
        "industry": "農業（野菜・果樹）・観光・ワイン産業",
        "attraction": "晴天率全国トップ。八ヶ岳・南アルプスに囲まれた絶景。東京から特急で1.5時間。移住者コミュニティが非常に活発。",
        "challenge": "公共交通が不便（車必須）。医療機関が少ない。物価はやや高め。",
        "score_nature": 5,
        "score_convenience": 2,
        "score_subsidy": 3,
        "score_community": 5,
    },

    # ===== 中部・関西 =====
    {
        "prefecture": "岐阜県",
        "city": "飛騨市",
        "population": 23000,
        "area_km2": "792.36",
        "climate": "内陸山岳気候。夏涼しく冬は豪雪。",
        "subsidy_max": 150,
        "subsidy_detail": "移住支援金150万円（世帯）、家賃補助2万円×2年、空き家改修補助200万円、林業就業支援金あり",
        "job_support": "林業・観光業・木工業への就業支援。飛騨の家具・木工産業が盛ん。",
        "industry": "林業・木工・観光（古川・白川郷）・農業",
        "attraction": "世界遺産・白川郷が近い。日本の原風景が残る古い町並み。ものづくり文化が豊か。移住者向けの受け入れ体制が整っている。",
        "challenge": "名古屋まで車で2時間。冬季は道路閉鎖の可能性。高齢化・人口減少が課題。",
        "score_nature": 5,
        "score_convenience": 2,
        "score_subsidy": 4,
        "score_community": 4,
    },
    {
        "prefecture": "兵庫県",
        "city": "養父市",
        "population": 22000,
        "area_km2": "422.91",
        "climate": "内陸型。夏は盆地性で暑く、冬は雪が積もる。",
        "subsidy_max": 120,
        "subsidy_detail": "移住支援金120万円（世帯）、農業参入補助・農地取得支援、空き家バンク活用補助100万円",
        "job_support": "農業（農地中間管理機構の活用で農地取得しやすい）。国家戦略特区で農業参入規制緩和済み。",
        "industry": "農業・林業・観光（但馬高原）",
        "attraction": "国家戦略特区「農業特区」として農業参入が特に容易。大阪・神戸から約2時間で行ける自然豊かな環境。",
        "challenge": "公共交通が少ない。冬季の積雪。若者の雇用機会が限られる。",
        "score_nature": 4,
        "score_convenience": 2,
        "score_subsidy": 4,
        "score_community": 3,
    },

    # ===== 中国・四国 =====
    {
        "prefecture": "島根県",
        "city": "邑南町",
        "population": 9000,
        "area_km2": "419.86",
        "climate": "山陰型。冬は曇りがちで雪が降る。夏は比較的過ごしやすい。",
        "subsidy_max": 200,
        "subsidy_detail": "移住支援金200万円（世帯・就業条件あり）、A級グルメ移住プロジェクト補助、農業参入支援、起業支援金あり",
        "job_support": "「A級グルメのまち」として食のまちづくりを推進。飲食業・農業への転職支援が充実。",
        "industry": "農業・畜産・林業・食品加工",
        "attraction": "「A級グルメのまち」で食文化が豊か。移住支援が全国的に有名で移住者数も増加中。自然豊か。",
        "challenge": "広島市まで約2時間。公共交通がほぼなく車必須。",
        "score_nature": 4,
        "score_convenience": 1,
        "score_subsidy": 5,
        "score_community": 5,
    },
    {
        "prefecture": "岡山県",
        "city": "真庭市",
        "population": 43000,
        "area_km2": "828.10",
        "climate": "内陸型。夏は高温、冬は積雪あり。年間を通じて降水量が少ない。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、空き家改修補助最大150万円、農業就農支援、子育て支援制度充実",
        "job_support": "農業・林業・バイオマス産業への就業支援。リモートワーク環境整備中。",
        "industry": "農業・林業・バイオマス・観光（湯原温泉）",
        "attraction": "バイオマス産業で全国的に注目。湯原温泉など観光資源豊か。岡山市から車1時間。",
        "challenge": "公共交通が不便。若者の流出が続く。",
        "score_nature": 4,
        "score_convenience": 2,
        "score_subsidy": 3,
        "score_community": 3,
    },
    {
        "prefecture": "高知県",
        "city": "四万十市",
        "population": 32000,
        "area_km2": "642.32",
        "climate": "温暖。四万十川流域は夏に非常に高温になる（日本記録41℃）。冬は温暖。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、漁業・農業就業支援、テレワーク移住補助あり、空き家バンク活用補助",
        "job_support": "漁業・農業・観光への就業支援。「四万十川」ブランドを活かした移住プロモーション。",
        "industry": "漁業・農業（栗・生姜）・観光",
        "attraction": "「日本最後の清流」四万十川。温暖な気候で農業・漁業がしやすい。食材が豊か。",
        "challenge": "高知市から車1.5時間。医療機関が少ない。台風・水害リスクあり。",
        "score_nature": 5,
        "score_convenience": 1,
        "score_subsidy": 3,
        "score_community": 3,
    },

    # ===== 九州・沖縄 =====
    {
        "prefecture": "大分県",
        "city": "由布市",
        "population": 33000,
        "area_km2": "319.44",
        "climate": "温暖。湯布院盆地は霧が多い。夏は涼しく冬は寒い（標高が高い）。",
        "subsidy_max": 100,
        "subsidy_detail": "移住支援金100万円（世帯）、温泉旅館・観光業への転職支援、農業参入補助あり",
        "job_support": "観光業（湯布院温泉）・農業・林業。福岡から車1時間の立地でUIJターン者が増加。",
        "industry": "観光（湯布院温泉）・農業・林業",
        "attraction": "湯布院温泉で有名。温泉付きの住宅も多い。福岡へのアクセス良好。インバウンドによる経済活性化。",
        "challenge": "観光地のため生活コストが高め。観光シーズンは渋滞。住宅価格が上昇中。",
        "score_nature": 5,
        "score_convenience": 3,
        "score_subsidy": 3,
        "score_community": 3,
    },
    {
        "prefecture": "宮崎県",
        "city": "日南市",
        "population": 52000,
        "area_km2": "526.90",
        "climate": "温暖。日照時間が長い。台風の通り道。",
        "subsidy_max": 150,
        "subsidy_detail": "移住支援金150万円（世帯）、テレワーク移住補助50万円、起業支援金最大100万円、子育て支援充実",
        "job_support": "IT企業誘致・テレワーカー誘致に積極的。農業・水産業の就業支援も充実。",
        "industry": "農業・水産業・観光・IT（誘致企業）",
        "attraction": "温暖で年中過ごしやすい。テレワーク移住施策が全国的に有名（ITベンチャー誘致成功）。食材（マグロ・地鶏）が豊か。",
        "challenge": "台風リスク。鹿児島・宮崎市への移動に時間がかかる。",
        "score_nature": 4,
        "score_convenience": 2,
        "score_subsidy": 5,
        "score_community": 4,
    },
    {
        "prefecture": "沖縄県",
        "city": "うるま市",
        "population": 122000,
        "area_km2": "86.38",
        "climate": "亜熱帯海洋性気候。年中温暖。台風が多い。",
        "subsidy_max": 80,
        "subsidy_detail": "移住支援金80万円（世帯）、IT・観光業への就業支援、子育て支援制度あり",
        "job_support": "IT産業・観光・医療福祉の求人多数。那覇へのアクセスも良好。",
        "industry": "観光・IT・農業（さとうきび）・水産業",
        "attraction": "温暖な気候と美しい海。那覇空港から約30分でアクセス良好（沖縄本島内）。都市機能も充実。",
        "challenge": "物価が全国的に高い。台風シーズンの影響。家賃が上昇傾向。",
        "score_nature": 5,
        "score_convenience": 3,
        "score_subsidy": 3,
        "score_community": 3,
    },
]


def seed_regions():
    db = SessionLocal()
    try:
        # 既存データを削除
        existing = db.query(RegionInfo).count()
        if existing > 0:
            print(f"⚠️  既存の地域データ {existing}件 を削除して再投入します")
            db.query(RegionInfo).delete()
            db.commit()

        # データ投入
        regions = [RegionInfo(**data) for data in REGION_DATA]
        db.add_all(regions)
        db.commit()

        print(f"✅ 地域情報データを {len(regions)}件 投入しました")

        # 投入確認
        for region in db.query(RegionInfo).order_by(RegionInfo.prefecture).all():
            print(f"   📍 {region.prefecture} {region.city or ''} — 支援金上限: {region.subsidy_max}万円")

    except Exception as e:
        db.rollback()
        print(f"❌ エラー: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌏 地域情報ダミーデータを投入中...")
    seed_regions()
