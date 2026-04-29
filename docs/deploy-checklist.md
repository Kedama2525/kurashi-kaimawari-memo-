# 公開チェックリスト

## GitHub

1. GitHubで `kurashi-kaimawari-memo` リポジトリを作成する
2. このローカルリポジトリに `origin` を設定する
3. `main` ブランチをpushする

```bash
git remote add origin git@github.com:<your-name>/kurashi-kaimawari-memo.git
git push -u origin main
```

## Cloudflare Pages

Cloudflare PagesでGitHubリポジトリを接続し、以下の設定にする。

- Framework preset: Astro
- Build command: `npm run build`
- Build output directory: `dist`
- Root directory: 空欄または `/`

独自ドメインを使う場合は、Cloudflare Pages側でドメインを追加し、`PUBLIC_SITE_URL` を本番URLに設定する。

## Google Search Console

1. 公開URLをプロパティに追加する
2. Cloudflare PagesのHTMLタグ、またはDNS TXTレコードで所有権確認する
3. サイトマップを送信する

```text
https://kurashi-kaimawari-memo.pages.dev/sitemap-index.xml
```
