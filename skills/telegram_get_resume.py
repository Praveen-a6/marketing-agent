#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "configs", "instagram.env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def fetch_and_send_resume(lead_id: int, chat_id: str):
    file_path = f"/home/praveen/marketing-agent/downloads/resumes/{lead_id}_resume.pdf"
    
    if not os.path.exists(file_path):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"❌ Resume file for Lead #{lead_id} not found."}
        )
        return

    with open(file_path, "rb") as doc:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={"chat_id": chat_id, "caption": f"📄 Resume for Lead #{lead_id}"},
            files={"document": doc}
        )

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        fetch_and_send_resume(int(sys.argv[1]), sys.argv[2])
