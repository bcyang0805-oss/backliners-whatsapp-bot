import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

GRAPH_API_VERSION = "v26.0"

# Temporary in-memory conversation state.
# This resets whenever Render restarts/redeploys.
user_states = {}
user_data = {}


def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp text message using Meta Cloud API."""
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        app.logger.warning("WhatsApp credentials are not configured.")
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

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        app.logger.warning(
            "META RESPONSE status=%s body=%s",
            response.status_code,
            response.text,
        )
    except requests.RequestException:
        app.logger.exception("Failed to send WhatsApp message")


WELCOME_MESSAGE = """Welcome to Backliners 👩‍⚕️

Please select your preferred language:

1️⃣ English
2️⃣ 中文

Reply with 1 or 2 to continue."""


ENGLISH_MENU = """Welcome to Backliners 👩‍⚕️

How may we assist you today?

1️⃣ Wound Care
2️⃣ Elderly / Patient Hygiene Care
3️⃣ Feeding Tube Insertion
4️⃣ Urinary Catheter Insertion
5️⃣ Home Physiotherapy
6️⃣ Care Home in Penang

Please reply with 1–6 to continue.

Type MENU anytime to return to the language menu."""


CHINESE_MENU = """欢迎联系 Backliners 👩‍⚕️

请问您需要哪一项服务？

1️⃣ 伤口护理 / 换药
2️⃣ 长者 / 病人卫生护理
3️⃣ 鼻胃喂食管置入 / 更换
4️⃣ 导尿管置入 / 更换
5️⃣ 上门物理治疗
6️⃣ 槟城安老护理中心

请输入 1–6 继续。

任何时候输入 MENU 可返回语言选择。"""


ENGLISH_SERVICES = {
    "1": (
    "wound_location",
    """Wound Care 🩹

To assist you, we will ask a few quick questions.

First, please provide the patient's location / area.

Example:
Bayan Lepas / Georgetown / Butterworth"""
),

    "2": ("hygiene_care", """Elderly / Patient Hygiene Care 🧼

Our care team provides hygiene assistance for elderly, bedridden and dependent patients at home.

To assist you, please provide:

1. Patient's location / area
2. Patient's age
3. Patient's current mobility
   - Walking
   - Wheelchair
   - Bedridden
4. Type of assistance required
   - Bathing / sponging
   - Diaper changing
   - Grooming / hygiene
   - Combination of the above

Once we receive the information, our team will review your care requirements and advise you accordingly."""),
    "3": ("feeding_tube", """Feeding Tube Insertion 🩺

To assist you, please provide:

1. Patient's location / area
2. Service required
   - New feeding tube insertion
   - Replacement of existing feeding tube
   - Feeding tube accidentally came out
3. Is the patient currently at home?
4. When is the service required?
   - Today
   - Tomorrow
   - Other date

Our nursing team will review the request and advise you on availability."""),
    "4": ("urinary_catheter", """Urinary Catheter Insertion / Replacement

To assist you, please provide:

1. Patient's location / area
2. Service required
   - New catheter insertion
   - Catheter replacement
   - Catheter removal
   - Catheter blockage / problem
   - Not sure
3. Patient's gender
   - Male
   - Female
4. When is the service required?
   - Today
   - Tomorrow
   - Other date

Our nursing team will review the request and advise you on availability."""),
    "5": ("home_physiotherapy", """Home Physiotherapy 🏠

To assist you, please provide:

1. Patient's location / area
2. Patient's age
3. Main reason for physiotherapy
   - Stroke rehabilitation
   - Post-surgery rehabilitation
   - Elderly mobility / strengthening
   - Walking difficulty
   - Fall recovery
   - Other
4. Patient's current mobility
   - Bedridden
   - Wheelchair
   - Walking with assistance
   - Walking independently
5. Preferred date for the first session

Our team will review the patient's requirements and advise you on physiotherapist availability."""),
    "6": ("care_home", """Care Home in Penang 🏡

To assist you, please provide:

1. Patient's age
2. Patient's current condition
   - Independent
   - Needs assistance with daily activities
   - Wheelchair
   - Bedridden
   - Dementia / cognitive impairment
   - Post-hospital / rehabilitation
3. Does the patient require nursing care?
4. Expected length of stay
   - Short-term
   - 1–3 months
   - Long-term
   - Not sure
5. When is admission required?
   - Immediately
   - Within 1 week
   - Within 1 month
   - Just enquiring

Our care team will review the patient's needs and recommend the most suitable care arrangement."""),
}


CHINESE_SERVICES = {
    "1": ("wound_care_cn", """伤口护理 / 换药 🩹

为了让我们的护士进一步了解病人的情况，请提供：

1. 病人所在地区
2. 伤口类型（如果知道）
3. 伤口出现多久了
4. 请发送一张清晰的伤口照片

我们收到资料后，护理团队会进一步评估并与您联系。

如情况紧急或严重，请尽快寻求紧急医疗协助。"""),
    "2": ("hygiene_care_cn", """长者 / 病人卫生护理 🧼

为了让我们进一步了解病人的护理需求，请提供：

1. 病人所在地区
2. 病人年龄
3. 病人的行动能力
   - 可自行行走
   - 使用轮椅
   - 长期卧床
4. 需要哪方面的协助
   - 洗澡 / 擦身
   - 更换尿片
   - 个人卫生 / 清洁
   - 以上多项服务

我们收到资料后，护理团队会进一步评估并与您联系。"""),
    "3": ("feeding_tube_cn", """鼻胃喂食管置入 / 更换

请提供：

1. 病人所在地区
2. 所需服务
   - 首次置入喂食管
   - 更换现有喂食管
   - 喂食管意外脱落
3. 病人目前是否在家？
4. 什么时候需要服务？
   - 今天
   - 明天
   - 其他日期

我们的护士团队会查看您的需求并告知服务安排。"""),
    "4": ("urinary_catheter_cn", """导尿管置入 / 更换

请提供：

1. 病人所在地区
2. 所需服务
   - 首次置入导尿管
   - 更换导尿管
   - 移除导尿管
   - 导尿管阻塞 / 出现问题
   - 不确定
3. 病人性别
   - 男
   - 女
4. 什么时候需要服务？
   - 今天
   - 明天
   - 其他日期

我们的护士团队会查看您的需求并告知服务安排。"""),
    "5": ("home_physiotherapy_cn", """上门物理治疗 🏠

请提供：

1. 病人所在地区
2. 病人年龄
3. 需要物理治疗的主要原因
   - 中风康复
   - 手术后康复
   - 长者肌力 / 活动能力训练
   - 行走困难
   - 跌倒后康复
   - 其他
4. 病人目前的行动能力
   - 长期卧床
   - 使用轮椅
   - 需要协助行走
   - 可自行行走
5. 希望什么时候进行第一次治疗？

我们的团队会查看病人的需求，并与您确认物理治疗师的时间安排。"""),
    "6": ("care_home_cn", """槟城安老护理中心 🏡

请提供：

1. 长者 / 病人的年龄
2. 目前身体状况
   - 可独立生活
   - 日常生活需要协助
   - 使用轮椅
   - 长期卧床
   - 失智症 / 认知障碍
   - 出院后康复
3. 是否需要专业护理？
4. 预计入住多久？
   - 短期入住
   - 1–3个月
   - 长期入住
   - 暂不确定
5. 预计什么时候入住？
   - 立即
   - 一星期内
   - 一个月内
   - 目前只是咨询

我们的护理团队会进一步了解长者的情况，并建议合适的护理安排。"""),
}


@app.get("/")
def health():
    return "Backliners WhatsApp Bot is running", 200


@app.get("/privacy")
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backliners Privacy Policy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6;">
        <h1>Backliners Privacy Policy</h1>
        <p><strong>Last updated: 14 August 2026</strong></p>
        <p>Backliners respects the privacy of our customers and patients.</p>
        <p>Information submitted through WhatsApp may be used to respond to enquiries, arrange healthcare services, coordinate appointments and provide customer support.</p>
        <p>We do not sell personal information.</p>
        <p>Backliners takes reasonable measures to protect personal information from unauthorised access, disclosure, alteration or misuse.</p>
        <p>Backliners<br>Penang, Malaysia</p>
    </body>
    </html>
    """, 200


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


def build_reply(sender: str, text: str) -> str:
    text = text.strip().lower()
    state = user_states.get(sender)

    if text in {"hi", "hello", "hey", "menu", "start", "restart"}:
        user_states.pop(sender, None)
        return WELCOME_MESSAGE
        
    if state == "wound_location":
        user_data[sender] = {
            "service": "Wound Care",
            "location": text
        }

        user_states[sender] = "wound_type"

        return """Thank you.

What type of wound does the patient have?

If you are not sure, you may briefly describe the wound."""


    if state == "wound_type":
        user_data[sender]["wound_type"] = text

        user_states[sender] = "wound_duration"

        return """Thank you.

How long has the wound been present?

Example:
3 days / 2 weeks / 1 month"""


    if state == "wound_duration":
        user_data[sender]["wound_duration"] = text

        user_states[sender] = "wound_photo"

        return """Thank you.

Please send a clear photo of the wound.

Once we receive the photo, our Backliners team will review the information and follow up with you."""

    if state == "english_menu":
        if text in ENGLISH_SERVICES:
            new_state, reply = ENGLISH_SERVICES[text]
            user_states[sender] = new_state
            return reply
        return ENGLISH_MENU

    if state == "chinese_menu":
        if text in CHINESE_SERVICES:
            new_state, reply = CHINESE_SERVICES[text]
            user_states[sender] = new_state
            return reply
        return CHINESE_MENU

    if text in {"1", "english"}:
        user_states[sender] = "english_menu"
        return ENGLISH_MENU

    if text in {"2", "中文", "chinese"}:
        user_states[sender] = "chinese_menu"
        return CHINESE_MENU

    if state in {
        "wound_care",
        "hygiene_care",
        "feeding_tube",
        "urinary_catheter",
        "home_physiotherapy",
        "care_home",
    }:
        return """Thank you. We have received your information.

Our Backliners team will review your enquiry and follow up with you shortly.

Type MENU if you would like to start a new enquiry."""

    if state in {
        "wound_care_cn",
        "hygiene_care_cn",
        "feeding_tube_cn",
        "urinary_catheter_cn",
        "home_physiotherapy_cn",
        "care_home_cn",
    }:
        return """谢谢，我们已经收到您提供的资料。

Backliners 团队会查看您的咨询并尽快与您联系。

如需开始新的咨询，请输入 MENU。"""

    return WELCOME_MESSAGE


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}
    app.logger.warning("WEBHOOK DATA: %s", data)

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                if not messages:
                    continue

                for message in messages:
                    sender = message.get("from")
                    if not sender:
                        continue

                    message_type = message.get("type")

                    if message_type == "text":
                        text = message.get("text", {}).get("body", "").strip()
                        reply = build_reply(sender, text)

                    elif message_type == "image":
                        state = user_states.get(sender)

                        if state == "wound_photo":
                            user_data.setdefault(sender, {})
                            user_data[sender]["photo_received"] = True
                            user_states[sender] = "wound_complete"

                            reply = """Thank you. The wound photo has been received. 🩹

Our Backliners team now has the following information:

📍 Location: {location}
🩹 Wound: {wound_type}
⏱️ Duration: {wound_duration}
📷 Wound photo: Received

Our team will review your case and follow up with you shortly.

Type MENU if you would like to start a new enquiry.""".format(
                                location=user_data[sender].get("location", "-"),
                                wound_type=user_data[sender].get("wound_type", "-"),
                                wound_duration=user_data[sender].get("wound_duration", "-"),
                            )

                        elif state == "wound_care_cn":
                            reply = """谢谢，我们已经收到伤口照片。

Backliners 团队会查看资料并尽快与您联系。"""

                        else:
                            reply = WELCOME_MESSAGE

                    else:
                        continue

                    app.logger.warning(
                        "REPLYING sender=%s state=%s",
                        sender,
                        user_states.get(sender),
                    )
                    send_whatsapp_message(sender, reply)

    except Exception:
        app.logger.exception("Error processing webhook")

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
