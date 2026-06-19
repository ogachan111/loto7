import smtplib
import os
import re
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_data_from_html():
    """index.htmlから最新データを取得"""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    latest = None

    # パターン1: const SEED_DATA = [...];
    m = re.search(r'const SEED_DATA = (\[[\s\S]*?\]);', html)
    if m:
        try:
            data = json.loads(m.group(1))
            if data:
                latest = data[0]
        except:
            pass

    # パターン2: 直接数字を探す
    if not latest:
        round_m = re.search(r'"round"\s*:\s*(\d+)', html)
        date_m = re.search(r'"date"\s*:\s*"([^"]+)"', html)
        nums_m = re.findall(r'"numbers"\s*:\s*\[([^\]]+)\]', html)
        bonus_m = re.findall(r'"bonus"\s*:\s*\[([^\]]+)\]', html)
        if round_m and date_m and nums_m and bonus_m:
            try:
                latest = {
                    "round": int(round_m.group(1)),
                    "date": date_m.group(1),
                    "numbers": [int(x.strip()) for x in nums_m[0].split(",")],
                    "bonus": [int(x.strip()) for x in bonus_m[0].split(",")]
                }
            except:
                pass

    return latest

def judge_grade(my_nums, win_nums, bonus_nums):
    s = set(my_nums)
    match = len([n for n in win_nums if n in s])
    bonus = len([n for n in bonus_nums if n in s])
    if match == 7: return {"grade":1,"label":"🏆 1等！","prize":"約4億円"}
    if match == 6 and bonus >= 1: return {"grade":2,"label":"🥇 2等！","prize":"約3000万円"}
    if match == 6: return {"grade":3,"label":"🥈 3等！","prize":"約100万円"}
    if match == 5 and bonus >= 1: return {"grade":4,"label":"🥉 4等！","prize":"約1万円"}
    if match == 5: return {"grade":5,"label":"✨ 5等！","prize":"約3000円"}
    if match == 4: return {"grade":6,"label":"🎉 6等！","prize":"約1000円"}
    if match == 3 or (match == 2 and bonus >= 1): return {"grade":7,"label":"🎊 7等！","prize":"約800円"}
    return None

def send_email(latest):
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    notify_email = os.environ.get("NOTIFY_EMAIL")

    if not all([gmail_user, gmail_password, notify_email]):
        print("⚠️ 環境変数が設定されていません")
        return

    win_nums = latest["numbers"]
    bonus_nums = latest["bonus"]
    round_num = latest["round"]
    date = latest["date"]

    subject = f"🎯【ロト7結果】第{round_num}回 当選番号のお知らせ ({date})"

    balls_html = "".join([
        f'<span style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#3b82f6);color:#fff;font-weight:700;font-size:13px;margin:3px;">{n:02d}</span>'
        for n in win_nums
    ])
    bonus_html = "".join([
        f'<span style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#f43f5e,#ec4899);color:#fff;font-weight:700;font-size:13px;margin:3px;">{n:02d}</span>'
        for n in bonus_nums
    ])

    html_body = f"""
    <html>
    <body style="font-family:sans-serif;background:#0f0e1a;padding:20px;">
        <div style="max-width:480px;margin:0 auto;background:#1e1b4b;border-radius:16px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#312e81,#1e1b4b);padding:20px;text-align:center;">
                <div style="font-size:32px;">🎯</div>
                <h1 style="color:#a5b4fc;margin:8px 0 4px;font-size:20px;">LOTO7 第{round_num}回 結果</h1>
                <p style="color:#64748b;margin:0;font-size:12px;">{date}</p>
            </div>
            <div style="padding:20px;">
                <div style="margin-bottom:16px;">
                    <p style="color:#64748b;font-size:11px;margin:0 0 8px;">当選番号</p>
                    <div>{balls_html}</div>
                    <p style="color:#64748b;font-size:11px;margin:12px 0 8px;">ボーナス数字</p>
                    <div>{bonus_html}</div>
                </div>
                <div style="text-align:center;margin-top:20px;">
                    <a href="https://ogachan111.github.io/loto7/"
                       style="background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">
                        アプリで詳細を見る
                    </a>
                </div>
            </div>
            <div style="background:#0f0e1a;padding:10px;text-align:center;">
                <p style="color:#334155;font-size:10px;margin:0;">※ロト7は完全ランダム抽選です</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = notify_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, notify_email, msg.as_string())
        print(f"✅ メール送信完了 → {notify_email}")
        print(f"   件名: {subject}")
    except Exception as e:
        print(f"❌ メール送信失敗: {e}")

if __name__ == "__main__":
    print("ロト7当選チェック中...")
    latest = get_data_from_html()

    if not latest:
        print("❌ 当選番号データが取得できませんでした")
        # エラーで終了せず警告のみ（メールは送らない）
        exit(0)

    print(f"最新: 第{latest['round']}回 [{','.join(map(str,latest['numbers']))}] B[{','.join(map(str,latest['bonus']))}]")
    send_email(latest)
