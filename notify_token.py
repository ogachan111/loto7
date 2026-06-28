import os
import smtplib
from datetime import date
from email.mime.text import MIMEText

# cron-job.org 用 GitHub fine-grained PAT「cron-job loto7」の有効期限。
# 更新したらこの日付も書き換えること。
EXPIRY = date(2027, 6, 26)
THRESHOLD_DAYS = 21  # この日数以内になったら毎回の実行で催促メールを送る


def main():
    days = (EXPIRY - date.today()).days
    if days > THRESHOLD_DAYS:
        print(f"🔑 トークン期限まで {days} 日（{THRESHOLD_DAYS}日以内で催促）")
        return

    user = os.environ.get("GMAIL_USER")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("NOTIFY_EMAIL")
    if not all([user, pw, to]):
        print("⚠️ 環境変数未設定のため催促メールは送れません")
        return

    body = (
        "cron-job.org の定刻起動に使っている GitHubトークン「cron-job loto7」の\n"
        "有効期限が近づいています。\n\n"
        f"■ 期限: {EXPIRY}（あと {days} 日）\n\n"
        "失効すると毎週金曜21:00の定刻起動が止まります\n"
        "（GitHubの遅延cronでは更新自体は継続します）。\n\n"
        "【更新手順】\n"
        "1) https://github.com/settings/personal-access-tokens で新しいトークンを作成\n"
        "   - Only select repositories → ogachan111/loto7\n"
        "   - Permissions → Actions = Read and write（期限は1年）\n"
        "2) https://console.cron-job.org のジョブ「loto7 自動更新」を編集 → ADVANCED →\n"
        "   Headers の Authorization を『Bearer <新トークン>』に貼り替えて保存\n"
        "   （Bearer の後ろに半角スペース必須）\n"
        "3) 更新後、notify_token.py の EXPIRY を新しい期限に書き換え\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"🔑【ロト7】定刻起動トークンの更新が必要です（あと{days}日）"
    msg["From"] = user
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(user, pw)
            s.sendmail(user, to, msg.as_string())
        print(f"✅ トークン更新リマインド送信（あと{days}日）")
    except Exception as e:
        print(f"❌ リマインド送信失敗: {e}")


if __name__ == "__main__":
    main()
