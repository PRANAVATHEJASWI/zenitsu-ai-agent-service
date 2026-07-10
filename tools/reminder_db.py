import os
from datetime import datetime
from db import get_db


def create_reminder(user_id: str, task: str, timestamp: int, natural_time: str) -> bool:
    """Store a new reminder in Firebase."""
    db = get_db()
    try:
        db.collection("reminders").add({
            "user_id": user_id,
            "task": task,
            "timestamp": timestamp,
            "natural_time": natural_time,
            "created_at": datetime.utcnow().isoformat(),
            "sent": False,
        })
        return True
    except Exception as e:
        print(f"[reminder_db] Error creating reminder: {e}")
        return False


def get_due_reminders() -> list:
    """Get all reminders that are due (timestamp <= now)."""
    from datetime import datetime
    db = get_db()
    now_timestamp = int(datetime.utcnow().timestamp())
    
    try:
        docs = db.collection("reminders").where(
            "sent", "==", False
        ).where(
            "timestamp", "<=", now_timestamp
        ).stream()
        
        reminders = []
        for doc in docs:
            reminders.append({
                "id": doc.id,
                "task": doc.get("task"),
                "natural_time": doc.get("natural_time"),
            })
        return reminders
    except Exception as e:
        print(f"[reminder_db] Error fetching reminders: {e}")
        return []


def mark_reminder_sent(reminder_id: str) -> bool:
    """Mark a reminder as sent."""
    db = get_db()
    try:
        db.collection("reminders").document(reminder_id).update({
            "sent": True,
            "sent_at": datetime.utcnow().isoformat(),
        })
        return True
    except Exception as e:
        print(f"[reminder_db] Error marking sent: {e}")
        return False