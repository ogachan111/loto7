import requests
import re
import json
import time
import os
from datetime import datetime

# みずほ銀行はAkamaiでデータセンターIP（GitHub Actions等）も住宅IPの素のHTTPも
# 403でブロックする。ブラウザ描画する Jina AI Reader (r.jina.ai) だけが通る。
# Jinaが落ちた/レート制限/仕様変更でも止まらないよう、別インフラの直接取得サイト
# (tokaikensyo.com・Akamai非保護) をフォールバック源として多段化している。
MIZUHO_URL = "https://www.mizuhobank.co.jp/takarakuji/check/loto/loto7/index.html"
JINA_URL = "https://r.jina.ai/" + MIZUHO_URL
# フォールバック源（いずれもAkamai非保護で直接取得可）
OHTASHP_URL = "https://www.ohtashp.com/topics/takarakuji/loto7/"  # 全回の一覧表（構造化・堅牢）
TOKAI_URL = "https://tokaikensyo.com/campaignwinning/loto7/"      # 最新回のみ（個人ブログ）

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*",
}

# data.jsonが無い場合のフォールバック（直近の既知データ）
KNOWN_DATA = [
    {"round":682,"date":"2026-06-19","numbers":[11,14,17,23,28,30,36],"bonus":[12,20]},
    {"round":681,"date":"2026-06-12","numbers":[1,10,12,13,19,33,35],"bonus":[14,37]},
    {"round":680,"date":"2026-06-05","numbers":[9,10,22,26,27,31,36],"bonus":[20,29]},
]


def load_existing_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ 既存data.json: {len(data)}件")
            return {d["round"]: d for d in data}
    except Exception:
        print("📋 data.jsonなし → 既知データで初期化")
        return {d["round"]: d for d in KNOWN_DATA}


def parse_markdown(text):
    """Jina AI Readerが返すMarkdownからロト7の各回を解析する。
    みずほのページは下記のような行で構成される：
        | 回別 | 第683回 |
        | 抽せん日 | 2026年6月26日 |
        | 本数字 | **11** | **21** | ... | **36** |
        | ボーナス数字 | **(08)** | **(32)** |  |
    """
    results = {}
    cur = None
    for line in text.splitlines():
        rm = re.match(r'\s*\|\s*回別\s*\|\s*第\s*(\d+)\s*回', line)
        if rm:
            cur = int(rm.group(1))
            results[cur] = {"round": cur}
            continue
        if cur is None:
            continue
        dm = re.match(r'\s*\|\s*抽せん日\s*\|\s*(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日', line)
        if dm:
            results[cur]["date"] = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
            continue
        nm = re.match(r'\s*\|\s*本数字\s*\|(.*)', line)
        if nm:
            nums = [int(x) for x in re.findall(r'\d{1,2}', nm.group(1))]
            nums = [n for n in nums if 1 <= n <= 37]
            if len(nums) >= 7:
                results[cur]["numbers"] = sorted(nums[:7])
            continue
        bm = re.match(r'\s*\|\s*ボーナス数字\s*\|(.*)', line)
        if bm:
            bnums = [int(x) for x in re.findall(r'\d{1,2}', bm.group(1))]
            bnums = [n for n in bnums if 1 <= n <= 37]
            if len(bnums) >= 2:
                results[cur]["bonus"] = sorted(bnums[:2])
            continue

    # 完全な（回号・日付・本数字7個・ボーナス2個が揃った）ものだけ採用
    valid = {}
    for rn, d in results.items():
        if d.get("date") and len(d.get("numbers", [])) == 7 and len(d.get("bonus", [])) == 2:
            valid[rn] = d
    return valid


def parse_tokai(html):
    """tokaikensyo.com（フォールバック）の最新結果を解析する。
    タグ除去後はこんな並び：
        ロト７【第683回】 … 抽選日：2026年6月26日 … 当せん番号 11 21 22 25 28 29 36 ボーナス番号 08 32
    最新回1件のみ取得できればよい（新regの検出に十分）。
    """
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    m = re.search(
        r'第\s*(\d+)\s*回'
        r'.*?(?:抽せん日|抽選日)[：:\s]*(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日'
        r'.*?当せん番号\s+((?:\d{1,2}\s+){6}\d{1,2})'
        r'\s+ボーナス(?:数字|番号)\s+(\d{1,2})\s+(\d{1,2})',
        text)
    if not m:
        return {}
    rn = int(m.group(1))
    dt = f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    nums = sorted(int(x) for x in m.group(5).split())
    bonus = sorted([int(m.group(6)), int(m.group(7))])
    if len(nums) != 7:
        return {}
    return {rn: {"round": rn, "date": dt, "numbers": nums, "bonus": bonus}}


def fetch_jina():
    """主: Jina AI Reader経由でみずほ最新ページ(markdown)。直近数回分。"""
    for attempt in range(1, 4):
        try:
            res = requests.get(JINA_URL, headers=HEADERS, timeout=90)
            if res.status_code == 200:
                res.encoding = "utf-8"
                data = parse_markdown(res.text)
                if data:
                    print(f"✅ [Jina] {len(data)}件取得（第{min(data)}〜{max(data)}回）")
                    return data
                print(f"⚠️ [Jina] 取得できたが解析0件（試行{attempt}）")
            else:
                print(f"⚠️ [Jina] HTTP {res.status_code}（試行{attempt}）")
        except Exception as e:
            print(f"⚠️ [Jina] 取得失敗（試行{attempt}）: {e}")
        time.sleep(5)
    return {}


def parse_ohtashp(html):
    """ohtashp.com の一覧表（フォールバック）を解析する。
    タグ除去後はこんな並び（全回・降順）：
        第683回 2026/6/26 11 21 22 25 28 29 36 08 32 2 4億4,758万円 0円
    日付の後ろに本数字7個＋ボーナス2個の計9個が並ぶ。
    """
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    results = {}
    for m in re.finditer(
            r'第(\d+)回\s+(\d{4})/(\d{1,2})/(\d{1,2})\s+((?:\d{1,2}\s+){8}\d{1,2})', text):
        nums = [int(x) for x in m.group(5).split()]
        if len(nums) != 9 or any(n < 1 or n > 37 for n in nums):
            continue
        rn = int(m.group(1))
        dt = f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        results[rn] = {"round": rn, "date": dt,
                       "numbers": sorted(nums[:7]), "bonus": sorted(nums[7:9])}
    return results


def fetch_ohtashp():
    """フォールバック1: ohtashp.com の一覧表を直接取得（Jina非依存・全回）。"""
    for attempt in range(1, 3):
        try:
            res = requests.get(OHTASHP_URL, headers=HEADERS, timeout=30)
            if res.status_code == 200:
                res.encoding = res.apparent_encoding or "utf-8"
                data = parse_ohtashp(res.text)
                if data:
                    print(f"✅ [ohtashp] フォールバック取得: {len(data)}件（第{min(data)}〜{max(data)}回）")
                    return data
                print(f"⚠️ [ohtashp] 取得できたが解析0件（試行{attempt}）")
            else:
                print(f"⚠️ [ohtashp] HTTP {res.status_code}（試行{attempt}）")
        except Exception as e:
            print(f"⚠️ [ohtashp] 取得失敗（試行{attempt}）: {e}")
        time.sleep(3)
    return {}


def fetch_tokai():
    """フォールバック2: tokaikensyo.com を直接取得（Jina非依存・Akamai非保護）。最新回のみ。"""
    for attempt in range(1, 3):
        try:
            res = requests.get(TOKAI_URL, headers=HEADERS, timeout=30)
            if res.status_code == 200:
                res.encoding = res.apparent_encoding or "utf-8"
                data = parse_tokai(res.text)
                if data:
                    print(f"✅ [tokai] フォールバック取得（第{max(data)}回）")
                    return data
                print(f"⚠️ [tokai] 取得できたが解析0件（試行{attempt}）")
            else:
                print(f"⚠️ [tokai] HTTP {res.status_code}（試行{attempt}）")
        except Exception as e:
            print(f"⚠️ [tokai] 取得失敗（試行{attempt}）: {e}")
        time.sleep(3)
    return {}


def fetch_latest():
    """主(Jina)→フォールバック(ohtashp→tokai)の順で最新データを取得。
    最初に取得できた経路の結果を返す（3段の多重化）。"""
    sources = [("Jina", fetch_jina), ("ohtashp", fetch_ohtashp), ("tokai", fetch_tokai)]
    # テスト用: FORCE_FALLBACK=1 で主(Jina)をスキップしフォールバックを検証できる
    if os.environ.get("FORCE_FALLBACK") == "1":
        print("🧪 FORCE_FALLBACK=1 → 主(Jina)をスキップ")
        sources = sources[1:]
    for name, fn in sources:
        data = fn()
        if data:
            return data
        print(f"⚠️ [{name}] 取得できず → 次の経路へ")
    print("❌ すべての経路で取得失敗")
    return {}


def save_data(merged):
    sorted_data = sorted(merged.values(), key=lambda x: x["round"], reverse=True)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print(f"✅ data.json: {len(sorted_data)}件保存")

    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        recent = sorted_data[:50]
        data_str = json.dumps(recent, ensure_ascii=False)
        new_html = re.sub(
            r'const SEED_DATA = \[[\s\S]*?\];',
            f'const SEED_DATA = {data_str};',
            html, count=1
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"✅ index.html: 最新{len(recent)}件更新")
    except Exception as e:
        print(f"⚠️ index.html更新失敗: {e}")

    latest = sorted_data[0]
    print(f"\n📊 結果: {len(sorted_data)}件 / 最新:第{latest['round']}回({latest['date']}) / 最古:第{sorted_data[-1]['round']}回")


if __name__ == "__main__":
    print("=" * 50)
    print("ロト7 当選番号取得（Jina主＋フォールバック3段）")
    print("=" * 50)

    merged = load_existing_data()

    print("\n--- 最新データ取得 ---")
    latest = fetch_latest()

    new_rounds = sorted(set(latest.keys()) - set(merged.keys()))
    merged.update(latest)

    if new_rounds:
        print(f"🆕 新規追加: {', '.join('第'+str(r)+'回' for r in new_rounds)}")
    else:
        print("ℹ️ 新しい回はありませんでした（既存が最新）")

    # データの鮮度チェック（=自動更新が滞っていないか）。ロト7は毎週金曜抽選なので
    # 最新回の抽選日が8日以上前なら「1サイクル丸ごと取得できていない」とみなす。
    days_old = ""
    stale = False
    try:
        latest_obj = sorted(merged.values(), key=lambda x: x["round"], reverse=True)[0]
        d = datetime.strptime(latest_obj["date"], "%Y-%m-%d")
        days_old = (datetime.utcnow() - d).days
        stale = days_old >= 8 or os.environ.get("FORCE_STALE") == "1"
        print(f"📅 最新回の経過日数: {days_old}日{'  ⚠️ 古い（更新が滞っている可能性）' if stale else ''}")
    except Exception as e:
        stale = True
        print(f"⚠️ 鮮度チェック失敗: {e}")

    # GitHub Actionsへ出力（メール通知の要否判定に使う）
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"new_round={'true' if new_rounds else 'false'}\n")
            f.write(f"fetch_error={'true' if stale else 'false'}\n")
            f.write(f"latest_round={max(merged.keys()) if merged else ''}\n")
            f.write(f"days_old={days_old}\n")

    print("\n--- 保存 ---")
    save_data(merged)
    print("\n✅ 完了！")
