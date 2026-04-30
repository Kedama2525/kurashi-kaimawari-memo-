# 公開チェックリスト

## GitHub

1. GitHubで `kurashi-kaimawari-memo-` リポジトリを作成する
2. このローカルリポジトリに `origin` を設定する
3. `main` ブランチをpushする

```bash
git remote add origin git@github.com:Kedama2525/kurashi-kaimawari-memo-.git
git push -u origin main
```

## Cloudflare Pages

Cloudflare PagesでGitHubリポジトリを接続し、以下の設定にする。

- Framework preset: Astro
- Build command: `npm run build`
- Build output directory: `dist`
- Root directory: 空欄または `/`

独自ドメイン `https://kurashi-kaimawari.com` をCloudflare Pages側に追加する。
Cloudflare Pagesの環境変数 `PUBLIC_SITE_URL` は `https://kurashi-kaimawari.com` に設定する。

## Google Search Console

1. 公開URLをプロパティに追加する
2. Cloudflare PagesのHTMLタグ、またはDNS TXTレコードで所有権確認する
3. サイトマップを送信する

```text
https://kurashi-kaimawari.com/sitemap-index.xml
```

Astroのサイトマップは `sitemap-index.xml` と `sitemap-0.xml` として生成される。
Cloudflare Pagesでは `/sitemap.xml` も `/sitemap-index.xml` にリダイレクトする。
