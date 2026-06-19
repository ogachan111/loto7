import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
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
    """既存のdata.jsonを読み込む"""
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ 既存data.json読み込み: {len(data)}件")
            return {d["round"]: d for d in data}
    except:
        print("📋 data.jsonなし → 既知データで初期化")
        return {d["round"]: d for d in KNOWN_DATA}

def parse_loto7_page(html):
    """みずほ銀行のロト7ページからデータを解析"""
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    # テーブルから取得
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td","th"])]
            if not cells:
                continue
            full = " ".join(cells)

            # 回号を探す
            round_m = re.search(r'第\s*(\d+)\s*回', full)
            if not round_m:
                continue

            # 日付を探す
            date_m = re.search(r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日?', full)
            if not date_m:
                continue

            # 数字を探す（1〜37の範囲）
            nums = []
            for cell in cells:
                cell_nums = re.findall(r'\b(\d{1,2})\b', cell)
                for n in cell_nums:
                    n = int(n)
                    if 1 <= n <= 37:
                        nums.append(n)

            if len(nums) >= 9:
                try:
                    rn = int(round_m.group(1))
                    dt = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
                    # 重複を除去して最初の9個
                    unique_nums = []
                    seen = set()
                    for n in nums:
                        if n not in seen:
                            unique_nums.append(n)
                            seen.add(n)
                        if len(unique_nums) == 9:
                            break

                    if len(unique_nums) >= 9:
                        results[rn] = {
                            "round": rn,
                            "date": dt,
                            "numbers": sorted(unique_nums[:7]),
                            "bonus": sorted(unique_nums[7:9])
                        }
                except:
                    pass

    return results

def fetch_backnumber_page(from_round, to_round):
    """みずほ銀行の過去当選番号ページを取得"""
    url = f"https://www.mizuhobank.co.jp/takarakuji/check/loto/backnumber/detail.html?fromto={from_round}_{to_round}&type=loto7"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            res.encoding = "utf-8"
            data = parse_loto7_page(res.text)
            if data:
                print(f"✅ 第{from_round}〜{to_round}回: {len(data)}件取得")
            else:
                print(f"⚠️ 第{from_round}〜{to_round}回: データ解析失敗")
            return data
        else:
            print(f"⚠️ 第{from_round}〜{to_round}回: HTTP {res.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ 第{from_round}〜{to_round}回: {e}")
        return {}

def fetch_latest():
    """最新の当選番号を取得"""
    url = "https://www.mizuhobank.co.jp/takarakuji/check/loto/loto7/index.html"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            res.encoding = "utf-8"
            data = parse_loto7_page(res.text)
            if data:
                print(f"✅ 最新データ: {len(data)}件取得")
            return data
        else:
            print(f"⚠️ 最新データ: HTTP {res.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ 最新データ取得失敗: {e}")
        return {}

def fetch_all_historical(existing, latest_round):
    """全過去データを20回ずつ取得"""
    all_data = {}
    
    # 20回ずつのブロックで取得（みずほ銀行のURLパターン）
    # 第1回〜第681回を20回ずつ
    step = 20
    for start in range(1, latest_round + 1, step):
        end = min(start + step - 1, latest_round)
        
        # 既存データが揃っているブロックはスキップ
        block_rounds = set(range(start, end + 1))
        existing_rounds = set(existing.keys())
        missing = block_rounds - existing_rounds
        
        if not missing:
            print(f"⏭️ 第{start}〜{end}回: 既存データあり、スキップ")
            continue
        
        data = fetch_backnumber_page(start, end)
        all_data.update(data)
        
        if data:
            time.sleep(1)  # サーバー負荷軽減

    return all_data

def save_data(merged):
    """data.jsonとindex.htmlを更新"""
    sorted_data = sorted(merged.values(), key=lambda x: x["round"], reverse=True)
    
    # data.jsonを保存
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print(f"✅ data.json保存: {len(sorted_data)}件")

    # index.htmlのSEED_DATAを最新50件に更新
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
        print(f"✅ index.html更新: 最新{len(recent)}件をSEED_DATAに設定")
    except Exception as e:
        print(f"⚠️ index.html更新失敗: {e}")

    latest = sorted_data[0]
    print(f"\n📊 最終結果:")
    print(f"   総件数: {len(sorted_data)}件")
    print(f"   最新: 第{latest['round']}回 ({latest['date']})")
    print(f"   最古: 第{sorted_data[-1]['round']}回 ({sorted_data[-1]['date']})")

if __name__ == "__main__":
    print("=" * 50)
    print("ロト7 全当選番号データ取得開始")
    print("=" * 50)

    # 既存データ読み込み
    merged = load_existing_data()
    print(f"既存: {len(merged)}件")

    # 最新データ取得
    print("\n--- 最新データ取得 ---")
    latest = fetch_latest()
    merged.update(latest)

    # 最新回号を確認
    latest_round = max(merged.keys()) if merged else 681
    print(f"最新回号: 第{latest_round}回")

    # 過去データ取得
    print("\n--- 過去データ取得 ---")
    historical = fetch_all_historical(merged, latest_round)
    merged.update(historical)

    # 保存
    print("\n--- データ保存 ---")
    save_data(merged)
    print("\n✅ 完了！")
