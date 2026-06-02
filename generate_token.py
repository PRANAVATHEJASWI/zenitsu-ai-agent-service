"""
generate_token.py
Run this ONCE on your local machine to complete Gmail OAuth.
It will print the base64 token to paste into HF Spaces secrets.
"""

import os
import json
import base64
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

print("Starting Gmail OAuth flow...")
print("A browser window will open — sign in with your Gmail account.\n")

creds = None

if Path("token.pickle").exists():
    with open("token.pickle", "rb") as f:
        creds = pickle.load(f)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.pickle", "wb") as f:
        pickle.dump(creds, f)

# Convert to base64 for HF Spaces secret
token_json = creds.to_json()
encoded = base64.b64encode(token_json.encode()).decode()

print("\n✅ Gmail connected successfully!")
print("\n--- COPY EVERYTHING BELOW THIS LINE ---")
print(encoded)
print("--- COPY EVERYTHING ABOVE THIS LINE ---")
print("\nPaste this into your .env file as GMAIL_TOKEN_JSON=<paste here>")

# Quick test
service = build("gmail", "v1", credentials=creds)
result = service.users().messages().list(userId="me", maxResults=1).execute()
count = result.get("resultSizeEstimate", 0)
print(f"\nTest successful — ~{count} emails found in inbox.")