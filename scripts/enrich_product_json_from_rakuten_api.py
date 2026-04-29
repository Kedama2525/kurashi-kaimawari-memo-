#!/usr/bin/env python3
"""Add Rakuten API candidates to product JSON files that have too few items."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
WORK_ROOT = Path("/Users/user/work/楽天アフィリエイト")
SITE_ROOT = WORK_ROOT / "kurashi-kaimawari-memo"
PRODUCTS_ROOT = SITE_ROOT / "src/content/products"
ENV_FILES = (
    WORK_ROOT / "02_初期設定/rakuten_api_config.env",
    WORK_ROOT / "02_初期設定/rakuten_account_config.env",
)


@dataclass(frozen=True)
class Target:
    product_id: str
    keyword: str
    capacity: str
    patterns: tuple[str, str, str]
    fallback_id: str | None = None


TARGETS: tuple[Target, ...] = (
    Target(
        "daily-goods/toilet-paper",
        "トイレットペーパー まとめ買い 芯なし",
        "ロール数、巻きの長さ、シングル/ダブル、保管場所",
        ("とにかく買い物の荷物を減らしたい人", "家族用に長く使えるストックが欲しい人", "紙質と価格のバランスを見たい人"),
    ),
    Target(
        "daily-goods/tissue",
        "ティッシュペーパー まとめ買い 200組",
        "箱数、組数、紙質、保管場所",
        ("家族分をまとめて補充したい人", "在宅時間が長く消費量が多い人", "花粉時期に切らしたくない人"),
    ),
    Target(
        "daily-goods/laundry-detergent",
        "洗濯洗剤 大容量 詰め替え",
        "容量、香り、詰め替え口、使い切れる量",
        ("洗濯回数が多い家庭", "重い洗剤を家まで届けてほしい人", "いつもの洗剤をまとめ買いしたい人"),
        "daily-goods/laundry-goods",
    ),
    Target(
        "daily-goods/fabric-softener",
        "柔軟剤 大容量 詰め替え まとめ買い",
        "香り、総容量、詰め替え回数、保管場所",
        ("いつもの香りが決まっている人", "洗剤と一緒に補充したい人", "香りの強さをレビューで見たい人"),
    ),
    Target(
        "daily-goods/bath-cleaner",
        "浴室洗剤 まとめ買い 詰め替え",
        "本体の有無、詰め替え容量、使用上の注意、換気",
        ("浴室洗剤を切らしたくない人", "詰め替え中心で補充したい人", "掃除頻度が高い家庭"),
        "daily-goods/cleaning-goods",
    ),
    Target(
        "daily-goods/floor-wiper-sheets",
        "フロアワイパーシート まとめ買い ウェット",
        "枚数、ドライ/ウェット、対応サイズ、乾きにくさ",
        ("こまめに床掃除したい人", "軽くて収納しやすい掃除用品が欲しい人", "ウェットとドライを使い分けたい人"),
    ),
    Target(
        "kitchen/kitchen-paper",
        "キッチンペーパー まとめ買い ペーパータオル",
        "枚数、サイズ、吸水性、取り出しやすさ",
        ("料理にも掃除にも使いたい人", "シート式でさっと取り出したい人", "大容量でも使い切れる家庭"),
        "kitchen/kitchen-consumables",
    ),
    Target(
        "kitchen/dishwashing-liquid",
        "食器用洗剤 詰め替え まとめ買い",
        "本体の有無、詰め替え容量、泡立ち、泡切れ",
        ("自炊が多く食器洗いの回数が多い人", "いつもの洗剤を切らしたくない人", "本体ボトルを持っている人"),
        "kitchen/kitchen-consumables",
    ),
    Target(
        "kitchen/dishwasher-detergent",
        "食洗機用洗剤 タブレット まとめ買い",
        "個数、1回分、溶け残り、対応機種",
        ("食洗機を毎日使う家庭", "計量の手間を減らしたい人", "1回分あたりで比較したい人"),
    ),
    Target(
        "kitchen/trash-bags",
        "ゴミ袋 45L 半透明 まとめ買い 厚手",
        "容量、枚数、厚み、透明度、自治体指定",
        ("45Lをよく使う家庭", "破れにくさを重視したい人", "自治体指定がない地域で使う人"),
        "kitchen/kitchen-consumables",
    ),
    Target(
        "food-drink/retort-food",
        "レトルト食品 常温保存 まとめ買い",
        "賞味期限、味の種類、1食あたり、保存場所",
        ("忙しい日の食事を用意したい人", "常温保存できる備蓄を増やしたい人", "家族で味の種類を選びたい人"),
        "food-drink/food-stock",
    ),
    Target(
        "food-drink/sparkling-water",
        "炭酸水 500ml 24本 ラベルレス",
        "炭酸の強さ、ラベルレス、フレーバー、1本あたり",
        ("毎日炭酸水を飲む人", "ラベルレスで分別を楽にしたい人", "フレーバー違いも試したい人"),
        "food-drink/drink-stock",
    ),
)


def load_env_files() -> None:
    for path in ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
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


def fetch_items(keyword: str, hits: int = 10) -> list[dict[str, Any]]:
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
    with urllib.request.urlopen(request, timeout=20) as response:
        return unwrap_items(json.loads(response.read().decode("utf-8")))


def image_url(item: dict[str, Any]) -> str:
    for field in ("mediumImageUrls", "smallImageUrls"):
        urls = item.get(field) or []
        if urls:
            first = urls[0]
            if isinstance(first, dict):
                return str(first.get("imageUrl") or "")
            return str(first)
    return "https://thumbnail.image.rakuten.co.jp/@0_mall/placeholder/no-image.jpg"


def short_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name)
    clean = re.sub(r"【.*?】", "", clean).strip()
    return clean[:34] + ("..." if len(clean) > 34 else "")


def product_from_item(item: dict[str, Any], target: Target, pattern: str) -> dict[str, Any]:
    product: dict[str, Any] = {
        "name": str(item.get("itemName") or item.get("itemCaption") or "楽天市場の商品"),
        "shortName": short_name(str(item.get("itemName") or "楽天市場の商品")),
        "priceText": f"{int(item['itemPrice']):,}円" if item.get("itemPrice") is not None else "楽天で確認",
        "capacity": target.capacity,
        "shipping": "商品ページで確認",
        "imageUrl": image_url(item),
        "affiliateUrl": str(item.get("affiliateUrl") or item.get("itemUrl") or ""),
        "features": [target.capacity, "買い回り候補", "レビュー確認推奨"],
        "recommendedFor": pattern,
        "caution": "価格、在庫、送料、ポイント倍率は購入前に楽天市場の商品ページで確認してください。",
    }
    if item.get("reviewCount") is not None:
        product["reviewCount"] = int(item["reviewCount"])
    if item.get("reviewAverage") is not None:
        product["reviewAverage"] = float(item["reviewAverage"])
    return product


def load_products(product_id: str) -> list[dict[str, Any]]:
    path = PRODUCTS_ROOT / f"{product_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_products(product_id: str, products: list[dict[str, Any]]) -> None:
    path = PRODUCTS_ROOT / f"{product_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parsed = urllib.parse.urlparse(value)
    query = urllib.parse.parse_qs(parsed.query)
    target = (query.get("pc") or query.get("m") or [""])[0]
    if target:
        return urllib.parse.unquote(target)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def signature(product: dict[str, Any]) -> str:
    url_sig = canonical_url(str(product.get("affiliateUrl", "")))
    if url_sig:
        return url_sig
    return re.sub(r"\s+", "", str(product.get("name", "")).lower())[:80]


def enrich(target: Target) -> bool:
    existing = load_products(target.product_id)

    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    def append_existing(product: dict[str, Any]) -> bool:
        sig = signature(product)
        if sig in seen:
            return False
        product["capacity"] = target.capacity
        product["recommendedFor"] = target.patterns[len(products) % len(target.patterns)]
        product["features"] = [target.capacity, "買い回り候補", "レビュー確認推奨"]
        products.append(product)
        seen.add(sig)
        return True

    for product in existing:
        append_existing(product)

    if len(products) >= 3 and len(products) == len(existing):
        return False

    if len(products) < 3:
        try:
            api_items = fetch_items(target.keyword)
        except Exception:
            api_items = []

        for item in api_items:
            name = str(item.get("itemName") or "")
            url = str(item.get("affiliateUrl") or item.get("itemUrl") or "")
            if not name or not url:
                continue
            sig = canonical_url(url) or re.sub(r"\s+", "", name.lower())[:80]
            if sig in seen:
                continue
            products.append(product_from_item(item, target, target.patterns[len(products) % len(target.patterns)]))
            seen.add(sig)
            if len(products) >= 3:
                break

    if len(products) < 3 and target.fallback_id:
        for product in load_products(target.fallback_id):
            append_existing(dict(product))
            if len(products) >= 3:
                break

    save_products(target.product_id, products[:3])
    return True


def main() -> None:
    load_env_files()
    updated = 0
    for target in TARGETS:
        if enrich(target):
            updated += 1
        time.sleep(0.7)
    print(f"Updated {updated} product JSON files.")


if __name__ == "__main__":
    main()
