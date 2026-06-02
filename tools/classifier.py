import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an enterprise-grade email security classifier.

Your task is to analyze an email and classify it into exactly one category:

- legitimate   : personal emails, work emails, OTPs, invoices, receipts, shipping updates, bank alerts
- newsletter   : newsletters, digests, updates the recipient intentionally subscribed to
- promotional  : advertisements, discounts, offers, marketing campaigns from known businesses
- spam         : unsolicited bulk email, low-quality marketing, unknown senders, irrelevant content
- phishing     : attempts to steal credentials, money, personal information, or impersonate trusted entities

Analyze ALL available signals before making a decision:

1. Sender Analysis
   - Display name
   - Actual sender email address
   - Domain reputation
   - Mismatch between display name and email domain
   - Lookalike domains (paypaI.com vs paypal.com)
   - Free email providers pretending to be businesses

2. Subject Analysis
   - Urgency language
   - Threats or pressure tactics
   - Excessive capitalization
   - Suspicious wording
   - Financial incentives

3. Content Analysis
   - Full email body
   - Grammar and spelling quality
   - Requests for passwords, OTPs, MFA codes
   - Requests for bank details
   - Requests for personal information
   - Unexpected attachments
   - Suspicious instructions

4. Link Analysis
   - Actual URLs present
   - URL shortening services
   - Mismatch between visible text and destination URL
   - Suspicious domains
   - Login pages hosted on unrelated domains

5. Attachment Analysis
   - Executable files
   - Macro-enabled documents
   - Unexpected ZIP files
   - Password-protected attachments
   - Requests to open files urgently

6. Business Context
   - Expected transactional email
   - Order confirmation
   - Shipping update
   - OTP
   - Invoice
   - Internal company communication
   - Known service notifications

PHISHING RED FLAGS:
- Credential requests
- Password reset requests not initiated by user
- MFA/OTP requests
- Banking verification requests
- Urgent account suspension warnings
- Gift card requests
- Wire transfer requests
- CEO/CFO impersonation
- Domain spoofing
- Suspicious login links

LEGITIMATE INDICATORS:
- Expected transaction emails
- Order receipts
- OTP messages
- Shipping notifications
- Internal work communications
- Bank alerts from verified domains

CLASSIFICATION PRIORITY:
1. If clear phishing indicators exist -> phishing
2. Else if legitimate transactional/business communication -> legitimate
3. Else if subscribed digest/newsletter -> newsletter
4. Else if marketing content from a real business -> promotional
5. Else -> spam

Rules:
- Never classify OTPs, receipts, invoices, or shipping updates as spam.
- Only classify as phishing when concrete indicators exist.
- When uncertain between spam and promotional, choose promotional.
- Use the email body more heavily than the subject line.
- Consider all evidence before deciding.

Respond ONLY with valid JSON.

Format:
{
  "category": "legitimate|newsletter|promotional|spam|phishing",
  "confidence": 0-100,
  "risk_score": 0-100,
  "reason": "One concise sentence explaining the strongest evidence."
}
"""


def classify_email(sender: str, subject: str, snippet: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Sender: {sender}\n"
                        f"Subject: {subject}\n"
                        f"Preview: {snippet[:300]}"
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"[classifier] JSON parse failed for: {subject}")
        return {"category": "legitimate", "reason": "parse error — defaulting to safe"}
    except Exception as e:
        print(f"[classifier] Groq error: {e}")
        return {"category": "legitimate", "reason": f"api error — defaulting to safe"}