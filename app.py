import os
import requests
from flask import Flask, request, jsonify
app = Flask(__name__)
MAX_TOKEN = os.environ.get("MAX_TOKEN")
MAX_API = "https://platform-api.max.ru
"
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
ACTIONS = [
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
@app.route("/")
def home():
    return "MAX Photobank Bot работает"
def make_keyboard(items):
    buttons = []
    for item in items:
        buttons.append([{"type": "message", "text": item}])
    return [{
        "type": "inline_keyboard",
        "payload": {"buttons": buttons}
    }]
def send_message(chat_id, text, buttons=None):
    url = f"{MAX_API}/messages?chat_id={chat_id}"
    headers = {
        "Authorization": MAX_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {"text": text}
    if buttons:
        payload["attachments"] = make_keyboard(buttons)
    response = requests.post
(url, json=payload, headers=headers)
    print("SEND RESPONSE:", response.status_code, response.text, flush=True)
    return response
def start_flow(chat_id, user_id):
    USER_STATES[user_id] = {"step": "participant_type"}
    send_message(
        chat_id,
        "Добро пожаловать в фотобанк.\n\nВыберите тип участника:",
        PARTICIPANT_TYPES
    )
def get_message_parts(data):
    message = data.get("message", {})
    body = message.get("body", {})
    chat_id = message.get("recipient", {}).get("chat_id")
    user_id = message.get("sender", {}).get("user_id")
    text = body.get("text", "")
    attachments = body.get("attachments", [])
    text = text.strip() if text else ""
    return message, body, chat_id, user_id, text, attachments
def has_media(attachments):
    if not attachments:
        return False
    for item in attachments:
        item_type = item.get("type", "")
        payload = item.get("payload", {})
        if item_type in ["image", "photo", "video", "media", "file"]:
            return True
        if payload.get("url") or payload.get("file_id") or payload.get("token"):
            return True
    return False
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("MAX EVENT:", data, flush=True)
    try:
        message, body, chat_id, user_id, text, attachments = get_message_parts(data)
        if not chat_id or not user_id:
            return jsonify({"status": "ok"})
        state = USER_STATES.get(user_id)
        if text in ["/start", "старт", "Старт", "начать", "Начать"]:
            start_flow(chat_id, user_id)
            return jsonify({"status": "ok"})
        if text == "Да, добавить ещё формат":
            old_state = USER_STATES.get(user_id, {})
            USER_STATES[user_id] = {
                "step": "format",
                "participant_type": old_state.get("participant_type"),
                "region": old_state.get("region"),
                "action": old_state.get("action")
            }
            send_message(chat_id, "Введите следующий формат мероприятия:")
            return jsonify({"status": "ok"})
        if text == "Завершить":
            USER_STATES.pop(user_id, None)
            send_message(chat_id, "Готово. Загрузка материалов завершена ✅")
            return jsonify({"status": "ok"})
        if not state:
            start_flow(chat_id, user_id)
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
            if not text:
                send_message(chat_id, "Введите регион текстом.")
                return jsonify({"status": "ok"})
            state["region"] = text
            state["step"] = "action"
            send_message(chat_id, "Выберите акцию:", ACTIONS)
            return jsonify({"status": "ok"})
        if state["step"] == "action":
            if text not in ACTIONS:
                send_message(chat_id, "Пожалуйста, выберите акцию кнопкой.", ACTIONS)
                return jsonify({"status": "ok"})
            state["action"] = text
            state["step"] = "format"
            send_message(chat_id, "Введите формат мероприятия:")
            return jsonify({"status": "ok"})
        if state["step"] == "format":
            if not text:
                send_message(chat_id, "Введите формат мероприятия текстом.")
                return jsonify({"status": "ok"})
            state["format"] = text
            state["step"] = "media"
            send_message(chat_id, "Теперь пришлите фото или видео.")
            return jsonify({"status": "ok"})
        if state["step"] == "media":
            print("MEDIA STEP BODY:", body, flush=True)
            if not has_media(attachments):
                send_message(chat_id, "Пришлите фото или видео файлом/медиа.")
                return jsonify({"status": "ok"})
            send_message(
                chat_id,
                "Материалы получил ✅\n\n"
                "Заявка сохранена в тестовом режиме.\n\n"
                f"Тип участника: {state.get('participant_type')}\n"
                f"Регион: {state.get('region')}\n"
                f"Акция: {state.get('action')}\n"
                f"Формат: {state.get('format')}\n\n"
                "Хотите добавить ещё один формат?",
                ["Да, добавить ещё формат", "Завершить"]
            )
            return jsonify({"status": "ok"})
    except Exception as e:
        print("ERROR:", e, flush=True)
    return jsonify({"status": "ok"})
if __name__ == "__main__":
    app.run()
