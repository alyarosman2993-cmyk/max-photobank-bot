import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MAX_TOKEN = os.environ.get("MAX_TOKEN")
MAX_API = "https://platform-api.max.ru"

USER_STATES = {}

PARTICIPANT_TYPES = [
    "Субъект РФ",
    "ФОИВ",
    "Вуз",
    "СУЗ",
    "Школа",
    "Организации и НКО",
    "Политические НКО",
]

@app.route("/")
def home():
    return "MAX Photobank Bot работает"

def make_keyboard(items):
    buttons = []
    for item in items:
        buttons.append([
            {
                "type": "message",
                "text": item
            }
        ])

    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": buttons
            }
        }
    ]

def send_message(chat_id, text, buttons=None):
    url = f"{MAX_API}/messages?chat_id={chat_id}"

    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text
    }

    if buttons:
        payload["attachments"] = make_keyboard(buttons)

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
        user_id = message.get("sender", {}).get("user_id")
        text = message.get("body", {}).get("text", "").strip()

        if not chat_id or not user_id:
            return jsonify({"status": "ok"})

        if text in ["/start", "старт", "Старт", "начать", "Начать"]:
            USER_STATES[user_id] = {"step": "participant_type"}
            send_message(
                chat_id,
                "Добро пожаловать в фотобанк.\n\nВыберите тип участника:",
                PARTICIPANT_TYPES
            )
            return jsonify({"status": "ok"})

        state = USER_STATES.get(user_id)

        if not state:
            send_message(chat_id, "Напишите /start, чтобы начать загрузку материалов.")
            return jsonify({"status": "ok"})

        if state["step"] == "participant_type":
            if text not in PARTICIPANT_TYPES:
                send_message(chat_id, "Пожалуйста, выберите тип участника кнопкой.", PARTICIPANT_TYPES)
                return jsonify({"status": "ok"})

            state["participant_type"] = text
            state["step"] = "region"
            send_message(chat_id, "Введите регион:")
            return jsonify({"status": "ok"})

        if state["step"] == "region":
            state["region"] = text
            state["step"] = "action"
            send_message(
                chat_id,
                "Выберите акцию:",
                [
                    "День семьи, любви и верности",
                    "День физкультурника",
                    "День Государственного флага РФ",
                    "День воссоединения исторических регионов",
                    "День рождения Президента РФ",
                    "День отца",
                    "День народного единства",
                    "День матери",
                    "День Героев Отечества",
                    "Новый год",
                ]
            )
            return jsonify({"status": "ok"})

        if state["step"] == "action":
            state["action"] = text
            state["step"] = "format"
            send_message(chat_id, "Введите формат мероприятия:")
            return jsonify({"status": "ok"})

        if state["step"] == "format":
            state["format"] = text
            state["step"] = "photo"
            send_message(chat_id, "Теперь пришлите фото.")
            return jsonify({"status": "ok"})

        if state["step"] == "photo":
            send_message(
                chat_id,
                "Пока тест: я получил шаг с фото.\n\nДанные заявки:\n"
                f"Тип участника: {state.get('participant_type')}\n"
                f"Регион: {stateet('region')}\n"
                f"Акция: {state.get('action')}\n"
                f"Формат: {state.get('format')}\n\n"
                "Следующим шагом подключим загрузку фото на Яндекс.Диск."
            )
            USER_STATES.pop(user_id, None)
            return jsonify({"status": "ok"})

    except Exception as e:
        print("ERROR:", e, flush=True)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
