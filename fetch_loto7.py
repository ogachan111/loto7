import requests
import re
import json
import time
import os

# みずほ銀行はデータセンターIP（GitHub Actions等）を403でブロックするため、
# サーバー側で代理取得してくれる Jina AI Reader (r.jina.ai) 経由で取得する。
MIZUHO_URL = "https://www.mizuhobank.co.jp/takarakuji/check/loto/loto7/index.html"
JINA_URL = "https://r.jina.ai/" + MIZUHO_URL

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


def fetch_latest():
    """Jina AI Reader経由でみずほ銀行の最新ページを取得（直近数回分が載っている）"""
    for attempt in range(1, 4):
        try:
            res = requests.get(JINA_URL, headers=HEADERS, timeout=90)
            if res.status_code == 200:
                res.encoding = "utf-8"
                data = parse_markdown(res.text)
                if data:
                    print(f"✅ Jina経由で取得: {len(data)}件（第{min(data)}〜{max(data)}回）")
                    return data
                print(f"⚠️ 取得できたが解析0件（試行{attempt}）")
            else:
                print(f"⚠️ Jina HTTP {res.status_code}（試行{attempt}）")
        except Exception as e:
            print(f"⚠️ Jina取得失敗（試行{attempt}）: {e}")
        time.sleep(5)
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
    print("ロト7 当選番号取得（Jina AI Reader経由）")
    print("=" * 50)

    merged = load_existing_data()
    before_latest = max(merged.keys()) if merged else 0

    print("\n--- 最新データ取得 ---")
    latest = fetch_latest()

    new_rounds = sorted(set(latest.keys()) - set(merged.keys()))
    merged.update(latest)

    if new_rounds:
        print(f"🆕 新規追加: {', '.join('第'+str(r)+'回' for r in new_rounds)}")
    else:
        print("ℹ️ 新しい回はありませんでした（既存が最新）")

    # GitHub Actionsへ「新しい回があったか」を出力（メール通知の要否判定に使う）
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"new_round={'true' if new_rounds else 'false'}\n")
            f.write(f"latest_round={max(merged.keys()) if merged else ''}\n")

    print("\n--- 保存 ---")
    save_data(merged)
    print("\n✅ 完了！")
