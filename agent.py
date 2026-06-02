import os
import time
import schedule
import pytz
from datetime import datetime
from dotenv import load_dotenv

from tools.gmail import fetch_recent_emails, unsubscribe
from tools.classifier import classify_email
from tools.notify import alert_phishing, send_daily_digest, send_startup_message
from db import is_processed, mark_processed, get_todays_summary

load_dotenv()

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
UNSUBSCRIBE_CATEGORIES = {"spam", "promotional"}


def _now() -> str:
    return datetime.now(TIMEZONE).strftime("%H:%M:%S")


def triage_inbox():
    print(f"\n[{_now()}] Running triage...")
    emails = fetch_recent_emails(minutes=30)
    new_emails = [e for e in emails if not is_processed(e["id"])]

    if not new_emails:
        print(f"[{_now()}] No new emails.")
        return

    counts = {}
    for email in new_emails:
        result = classify_email(
            email["sender"],
            email["subject"],
            email["snippet"],
        )
        category = result.get("category", "legitimate")
        reason = result.get("reason", "")
        counts[category] = counts.get(category, 0) + 1

        print(f"  [{category}] {email['subject'][:55]}")

        if category == "phishing":
            alert_phishing(email["sender"], email["subject"], reason)

        if category in UNSUBSCRIBE_CATEGORIES and email["unsubscribe_header"]:
            success = unsubscribe(email["unsubscribe_header"])
            if success:
                print(f"    → Unsubscribed from {email['sender'][:50]}")

        mark_processed(
            email["id"],
            email["subject"],
            email["sender"],
            category,
        )

    print(f"[{_now()}] Done. {counts}")


def send_digest():
    print(f"\n[{_now()}] Sending daily digest...")
    summary = get_todays_summary()
    send_daily_digest(summary)
    total = sum(len(v) for v in summary.values())
    print(f"[{_now()}] Digest sent. {total} emails in summary.")


def main():
    print("=" * 50)
    print("  Zenitsu Email Agent — Starting Up")
    print("=" * 50)

    send_startup_message()
    triage_inbox()

    schedule.every(30).minutes.do(triage_inbox)
    schedule.every().day.at("21:45").do(send_digest)

    print(f"\n[{_now()}] Scheduler running. Triage every 30 min. Digest at 21:45 IST.")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
