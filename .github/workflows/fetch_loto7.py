import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

def fetch_loto7():
    """みずほ銀行からロト7当選番号を取得"""
    url = "https://www.mizuhobank.co.jp/takarakuji/check/loto/loto7/index.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        # テーブルから当選番号を取得
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                texts = [c.get_text(strip=True) for c in cells]
                full = " ".join(texts)

                # 回号を探す
                round_m = re.search(r'第(\d+)回', full)
                date_m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', full)
                nums = re.findall(r'\b([1-9]|[1-2]\d|3[0-7])\b', full)

                if round_m and len(nums) >= 9:
                    try:
                        round_num = int(round_m.group(1))
                        date_str = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}" if date_m else ""
                        all_nums = [int(n) for n in nums[:9]]
                        numbers = sorted(all_nums[:7])
                        bonus = sorted(all_nums[7:9])
                        results.append({
                            "round": round_num,
                            "date": date_str,
                            "numbers": numbers,
                            "bonus": bonus
                        })
                    except:
                        pass

        if results:
            print(f"✅ みずほ銀行から{len(results)}件取得成功")
            return sorted(results, key=lambda x: x["round"], reverse=True)

    except Exception as e:
        print(f"⚠️ みずほ銀行取得失敗: {e}")

    # フォールバック：宝くじ公式サイト
    try:
        url2 = "https://www.takarakuji-official.jp/lottery/loto7/"
        res2 = requests.get(url2, headers=headers, timeout=15)
        res2.encoding = "utf-8"
        soup2 = BeautifulSoup(res2.text, "html.parser")
        text = soup2.get_text()

        round_m = re.search(r'第(\d+)回', text)
        date_m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        nums = re.findall(r'\b([1-9]|[1-2]\d|3[0-7])\b', text)

        if round_m and len(nums) >= 9:
            round_num = int(round_m.group(1))
            date_str = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}" if date_m else ""
            all_nums = [int(n) for n in nums[:9]]
            numbers = sorted(all_nums[:7])
            bonus = sorted(all_nums[7:9])
            print(f"✅ 宝くじ公式から取得成功: 第{round_num}回")
            return [{"round": round_num, "date": date_str, "numbers": numbers, "bonus": bonus}]

    except Exception as e:
        print(f"⚠️ 宝くじ公式取得失敗: {e}")

    return []

def update_html(new_data):
    """index.htmlのSEED_DATAを更新"""
    if not new_data:
        print("❌ 取得データなし、更新スキップ")
        return False

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 既存のSEED_DATAを取得
    m = re.search(r'const SEED_DATA = \[([\s\S]*?)\];', html)
    existing = []
    if m:
        try:
            existing = json.loads("[" + m.group(1) + "]")
        except:
            pass

    # マージして重複を除去
    merged = {d["round"]: d for d in existing}
    for d in new_data:
        merged[d["round"]] = d

    sorted_data = sorted(merged.values(), key=lambda x: x["round"], reverse=True)[:50]

    # JSON文字列に変換
    data_str = json.dumps(sorted_data, ensure_ascii=False, indent=2)
    data_str = data_str.replace('"round"', '"round"').strip()

    # HTMLを更新
    new_html = re.sub(
        r'const SEED_DATA = \[[\s\S]*?\];',
        f'const SEED_DATA = {data_str};',
        html,
        count=1
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)

    latest = sorted_data[0]
    print(f"✅ 更新完了: 第{latest['round']}回 [{','.join(map(str,latest['numbers']))}] B[{','.join(map(str,latest['bonus']))}]")
    print(f"   合計{len(sorted_data)}件のデータを保持")
    return True

if __name__ == "__main__":
    print("ロト7当選番号を取得中...")
    data = fetch_loto7()
    if data:
        update_html(data)
    else:
        print("⚠️ データ取得失敗、HTMLは更新しません")
