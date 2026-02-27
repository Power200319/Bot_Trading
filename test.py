import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print("Looking for .env at:", ENV_PATH)
print("Exists:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

token = os.getenv("TG_BOT_TOKEN")
chat_id = os.getenv("TG_CHAT_ID")

if not token or not chat_id:
    print("Missing TG_BOT_TOKEN or TG_CHAT_ID in .env")
    raise SystemExit(1)

text = "Test message from bot (test.py)"
url = f"https://api.telegram.org/bot{token}/sendMessage"

try:
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=10,
    )
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except requests.RequestException as exc:
    print("Telegram request failed:", exc)
