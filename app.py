import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MAX_TOKEN = os.environ.get("MAX_TOKEN")
MAX_API = "https://platform-api.max.ru"

@app.route("/")
def home():
    return "MAX Photobank Bot работает"

def send_message(chat_id, text):
    url = f"{MAX_API}/messages"
    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {
            "chat_id": chat_id
        },
        "text": text
    }

    response = requests.post(url, json=payload, headers=headers)
    print("SEND RESPONSE:", response.status_code, response.text, flush=True)
    return response

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("MAX EVENT:", data, flush=True)

    try:
        message = data.get("message", {})
        chat_id = message.get("recipient", {}).get("chat_id")

        if chat_id:
            send_message(chat_id, "Бот работает ✅")
    except Exception as e:
        print("ERROR:", e, flush=True)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
