import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

GRAPH_API_VERSION = "v25.0"


def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp text message using Meta Cloud API."""
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        app.logger.warning("WhatsApp credentials are not configured yet.")
        return

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)
    app.logger.info("Meta response: %s %s", response.status_code, response.text)


WELCOME_MESSAGE = """Welcome to Backliners 👩‍⚕️

Please select your preferred language:

1️⃣ English
2️⃣ 中文
3️⃣ Bahasa Malaysia

Reply with 1, 2 or 3 to continue."""


@app.get("/")
def health():
    return "Backliners WhatsApp Bot is running", 200


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}

    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    if message.get("type") != "text":
                        continue

                    sender = message.get("from")
                    text = (
                        message.get("text", {})
                        .get("body", "")
                        .strip()
                        .lower()
                    )

                    if not sender:
                        continue

                    if text in {"1", "english"}:
                        reply = """Welcome to Backliners 👩‍⚕️
How may we assist you today?

1️⃣ Wound Care
2️⃣ Elderly / Patient Hygiene Care
3️⃣ Feeding Tube Insertion
4️⃣ Urinary Catheter Insertion
5️⃣ Stoma Care
6️⃣ Home Physiotherapy
7️⃣ Medical Escort Service
8️⃣ Care Home in Penang

Please reply with 1–8 to continue."""
                    elif text in {"2", "中文", "chinese"}:
                        reply = """欢迎联系 Backliners 👩‍⚕️

请问您需要哪一项服务？

1️⃣ 伤口护理 / 换药
2️⃣ 长者 / 病人卫生护理
3️⃣ 鼻胃喂食管置入 / 更换
4️⃣ 导尿管置入 / 更换
5️⃣ 造口护理
6️⃣ 上门物理治疗
7️⃣ 医疗陪诊服务 Medscort
8️⃣ 槟城安老护理中心

请输入 1–8 继续。"""
                    elif text in {"3", "bm", "bahasa", "bahasa malaysia"}:
                        reply = """Selamat datang ke Backliners 👩‍⚕️

Bagaimanakah kami boleh membantu anda?

1️⃣ Penjagaan Luka
2️⃣ Penjagaan Kebersihan Warga Emas / Pesakit
3️⃣ Pemasangan / Penukaran Tiub Pemakanan
4️⃣ Pemasangan / Penukaran Kateter Urin
5️⃣ Penjagaan Stoma
6️⃣ Fisioterapi Di Rumah
7️⃣ Perkhidmatan Pengiring Perubatan – Medscort
8️⃣ Pusat Jagaan Warga Emas di Pulau Pinang

Sila balas 1–8 untuk meneruskan."""
                    else:
                        reply = WELCOME_MESSAGE

                    send_whatsapp_message(sender, reply)

    except Exception:
        app.logger.exception("Error processing webhook")

    # Meta expects a fast 200 response.
    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
