import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MAX_TOKEN = os.environ.get("MAX_TOKEN")
MAX_API = "https://platform-api.max.ru"
WEBHOOK_URL = "https://max-photobank-bot.onrender.com/webhook"

@app.route("/")
def home():
    return "MAX Photobank Bot работает"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("MAX EVENT:", data, flush=True)
    return jsonify({"status": "ok"})

@app.route("/setup-webhook")
def setup_webhook():
    if not MAX_TOKEN:
        return "Ошибка: MAX_TOKEN не найден в Render"

    url = f"{MAX_API}/subscriptions"

    payload = {
        "url": WEBHOOK_URL,
        "update_types": [
            "message_created",
            "bot_started"
        ]
    }

    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

@app.route("/check-webhook")
def check_webhook():
    if not MAX_TOKEN:
        return "Ошибка: MAX_TOKEN не найден в Render"

    url = f"{MAX_API}/subscriptions"

    headers = {
        "Authorization": MAX_TOKEN
    }

    response = requests.get(url, headers=headers)

    return {
        "status_code": response.status_code,
        "response": response.text
    }

if __name__ == "__main__":
    app.run()
