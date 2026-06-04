import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Trusted platforms — even if promotional, mark as newsletter
AUTHORIZED_PLATFORMS = {
    "github.com",
    "wellfound.com",
    "notion.so",
    "slack.com",
    "stripe.com",
    "google.com",
    "microsoft.com",
    "linkedin.com",
    "producthunt.com",
    "hacker-news.firebaseapp.com",
    "dribbble.com",
    "behance.net",
}

SYSTEM_PROMPT = """
You are an email security classifier.

Classify into exactly one category:
- legitimate   : personal emails, work emails, OTPs, invoices, receipts, shipping, bank alerts
- newsletter   : subscribed digests, updates from trusted platforms
- promotional  : marketing campaigns, discounts, offers from known businesses
- spam         : unsolicited bulk email, unknown senders, low-quality content
- phishing     : credential theft attempts, impersonation, malicious links, urgent account threats

Rules:
- OTPs, receipts, invoices, shipping = always legitimate
- GitHub/Google/Stripe notifications = newsletter (even if promotional content)
- Marketing from real businesses = promotional
- Phishing only if clear malicious intent

Respond ONLY with JSON:
{"category": "legitimate|newsletter|promotional|spam|phishing", "reason": "One sentence."}
"""


def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    try:
        return email.split("@")[1].lower()
    except:
        return email.lower()


def classify_email(sender: str, subject: str, snippet: str) -> dict:
    domain = extract_domain(sender)
    
    # Check if sender is from authorized platform
    is_authorized = any(
        auth_domain in domain 
        for auth_domain in AUTHORIZED_PLATFORMS
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Sender: {sender}\n"
                        f"Domain: {domain}\n"
                        f"Subject: {subject}\n"
                        f"Preview: {snippet[:300]}"
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        
        # Override: if authorized platform and promotional/newsletter -> make it newsletter
        if is_authorized and result.get("category") in ["promotional", "newsletter"]:
            result["category"] = "newsletter"
        
        return {
            "category": result.get("category", "legitimate"),
            "domain": domain,
            "reason": result.get("reason", ""),
        }
    except json.JSONDecodeError:
        return {
            "category": "legitimate",
            "domain": domain,
            "reason": "parse error"
        }
    except Exception as e:
        return {
            "category": "legitimate",
            "domain": domain,
            "reason": f"api error: {e}"
        }