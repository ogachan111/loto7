# LOTO7 予想アプリ

みずほ銀行のロト7当選番号を自動取得して表示・統計予想・当選自動チェック・メール通知を行うモバイル風 PWA。

- 公開URL（GitHub Pages）: https://ogachan111.github.io/loto7/
- デフォルトブランチ: **`main1`**

---

## 構成ファイル

| ファイル | 役割 |
|---|---|
| `index.html` | 公開される本体（**ビルド成果物**。`app.jsx` をトランスパイルして埋め込んだもの） |
| `app.jsx` | フロントのソース（React/JSX）。**アプリのロジックはここを編集する** |
| `index.template.html` | HTMLシェル（`<head>`・CSS・React CDN）。`/*__APP__*/` にJSが入る |
| `build.js` | `app.jsx` + `data.json` → `index.html` を生成するビルドスクリプト |
| `data.json` | 全当選番号（全回） |
| `fetch_loto7.py` | 当選番号を取得して `data.json` / `index.html` を更新（取得は多段フォールバック） |
| `notify_loto7.py` | 新しい回が出た時に当選チェック＋結果メール送信 |
| `notify_error.py` | 取得失敗／データ滞留時に自分へ警告メール |
| `.github/workflows/update-loto7.yml` | 自動更新ワークフロー |
| `manifest.json` / `sw.js` / `icon.png` | PWA用 |

---

## データ取得（多段フォールバック）

みずほ銀行は Akamai でデータセンターIPも素のHTTPも 403 で弾くため、**ブラウザ描画する Jina AI Reader 経由**でのみ取得できる。Jina障害に備え、別インフラの直接取得サイトを保険として多段化している（`fetch_loto7.py` の `fetch_latest()`）。

1. **主**: `r.jina.ai` 経由でみずほ公式ページ（Markdown）
2. **保険1**: `ohtashp.com` の一覧表（全回・構造化）
3. **保険2**: `tokaikensyo.com`（最新回のみ）

最初に取得できた経路の結果を採用。すべて失敗した場合は、データ鮮度チェック（最新回が8日以上前）で `fetch_error` を立て、警告メールを送る。

アプリ側（`app.jsx`）は GitHub Pages 上の `data.json` を読み込んで表示する（10分ごとに再読込）。

---

## ビルド方法

`app.jsx`（ロジック）を変更したら再ビルドして `index.html` を更新する:

```bash
npm install @babel/standalone
node build.js
```

- JSXを **classic ランタイム**でトランスパイル（`React.createElement` 出力。ブラウザ内 babel は不要）
- `SEED_DATA` は `data.json` の最新50件から自動注入される（ソースが古くても出力は最新）

> `node_modules` / `package-lock.json` は `.gitignore` 済み。

---

## 自動化

### GitHub Actions（`update-loto7.yml`）
- スケジュール: `0 12 * * 5`（金21:00 JST）/ `0 0 * * 6`（土9:00 JST・保険）
- 手動実行（workflow_dispatch）の入力:
  - `test_alert=true` … エラー通知メールをテスト送信（`FORCE_STALE`）
  - `test_fallback=true` … 主(Jina)をスキップしフォールバック取得を検証（`FORCE_FALLBACK`）
- 必要な Secrets: `GMAIL_USER` / `GMAIL_APP_PASSWORD` / `NOTIFY_EMAIL`
- ステップ: 取得 → push（`index.html`/`data.json`）→ **新regがある時だけ**結果メール → 失敗/滞留時は警告メール

### cron-job.org（定刻起動）
GitHub無料cronは最大半日遅延するため、cron-job.org から毎週金21:00 JST に workflow_dispatch を叩いて定刻化している。

- ジョブ「loto7 自動更新」: `POST https://api.github.com/repos/ogachan111/loto7/actions/workflows/update-loto7.yml/dispatches`、body `{"ref":"main1"}`
- ヘッダー: `Authorization: Bearer <PAT>` / `Accept: application/vnd.github+json` / `X-GitHub-Api-Version: 2022-11-28` / `Content-Type: application/json`
- ⚠️ **トークン「cron-job loto7」の有効期限: 2027-06-26**。失効前に再発行→cron-job.org に貼り直すこと（失効後はGitHubの遅延cronのみで動作継続）。

---

## メモ
- ロト7は完全ランダム抽選。統計予想は参考情報であり当選を保証しない。
