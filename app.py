import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import pytz
from agent import main as run_agent
from db import get_todays_summary

app = FastAPI()

def start_agent():
    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

@app.get("/", response_class=HTMLResponse)
def index():
    try:
        summary = get_todays_summary()
        total = sum(len(v) for v in summary.values())
        emoji_map = {
            "legitimate": "✅", "newsletter": "📰",
            "promotional": "🛍️", "spam": "🚫", "phishing": "⚠️"
        }
        rows = ""
        for cat, items in summary.items():
            e = emoji_map.get(cat, "•")
            rows += f"<tr><td>{e} {cat.capitalize()}</td><td>{len(items)}</td></tr>"

        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz).strftime("%d %b %Y %H:%M:%S IST")

        html = f"""
        <html>
        <head>
            <title>Zenitsu Email Agent</title>
            <meta http-equiv="refresh" content="60">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }}
                h1 {{ color: #f0a500; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                td {{ padding: 10px; border: 1px solid #ddd; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                .total {{ font-size: 1.2em; font-weight: bold; margin: 20px 0; }}
                .time {{ color: #888; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>⚡ Zenitsu Email Agent</h1>
            <p class="time">Last updated: {now} (auto-refreshes every 60s)</p>
            <p class="total">Emails processed today: {total}</p>
            <table>
                <tr><th>Category</th><th>Count</th></tr>
                {rows if rows else "<tr><td colspan='2'>No emails yet today</td></tr>"}
            </table>
            <p class="time">Agent is running — monitoring inbox every 30 minutes.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    except Exception as ex:
        return HTMLResponse(content=f"<h1>Loading...</h1><p>{ex}</p>")

start_agent()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
