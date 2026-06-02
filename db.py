import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
        cert = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": key,
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        cred = credentials.Certificate(cert)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def is_processed(message_id: str) -> bool:
    db = get_db()
    doc = db.collection("processed_emails").document(message_id).get()
    return doc.exists


def mark_processed(message_id: str, subject: str, sender: str, category: str):
    from datetime import datetime
    db = get_db()
    db.collection("processed_emails").document(message_id).set({
        "subject": subject,
        "sender": sender,
        "category": category,
        "processed_at": datetime.utcnow().isoformat(),
    })


def get_todays_summary() -> dict:
    from datetime import datetime, timezone
    import pytz

    tz = pytz.timezone(os.getenv("TIMEZONE", "Asia/Kolkata"))
    today_start = datetime.now(tz).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).astimezone(timezone.utc).isoformat().replace("+00:00", "")

    db = get_db()
    docs = (
        db.collection("processed_emails")
        .where("processed_at", ">=", today_start)
        .stream()
    )

    summary = {}
    for doc in docs:
        data = doc.to_dict()
        cat = data.get("category", "unknown")
        if cat not in summary:
            summary[cat] = []
        summary[cat].append({
            "subject": data.get("subject", ""),
            "sender": data.get("sender", ""),
        })

    return summary