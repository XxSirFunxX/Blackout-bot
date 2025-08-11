import os
import csv
import json
import requests
from flask import Flask, request, jsonify
from fetch_and_save import scrape, save_csv

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است!")

CSV_PATH = "blackouts.csv"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# دیکشنری برای ذخیره حالت کاربران
user_states = {}

cities_keyboard = {
    "keyboard": [
        ["آمل", "بابل", "بابلسر"],
        ["بهشهر", "جویبار", "ساري"],
        ["سوادکوه شمالي", "سوادکوه", "سیمرغ"],
        ["فریدون کنار", "قائمشهر", "میاندرود"],
        ["نکا", "گلوگاه"]
    ],
    "one_time_keyboard": True,
    "resize_keyboard": True
}

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("خطا در ارسال پیام:", e, resp.text if 'resp' in locals() else "")

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update:
        return jsonify({"ok": True})

    message = update.get("message")
    if not message:
        return jsonify({"ok": True})

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # بروزرسانی داده‌ها و ذخیره CSV
    data, last_update = scrape()
    if data:
        save_csv(data)
    else:
        print("داده‌ای دریافت نشد برای به‌روزرسانی فایل CSV.")

    state = user_states.get(chat_id)

    if text == "/start":
        send_message(chat_id, "لطفا شهر خود را انتخاب کنید:", reply_markup=cities_keyboard)
        user_states[chat_id] = "awaiting_city"
        return jsonify({"ok": True})

    if state == "awaiting_city":
        if text in sum(cities_keyboard["keyboard"], []):
            user_states[chat_id] = {"city": text, "awaiting_address": True}
            send_message(chat_id, f"شهر {text} انتخاب شد. حالا آدرس مورد نظر را بفرست:")
        else:
            send_message(chat_id, "لطفا یکی از شهرهای موجود را انتخاب کنید:", reply_markup=cities_keyboard)
        return jsonify({"ok": True})

    if isinstance(state, dict) and state.get("awaiting_address"):
        city = state["city"]
        keyword = text.lower()
        results = []
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("شهر", "").lower() == city.lower() and keyword in row.get("آدرس", "").lower():
                        results.append(row)
                        if len(results) >= 10:
                            break
        if results:
            reply = f"نتایج جستجو برای '{text}' در شهر {city}:\n\n"
            for r in results:
                reply += (f"تاریخ: {r['تاریخ']}\n"
                          f"ساعت: {r['شروع']} تا {r['پایان']}\n"
                          f"آدرس: {r['آدرس']}\n\n")
            send_message(chat_id, reply)
        else:
            send_message(chat_id, f"هیچ خاموشی‌ای مطابق '{text}' در شهر {city} پیدا نشد.")

        return jsonify({"ok": True})

    # اگر حالت نداشته باشه یا پیام نامربوط بود، مجدد کیبورد انتخاب شهر رو بفرست
    send_message(chat_id, "شهر خود را انتخاب کنید:", reply_markup=cities_keyboard)
    user_states[chat_id] = "awaiting_city"

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
