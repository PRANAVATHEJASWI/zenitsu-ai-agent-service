import threading
import gradio as gr
from agent import main as run_agent
from db import get_todays_summary


def start_agent():
    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()


def get_status():
    try:
        summary = get_todays_summary()
        total = sum(len(v) for v in summary.values())
        lines = [f"Emails processed today: {total}\n"]
        emoji_map = {
            "legitimate": "✅", "newsletter": "📰",
            "promotional": "🛍️", "spam": "🚫", "phishing": "⚠️"
        }
        for cat, items in summary.items():
            e = emoji_map.get(cat, "•")
            lines.append(f"{e} {cat.capitalize()}: {len(items)}")
        return "\n".join(lines)
    except Exception as ex:
        return f"Loading... ({ex})"


start_agent()

demo = gr.Interface(
    fn=get_status,
    inputs=[],
    outputs=gr.Textbox(label="Today's Email Summary", lines=10),
    title="Zenitsu Email Agent",
    description="Monitoring your inbox every 30 minutes. Click Run to refresh.",
)

demo.launch(server_name="0.0.0.0", server_port=7860)
