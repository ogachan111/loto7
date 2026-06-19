import smtplib
import os
import re
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_data_from_html():
    """index.htmlから最新データと保存セットを取得"""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # SEED_DATAから最新当選番号を取得
    m = re.search(r'const SEED_DATA = (\[[\s\S]*?\]);', html)
    latest = None
    if m:
        try:
            data = json.loads(m.group(1))
            if data:
                latest = data[0]
        except:
            pass

    return latest

def judge_grade(my_nums, win_nums, bonus_nums):
    """等級判定"""
    s = set(my_nums)
    match = len([n for n in win_nums if n in s])
    bonus = len([n for n in bonus_nums if n in s])

    if match == 7:
        return {"grade": 1, "label": "🏆 1等！", "prize": "約4億円"}
    if match == 6 and bonus >= 1:
        return {"grade": 2, "label": "🥇 2等！", "prize": "約3000万円"}
    if match == 6:
        return {"grade": 3, "label": "🥈 3等！", "prize": "約100万円"}
    if match == 5 and bonus >= 1:
        return {"grade": 4, "label": "🥉 4等！", "prize": "約1万円"}
    if match == 5:
        return {"grade": 5, "label": "✨ 5等！", "prize": "約3000円"}
    if match == 4:
        return {"grade": 6, "label": "🎉 6等！", "prize": "約1000円"}
    if match == 3 or (match == 2 and bonus >= 1):
        return {"grade": 7, "label": "🎊 7等！", "prize": "約800円"}
    return None

def send_email(latest, hit_sets, all_sets):
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

    has_hit = len(hit_sets) > 0

    if has_hit:
        subject = f"🎯【ロト7当選！】第{round_num}回 {hit_sets[0]['result']['label']}"
    else:
        subject = f"🎯【ロト7結果】第{round_num}回 当選番号のお知らせ"

    # 当選番号HTML
    balls_html = "".join([
        f'<span style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#3b82f6);color:#fff;font-weight:700;font-size:13px;margin:3px;">{n:02d}</span>'
        for n in win_nums
    ])
    bonus_html = "".join([
        f'<span style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#f43f5e,#ec4899);color:#fff;font-weight:700;font-size:13px;margin:3px;">{n:02d}</span>'
        for n in bonus_nums
    ])

    # 登録セットのHTML
    sets_html = ""
    if all_sets:
        for i, s in enumerate(all_sets):
            result = judge_grade(s["numbers"], win_nums, bonus_nums)
            match_count = len([n for n in win_nums if n in set(s["numbers"])])
            bonus_count = len([n for n in bonus_nums if n in set(s["numbers"])])

            set_balls = "".join([
                f'<span style="display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;background:{("#fde047" if n in win_nums else "#6366f1") if n in win_nums else ("#f43f5e" if n in bonus_nums else "#334155")};color:#fff;font-weight:700;font-size:11px;margin:2px;">{n:02d}</span>'
                for n in s["numbers"]
            ])

            result_str = result["label"] if result else f"一致{match_count}個"
            if bonus_count > 0 and not result:
                result_str += f" + ボーナス{bonus_count}個"

            sets_html += f"""
            <div style="background:#1e1b4b;border-radius:10px;padding:12px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="color:#a5b4fc;font-size:12px;font-weight:700;">{s.get('label','セット'+str(i+1))}</span>
                    <span style="color:{'#fde047' if result else '#64748b'};font-size:12px;font-weight:700;">{result_str}</span>
                </div>
                <div>{set_balls}</div>
            </div>
            """

    hit_banner = ""
    if has_hit:
        hit_banner = f"""
        <div style="background:linear-gradient(135deg,#78350f,#92400e);border:2px solid #fde047;border-radius:12px;padding:16px;margin-bottom:16px;text-align:center;">
            <div style="font-size:28px;margin-bottom:4px;">🏆</div>
            <div style="color:#fde047;font-size:18px;font-weight:900;">{hit_sets[0]['result']['label']}</div>
            <div style="color:#fbbf24;font-size:13px;">おめでとうございます！</div>
        </div>
        """

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
                {hit_banner}
                <div style="margin-bottom:16px;">
                    <p style="color:#64748b;font-size:11px;margin:0 0 6px;">当選番号</p>
                    <div>{balls_html}</div>
                    <p style="color:#64748b;font-size:11px;margin:10px 0 6px;">ボーナス数字</p>
                    <div>{bonus_html}</div>
                </div>
                {'<div style="margin-bottom:16px;"><p style="color:#64748b;font-size:11px;margin:0 0 8px;">購入セット照合結果</p>' + sets_html + '</div>' if all_sets else ''}
                <div style="text-align:center;margin-top:16px;">
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
        exit(1)

    print(f"最新: 第{latest['round']}回 [{','.join(map(str,latest['numbers']))}] B[{','.join(map(str,latest['bonus']))}]")

    # 当選チェック（登録セットがない場合でも結果メールを送信）
    hit_sets = []
    all_sets = []

    # index.htmlからは登録セットを取得できないため、結果通知のみ行う
    send_email(latest, hit_sets, all_sets)
