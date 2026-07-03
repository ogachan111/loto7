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

def get_prediction():
    """predict.js が生成した prediction.json を読む（無ければ None → 従来の簡易メール）"""
    try:
        with open("prediction.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ prediction.json が読めません（簡易メールで送信）: {e}")
        return None

BALL_BG = {
    "main":  "linear-gradient(135deg,#6366f1,#3b82f6)",
    "bonus": "linear-gradient(135deg,#f43f5e,#ec4899)",
    "hit":   "linear-gradient(135deg,#eab308,#f59e0b)",
    "pred":  "linear-gradient(135deg,#8b5cf6,#7c3aed)",
}

def ball(n, kind="main", size=36):
    fs = 13 if size >= 36 else 11
    return (f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:{size}px;height:{size}px;border-radius:50%;background:{BALL_BG[kind]};'
            f'color:#fff;font-weight:700;font-size:{fs}px;margin:3px;">{n:02d}</span>')

def section(title, inner):
    return (f'<div style="margin-bottom:18px;">'
            f'<p style="color:#a5b4fc;font-size:13px;font-weight:700;margin:0 0 8px;border-bottom:1px solid #312e81;padding-bottom:4px;">{title}</p>'
            f'{inner}</div>')

def review_html(pred):
    """前回予想の答え合わせセクション（本数字一致は金色で表示）"""
    rv = pred.get("review")
    if not rv:
        return ""
    win = set(pred["latest"]["numbers"])
    bon = set(pred["latest"]["bonus"])
    rows = []
    for s in rv["sets"]:
        balls = "".join(
            ball(n, "hit" if n in win else ("bonus" if n in bon else "pred"), 30)
            for n in s["numbers"]
        )
        result = f'{len(s["hits"])}個一致'
        if s["bonusHits"]:
            result += f' +ボーナス{len(s["bonusHits"])}個'
        if s["grade"]:
            result += f' <span style="color:#86efac;font-weight:700;">{s["grade"]}</span>'
        rows.append(
            f'<div style="margin-bottom:10px;">'
            f'<p style="color:#94a3b8;font-size:11px;margin:0 0 2px;">{s["label"]} — <span style="color:#e2e8f0;">{result}</span></p>'
            f'<div>{balls}</div></div>'
        )
    note = '<p style="color:#475569;font-size:10px;margin:6px 0 0;">金色 = 本数字一致（抽選前に固定されていた予想での結果です）</p>'
    return section("📝 前回予想の答え合わせ", "".join(rows) + note)

def next_html(pred):
    """次回の固定予想セクション（アプリの予想と同一）"""
    nx = pred.get("next")
    if not nx:
        return ""
    rows = []
    for s in nx["sets"]:
        balls = "".join(ball(n, "pred", 30) for n in s["numbers"])
        bballs = "".join(ball(n, "bonus", 24) for n in s.get("bonus") or [])
        rows.append(
            f'<div style="margin-bottom:10px;">'
            f'<p style="color:#94a3b8;font-size:11px;margin:0 0 2px;">{s["label"]}</p>'
            f'<div>{balls}'
            + (f'<span style="color:#f43f5e;font-size:10px;font-weight:700;margin:0 2px 0 8px;">B</span>{bballs}' if bballs else "")
            + '</div></div>'
        )
    intro = nx.get("commentaryIntro") or ""
    if intro:
        intro = f'<p style="color:#64748b;font-size:11px;margin:6px 0 0;line-height:1.6;">{intro}</p>'
    note = '<p style="color:#475569;font-size:10px;margin:6px 0 0;">🔒 この予想は次回抽選まで固定です（アプリの表示と同じ番号）</p>'
    return section("🔮 次回の予想 4セット", "".join(rows) + intro + note)

def stats_html(pred):
    st = pred.get("statsSummary")
    if not st:
        return ""
    hot = "・".join(f'{x["num"]}番({x["count"]}回)' for x in st.get("hotTop3", []))
    cold = st.get("cold20", [])
    cold_s = "・".join(f'{n}番' for n in cold) if cold else "なし"
    inner = (f'<p style="color:#cbd5e1;font-size:11px;margin:0 0 4px;">分析データ: 全{st["n"]}回分</p>'
             f'<p style="color:#cbd5e1;font-size:11px;margin:0 0 4px;">🔥 頻出TOP3: {hot}</p>'
             f'<p style="color:#cbd5e1;font-size:11px;margin:0;">❄️ 直近20回未出現: {cold_s}</p>')
    return section("📊 統計サマリー", inner)

def send_email(latest, pred=None):
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

    balls_html = "".join(ball(n, "main") for n in win_nums)
    bonus_html = "".join(ball(n, "bonus") for n in bonus_nums)

    result_sec = (
        f'<div style="margin-bottom:16px;">'
        f'<p style="color:#64748b;font-size:11px;margin:0 0 8px;">当選番号</p>'
        f'<div>{balls_html}</div>'
        f'<p style="color:#64748b;font-size:11px;margin:12px 0 8px;">ボーナス数字</p>'
        f'<div>{bonus_html}</div>'
        f'</div>'
    )

    extra = ""
    if pred:
        extra = review_html(pred) + next_html(pred) + stats_html(pred)

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
                {result_sec}
                {extra}
                <div style="text-align:center;margin-top:20px;">
                    <a href="https://ogachan111.github.io/loto7/"
                       style="background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">
                        アプリで詳細を見る
                    </a>
                </div>
            </div>
            <div style="background:#0f0e1a;padding:10px;text-align:center;">
                <p style="color:#334155;font-size:10px;margin:0;">※ロト7は完全ランダム抽選です。予想は統計に基づく参考情報で、当選を保証するものではありません。</p>
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
        print(f"   内容: 結果{'+答え合わせ+次回予想+統計' if pred else 'のみ（簡易版）'}")
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

    pred = get_prediction()
    # prediction.json が古い回のものなら使わない（安全側）
    if pred and pred.get("latest", {}).get("round") != latest["round"]:
        print(f"⚠️ prediction.json の回({pred.get('latest',{}).get('round')})が最新({latest['round']})と不一致のため簡易メールで送信")
        pred = None

    send_email(latest, pred)
