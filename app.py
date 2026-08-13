import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

GRAPH_API_VERSION = "v26.0"

# Remember where each customer is in the conversation
user_states = {}
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

        <p><strong>Last updated: 13 August 2026</strong></p>

        <p>
        Backliners respects the privacy of our customers and patients.
        This Privacy Policy explains how information submitted through our
        WhatsApp communication service may be collected, used and protected.
        </p>

        <h2>Information We Collect</h2>
        <p>
        Information may include your name, telephone number, location,
        service enquiries, patient care information, appointment information,
        photographs voluntarily provided by you, and other information
        necessary for us to respond to your enquiry.
        </p>

        <h2>How We Use Information</h2>
        <p>
        Information is used to respond to enquiries, arrange home healthcare
        services, coordinate appointments, provide customer support and
        communicate with customers regarding requested Backliners services.
        </p>

        <h2>Healthcare Information</h2>
        <p>
        Customers should only provide information reasonably necessary for
        Backliners to understand and respond to their service request.
        Information provided through WhatsApp does not replace an in-person
        medical or nursing assessment.
        </p>

        <h2>Information Sharing</h2>
        <p>
        We do not sell personal information. Information may be shared with
        authorised Backliners personnel or healthcare professionals where
        necessary to provide the requested service, or where required by law.
        </p>

        <h2>Data Security</h2>
        <p>
        Backliners takes reasonable measures to protect personal information
        from unauthorised access, disclosure, alteration or misuse.
        </p>

        <h2>Data Retention</h2>
        <p>
        Information is retained only for as long as reasonably necessary for
        service delivery, operational, legal and record-keeping purposes.
        </p>

        <h2>Your Choices</h2>
        <p>
        You may contact Backliners to request correction or deletion of
        personal information, subject to applicable legal and record-keeping
        requirements.
        </p>

        <h2>Contact Us</h2>
        <p>
        For privacy-related enquiries, please contact Backliners through our
        official communication channels.
        </p>

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


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}
    app.logger.warning("WEBHOOK DATA: %s", data)

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
                    app.logger.info(
                        "INCOMING sender=%s state=%s text=%s",
                        sender,
                        user_states.get(sender),
                        text
                        )

                if user_states.get(sender) == "english_menu" and text == "1":
                    user_states[sender] = "wound_care"
                    reply = """Wound Care 🩹

Our registered nurses provide professional wound assessment and dressing services at your home.

To assist you, please provide:

1. Patient's location / area
2. Type of wound (if known)
3. How long the wound has been present
4. A clear photo of the wound

Once we receive the information, our team will review your case and advise you accordingly.

For urgent or serious conditions, please seek immediate medical attention."""

                elif user_states.get(sender) == "english_menu" and text == "2":
                    user_states[sender] = "hygiene_care"
                    reply = """Elderly / Patient Hygiene Care 🧼

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

Once we receive the information, our team will review your care requirements and advise you accordingly."""
                    
                elif user_states.get(sender) == "english_menu" and text == "3":
                    user_states[sender] = "feeding_tube"
                    reply = """Feeding Tube Insertion 🩺

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

Our nursing team will review the request and advise you on availability."""

                elif user_states.get(sender) == "english_menu" and text == "4":
                    user_states[sender] = "urinary_catheter"
                    reply = """Urinary Catheter Insertion / Replacement

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

Our nursing team will review the request and advise you on availability."""

                elif user_states.get(sender) == "english_menu" and text == "5":
                    user_states[sender] = "stoma_care"
                    reply = """Stoma Care

To assist you, please provide:

1. Patient's location / area
2. Assistance required
   - Stoma bag changing
   - Stoma cleaning / skin care
   - Stoma care education
   - Leakage / difficulty managing the stoma
   - Not sure
3. Is this a newly created stoma?
4. When would you like our nurse to visit?

Our nursing team will review the information and advise you accordingly."""

                elif user_states.get(sender) == "english_menu" and text == "6":
                    user_states[sender] = "home_physiotherapy"
                    reply = """Home Physiotherapy 🏠

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

Our team will review the patient's requirements and advise you on physiotherapist availability."""

                elif user_states.get(sender) == "english_menu" and text == "7":
                    user_states[sender] = "medical_escort"
                    reply = """Medical Escort Service – Medscort

To assist you, please provide:

1. Pick-up location
2. Hospital / clinic
3. Appointment date
4. Appointment time
5. Patient's mobility
   - Walking
   - Walking with assistance
   - Wheelchair
   - Bedridden
6. Service required
   - Escort only
   - Escort + transportation
   - Not sure

Our Medscort team will check availability and contact you regarding the arrangement."""

                elif user_states.get(sender) == "english_menu" and text == "8":
                    user_states[sender] = "care_home"
                    reply = """Care Home in Penang 🏡

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

Our care team will review the patient's needs and recommend the most suitable care arrangement."""

                elif text in {"1", "english"}:
                    user_states[sender] = "english_menu"
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
                app.logger.info("REPLYING to=%s reply=%s", sender, reply[:80])
                send_whatsapp_message(sender, reply)

    except Exception:
        app.logger.exception("Error processing webhook")

    # Meta expects a fast 200 response.
    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
