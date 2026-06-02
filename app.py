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
        lines = [f"**Emails processed today: {total}**\n"]
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

with gr.Blocks(title="Zenitsu Email Agent") as demo:
    gr.Markdown("## ⚡ Zenitsu Email Agent")
    gr.Markdown("Monitoring your inbox every 30 minutes.")
    status = gr.Markdown(get_status())
    refresh_btn = gr.Button("Refresh Stats")
    refresh_btn.click(fn=get_status, inputs=None, outputs=status)

demo.launch(server_name="0.0.0.0", server_port=7860)
