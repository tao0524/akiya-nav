"""
文書取り込みスクリプト（RAGのインデックス構築）
=========================================
使い方:
  # PDFを取り込む
  python scripts/ingest.py --file data/raw/空き家対策特別措置法.pdf --domain law_akiya

  # フォルダ内の全PDFを取り込む
  python scripts/ingest.py --dir data/raw/laws --domain law_akiya

  # テキストファイルを取り込む
  python scripts/ingest.py --file data/raw/sample.txt --domain case_study

  # サンプルデータで動作確認（API Keyなしでテスト可）
  python scripts/ingest.py --sample
"""

import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from app.config import get_settings
from app.database import engine, init_db
from app.models import Document

settings = get_settings()

# サンプルデータ（API Keyなしで動作確認用）
SAMPLE_DOCUMENTS = [
    {
        "domain": "law_akiya",
        "source": "空き家対策特別措置法（サンプル）",
        "content": """空家等対策の推進に関する特別措置法（平成26年法律第127号）

第1条（目的）
この法律は、適切な管理が行われていない空家等が防災、衛生、景観等の地域住民の生活環境に深刻な影響を及ぼしていることに鑑み、地域住民の生命、身体又は財産を保護するとともに、その生活環境の保全を図り、あわせて空家等の活用を促進するため、空家等に関する施策に関し、国による基本指針の策定、市町村による空家等対策計画の作成その他の空家等に関する施策を推進するために必要な事項を定めることにより、空家等に関する施策を総合的かつ計画的に推進し、もって公共の福祉の増進と地域の振興に寄与することを目的とする。

第2条（定義）
この法律において「空家等」とは、建築物又はこれに附属する工作物であって居住その他の使用がなされていないことが常態であるもの及びその敷地（立木その他の土地に定着する物を含む。）をいう。

第14条（特定空家等に対する措置）
市町村長は、特定空家等の所有者等に対し、特定空家等に関し、除却、修繕、立木竹の伐採その他周辺の生活環境の保全を図るために必要な措置をとるよう助言又は指導をすることができる。
2 市町村長は、前項の規定による助言又は指導をした場合において、なお当該特定空家等の状態が改善されないと認めるときは、当該助言又は指導を受けた者に対し、相当の猶予期限を付けて、除却、修繕、立木竹の伐採その他周辺の生活環境の保全を図るために必要な措置をとることを勧告することができる。"""
    },
    {
        "domain": "law_akiya",
        "source": "空き家の相続・固定資産税（サンプル）",
        "content": """相続した空き家と固定資産税について

空き家を相続した場合、相続人は固定資産税の納税義務者となります。

固定資産税の軽減措置について：
建物が建っている土地には「住宅用地特例」が適用され、固定資産税が最大1/6に軽減されます。
ただし、特定空家等に指定された建物については、この特例が適用されなくなる可能性があります。

特定空家に指定されると：
1. 助言・指導：市町村から適切な管理を求める指導が入ります
2. 勧告：指導に従わない場合、固定資産税の住宅用地特例が解除される場合があります
3. 命令：勧告に従わない場合、措置命令が出されます
4. 代執行：命令に従わない場合、行政代執行（強制撤去等）が行われる場合があります

相続放棄との関係：
相続放棄をしても、現実に占有・管理している場合は管理責任が生じる可能性があります。
2023年4月の民法改正により、相続土地国庫帰属制度が創設され、一定の要件を満たす場合に国への帰属申請ができるようになりました。"""
    },
    {
        "domain": "subsidy_national",
        "source": "移住支援金制度（サンプル）",
        "content": """地方への移住支援金制度について

内閣府・総務省が推進する「移住支援事業」

対象者：
東京圏（東京都・埼玉県・千葉県・神奈川県）から地方に移住し、就業・起業した方

支援金額：
- 世帯での移住：最大100万円
- 単身での移住：最大60万円
- 18歳未満の子どもがいる場合：1人あたり最大100万円を加算

主な要件：
1. 移住元：東京圏に5年以上在住していた方
2. 移住先：対象自治体が指定した「移住支援金対象求人」に就職
   または対象となる社会的事業を起こした方
3. 移住後5年以上、移住先に定住する意思がある方

申請先：
移住先の市区町村窓口（担当部署は各自治体で異なります）

注意事項：
- 補助金の予算は年度ごとに設定されており、なくなり次第終了します
- 要件・金額は変更される場合があります。最新情報は移住先自治体にご確認ください。"""
    },
    {
        "domain": "case_study",
        "source": "古民家カフェ成功事例（サンプル）",
        "content": """事例：築100年古民家をカフェ兼交流スペースに再生（岡山県瀬戸内市）

概要：
空き家となっていた築100年超の古民家を、地域住民と移住者が協力してリノベーションし、
カフェ兼地域交流スペースとして再生した事例です。

取り組みのポイント：
1. 地域住民との協力：近隣住民がDIY作業に参加し、コスト削減と愛着形成を同時に実現
2. 補助金の活用：地域創生交付金と空き家改修補助金を組み合わせ、初期費用を大幅削減
3. 多機能な運営：カフェ営業に加え、移住相談窓口・テレワークスペースとしても活用
4. 地元食材の活用：近隣農家と連携し、地元野菜を使ったメニューを提供

成果：
- 開業から1年で地域外からの来客数が約500人に増加
- 移住希望者3組のマッチングに成功
- 廃業寸前だった地元農家2軒の販路拡大に貢献

初期費用の目安：
- 物件取得：0円（空き家バンク経由で無償貸与）
- リノベーション費用：約200万円（補助金活用後の実質負担は約80万円）
- 設備・備品：約50万円

学べること：
補助金を組み合わせることで、初期費用を大幅に抑えられます。
地域住民を巻き込むことで、「外から来た人のもの」ではなく「地域のもの」として受け入れてもらいやすくなります。"""
    },
]


def ingest_sample_data():
    """API Keyなしで動作確認できるサンプルデータを投入"""
    print("📦 サンプルデータを投入します...")

    # DBを初期化
    init_db()

    # テキスト分割設定
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    # 埋め込みモデル初期化
    print("🔄 埋め込みモデルを初期化中...")
    embeddings_model = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key
    )

    with Session(engine) as db:
        total_chunks = 0
        for doc_data in SAMPLE_DOCUMENTS:
            # テキストをチャンクに分割
            chunks = splitter.split_text(doc_data["content"])

            for i, chunk in enumerate(chunks):
                # ベクトル埋め込みを生成
                embedding = embeddings_model.embed_query(chunk)

                # DBに保存
                doc = Document(
                    content=chunk,
                    embedding=embedding,
                    domain=doc_data["domain"],
                    source=doc_data["source"],
                    source_page=i
                )
                db.add(doc)
                total_chunks += 1
                print(f"  ✓ [{doc_data['domain']}] {doc_data['source']} chunk {i+1}/{len(chunks)}")

        db.commit()
        print(f"\n✅ サンプルデータ投入完了: {total_chunks}チャンクを登録しました")


def ingest_pdf(file_path: str, domain: str):
    """PDFファイルを読み込んでRAGに投入"""
    print(f"📄 PDF取り込み: {file_path} → ドメイン: {domain}")

    loader = PyPDFLoader(file_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    embeddings_model = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key
    )

    source_name = Path(file_path).name

    with Session(engine) as db:
        total_chunks = 0
        for page in pages:
            chunks = splitter.split_text(page.page_content)
            for chunk in chunks:
                if not chunk.strip():
                    continue
                embedding = embeddings_model.embed_query(chunk)
                doc = Document(
                    content=chunk,
                    embedding=embedding,
                    domain=domain,
                    source=source_name,
                    source_page=page.metadata.get("page", 0)
                )
                db.add(doc)
                total_chunks += 1

        db.commit()
        print(f"✅ 完了: {total_chunks}チャンクを登録しました")


def ingest_text(file_path: str, domain: str):
    """テキストファイルを読み込んでRAGに投入"""
    print(f"📝 テキスト取り込み: {file_path} → ドメイン: {domain}")

    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    embeddings_model = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key
    )

    source_name = Path(file_path).name

    with Session(engine) as db:
        total_chunks = 0
        for doc in documents:
            chunks = splitter.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                embedding = embeddings_model.embed_query(chunk)
                db_doc = Document(
                    content=chunk,
                    embedding=embedding,
                    domain=domain,
                    source=source_name,
                    source_page=i
                )
                db.add(db_doc)
                total_chunks += 1

        db.commit()
        print(f"✅ 完了: {total_chunks}チャンクを登録しました")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG文書取り込みスクリプト")
    parser.add_argument("--sample", action="store_true", help="サンプルデータを投入")
    parser.add_argument("--file", type=str, help="取り込むファイルパス")
    parser.add_argument("--dir", type=str, help="取り込むフォルダパス")
    parser.add_argument("--domain", type=str, default="default", help="ドメインタグ")
    args = parser.parse_args()

    if args.sample:
        ingest_sample_data()
    elif args.file:
        init_db()
        path = args.file
        if path.endswith(".pdf"):
            ingest_pdf(path, args.domain)
        else:
            ingest_text(path, args.domain)
    elif args.dir:
        init_db()
        dir_path = Path(args.dir)
        for file_path in dir_path.glob("**/*"):
            if file_path.suffix.lower() == ".pdf":
                ingest_pdf(str(file_path), args.domain)
            elif file_path.suffix.lower() in [".txt", ".md"]:
                ingest_text(str(file_path), args.domain)
    else:
        parser.print_help()
