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
    "unknown": "❓",
}


def wake_service(
    max_wait_seconds: int = 300,
    poll_interval: int = 5,
) -> bool:
    """
    Wake Render service and wait until it responds.

    Returns:
        True if service becomes available.
        False if timeout occurs.
    """

    print("[notification-service] Waking service...")

    start_time = time.time()

    while (time.time() - start_time) < max_wait_seconds:
        try:
            response = requests.get(
                WAKE_URL,
                timeout=15,
            )

            if response.status_code == 200:
                print(
                    "[notification-service] Service is awake."
                )
                return True

        except Exception:
            pass

        print(
            f"[notification-service] "
            f"Waiting {poll_interval}s..."
        )

        time.sleep(poll_interval)

    print(
        "[notification-service] "
        "Failed to wake service within timeout."
    )

    return False


def _send(text: str):
    """
    Wake Render service and send notification.
    """

    if not wake_service():
        print(
            "[notification-service] "
            "Notification skipped due to wake timeout."
        )
        return

    try:
        response = requests.post(
            NOTIFY_URL,
            json={"message": text},
            timeout=30,
        )

        if response.status_code == 200:
            print(
                "[notification-service] "
                "Notification sent successfully."
            )
        else:
            print(
                f"[notification-service] "
                f"Error {response.status_code}: "
                f"{response.text}"
            )

    except Exception as e:
        print(
            f"[notification-service] "
            f"Request failed: {e}"
        )


def alert_phishing(
    sender: str,
    subject: str,
    reason: str,
):
    _send(
        f"⚠️ *PHISHING ALERT*\n\n"
        f"*From:* `{sender}`\n"
        f"*Subject:* {subject}\n"
        f"*Why flagged:* {reason}\n\n"
        f"_Do not click any links in this email._"
    )


def send_daily_digest(summary: dict):
    today = date.today().strftime("%d %b %Y")

    total = sum(
        len(items)
        for items in summary.values()
    )

    if total == 0:
        _send(
            f"📬 *Email Digest — {today}*\n\n"
            f"No new emails today."
        )
        return

    lines = [
        f"📬 *Email Digest — {today}*",
        f"_{total} emails processed_\n",
    ]

    for category in [
        "legitimate",
        "newsletter",
        "promotional",
        "spam",
        "phishing",
    ]:
        items = summary.get(category, [])

        if items:
            emoji = CATEGORY_EMOJI.get(
                category,
                "•",
            )

            lines.append(
                f"{emoji} *{category.capitalize()}:* "
                f"{len(items)}"
            )

    actioned = (
        summary.get("spam", [])
        + summary.get("promotional", [])
    )

    if actioned:
        lines.append(
            "\n*Unsubscribed / flagged:*"
        )

        for item in actioned[:8]:
            subject = item.get(
                "subject",
                "No Subject",
            )[:45]

            sender = item.get(
                "sender",
                "Unknown Sender",
            )[:35]

            lines.append(
                f"• {subject}\n"
                f"  `{sender}`"
            )

    _send("\n".join(lines))


def send_startup_message():
    _send(
        "🤖 *Zenitsu Agent started*\n\n"
        "Monitoring your inbox every 30 minutes."
    )


if __name__ == "__main__":
    send_startup_message()