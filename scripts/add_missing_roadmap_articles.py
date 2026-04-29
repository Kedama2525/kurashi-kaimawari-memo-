#!/usr/bin/env python3
"""Create missing roadmap articles and product JSON.

Product articles fetch three Rakuten affiliate candidates. Guide articles are
static Markdown with internal links to existing product roundups.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
WORK_ROOT = Path("/Users/user/work/楽天アフィリエイト")
SITE_ROOT = WORK_ROOT / "kurashi-kaimawari-memo"
ARTICLES_ROOT = SITE_ROOT / "src/content/articles"
PRODUCTS_ROOT = SITE_ROOT / "src/content/products"
ENV_FILES = (
    WORK_ROOT / "02_初期設定/rakuten_api_config.env",
    WORK_ROOT / "02_初期設定/rakuten_account_config.env",
)


@dataclass(frozen=True)
class ProductArticle:
    category: str
    slug: str
    title: str
    description: str
    keyword: str
    capacity: str
    intro: str
    patterns: tuple[str, str, str]
    related: tuple[str, ...]


@dataclass(frozen=True)
class GuideArticle:
    category: str
    slug: str
    type: str
    title: str
    description: str
    points: tuple[str, str, str, str]
    sections: tuple[tuple[str, str], ...]
    related: tuple[str, ...]


PRODUCT_ARTICLES: tuple[ProductArticle, ...] = (
    ProductArticle(
        "food-drink",
        "rice",
        "楽天で買えるお米まとめ買いおすすめ",
        "楽天市場で買えるお米を、無洗米・容量・保存しやすさと一緒に整理します。",
        "米 10kg 無洗米 送料無料",
        "容量、精米日、無洗米かどうか、保管場所",
        "お米は重く、楽天で買うと配送メリットが大きい食品です。",
        ("家族用に10kg前後をまとめて買いたい人", "無洗米で炊飯の手間を減らしたい人", "精米日や産地も見て選びたい人"),
        ("rakuten-marathon/food-drink-marathon", "food-drink/food-stock"),
    ),
    ProductArticle(
        "food-drink",
        "canned-food",
        "楽天で買える缶詰まとめ買いおすすめ",
        "楽天市場で買える缶詰を、保存期間・味の種類・使い切りやすさと一緒に整理します。",
        "缶詰 まとめ買い 常温保存",
        "個数、味の種類、賞味期限、保存場所",
        "缶詰は常温保存しやすく、普段の食事にも備蓄にも使いやすい食品です。",
        ("備蓄用の常温食品を増やしたい人", "魚や惣菜を手軽に足したい人", "賞味期限の長い食品を選びたい人"),
        ("rakuten-marathon/stock-items", "food-drink/food-stock"),
    ),
    ProductArticle(
        "food-drink",
        "staple-food",
        "楽天で買える常備食まとめ買いおすすめ",
        "楽天市場で買える常備食を、パックご飯・麺類・レトルトの使い分けと一緒に整理します。",
        "保存食 セット 常温保存 非常食",
        "保存方法、食数、賞味期限、調理の手軽さ",
        "常備食は忙しい日と非常時の両方で使えるため、使い切りながら補充しやすいジャンルです。",
        ("忙しい日の食事をラクにしたい人", "ローリングストックを始めたい人", "家族で食べやすい味を選びたい人"),
        ("food-drink/retort-food", "rakuten-marathon/stock-items"),
    ),
    ProductArticle(
        "kitchen",
        "plastic-wrap",
        "楽天で買えるラップまとめ買いおすすめ",
        "楽天市場で買える食品用ラップを、幅・長さ・電子レンジ対応と一緒に整理します。",
        "食品ラップ まとめ買い 22cm 30cm",
        "幅、長さ、本数、電子レンジ対応",
        "食品用ラップは毎日使いやすく、まとめ買いしても消費しやすいキッチン消耗品です。",
        ("毎日料理をする家庭", "22cmと30cmを使い分けたい人", "業務用や長巻きを選びたい人"),
        ("kitchen/kitchen-consumables", "rakuten-marathon/1000yen-items"),
    ),
    ProductArticle(
        "kitchen",
        "storage-containers",
        "楽天で買える保存容器まとめ買いおすすめ",
        "楽天市場で買える保存容器を、サイズ展開・電子レンジ対応・収納しやすさと一緒に整理します。",
        "保存容器 セット 電子レンジ対応 楽天",
        "サイズ、個数、電子レンジ対応、重ねやすさ",
        "保存容器は作り置きや冷蔵庫整理に使いやすく、セット買いでそろえやすいキッチン用品です。",
        ("作り置きをしたい人", "冷蔵庫内を整理したい人", "サイズ違いをまとめてそろえたい人"),
        ("kitchen/kitchen-consumables", "food-drink/food-stock"),
    ),
    ProductArticle(
        "pet",
        "pet-sheets",
        "楽天で買えるペットシーツまとめ買いおすすめ",
        "楽天市場で買えるペットシーツを、薄型・厚型・枚数・吸収力と一緒に整理します。",
        "ペットシーツ まとめ買い レギュラー ワイド",
        "サイズ、枚数、薄型/厚型、吸収力",
        "ペットシーツは消費ペースが読みやすく、楽天でまとめ買いしやすいペット日用品です。",
        ("犬用に枚数を多めに確保したい人", "薄型でこまめに交換したい人", "厚型で吸収力を重視したい人"),
        ("pet/pet-daily-goods", "rakuten-marathon/stock-items"),
    ),
    ProductArticle(
        "pet",
        "pet-food",
        "楽天で買えるペットフードまとめ買いおすすめ",
        "楽天市場で買えるペットフードを、犬用・猫用・容量・いつもの商品かどうかと一緒に整理します。",
        "ペットフード ドッグフード キャットフード まとめ買い",
        "対象、容量、賞味期限、いつものフードかどうか",
        "ペットフードは重い商品が多く、普段のフードが決まっている場合は楽天で補充しやすいです。",
        ("いつものフードを切らしたくない人", "重い袋を家まで届けてほしい人", "犬猫別に容量を見て選びたい人"),
        ("pet/pet-daily-goods", "rakuten-marathon/stock-items"),
    ),
    ProductArticle(
        "pet",
        "odor-bags",
        "楽天で買えるペット用消臭袋まとめ買いおすすめ",
        "楽天市場で買えるペット用消臭袋を、サイズ・枚数・におい対策と一緒に整理します。",
        "ペット 消臭袋 まとめ買い 犬 猫",
        "枚数、サイズ、におい漏れ、取り出しやすさ",
        "ペット用消臭袋は毎日使う家庭ほどストックしやすく、買い回りにも入れやすい消耗品です。",
        ("散歩やトイレ処理で毎日使う人", "におい漏れを抑えたい人", "サイズ違いを選びたい人"),
        ("pet/pet-daily-goods", "rakuten-marathon/1000yen-items"),
    ),
    ProductArticle(
        "pet",
        "pet-care",
        "楽天で買えるペットお手入れ用品まとめ買いおすすめ",
        "楽天市場で買えるペットのお手入れ用品を、ウェットシート・ブラシ・ケア用品の選び方と一緒に整理します。",
        "ペット ウェットシート まとめ買い 犬 猫",
        "用途、枚数、肌に合うか、使いやすさ",
        "ペットのお手入れ用品は、普段のケア頻度に合わせて補充すると無駄になりにくいジャンルです。",
        ("散歩後の足拭きをしたい人", "日常ケア用品をまとめたい人", "肌に合うかレビューも見たい人"),
        ("pet/pet-daily-goods", "daily-goods/hygiene-goods"),
    ),
)


GUIDE_ARTICLES: tuple[GuideArticle, ...] = (
    GuideArticle(
        "rakuten-marathon",
        "shopping-list",
        "marathon-guide",
        "楽天お買い物マラソンで買うものリスト",
        "楽天お買い物マラソンで無駄買いしにくい日用品・食品・ペット用品を目的別に整理します。",
        ("買うもの候補", "ジャンル別の使い分け", "買いすぎ防止", "関連記事への進み方"),
        (
            ("まず買うものを決める", "お買い物マラソンでは、店舗数を増やす前に家で確実に使うものを決めます。紙類、洗剤、食品、飲料、ペット用品の順に見ると、無理なく候補を作れます。"),
            ("日用品の候補", "トイレットペーパー、ティッシュ、洗濯洗剤、食器用洗剤は消費ペースが読みやすく、買い回りに入れやすい商品です。"),
            ("食品・飲料の候補", "米、炭酸水、レトルト食品、缶詰は重さや保存性の面で楽天と相性があります。賞味期限と置き場所を先に確認します。"),
            ("買わない方がいいもの", "初めて使う香り、肌に合うか分からないもの、置き場所を大きく取るものは、買い回り目的で大容量にしすぎない方が安心です。"),
        ),
        ("daily-goods/toilet-paper", "food-drink/rice", "pet/pet-sheets"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "five-store-set",
        "marathon-guide",
        "楽天買い回り5店舗セットの作り方",
        "楽天買い回りを5店舗で無理なく組むための日用品・食品の組み合わせ例を整理します。",
        ("5店舗の基本", "ジャンル分散", "無駄買い防止", "おすすめ導線"),
        (
            ("5店舗なら生活必需品だけで組みやすい", "5店舗を狙う場合は、紙類、洗剤、食品、飲料、ペット用品のようにジャンルを分けると買いすぎを防ぎやすいです。"),
            ("セット例", "トイレットペーパー、洗濯洗剤、炭酸水、レトルト食品、ペットシーツのように、毎月使うものを中心にします。"),
            ("確認すること", "送料込みか、1店舗の条件に届くか、配送日が重なりすぎないかを見ておきます。"),
            ("まとめ", "5店舗は無理に広げすぎず、今月中に使うものとストック品の範囲で組むのが現実的です。"),
        ),
        ("daily-goods/laundry-detergent", "food-drink/sparkling-water", "pet/pet-sheets"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "seven-store-set",
        "marathon-guide",
        "楽天買い回り7店舗セットの作り方",
        "楽天買い回りを7店舗まで広げるときに、重いもの・かさばるものを無理なく組み込む考え方を整理します。",
        ("7店舗の考え方", "追加しやすい商品", "注意点", "関連記事"),
        (
            ("7店舗は重いものを足す", "5店舗の基本セットに、水、米、ペットフード、保存容器などを足すと、必要な買い物の範囲で7店舗を組みやすくなります。"),
            ("追加候補", "米、飲料ストック、ペットフード、キッチン消耗品、衛生用品が候補です。"),
            ("注意点", "重い商品は受け取りが集中すると負担になります。配送日と置き場所を先に確認しましょう。"),
            ("まとめ", "7店舗は、必要なものを少し広げるラインです。ポイント目的だけの商品を足しすぎないことが大切です。"),
        ),
        ("food-drink/rice", "pet/pet-food", "kitchen/kitchen-consumables"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "ten-shop-set",
        "marathon-guide",
        "楽天で10店舗買い回りする時の日用品リスト",
        "楽天で10店舗買い回りを狙うときに、日用品・食品・ペット用品をどう組み合わせるか整理します。",
        ("10店舗の組み方", "日用品リスト", "食品リスト", "買いすぎ防止"),
        (
            ("10店舗はジャンルを分ける", "日用品だけで10店舗を埋めようとすると無理が出やすいです。食品、飲料、ペット用品、楽天経済圏の記事も合わせて確認します。"),
            ("日用品候補", "トイレットペーパー、ティッシュ、洗剤、柔軟剤、浴室洗剤、フロアシートなどが候補です。"),
            ("食品・ペット候補", "米、炭酸水、レトルト食品、缶詰、ペットシーツ、ペットフードはストックしやすい商品です。"),
            ("まとめ", "10店舗を狙うときほど、買う前に一覧を作り、使い切れる量だけに絞るのが大事です。"),
        ),
        ("daily-goods/tissue", "food-drink/canned-food", "pet/pet-food"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "super-sale-consumables",
        "marathon-guide",
        "楽天スーパーSALEで買いたい消耗品まとめ",
        "楽天スーパーSALEで候補にしやすい日用品・食品・キッチン消耗品を、買いすぎない目線で整理します。",
        ("スーパーSALE向きの消耗品", "日用品", "食品・飲料", "注意点"),
        (
            ("スーパーSALEはストック品と相性がいい", "セール時は普段から使う消耗品を補充するのが安全です。安さより、使い切れるかを優先します。"),
            ("日用品", "紙類、洗剤、衛生用品はストックしやすく、家族構成に合わせて量を調整しやすいです。"),
            ("食品・飲料", "米、炭酸水、レトルト食品、缶詰は保存期間と置き場所を確認して選びます。"),
            ("まとめ", "スーパーSALEでは、初めての商品を大容量で買うより、いつもの商品を補充する方が失敗しにくいです。"),
        ),
        ("daily-goods/toilet-paper", "food-drink/rice", "kitchen/plastic-wrap"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "stock-items",
        "marathon-guide",
        "楽天買い回りで後悔しにくいストック品まとめ",
        "楽天買い回りで買っても無駄になりにくいストック品を、日用品・食品・ペット用品に分けて整理します。",
        ("後悔しにくい条件", "ストック向き商品", "避けたい商品", "関連記事"),
        (
            ("後悔しにくい条件", "毎月使うもの、賞味期限が長いもの、置き場所が決まっているものはストック向きです。"),
            ("候補", "紙類、洗剤、米、缶詰、炭酸水、ペットシーツ、消臭袋などが候補です。"),
            ("避けたい商品", "好みが分かれる香りや味、初めて使う大容量商品は慎重に選びます。"),
            ("まとめ", "ストック品は安さだけでなく、使い切れる量と置き場所で判断しましょう。"),
        ),
        ("food-drink/staple-food", "pet/odor-bags", "daily-goods/hygiene-goods"),
    ),
    GuideArticle(
        "rakuten-marathon",
        "food-drink-marathon",
        "marathon-guide",
        "楽天買い回りで食品・飲料を買うなら何がいい？",
        "楽天買い回りで食品・飲料を買うときに、重いもの・常温保存・日常使いの目線で候補を整理します。",
        ("食品・飲料の選び方", "重いもの", "常温保存", "注意点"),
        (
            ("食品・飲料は楽天と相性がいい", "水、炭酸水、米のような重いものは、配送メリットがはっきり出ます。"),
            ("常温保存の候補", "レトルト食品、缶詰、パックご飯、麺類は賞味期限を見ながらローリングストックしやすいです。"),
            ("買い回りでの注意点", "まとめ買いしすぎると保管場所を取ります。味の好みが分かれる商品は少量から選びます。"),
            ("まとめ", "食品・飲料は、日常で使いながら補充できるものを中心に選ぶと失敗しにくいです。"),
        ),
        ("food-drink/rice", "food-drink/sparkling-water", "food-drink/retort-food"),
    ),
    GuideArticle(
        "rakuten-economy",
        "five-zero-day",
        "economy-guide",
        "楽天市場の5と0のつく日は日用品まとめ買いに使うべき？",
        "楽天市場の5と0のつく日を、日用品や食品のまとめ買いでどう使うか整理します。",
        ("5と0の日の基本", "向いている買い物", "注意点", "関連記事"),
        (
            ("5と0のつく日は日用品と相性がある", "日用品や食品を買う日を急がないなら、キャンペーン日に合わせることでポイント面の確認がしやすくなります。"),
            ("向いている買い物", "トイレットペーパー、洗剤、米、飲料など、買う予定が決まっている商品と相性があります。"),
            ("注意点", "エントリー条件や上限は変わるため、購入前に楽天市場のキャンペーンページで最新条件を確認します。"),
            ("まとめ", "5と0のつく日は、必要な買い物を寄せる日として使うと無理がありません。"),
        ),
        ("rakuten-economy/rakuten-card-daily-goods", "rakuten-marathon/shopping-list"),
    ),
    GuideArticle(
        "rakuten-economy",
        "rakuten-pay",
        "economy-guide",
        "楽天ペイは日用品の買い物で使うべき？",
        "楽天ペイを、楽天市場と街の買い物を分けて、日用品購入目線で整理します。",
        ("楽天ペイの使いどころ", "楽天市場との違い", "向いている人", "注意点"),
        (
            ("楽天ペイは街の買い物で出番が多い", "楽天市場の記事とは少し役割が違い、ドラッグストアやスーパーなど街の支払いで使う場面が多いです。"),
            ("楽天市場との関係", "楽天市場での買い回りは、ショップ数やキャンペーン条件を確認することが中心です。楽天ペイは日常の支払い管理として考えます。"),
            ("向いている人", "楽天ポイントを街でも使いたい人、日用品の支払いを楽天系にまとめたい人に向いています。"),
            ("まとめ", "楽天ペイは、楽天市場だけでなく普段の買い物も楽天ポイント圏に寄せたい人向けです。"),
        ),
        ("rakuten-economy/rakuten-card-daily-goods", "daily-goods/hygiene-goods"),
    ),
    GuideArticle(
        "rakuten-economy",
        "rakuten-bank",
        "economy-guide",
        "楽天銀行は楽天市場の買い物に必要？",
        "楽天銀行を、楽天市場で日用品を買う人にとって必要かどうかという目線で整理します。",
        ("楽天銀行の位置づけ", "向いている人", "急がなくていい人", "関連記事"),
        (
            ("楽天銀行は必須ではない", "楽天市場で日用品を買うだけなら、最初から楽天銀行までそろえる必要はありません。"),
            ("向いている人", "楽天カードや楽天証券など、楽天サービスをまとめて使う予定がある人は検討しやすいです。"),
            ("急がなくていい人", "まだ楽天市場の利用額が少ない人は、まず日用品の買い方と買い回りの使い方を整える方が先です。"),
            ("まとめ", "楽天銀行は後から検討で大丈夫です。まずは楽天市場で何をどのくらい買うかを見ましょう。"),
        ),
        ("rakuten-economy/rakuten-card-daily-goods", "rakuten-marathon/1000yen-items"),
    ),
    GuideArticle(
        "rakuten-economy",
        "furusato-tax",
        "economy-guide",
        "楽天ふるさと納税は日用品・食品ストックと相性がいい？",
        "楽天ふるさと納税を、米・ティッシュ・キッチン用品など暮らしのストック目線で整理します。",
        ("ふるさと納税の使いどころ", "相性の良い返礼品", "注意点", "関連記事"),
        (
            ("暮らしのストックと相性がある", "楽天ふるさと納税では、米、ティッシュ、キッチンペーパーなど暮らしで使う返礼品を選ぶ考え方もあります。"),
            ("相性の良い返礼品", "消費ペースが読める食品や日用品は、家計管理にもつなげやすいです。"),
            ("注意点", "寄付上限や配送時期、保管場所は必ず確認します。通常の楽天市場商品とは判断軸が少し違います。"),
            ("まとめ", "ふるさと納税は、必要なストック品を選ぶなら暮らし系サイトとも相性があります。"),
        ),
        ("food-drink/rice", "daily-goods/tissue", "kitchen/kitchen-paper"),
    ),
    GuideArticle(
        "rakuten-economy",
        "rakuten-economy-daily-goods",
        "economy-guide",
        "楽天経済圏は日用品のまとめ買いだけでも得になる？",
        "楽天経済圏を、日用品や食品のまとめ買いだけでどこまで考えるべきか整理します。",
        ("日用品だけの考え方", "向いている人", "無理しない範囲", "関連記事"),
        (
            ("日用品だけでも整理する意味はある", "毎月楽天市場で日用品や食品を買うなら、支払い方法やキャンペーン日を整理するだけでも迷いを減らせます。"),
            ("向いている人", "毎月の買い物が楽天市場に寄っている人、買い回りを使う人、ポイント管理が苦にならない人に向いています。"),
            ("無理しない範囲", "サービスを増やすことが目的になると疲れます。まずは楽天市場、楽天カード、5と0のつく日くらいからで十分です。"),
            ("まとめ", "楽天経済圏は、生活用品の買い方を整えた後に少しずつ広げるのが続けやすいです。"),
        ),
        ("rakuten-economy/rakuten-card-daily-goods", "rakuten-economy/five-zero-day"),
    ),
)


def load_env_files() -> None:
    for path in ENV_FILES:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line.removeprefix("export ").strip()
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def unwrap_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for raw in payload.get("Items") or payload.get("items") or []:
        if isinstance(raw, dict) and "Item" in raw:
            items.append(raw["Item"])
        elif isinstance(raw, dict):
            items.append(raw)
    return items


def fetch_items(keyword: str, hits: int = 12) -> list[dict[str, Any]]:
    params = {
        "applicationId": env_required("RAKUTEN_APPLICATION_ID"),
        "accessKey": env_required("RAKUTEN_ACCESS_KEY"),
        "affiliateId": env_required("RAKUTEN_AFFILIATE_ID"),
        "format": "json",
        "keyword": keyword,
        "hits": str(hits),
        "sort": "-reviewCount",
        "availability": "1",
        "imageFlag": "1",
        "NGKeyword": "中古",
    }
    referer = os.environ.get("RAKUTEN_ALLOWED_REFERER", "https://kurashi-kaimawari-memo.hatenablog.com/")
    request = urllib.request.Request(
        API_URL + "?" + urllib.parse.urlencode(params),
        headers={
            "User-Agent": "kurashi-kaimawari-memo/1.0",
            "Referer": referer,
            "Referrer": referer,
            "Origin": referer.rstrip("/"),
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return unwrap_items(json.loads(response.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                time.sleep(20)
                continue
            raise
    return []


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parsed = urllib.parse.urlparse(value)
    query = urllib.parse.parse_qs(parsed.query)
    target = (query.get("pc") or query.get("m") or [""])[0]
    if target:
        return urllib.parse.unquote(target)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def image_url(item: dict[str, Any]) -> str:
    for field in ("mediumImageUrls", "smallImageUrls"):
        urls = item.get(field) or []
        if not urls:
            continue
        first = urls[0]
        if isinstance(first, dict):
            value = str(first.get("imageUrl") or "")
        else:
            value = str(first)
        if value:
            return value
    return "https://thumbnail.image.rakuten.co.jp/@0_mall/placeholder/no-image.jpg"


def short_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name)
    clean = re.sub(r"【.*?】", "", clean).strip()
    return clean[:34] + ("..." if len(clean) > 34 else "")


def product_from_item(item: dict[str, Any], spec: ProductArticle, pattern: str) -> dict[str, Any]:
    name = str(item.get("itemName") or item.get("itemCaption") or "楽天市場の商品")
    product: dict[str, Any] = {
        "name": name,
        "shortName": short_name(name),
        "priceText": f"{int(item['itemPrice']):,}円" if item.get("itemPrice") is not None else "楽天で確認",
        "capacity": spec.capacity,
        "shipping": "商品ページで確認",
        "imageUrl": image_url(item),
        "affiliateUrl": str(item.get("affiliateUrl") or item.get("itemUrl") or ""),
        "features": [spec.capacity, "買い回り候補", "レビュー確認推奨"],
        "recommendedFor": pattern,
        "caution": "価格、在庫、送料、ポイント倍率は購入前に楽天市場の商品ページで確認してください。",
    }
    if item.get("reviewCount") is not None:
        product["reviewCount"] = int(item["reviewCount"])
    if item.get("reviewAverage") is not None:
        product["reviewAverage"] = float(item["reviewAverage"])
    return product


def unique_products(items: list[dict[str, Any]], spec: ProductArticle) -> list[dict[str, Any]]:
    products = []
    seen = set()
    for item in items:
        url = str(item.get("affiliateUrl") or item.get("itemUrl") or "")
        name = str(item.get("itemName") or "")
        if not url or not name:
            continue
        sig = canonical_url(url) or re.sub(r"\s+", "", name.lower())[:80]
        if sig in seen:
            continue
        products.append(product_from_item(item, spec, spec.patterns[len(products) % len(spec.patterns)]))
        seen.add(sig)
        if len(products) >= 3:
            break
    return products


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def product_article_markdown(spec: ProductArticle) -> str:
    related_lines = "\n".join(f"  - {yaml_string(item)}" for item in spec.related)
    return f"""---
title: {yaml_string(spec.title)}
description: {yaml_string(spec.description)}
slug: {yaml_string(spec.slug)}
category: {yaml_string(spec.category)}
type: "product-roundup"
date: "2026-04-29"
updated: "2026-04-29"
affiliate: true
products: {yaml_string(f"{spec.category}/{spec.slug}")}
points:
  - "楽天で買うメリット"
  - "失敗しにくい選び方"
  - "買い回りで使うコツ"
  - "楽天で買わない方がいいケース"
related:
{related_lines}
---

## 楽天で買うメリット

{spec.intro} 重いもの、かさばるもの、定期的に使うものは、楽天でまとめ買いすると家まで届く便利さがあります。

買い回りでは1店舗として組み込みやすく、普段から使う商品なら無駄買いになりにくいのもメリットです。

## 選び方

まずは{spec.capacity}を確認します。商品名だけで判断すると、サイズやセット数、保存方法、使い切りやすさを見落とすことがあります。

初めて使う商品は、評価の高さだけで決めず、低評価レビューで「使いにくい」「量が多すぎる」「想像と違う」といった声がないかも見ておくと安心です。

## 買い回りで使うコツ

買い回りに入れるなら、送料込みか、1店舗の購入金額条件に届くかを先に確認します。ポイント倍率だけで選ぶより、家で確実に使い切れる商品を選ぶ方が続けやすいです。

複数ショップに分かれる場合は、配送日や受け取りの手間も含めて考えると、届いた後の負担を減らせます。

## 楽天で買わない方がいいケース

近所の店舗で少量を安く買える場合や、置き場所が足りない場合は、無理に楽天でまとめ買いしなくても大丈夫です。

また、好みが分かれる味、香り、サイズ感がある商品は、初回から大容量にしすぎない方が失敗しにくくなります。

## まとめ

{spec.title.replace("楽天で買える", "").replace("おすすめ", "").strip()}は、消費ペースが読める家庭ほど楽天のまとめ買いと相性があります。価格だけでなく、容量、送料、置き場所、レビューまで確認して選びましょう。
"""


def guide_article_markdown(spec: GuideArticle) -> str:
    points = "\n".join(f"  - {yaml_string(point)}" for point in spec.points)
    related = "\n".join(f"  - {yaml_string(item)}" for item in spec.related)
    sections = "\n\n".join(f"## {heading}\n\n{body}" for heading, body in spec.sections)
    return f"""---
title: {yaml_string(spec.title)}
description: {yaml_string(spec.description)}
slug: {yaml_string(spec.slug)}
category: {yaml_string(spec.category)}
type: {yaml_string(spec.type)}
date: "2026-04-29"
updated: "2026-04-29"
affiliate: true
points:
{points}
related:
{related}
---

{sections}
"""


def write_product_article(spec: ProductArticle) -> bool:
    article_path = ARTICLES_ROOT / spec.category / f"{spec.slug}.md"
    product_path = PRODUCTS_ROOT / spec.category / f"{spec.slug}.json"
    if article_path.exists() and product_path.exists():
        return False

    items = fetch_items(spec.keyword)
    products = unique_products(items, spec)
    if len(products) < 3:
        raise RuntimeError(f"Only fetched {len(products)} products for {spec.category}/{spec.slug}")

    article_path.parent.mkdir(parents=True, exist_ok=True)
    product_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(product_article_markdown(spec), encoding="utf-8")
    product_path.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def write_guide_article(spec: GuideArticle) -> bool:
    article_path = ARTICLES_ROOT / spec.category / f"{spec.slug}.md"
    if article_path.exists():
        return False
    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(guide_article_markdown(spec), encoding="utf-8")
    return True


def main() -> None:
    load_env_files()
    product_count = 0
    guide_count = 0
    for index, spec in enumerate(PRODUCT_ARTICLES):
        if write_product_article(spec):
            product_count += 1
            time.sleep(4 if index < len(PRODUCT_ARTICLES) - 1 else 0)
    for spec in GUIDE_ARTICLES:
        if write_guide_article(spec):
            guide_count += 1
    print(f"Created {product_count} product articles and {guide_count} guide articles.")


if __name__ == "__main__":
    main()
