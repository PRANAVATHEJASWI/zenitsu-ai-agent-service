import datetime
import os
import requests
import time
from datetime import date

BASE_URL = "https://zenitsu-notification-service.onrender.com"
WAKE_URL = f"{BASE_URL}/wake"
NOTIFY_URL = f"{BASE_URL}/notify"

CATEGORY_EMOJI = {
    "legitimate": "✅",
    "newsletter": "📰",
    "promotional": "🛍️",
    "spam": "🚫",
    "phishing": "⚠️",
}


def wake_service(max_wait_seconds: int = 300, poll_interval: int = 5) -> bool:
    print("[notification-service] Waking service...")
    start_time = time.time()

    while (time.time() - start_time) < max_wait_seconds:
        try:
            response = requests.get(WAKE_URL, timeout=15)
            if response.status_code == 200:
                print("[notification-service] Service is awake.")
                return True
        except Exception:
            pass

        print(f"[notification-service] Waiting {poll_interval}s...")
        time.sleep(poll_interval)

    print("[notification-service] Failed to wake service within timeout.")
    return False


def _send(text: str):
    if not wake_service():
        print("[notification-service] Notification skipped due to wake timeout.")
        return

    try:
        response = requests.post(
            NOTIFY_URL,
            json={"message": text},
            timeout=30,
        )
        if response.status_code == 200:
            print("[notification-service] Notification sent successfully.")
        else:
            print(f"[notification-service] Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[notification-service] Request failed: {e}")


def alert_phishing(sender: str, subject: str, reason: str, domain: str = ""):
    _send(
        f"⚠️ *PHISHING ALERT*\n\n"
        f"*From:* `{sender}`\n"
        f"*Domain:* `{domain}`\n"
        f"*Subject:* {subject}\n"
        f"*Why:* {reason}\n\n"
        f"_Do not click any links._"
    )


def send_daily_digest(summary: dict):
    today = date.today().strftime("%d %b %Y")
    total = sum(len(items) for items in summary.values())

    if total == 0:
        _send(f"📬 *Email Digest — {today}*\n\nNo emails today.")
        return

    lines = [
        f"📬 *Email Digest — {today}*",
        f"_{total} emails processed_\n",
    ]

    # Category summary
    for category in ["legitimate", "newsletter", "promotional", "spam", "phishing"]:
        items = summary.get(category, [])
        if items:
            emoji = CATEGORY_EMOJI.get(category, "•")
            lines.append(f"{emoji} *{category.capitalize()}:* {len(items)}")

    lines.append("\n*Details (reply with numbers to unsubscribe):*\n")

    # Numbered list of ALL emails
    counter = 1
    for category in ["legitimate", "newsletter", "promotional", "spam", "phishing"]:
        items = summary.get(category, [])
        for item in items:
            subject = item.get("subject", "No Subject")[:40]
            domain = item.get("domain", "unknown")[:25]
            emoji = CATEGORY_EMOJI.get(category, "•")
            
            lines.append(
                f"{counter}. {emoji} {subject}\n"
                f"   From: `{domain}`"
            )
            counter += 1

    lines.append("\n_Reply with: unsubscribe 1 3 5_ (unsubscribe from items 1, 3, 5)")

    _send("\n".join(lines))


def send_startup_message():
    _send(
        "🤖 *Zenitsu Agent started*\n\n"
        "Monitoring your inbox every 30 minutes.\n"
        "Digest at 8:00 PM IST."
    )
    
def send_reminder_alert(task: str):
    """Send reminder to Render to display with buttons."""
    import uuid
    reminder_id = str(uuid.uuid4())[:8]
    
    try:
        response = requests.post(
            f"{BASE_URL}/send_reminder",
            json={
                "task": task,
                "id": reminder_id,
            },
            timeout=30,
        )
        if response.status_code == 200:
            print(f"[reminder-alert] Reminder sent: {task}")
            return True
    except Exception as e:
        print(f"[reminder-alert] Error: {e}")
    return False