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

from tools.reminder_db import get_due_reminders
from tools.reminder_parser import parse_reminder
from tools.notify import send_reminder_alert

load_dotenv()

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
UNSUBSCRIBE_CATEGORIES = {"spam", "promotional"}

import requests

HF_SPACE_URL = "https://Pranavathejaswi-zenitsu-agent.hf.space"

def keep_alive():
    """Ping self every 5 minutes to prevent sleep."""
    try:
        requests.get(f"{HF_SPACE_URL}/", timeout=5)
        print(f"[{_now()}] Keep-alive ping sent.")
    except Exception as e:
        print(f"[{_now()}] Keep-alive ping failed: {e}")
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


def send_digest_wrapper():
    """Run digest only during 8:00 PM - 8:10 PM IST."""
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    
    # Check if current time is between 20:00 and 20:10 IST
    if now.hour == 20 and 0 <= now.minute < 10:
        print(f"\n[{_now()}] Sending daily digest...")
        summary = get_todays_summary()
        send_daily_digest(summary)
        total = sum(len(v) for v in summary.values())
        print(f"[{_now()}] Digest sent. {total} emails in summary.")

def check_due_reminders():
    """Check and send due reminders every minute."""
    due = get_due_reminders()
    for reminder in due:
        print(f"[{_now()}] Reminder due: {reminder['task']}")
        send_reminder_alert(reminder['task'])

def check_reminders():
    """Check and send due reminders every minute."""
    due = get_due_reminders()
    for reminder in due:
        print(f"[{_now()}] Reminder due: {reminder['task']}")
        send_reminder_alert(reminder['task'], reminder['natural_time'])
        mark_reminder_sent(reminder['id'])
        schedule.every(1).minutes.do(check_reminders) 

def main():
    print("=" * 50)
    print("  Zenitsu Email Agent — Starting Up")
    print("=" * 50)

    send_startup_message()
    triage_inbox()

    # Run triage every 30 minutes
    schedule.every(30).minutes.do(triage_inbox)
    
    # Check every 10 minutes if it's 8pm IST
    schedule.every(10).minutes.do(send_digest_wrapper)
    schedule.every(5).minutes.do(keep_alive)
    schedule.every(1).minutes.do(check_due_reminders)
    print(f"\n[{_now()}] Scheduler running. Triage every 30 min. Digest check every 10 min (sends at 8:00 PM IST).")

    while True:
        schedule.run_pending()
        time.sleep(30)



if __name__ == "__main__":
    main()