import os
import json
import base64
import pickle
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    creds = None
    token_env = os.getenv("GMAIL_TOKEN_JSON", "")

    if token_env:
        token_data = json.loads(base64.b64decode(token_env).decode())
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            encoded = base64.b64encode(creds.to_json().encode()).decode()
            print(f"\n[gmail] Copy this into GMAIL_TOKEN_JSON:\n{encoded}\n")

    return build("gmail", "v1", credentials=creds)


def fetch_recent_emails(minutes: int = 30) -> list:
    service = get_gmail_service()
    since = int(
        (datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp()
    )

    results = service.users().messages().list(
        userId="me",
        q=f"after:{since}",
        maxResults=50,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "List-Unsubscribe"],
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in detail["payload"]["headers"]
        }

        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "sender": headers.get("From", "unknown"),
            "unsubscribe_header": headers.get("List-Unsubscribe", ""),
            "snippet": detail.get("snippet", ""),
        })

    return emails


def unsubscribe(unsubscribe_header: str) -> bool:
    if not unsubscribe_header:
        return False

    entries = [
        e.strip().strip("<>")
        for e in unsubscribe_header.split(",")
    ]

    for entry in entries:
        if entry.startswith("https://"):
            try:
                r = requests.post(entry, timeout=10)
                return r.status_code < 400
            except Exception as e:
                print(f"[unsubscribe] Failed: {e}")
                continue

    return False