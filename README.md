# 暮らしの買い回りメモ

楽天で日用品・食品・キッチン用品を買う人向けの、商品比較・買い回り・楽天経済圏ガイドサイトです。

## 役割

- 商品まとめ記事: 楽天商品リンクへの主導線
- 買い回り攻略記事: 集客と内部リンク
- 楽天経済圏記事: 楽天カードなどへの将来導線

## 開発

```bash
npm install
npm run dev
```

## ビルド

```bash
npm run build
```

## ディレクトリ

- `src/pages/`: トップ、カテゴリ、記事ページ
- `src/content/articles/`: Markdown記事
- `src/content/products/`: 商品JSON
- `src/components/`: 表示部品
- `scripts/`: 楽天API取得や記事生成ツール
- `tools/`: キーワード、取得結果、採用商品、プロンプト
