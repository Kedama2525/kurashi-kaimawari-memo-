#!/usr/bin/env python3
"""Import existing Rakuten article HTML into Astro content.

The Hatena draft HTML files already contain affiliate URLs, product images,
review counts, and ratings fetched from Rakuten. This script normalizes those
selected products into Astro article Markdown and product JSON files.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path


WORK_ROOT = Path("/Users/user/work/楽天アフィリエイト")
SOURCE_ROOT = WORK_ROOT / "03_記事作成"
SITE_ROOT = WORK_ROOT / "kurashi-kaimawari-memo"
ARTICLES_ROOT = SITE_ROOT / "src/content/articles"
PRODUCTS_ROOT = SITE_ROOT / "src/content/products"


@dataclass(frozen=True)
class ArticleSpec:
    source_dir: str
    category: str
    slug: str
    title: str
    description: str
    intro: str
    focus: str
    eyecatch: str | None = None
    card_indexes: tuple[int, ...] | None = None
    related: tuple[str, ...] = (
        "rakuten-marathon/1000yen-items",
        "rakuten-economy/rakuten-card-daily-goods",
    )


ARTICLE_SPECS: tuple[ArticleSpec, ...] = (
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="daily-goods",
        slug="tissue",
        title="楽天で買えるティッシュペーパーまとめ買いおすすめ",
        description="楽天市場で買えるティッシュペーパーの箱買い・まとめ買い向け商品を、置き場所や使い切りやすさと一緒に整理します。",
        intro="ティッシュペーパーは家族用や在宅用のストックとして使いやすい日用品です。",
        focus="箱数、組数、紙質、保管場所",
        eyecatch="/images/articles/daily-goods/tissue.webp",
        card_indexes=(1,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="kitchen",
        slug="kitchen-paper",
        title="楽天で買えるキッチンペーパーまとめ買いおすすめ",
        description="楽天市場で買えるキッチンペーパーを、ロール式・シート式の違いや保管しやすさと一緒に整理します。",
        intro="キッチンペーパーは料理にも掃除にも使えるため、買い回りに入れやすい消耗品です。",
        focus="枚数、サイズ、吸水性、取り出しやすさ",
        card_indexes=(2,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="daily-goods",
        slug="laundry-detergent",
        title="楽天で買える洗濯洗剤まとめ買いおすすめ",
        description="楽天市場で買える洗濯洗剤の大容量・詰め替え商品を、香りや詰め替えやすさと一緒に整理します。",
        intro="洗濯洗剤は重い液体商品が多く、楽天で買うメリットが出やすい日用品です。",
        focus="容量、香り、詰め替え口、使い切れる量",
        eyecatch="/images/articles/daily-goods/laundry-detergent.webp",
        card_indexes=(3,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="daily-goods",
        slug="fabric-softener",
        title="楽天で買える柔軟剤まとめ買いおすすめ",
        description="楽天市場で買える柔軟剤の大容量詰め替えを、香りの好みやストック量と一緒に整理します。",
        intro="柔軟剤はいつもの香りが決まっている家庭ならまとめ買いしやすい日用品です。",
        focus="香り、総容量、詰め替え回数、保管場所",
        card_indexes=(4,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="kitchen",
        slug="dishwashing-liquid",
        title="楽天で買える食器用洗剤まとめ買いおすすめ",
        description="楽天市場で買える食器用洗剤の詰め替えセットを、本体ボトルの有無や泡切れと一緒に整理します。",
        intro="食器用洗剤は毎日使うため、ストックしても無駄になりにくいキッチン消耗品です。",
        focus="本体の有無、詰め替え容量、泡立ち、泡切れ",
        card_indexes=(5,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="kitchen",
        slug="dishwasher-detergent",
        title="楽天で買える食洗機用洗剤まとめ買いおすすめ",
        description="楽天市場で買える食洗機用洗剤を、タブレット・粉末・液体の違いや1回分の見方と一緒に整理します。",
        intro="食洗機用洗剤は1回分で比較しやすく、毎日使う家庭なら買い回りにも入れやすい商品です。",
        focus="個数、1回分、溶け残り、対応機種",
        card_indexes=(6,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="daily-goods",
        slug="bath-cleaner",
        title="楽天で買える浴室洗剤まとめ買いおすすめ",
        description="楽天市場で買える浴室洗剤・カビ取り系商品を、容量や使用上の注意と一緒に整理します。",
        intro="浴室洗剤は切れると困る掃除用品ですが、使い方の確認も大切です。",
        focus="本体の有無、詰め替え容量、使用上の注意、換気",
        card_indexes=(7,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="daily-goods",
        slug="floor-wiper-sheets",
        title="楽天で買えるフロアワイパーシートまとめ買いおすすめ",
        description="楽天市場で買えるフロアワイパーシートを、ドライ・ウェットの違いや対応サイズと一緒に整理します。",
        intro="フロアワイパーシートは軽くて保管しやすく、掃除用品の買い回り候補にしやすい商品です。",
        focus="枚数、ドライ/ウェット、対応サイズ、乾きにくさ",
        card_indexes=(8,),
    ),
    ArticleSpec(
        source_dir="01_楽天で買える日用品まとめ",
        category="kitchen",
        slug="trash-bags",
        title="楽天で買えるゴミ袋まとめ買いおすすめ",
        description="楽天市場で買えるゴミ袋・ポリ袋を、サイズや厚み、自治体指定の確認ポイントと一緒に整理します。",
        intro="ゴミ袋はサイズと厚みが合えば失敗しにくく、ストック向きのキッチン消耗品です。",
        focus="容量、枚数、厚み、透明度、自治体指定",
        card_indexes=(9,),
    ),
    ArticleSpec(
        source_dir="02_楽天で買える掃除用品まとめ",
        category="daily-goods",
        slug="cleaning-goods",
        title="楽天で買える掃除用品まとめ",
        description="楽天市場で買える浴室洗剤、トイレ洗剤、床掃除シートなどの掃除用品を、買う前の確認ポイントと一緒に整理します。",
        intro="掃除用品は切らすと困る一方で、詰め替えやセット数で迷いやすい日用品です。",
        focus="容量、用途、置き場所、低評価レビュー",
    ),
    ArticleSpec(
        source_dir="03_楽天で買える洗濯用品まとめ",
        category="daily-goods",
        slug="laundry-goods",
        title="楽天で買える洗濯用品まとめ",
        description="楽天市場で買える洗剤、柔軟剤、洗濯槽クリーナーなどの洗濯用品を、使い切りやすさと一緒に整理します。",
        intro="洗濯用品は重いものや定期的に使うものが多く、楽天のまとめ買いと相性があります。",
        focus="香り、容量、詰め替えやすさ、保管場所",
    ),
    ArticleSpec(
        source_dir="04_楽天で買えるキッチン消耗品まとめ",
        category="kitchen",
        slug="kitchen-consumables",
        title="楽天で買えるキッチン消耗品まとめ",
        description="楽天市場で買えるラップ、保存袋、キッチンペーパーなどのキッチン消耗品を、日常使いのしやすさと一緒に整理します。",
        intro="キッチン消耗品は毎日使うものが多く、買い回りの1店舗にも組み込みやすいジャンルです。",
        focus="サイズ、枚数、対応温度、収納しやすさ",
    ),
    ArticleSpec(
        source_dir="05_楽天で買える防災備蓄まとめ",
        category="daily-goods",
        slug="disaster-stock",
        title="楽天で買える防災備蓄まとめ",
        description="楽天市場で買える水、非常食、簡易トイレなどの防災備蓄品を、賞味期限や保管場所と一緒に整理します。",
        intro="防災備蓄は一度にそろえようとすると大変なので、必要なものから少しずつ整えるのが現実的です。",
        focus="賞味期限、人数分、保管場所、使い方",
    ),
    ArticleSpec(
        source_dir="06_楽天で買える衛生用品まとめ",
        category="daily-goods",
        slug="hygiene-goods",
        title="楽天で買える衛生用品まとめ",
        description="楽天市場で買えるマスク、除菌シート、ハンドソープなどの衛生用品を、消費ペースや置き場所と一緒に整理します。",
        intro="衛生用品は家族分をストックしやすい一方で、サイズや肌に合うかも見ておきたい商品です。",
        focus="サイズ、肌あたり、容量、使用期限",
    ),
    ArticleSpec(
        source_dir="07_楽天で買えるベビー日用品まとめ",
        category="daily-goods",
        slug="baby-goods",
        title="楽天で買えるベビー日用品まとめ",
        description="楽天市場で買えるおむつ、おしりふき、ベビー用消耗品を、サイズ選びや使い切りやすさと一緒に整理します。",
        intro="ベビー日用品は消費ペースが早いため、買い回りで補充しやすいジャンルです。",
        focus="サイズ、肌に合うか、消費ペース、保管場所",
    ),
    ArticleSpec(
        source_dir="08_楽天で買えるペット日用品まとめ",
        category="pet",
        slug="pet-daily-goods",
        title="楽天で買えるペット日用品まとめ",
        description="楽天市場で買えるペットフード、ペットシーツ、消臭袋などを、いつもの商品かどうかと一緒に整理します。",
        intro="ペット日用品は重いものやかさばるものが多く、楽天でまとめ買いするメリットが出やすいです。",
        focus="サイズ、香り、消費ペース、保管場所",
    ),
    ArticleSpec(
        source_dir="09_楽天で買える食品ストックまとめ",
        category="food-drink",
        slug="food-stock",
        title="楽天で買える食品ストックまとめ",
        description="楽天市場で買える米、レトルト食品、缶詰などの食品ストックを、賞味期限や保存場所と一緒に整理します。",
        intro="食品ストックは常温保存しやすいものを中心に選ぶと、日常用にも備蓄用にも使いやすくなります。",
        focus="賞味期限、保存方法、味の好み、消費ペース",
    ),
    ArticleSpec(
        source_dir="09_楽天で買える食品ストックまとめ",
        category="food-drink",
        slug="retort-food",
        title="楽天で買えるレトルト食品まとめ買いおすすめ",
        description="楽天市場で買えるレトルト食品を、味の好みや賞味期限、常温保存のしやすさと一緒に整理します。",
        intro="レトルト食品は忙しい日の食事にも備蓄にも使いやすく、買い回りに入れやすい食品ストックです。",
        focus="賞味期限、味の種類、1食あたり、保存場所",
        eyecatch="/images/articles/food-drink/retort-food.webp",
        card_indexes=(2,),
    ),
    ArticleSpec(
        source_dir="10_楽天で買える飲料ストックまとめ",
        category="food-drink",
        slug="drink-stock",
        title="楽天で買える飲料ストックまとめ",
        description="楽天市場で買える水、お茶、炭酸水、コーヒーなどの飲料ストックを、重さや置き場所と一緒に整理します。",
        intro="飲料は重く、箱買いすると配送メリットが大きく出るジャンルです。",
        focus="容量、賞味期限、ラベル有無、保管場所",
    ),
    ArticleSpec(
        source_dir="10_楽天で買える飲料ストックまとめ",
        category="food-drink",
        slug="sparkling-water",
        title="楽天で買える炭酸水まとめ買いおすすめ",
        description="楽天市場で買える炭酸水を、強炭酸・ラベルレス・フレーバーの違いと一緒に整理します。",
        intro="炭酸水は毎日飲む人なら消費ペースが読みやすく、楽天で箱買いしやすい飲料です。",
        focus="炭酸の強さ、ラベルレス、フレーバー、1本あたり",
        eyecatch="/images/articles/food-drink/sparkling-water.webp",
        card_indexes=(1,),
    ),
)


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(value)).strip()


def source_html(source_dir: str) -> str:
    directory = SOURCE_ROOT / source_dir
    files = sorted(directory.glob("*.html"))
    if not files:
        raise FileNotFoundError(f"No HTML file found in {directory}")
    return files[0].read_text(encoding="utf-8")


def parse_number(value: str) -> int | None:
    match = re.search(r"([\d,]+)", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_float(value: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    return float(match.group(1))


def extract_meta(meta: str) -> dict[str, object]:
    result: dict[str, object] = {
        "priceText": "楽天で確認",
        "shipping": "商品ページで確認",
    }
    for part in [item.strip() for item in meta.split("/")]:
        if part.startswith("価格:"):
            price = part.split(":", 1)[1].strip()
            result["priceText"] = price if price else "楽天で確認"
        elif part.startswith("レビュー:"):
            count = parse_number(part)
            if count is not None:
                result["reviewCount"] = count
        elif part.startswith("評価:"):
            rating = parse_float(part)
            if rating is not None:
                result["reviewAverage"] = rating
    return result


def extract_cards(raw_html: str) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []
    parts = raw_html.split('<div class="rakuten-product-card">')[1:]
    for part in parts:
        block = part.split("<p><strong>確認ポイント:", 1)[0]
        image_match = re.search(r'<img src="([^"]+)"', block)
        name_match = re.search(
            r'<p class="rakuten-product-card__name"><a href="([^"]+)">(.*?)</a></p>',
            block,
            re.S,
        )
        meta_match = re.search(r'<p class="rakuten-product-card__meta">(.*?)</p>', block, re.S)
        if not (image_match and name_match and meta_match):
            continue

        description_match = re.search(r"</p>\s*<p>(.*?)</p>", block[meta_match.end() :], re.S)
        name = strip_tags(name_match.group(2))
        meta = strip_tags(meta_match.group(1))
        data = {
            "name": name,
            "shortName": short_name(name),
            "affiliateUrl": html.unescape(name_match.group(1)),
            "imageUrl": html.unescape(image_match.group(1)),
            "description": strip_tags(description_match.group(1)) if description_match else "",
        }
        data.update(extract_meta(meta))
        cards.append(data)
    return cards


def short_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name)
    clean = re.sub(r"【.*?】", "", clean).strip()
    return clean[:34] + ("..." if len(clean) > 34 else "")


def select_cards(cards: list[dict[str, object]], indexes: tuple[int, ...] | None) -> list[dict[str, object]]:
    if indexes is None:
        return cards[:5]
    selected = []
    for index in indexes:
        if index >= len(cards):
            raise IndexError(f"Card index {index} is out of range. Found {len(cards)} cards.")
        selected.append(cards[index])
    return selected


def product_json(spec: ArticleSpec, cards: list[dict[str, object]]) -> list[dict[str, object]]:
    products = []
    for card in cards:
        product = {
            "name": card["name"],
            "shortName": card["shortName"],
            "priceText": card.get("priceText", "楽天で確認"),
            "capacity": spec.focus,
            "shipping": card.get("shipping", "商品ページで確認"),
            "imageUrl": card["imageUrl"],
            "affiliateUrl": card["affiliateUrl"],
            "features": [
                spec.focus,
                "買い回り候補",
                "レビュー確認推奨",
            ],
            "recommendedFor": "普段から使う量が読める人",
            "caution": "価格、在庫、送料、ポイント倍率は購入前に楽天市場の商品ページで確認してください。",
        }
        if "reviewCount" in card:
            product["reviewCount"] = card["reviewCount"]
        if "reviewAverage" in card:
            product["reviewAverage"] = card["reviewAverage"]
        products.append(product)
    return products


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def article_markdown(spec: ArticleSpec) -> str:
    related_lines = "\n".join(f"  - {yaml_string(item)}" for item in spec.related)
    eyecatch_line = f"eyecatch: {yaml_string(spec.eyecatch)}\n" if spec.eyecatch else ""
    return f"""---
title: {yaml_string(spec.title)}
description: {yaml_string(spec.description)}
slug: {yaml_string(spec.slug)}
category: {yaml_string(spec.category)}
type: "product-roundup"
date: "2026-04-29"
updated: "2026-04-29"
{eyecatch_line}affiliate: true
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

{spec.intro} かさばるもの、重いもの、毎月使うものは、楽天でまとめ買いすると家まで届く便利さがあります。

買い回りでは1店舗として組み込みやすく、普段から使う商品なら無駄買いになりにくいのもメリットです。

## 選び方

まずは{spec.focus}を確認します。商品名だけで判断すると、サイズやセット数、詰め替えか本体付きかを見落とすことがあります。

初めて使う商品は、評価の高さだけで決めず、低評価レビューで「使いにくい」「量が多すぎる」「想像と違う」といった声がないかも見ておくと安心です。

## 買い回りで使うコツ

買い回りに入れるなら、送料込みか、1店舗の購入金額条件に届くかを先に確認します。ポイント倍率だけで選ぶより、家で確実に使い切れる商品を選ぶ方が続けやすいです。

複数ショップに分かれる場合は、配送日や受け取りの手間も含めて考えると、届いた後の負担を減らせます。

## 楽天で買わない方がいいケース

近所の店舗で少量を安く買える場合や、置き場所が足りない場合は、無理に楽天でまとめ買いしなくても大丈夫です。

また、好みが分かれる香り、味、肌ざわり、サイズ感がある商品は、初回から大容量にしすぎない方が失敗しにくくなります。

## まとめ

{spec.title.replace("楽天で買える", "").replace("おすすめ", "").strip()}は、消費ペースが読める家庭ほど楽天のまとめ買いと相性があります。価格だけでなく、容量、送料、置き場所、レビューまで確認して選びましょう。
"""


def write_article(spec: ArticleSpec, products: list[dict[str, object]]) -> None:
    product_path = PRODUCTS_ROOT / spec.category / f"{spec.slug}.json"
    article_path = ARTICLES_ROOT / spec.category / f"{spec.slug}.md"
    product_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.parent.mkdir(parents=True, exist_ok=True)

    product_path.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    article_path.write_text(article_markdown(spec), encoding="utf-8")


def main() -> None:
    imported = 0
    for spec in ARTICLE_SPECS:
        cards = extract_cards(source_html(spec.source_dir))
        selected = select_cards(cards, spec.card_indexes)
        write_article(spec, product_json(spec, selected))
        imported += 1
    print(f"Imported {imported} articles into Astro content.")


if __name__ == "__main__":
    main()
