import smtplib
import os
from email.mime.text import MIMEText


def main():
    user = os.environ.get("GMAIL_USER")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("NOTIFY_EMAIL")
    if not all([user, pw, to]):
        print("⚠️ 環境変数が設定されていないため、エラー通知メールは送れません")
        return

    reason = os.environ.get("REASON", "不明なエラー")
    run_url = os.environ.get("RUN_URL", "")
    days = os.environ.get("DAYS_OLD", "")

    body = (
        "ロト7アプリの自動更新でエラーが発生しました。\n\n"
        f"■ 理由: {reason}\n"
        f"■ 最新データの経過日数: {days}日\n"
        f"■ 実行ログ: {run_url}\n\n"
        "みずほ銀行 / Jina AI Reader の一時的な不調か、ページ構成の変更が\n"
        "考えられます。上記の実行ログを確認してください。\n"
        "（一時的な不調なら次回の自動実行で復旧することもあります）"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "⚠️【ロト7】自動更新エラーのお知らせ"
    msg["From"] = user
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(user, pw)
            s.sendmail(user, to, msg.as_string())
        print(f"✅ エラー通知メール送信 → {to}")
    except Exception as e:
        print(f"❌ エラー通知メール送信失敗: {e}")


if __name__ == "__main__":
    main()
