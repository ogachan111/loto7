import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime

# より本物に近いブラウザヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Referer": "https://www.mizuhobank.co.jp/takarakuji/check/loto/backnumber/index.html",
}

# 既知の実データ
KNOWN_DATA = [
    {"round":681,"date":"2026-06-12","numbers":[1,10,12,13,19,33,35],"bonus":[14,37]},
    {"round":680,"date":"2026-06-05","numbers":[9,10,22,26,27,31,36],"bonus":[20,29]},
    {"round":679,"date":"2026-05-29","numbers":[6,8,9,18,22,24,35],"bonus":[4,20]},
    {"round":678,"date":"2026-05-22","numbers":[2,6,12,15,24,26,34],"bonus":[18,20]},
    {"round":677,"date":"2026-05-15","numbers":[5,6,7,8,15,17,19],"bonus":[1,33]},
    {"round":676,"date":"2026-05-08","numbers":[2,6,15,19,20,22,27],"bonus":[31,33]},
    {"round":675,"date":"2026-05-01","numbers":[5,8,16,18,24,28,31],"bonus":[6,23]},
    {"round":674,"date":"2026-04-24","numbers":[1,6,7,9,12,22,26],"bonus":[8,14]},
    {"round":673,"date":"2026-04-17","numbers":[6,9,10,12,16,24,32],"bonus":[17,19]},
    {"round":672,"date":"2026-04-10","numbers":[7,11,15,16,17,24,33],"bonus":[6,9]},
    {"round":671,"date":"2026-04-03","numbers":[7,13,16,22,28,33,36],"bonus":[2,25]},
    {"round":670,"date":"2026-03-27","numbers":[3,4,9,10,18,21,37],"bonus":[15,23]},
    {"round":669,"date":"2026-03-20","numbers":[3,5,6,7,9,13,16],"bonus":[11,23]},
    {"round":668,"date":"2026-03-13","numbers":[1,8,11,14,18,22,29],"bonus":[19,35]},
    {"round":667,"date":"2026-03-06","numbers":[9,13,20,22,28,29,33],"bonus":[21,23]},
    {"round":666,"date":"2026-02-27","numbers":[2,17,18,22,23,25,33],"bonus":[16,34]},
    {"round":665,"date":"2026-02-20","numbers":[6,8,14,19,22,25,35],"bonus":[12,17]},
    {"round":664,"date":"2026-02-13","numbers":[3,6,8,14,21,22,31],"bonus":[17,37]},
    {"round":663,"date":"2026-02-06","numbers":[4,6,10,11,13,17,23],"bonus":[25,32]},
    {"round":662,"date":"2026-01-30","numbers":[4,14,15,21,22,24,37],"bonus":[5,20]},
    {"round":661,"date":"2026-01-23","numbers":[7,12,17,22,31,34,35],"bonus":[20,32]},
    {"round":660,"date":"2026-01-16","numbers":[4,6,12,13,16,17,31],"bonus":[14,20]},
    {"round":659,"date":"2026-01-09","numbers":[2,8,9,14,27,34,36],"bonus":[5,18]},
]

def load_existing_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ 既存data.json: {len(data)}件")
            return {d["round"]: d for d in data}
    except:
        print("📋 data.jsonなし → 既知データで初期化")
        return {d["round"]: d for d in KNOWN_DATA}

def parse_page(html):
    """ページからロト7データを解析"""
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 9:
                continue

            texts = [c.get_text(strip=True) for c in cells]

            # 回号
            round_m = re.search(r'第\s*(\d+)\s*回', texts[0])
            if not round_m:
                continue

            # 日付
            date_m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', texts[1])
            if not date_m:
                continue

            # 本数字（3〜9列目）とボーナス数字（10〜11列目）
            try:
                nums = []
                for t in texts[2:]:
                    m = re.match(r'^(\d{1,2})$', t)
                    if m:
                        n = int(m.group(1))
                        if 1 <= n <= 37:
                            nums.append(n)

                if len(nums) >= 9:
                    rn = int(round_m.group(1))
                    dt = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
                    results[rn] = {
                        "round": rn,
                        "date": dt,
                        "numbers": sorted(nums[:7]),
                        "bonus": sorted(nums[7:9])
                    }
            except:
                continue

    return results

def fetch_page(from_r, to_r, session):
    """1ページ分取得"""
    url = f"https://www.mizuhobank.co.jp/takarakuji/check/loto/backnumber/detail.html?fromto={from_r}_{to_r}&type=loto7"
    try:
        res = session.get(url, timeout=20)
        if res.status_code == 200:
            res.encoding = "utf-8"
            data = parse_page(res.text)
            if data:
                print(f"✅ 第{from_r}〜{to_r}回: {len(data)}件")
            else:
                print(f"⚠️ 第{from_r}〜{to_r}回: データ解析失敗")
            return data
        else:
            print(f"⚠️ 第{from_r}〜{to_r}回: HTTP {res.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ 第{from_r}〜{to_r}回: {e}")
        return {}

def fetch_latest(session):
    """最新データ取得"""
    url = "https://www.mizuhobank.co.jp/takarakuji/check/loto/loto7/index.html"
    try:
        res = session.get(url, timeout=20)
        if res.status_code == 200:
            res.encoding = "utf-8"
            data = parse_page(res.text)
            print(f"✅ 最新: {len(data)}件")
            return data
        else:
            print(f"⚠️ 最新: HTTP {res.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ 最新取得失敗: {e}")
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
    print(f"\n📊 結果: {len(sorted_data)}件 / 最新:第{latest['round']}回 / 最古:第{sorted_data[-1]['round']}回")

if __name__ == "__main__":
    print("=" * 50)
    print("ロト7 全当選番号データ取得")
    print("=" * 50)

    merged = load_existing_data()

    # セッションを使ってCookieを維持
    session = requests.Session()
    session.headers.update(HEADERS)

    # まずトップページにアクセスしてCookieを取得
    try:
        top = session.get("https://www.mizuhobank.co.jp/takarakuji/check/loto/backnumber/index.html", timeout=15)
        print(f"トップページ: HTTP {top.status_code}")
        time.sleep(1)
    except:
        pass

    # 最新データ
    print("\n--- 最新データ ---")
    latest = fetch_latest(session)
    merged.update(latest)

    latest_round = max(merged.keys()) if merged else 681
    print(f"最新回: 第{latest_round}回")

    # 過去データ（20回ずつ）
    print("\n--- 過去データ ---")
    success_count = 0
    for start in range(1, latest_round + 1, 20):
        end = min(start + 19, latest_round)
        block = set(range(start, end + 1))
        missing = block - set(merged.keys())

        if not missing:
            print(f"⏭️ 第{start}〜{end}回: スキップ")
            continue

        data = fetch_page(start, end, session)
        if data:
            merged.update(data)
            success_count += 1
            time.sleep(1.5)
        else:
            time.sleep(0.5)

    print(f"\n取得成功: {success_count}ブロック")

    # 保存
    print("\n--- 保存 ---")
    save_data(merged)
    print("\n✅ 完了！")
