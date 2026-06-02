import requests
from datetime import date

NOTIFICATION_SERVICE_URL = (
    "https://zenitsu-notification-service.onrender.com/notify"
)

CATEGORY_EMOJI = {
    "legitimate": "✅",
    "newsletter": "📰",
    "promotional": "🛍️",
    "spam": "🚫",
    "phishing": "⚠️",
    "unknown": "❓",
}


def _send(text: str):
    try:
        r = requests.post(
            NOTIFICATION_SERVICE_URL,
            json={"message": text},
            timeout=30,
        )

        if r.status_code != 200:
            print(
                f"[notification-service] Error {r.status_code}: "
                f"{r.text}"
            )

    except Exception as e:
        print(f"[notification-service] Request failed: {e}")


def alert_phishing(sender: str, subject: str, reason: str):
    _send(
        f"⚠️ *PHISHING ALERT*\n\n"
        f"*From:* `{sender}`\n"
        f"*Subject:* {subject}\n"
        f"*Why flagged:* {reason}\n\n"
        f"_Do not click any links in this email._"
    )


def send_daily_digest(summary: dict):
    today = date.today().strftime("%d %b %Y")
    total = sum(len(v) for v in summary.values())

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

    for cat in [
        "legitimate",
        "newsletter",
        "promotional",
        "spam",
        "phishing",
    ]:
        items = summary.get(cat, [])
        if items:
            emoji = CATEGORY_EMOJI.get(cat, "•")
            lines.append(
                f"{emoji} *{cat.capitalize()}:* {len(items)}"
            )

    actioned = (
        summary.get("spam", [])
        + summary.get("promotional", [])
    )

    if actioned:
        lines.append("\n*Unsubscribed / flagged:*")

        for item in actioned[:8]:
            subject = item["subject"][:45]
            sender = item["sender"][:35]

            lines.append(
                f"  • {subject}\n"
                f"    `{sender}`"
            )

    _send("\n".join(lines))


def send_startup_message():
    _send(
        "🤖 *Zenitsu Agent started* — "
        "monitoring your inbox every 30 minutes."
    )