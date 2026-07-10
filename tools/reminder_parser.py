import os
import json
from groq import Groq
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Parse natural language reminders into task + timestamp.

Extract:
- task: what to remind about
- timestamp: Unix timestamp (seconds since epoch)

Current time IST: {current_time}

Examples:
- "remind me to call john tomorrow at 2pm" → task: "call john", timestamp for tomorrow 2pm IST
- "remind me in 30 minutes to buy milk" → task: "buy milk", timestamp 30 mins from now

Respond ONLY with JSON:
{{"task": "...", "timestamp": 1234567890, "natural_time": "tomorrow at 2pm"}}
"""

def parse_reminder(user_message: str) -> dict:
    """Parse natural language reminder."""
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(current_time=now.isoformat())},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        
        return {
            "task": result.get("task", ""),
            "timestamp": result.get("timestamp", 0),
            "natural_time": result.get("natural_time", ""),
        }
    except Exception as e:
        return {"error": str(e)}