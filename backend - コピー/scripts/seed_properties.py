"""
空き家マップ用ダミーデータ投入スクリプト
=========================================
使い方:
  docker-compose exec backend python scripts/seed_properties.py

全国の代表的な空き家・移住先エリアのサンプル物件を50件登録します。
後で国交省オープンデータや空き家バンクのCSVに差し替え可能な設計です。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from sqlalchemy.orm import Session
from app.database import engine, init_db
from app.models import Property

# =============================================
# サンプル物件データ（実在エリアの代表座標ベース）
# =============================================

SAMPLE_PROPERTIES = [
    # --- 岡山県 ---
    {
        "title": "古民家（築90年・蔵付き）",
        "description": "明治期築の風格ある古民家。蔵と母屋の2棟構成。リノベーション済みの水回りあり。カフェ・ゲストハウスへの転用実績が多いエリア。",
        "prefecture": "岡山県", "city": "真庭市",
        "address": "岡山県真庭市勝山地区",
        "latitude": "35.0495", "longitude": "133.6833",
        "property_type": "house", "structure": "木造",
        "area_m2": "180", "land_area_m2": "450", "built_year": 1930,
        "price": 0, "price_type": "free",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "元診療所（平屋・広間付き）",
        "description": "廃業した個人診療所を空き家バンクに登録。待合室の広間がそのまま残り、コワーキングスペースに最適。駐車場10台分あり。",
        "prefecture": "岡山県", "city": "美作市",
        "address": "岡山県美作市作東地区",
        "latitude": "34.9973", "longitude": "134.1644",
        "property_type": "commercial", "structure": "木造",
        "area_m2": "220", "land_area_m2": "600", "built_year": 1965,
        "price": 200, "price_type": "sale",
        "status": "available",
        "potential_cafe": "medium", "potential_lodging": "low",
        "potential_office": "high", "potential_farm": "low",
        "source": "sample",
    },
    # --- 島根県 ---
    {
        "title": "農家住宅（田畑付き）",
        "description": "母屋＋農具小屋＋田畑1500㎡のセット。自給自足ライフや農業体験施設に最適。近隣農家が農作業を手伝ってくれるコミュニティあり。",
        "prefecture": "島根県", "city": "雲南市",
        "address": "島根県雲南市木次町",
        "latitude": "35.2802", "longitude": "132.9088",
        "property_type": "house", "structure": "木造",
        "area_m2": "130", "land_area_m2": "1500", "built_year": 1955,
        "price": 100, "price_type": "sale",
        "status": "available",
        "potential_cafe": "low", "potential_lodging": "medium",
        "potential_office": "low", "potential_farm": "high",
        "source": "sample",
    },
    {
        "title": "海辺の古民家（眺望抜群）",
        "description": "日本海を一望できる高台の古民家。ダイビングスポットまで車5分。民泊・グランピング施設として高いポテンシャル。",
        "prefecture": "島根県", "city": "出雲市",
        "address": "島根県出雲市大社町",
        "latitude": "35.4024", "longitude": "132.6869",
        "property_type": "house", "structure": "木造",
        "area_m2": "95", "land_area_m2": "280", "built_year": 1970,
        "price": 3, "price_type": "rent",
        "rent": 3,
        "status": "available",
        "potential_cafe": "medium", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
    },
    # --- 高知県 ---
    {
        "title": "元旅館（温泉権利付き）",
        "description": "1970年代に廃業した温泉旅館。源泉権利が残っており、小規模旅館・サウナ施設として再生可能。要リノベ。",
        "prefecture": "高知県", "city": "四万十市",
        "address": "高知県四万十市西土佐",
        "latitude": "33.0179", "longitude": "132.9127",
        "property_type": "commercial", "structure": "木造",
        "area_m2": "480", "land_area_m2": "900", "built_year": 1968,
        "price": 800, "price_type": "negotiable",
        "status": "available",
        "potential_cafe": "low", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "築50年の農家住宅",
        "description": "四万十川沿いの静かな農村エリア。カヌーや釣りが楽しめる環境。都会からのワーケーション需要が高いエリア。",
        "prefecture": "高知県", "city": "四万十町",
        "address": "高知県高岡郡四万十町窪川",
        "latitude": "33.2034", "longitude": "133.0883",
        "property_type": "house", "structure": "木造",
        "area_m2": "110", "land_area_m2": "350", "built_year": 1975,
        "price": 0, "price_type": "free",
        "status": "available",
        "potential_cafe": "medium", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "medium",
        "source": "sample",
    },
    # --- 長野県 ---
    {
        "title": "信州古民家（スキー場5km）",
        "description": "白馬エリアの古民家。冬はスキー客、夏は登山客で年間需要が見込める。民泊・ゲストハウスとして即活用可能なポテンシャル。",
        "prefecture": "長野県", "city": "白馬村",
        "address": "長野県北安曇郡白馬村北城",
        "latitude": "36.6983", "longitude": "137.8603",
        "property_type": "house", "structure": "木造",
        "area_m2": "160", "land_area_m2": "520", "built_year": 1960,
        "price": 600, "price_type": "sale",
        "status": "available",
        "potential_cafe": "medium", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "元そば屋（設備そのまま）",
        "description": "製麺設備・厨房機器が残った状態で廃業。そば屋としての再開か、カフェへの転換が見込める。国道沿いで視認性良好。",
        "prefecture": "長野県", "city": "飯田市",
        "address": "長野県飯田市座光寺",
        "latitude": "35.5143", "longitude": "137.8218",
        "property_type": "commercial", "structure": "木造",
        "area_m2": "85", "land_area_m2": "200", "built_year": 1982,
        "price": 5, "price_type": "rent",
        "rent": 5,
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "low",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    # --- 秋田県 ---
    {
        "title": "武家屋敷跡（文化財候補）",
        "description": "江戸期の武家屋敷の面影が残る大型古民家。文化財指定を受ければ補助金活用が可能。地域の観光資源として期待大。",
        "prefecture": "秋田県", "city": "横手市",
        "address": "秋田県横手市増田地区",
        "latitude": "39.1936", "longitude": "140.5636",
        "property_type": "house", "structure": "木造",
        "area_m2": "300", "land_area_m2": "800", "built_year": 1850,
        "price": 0, "price_type": "negotiable",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "農地付き空き家（秋田杉の里）",
        "description": "秋田杉の産地・能代エリアの農家住宅。林業・木工クラフトの起業拠点として注目。移住支援金の対象エリア。",
        "prefecture": "秋田県", "city": "能代市",
        "address": "秋田県能代市二ツ井町",
        "latitude": "40.1894", "longitude": "140.3278",
        "property_type": "house", "structure": "木造",
        "area_m2": "120", "land_area_m2": "2000", "built_year": 1963,
        "price": 150, "price_type": "sale",
        "status": "available",
        "potential_cafe": "low", "potential_lodging": "medium",
        "potential_office": "low", "potential_farm": "high",
        "source": "sample",
    },
    # --- 兵庫県 ---
    {
        "title": "淡路島の海辺ヴィラ",
        "description": "大阪・神戸から明石大橋で1時間。オーシャンビューのリゾート型空き家。観光農園・グランピング施設に最適なロケーション。",
        "prefecture": "兵庫県", "city": "淡路市",
        "address": "兵庫県淡路市岩屋",
        "latitude": "34.5931", "longitude": "134.9209",
        "property_type": "house", "structure": "RC",
        "area_m2": "140", "land_area_m2": "600", "built_year": 1990,
        "price": 1200, "price_type": "sale",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "篠山の丹波古民家",
        "description": "丹波篠山の黒豆・松茸の産地。古民家カフェや農家レストランとして成功事例多数のエリア。観光客の立ち寄り需要が安定。",
        "prefecture": "兵庫県", "city": "丹波篠山市",
        "address": "兵庫県丹波篠山市河原町",
        "latitude": "35.0738", "longitude": "135.2271",
        "property_type": "house", "structure": "木造",
        "area_m2": "200", "land_area_m2": "700", "built_year": 1920,
        "price": 400, "price_type": "sale",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "high",
        "source": "sample",
    },
    # --- 大分県 ---
    {
        "title": "温泉街の空き店舗",
        "description": "由布院温泉街から徒歩5分の元土産物店。観光客動線上に位置し、カフェ・雑貨店として高ポテンシャル。賃料交渉可。",
        "prefecture": "大分県", "city": "由布市",
        "address": "大分県由布市湯布院町川上",
        "latitude": "33.2554", "longitude": "131.3713",
        "property_type": "commercial", "structure": "木造",
        "area_m2": "60", "land_area_m2": "90", "built_year": 1978,
        "price": 8, "price_type": "rent",
        "rent": 8,
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "low",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "農家住宅（みかん畑付き）",
        "description": "豊後水道を望む傾斜地に建つ農家住宅。みかん畑1200㎡が付属し、農業体験・観光農園として活用可能。",
        "prefecture": "大分県", "city": "臼杵市",
        "address": "大分県臼杵市野津町",
        "latitude": "32.9918", "longitude": "131.7979",
        "property_type": "house", "structure": "木造",
        "area_m2": "90", "land_area_m2": "1200", "built_year": 1972,
        "price": 50, "price_type": "sale",
        "status": "available",
        "potential_cafe": "low", "potential_lodging": "medium",
        "potential_office": "low", "potential_farm": "high",
        "source": "sample",
    },
    # --- 北海道 ---
    {
        "title": "廃校活用型古民家（北海道）",
        "description": "廃校となった小学校の教員住宅を空き家バンクに登録。大きな庭と農地付き。北海道移住者に人気のエリア。",
        "prefecture": "北海道", "city": "富良野市",
        "address": "北海道富良野市山部",
        "latitude": "43.3423", "longitude": "142.3853",
        "property_type": "house", "structure": "木造",
        "area_m2": "110", "land_area_m2": "3000", "built_year": 1968,
        "price": 200, "price_type": "sale",
        "status": "available",
        "potential_cafe": "medium", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "high",
        "source": "sample",
    },
    {
        "title": "函館山麓の洋館",
        "description": "明治期の洋館を改修した歴史的建造物。函館観光の人気エリアに位置し、カフェ・ギャラリーとして観光客集客が期待できる。",
        "prefecture": "北海道", "city": "函館市",
        "address": "北海道函館市元町",
        "latitude": "41.7700", "longitude": "140.7119",
        "property_type": "house", "structure": "木造",
        "area_m2": "170", "land_area_m2": "320", "built_year": 1910,
        "price": 1500, "price_type": "sale",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    # --- 沖縄県 ---
    {
        "title": "赤瓦の琉球古民家",
        "description": "石垣に囲まれた伝統的な琉球古民家。ゲストハウス・民泊として既に近隣での成功事例多数。インバウンド需要が高い。",
        "prefecture": "沖縄県", "city": "読谷村",
        "address": "沖縄県中頭郡読谷村渡具知",
        "latitude": "26.3938", "longitude": "127.7454",
        "property_type": "house", "structure": "木造",
        "area_m2": "85", "land_area_m2": "250", "built_year": 1940,
        "price": 800, "price_type": "sale",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "名護の農地付き空き家",
        "description": "北部農業エリアの広い農地付き住宅。パイナップルやシークワーサーの産地。農業体験ツーリズムに最適。",
        "prefecture": "沖縄県", "city": "名護市",
        "address": "沖縄県名護市勝山",
        "latitude": "26.6167", "longitude": "127.9869",
        "property_type": "house", "structure": "RC",
        "area_m2": "100", "land_area_m2": "2500", "built_year": 1988,
        "price": 500, "price_type": "sale",
        "status": "available",
        "potential_cafe": "low", "potential_lodging": "medium",
        "potential_office": "low", "potential_farm": "high",
        "source": "sample",
    },
    # --- 京都府 ---
    {
        "title": "京町家（1棟貸し対応済み）",
        "description": "西陣エリアの格子戸が美しい京町家。1棟貸し民泊のライセンス取得済み。外国人観光客の需要が特に高いエリア。",
        "prefecture": "京都府", "city": "京都市",
        "address": "京都府京都市上京区西陣",
        "latitude": "35.0276", "longitude": "135.7451",
        "property_type": "house", "structure": "木造",
        "area_m2": "120", "land_area_m2": "80", "built_year": 1925,
        "price": 35, "price_type": "rent",
        "rent": 35,
        "status": "negotiating",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "medium", "potential_farm": "low",
        "source": "sample",
    },
    {
        "title": "美山かやぶき集落の空き家",
        "description": "国の重要伝統的建造物群保存地区「美山かやぶきの里」周辺の空き家。景観規制あり。補助金の活用で大規模修繕も可能。",
        "prefecture": "京都府", "city": "南丹市",
        "address": "京都府南丹市美山町",
        "latitude": "35.3083", "longitude": "135.5369",
        "property_type": "house", "structure": "木造",
        "area_m2": "145", "land_area_m2": "500", "built_year": 1870,
        "price": 0, "price_type": "negotiable",
        "status": "available",
        "potential_cafe": "high", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "medium",
        "source": "sample",
    },
]

# 交渉中・成約済みのサンプルも数件追加
CONTRACTED_SAMPLES = [
    {
        "title": "岡山・蒜山高原のログハウス（成約済み）",
        "prefecture": "岡山県", "city": "真庭市",
        "latitude": "35.2283", "longitude": "133.5456",
        "property_type": "house", "structure": "木造",
        "area_m2": "90", "land_area_m2": "800", "built_year": 1995,
        "price": 1000, "price_type": "sale", "rent": 0,
        "status": "contracted",
        "potential_cafe": "medium", "potential_lodging": "high",
        "potential_office": "low", "potential_farm": "low",
        "source": "sample",
        "description": "成約済みの参考事例",
        "address": "岡山県真庭市蒜山地区",
        "structure": "木造",
    },
]


def seed():
    print("🌱 空き家マップ用サンプル物件を登録します...")
    init_db()

    all_properties = SAMPLE_PROPERTIES + CONTRACTED_SAMPLES

    with Session(engine) as db:
        # 既存のサンプルデータを削除
        deleted = db.query(Property).filter(Property.source == "sample").delete()
        db.commit()
        if deleted:
            print(f"  🗑️  既存のサンプルデータ {deleted}件を削除しました")

        # 新しいデータを登録
        for data in all_properties:
            prop = Property(**data)
            if "rent" not in data:
                prop.rent = 0
            db.add(prop)

        db.commit()
        total = db.query(Property).filter(Property.source == "sample").count()
        print(f"✅ 登録完了: {total}件の物件を追加しました")

        # サマリー表示
        from sqlalchemy import text
        result = db.execute(text(
            "SELECT prefecture, COUNT(*) as c FROM properties WHERE source='sample' GROUP BY prefecture ORDER BY c DESC"
        ))
        print("\n📊 都道府県別:")
        for row in result:
            print(f"  {row.prefecture}: {row.c}件")


if __name__ == "__main__":
    seed()
