import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MAX_TOKEN = os.environ.get("MAX_TOKEN")
MAX_API = "https://platform-api.max.ru"

USER_STATES = {}

PARTICIPANT_TYPES = [
    "Субъект РФ",
    "ФОИВ",
    "ВУЗ",
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

    response = requests.post(url, json=payload, headers=headers)
    print("SEND RESPONSE:", response.status_code, response.text, flush=True)
    return response


def start_screen(chat_id):
    send_message(
        chat_id,
        "Здравствуйте!\n\n"
        "Данный бот создан для сбора фото- и видеоматериалов по реализации "
        "Всероссийских акций, приуроченных к государственным праздникам Российской Федерации.\n\n"
        "Для направления материалов нажмите кнопку ниже.",
        ["Начать работу"]
    )


def start_flow(chat_id, user_id):
    USER_STATES[user_id] = {"step": "participant_type"}

    send_message(
        chat_id,
        "Для направления материалов Вам потребуется последовательно указать:\n"
        "• тип участника;\n"
        "• наименование участника;\n"
        "• регион проведения;\n"
        "• Всероссийскую акцию;\n"
        "• формат мероприятия;\n"
        "• ссылку на Яндекс.Диск с фото- и видеоматериалами.\n\n"
        "Выберите тип участника:",
        PARTICIPANT_TYPES
    )


def get_message_parts(data):
    message = data.get("message", {})
    body = message.get("body", {})

    chat_id = message.get("recipient", {}).get("chat_id")
    user_id = message.get("sender", {}).get("user_id")
    text = body.get("text", "")

    text = text.strip() if text else ""

    return chat_id, user_id, text


def has_link(text):
    return bool(re.search(r"https?://\S+", text or ""))
    def yandex_headers():
    return {
        "Authorization": f"OAuth {os.environ.get('YANDEX_TOKEN')}"
    }

@app.route("/check-yandex")
def check_yandex():
    yandex_path = os.environ.get("YANDEX_EXCEL_PATH")

    response = requests.get(
        "https://cloud-api.yandex.net/v1/disk/resources",
        headers=yandex_headers(),
        params={"path": yandex_path}
    )

    return jsonify({
        "status_code": response.status_code,
        "response": response.text
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("MAX EVENT:", data, flush=True)

    try:
        chat_id, user_id, text = get_message_parts(data)

        if not chat_id or not user_id:
            return jsonify({"status": "ok"})

        state = USER_STATES.get(user_id)

        if text in ["/start", "старт", "Старт", "начать", "Начать"]:
            start_screen(chat_id)
            return jsonify({"status": "ok"})

        if text == "Начать работу":
            start_flow(chat_id, user_id)
            return jsonify({"status": "ok"})

        if text == "Добавить ещё один формат":
            old_state = USER_STATES.get(user_id, {})
            USER_STATES[user_id] = {
                "step": "format",
                "participant_type": old_state.get("participant_type"),
                "participant_name": old_state.get("participant_name"),
                "region": old_state.get("region"),
                "action": old_state.get("action")
            }
            send_message(chat_id, "Введите следующий формат мероприятия:")
            return jsonify({"status": "ok"})

        if text == "Завершить работу":
            USER_STATES.pop(user_id, None)
            send_message(
                chat_id,
                "Благодарим за направление материалов!\n\n"
                "Для повторной загрузки материалов Вы можете вернуться в бот "
                "в любое время и нажать кнопку «Начать работу».",
                ["Начать работу"]
            )
            return jsonify({"status": "ok"})

        if not state:
            start_screen(chat_id)
            return jsonify({"status": "ok"})

        if state["step"] == "participant_type":
            if text not in PARTICIPANT_TYPES:
                send_message(chat_id, "Пожалуйста, выберите тип участника кнопкой.", PARTICIPANT_TYPES)
                return jsonify({"status": "ok"})

            state["participant_type"] = text
            state["step"] = "participant_name"

            name_prompts = {
                "Субъект РФ": "Укажите наименование органа исполнительной власти субъекта Российской Федерации, направляющего материалы.",
                "ФОИВ": "Укажите полное наименование федерального органа исполнительной власти.",
                "ВУЗ": "Укажите полное наименование образовательной организации высшего образования.",
                "СУЗ": "Укажите полное наименование среднего профессионального образовательного учреждения.",
                "Школа": "Укажите полное наименование общеобразовательной организации.",
                "Организации и НКО": "Укажите полное наименование организации или НКО.",
                "Политические НКО": "Укажите полное наименование политической некоммерческой организации."
            }

            send_message(chat_id, name_prompts.get(text, "Укажите полное наименование участника."))
            return jsonify({"status": "ok"})

        if state["step"] == "participant_name":
            if not text:
                send_message(chat_id, "Укажите наименование участника текстом.")
                return jsonify({"status": "ok"})

            state["participant_name"] = text
            state["step"] = "region"
            send_message(chat_id, "Введите регион проведения:")
            return jsonify({"status": "ok"})

        if state["step"] == "region":
            if not text:
                send_message(chat_id, "Введите регион проведения текстом.")
                return jsonify({"status": "ok"})

            state["region"] = text
            state["step"] = "action"
            send_message(chat_id, "Выберите Всероссийскую акцию:", ACTIONS)
            return jsonify({"status": "ok"})

        if state["step"] == "action":
            if text not in ACTIONS:
                send_message(chat_id, "Пожалуйста, выберите Всероссийскую акцию кнопкой.", ACTIONS)
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
            state["step"] = "disk_link"
            send_message(
                chat_id,
                "Пришлите ссылку на Яндекс.Диск с фото- и видеоматериалами "
                "по данному формату."
            )
            return jsonify({"status": "ok"})

        if state["step"] == "disk_link":
            if not has_link(text):
                send_message(
                    chat_id,
                    "Пожалуйста, пришлите ссылку на Яндекс.Диск с фото- и видеоматериалами."
                )
                return jsonify({"status": "ok"})

            state["disk_link"] = text

            send_message(
                chat_id,
                "Заявка успешно зарегистрирована ✅\n\n"
                f"Тип участника: {state.get('participant_type')}\n"
                f"Наименование участника: {state.get('participant_name')}\n"
                f"Регион: {state.get('region')}\n"
                f"Всероссийская акция: {state.get('action')}\n"
                f"Формат мероприятия: {state.get('format')}\n"
                f"Ссылка на материалы: {state.get('disk_link')}\n\n"
                "Если у Вас есть материалы по другому формату в рамках этой же акции, "
                "Вы можете добавить ещё одну заявку.\n\n"
                "Выберите дальнейшее действие:",
                ["Добавить ещё один формат", "Завершить работу"]
            )
            return jsonify({"status": "ok"})

    except Exception as e:
        print("ERROR:", e, flush=True)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run()
