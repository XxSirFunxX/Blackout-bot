import os
import csv
import requests
from flask import Flask, request, jsonify

from fetch_and_save import scrape_all_cities, get_last_update, save_csv

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است!")

CSV_PATH = "blackouts.csv"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

cities = [
    "آمل", "بابل", "بابلسر", "بهشهر", "جویبار", "ساري", "سوادکوه شمالي",
    "سوادکوه", "سیمرغ", "فریدون کنار", "قائمشهر", "میاندرود", "نکا", "گلوگاه"
]

user_states = {}

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("خطا در ارسال پیام:", e, resp.text if 'resp' in locals() else "")

def build_city_buttons():
    keyboard = []
    row = []
    for i, city in enumerate(cities, 1):
        row.append({"text": city, "callback_data": f"city_{city}"})
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return {"inline_keyboard": keyboard}

def search_csv(keyword, limit=10):
    keyword = keyword.strip().lower()
    results = []
    if not os.path.exists(CSV_PATH):
        return results, "نامشخص"
    last_update = "نامشخص"
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("تاریخ") == "آخرین آپدیت":
                last_update = row.get("شروع", "نامشخص")
                continue
            addr = row.get("آدرس", "").lower()
            city = row.get("شهر", "").lower()
            if keyword in addr or keyword in city:
                results.append(row)
                if len(results) >= limit:
                    break
    return results, last_update

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update:
        return jsonify({"ok": True})

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text == "/start":
            send_message(chat_id, "داده‌ها در حال به‌روزرسانی هستند. لطفا کمی صبر کنید...")
            rows = scrape_all_cities(cities)
            last_update = get_last_update()
            if rows:
                save_csv(rows, last_update)
                send_message(chat_id, f"داده‌ها با موفقیت به‌روز شدند.\nآخرین آپدیت: {last_update}")
            else:
                send_message(chat_id, "متأسفانه نتوانستم داده‌ها را به‌روز کنم.")

            send_message(chat_id, "لطفا شهر خود را انتخاب کن:", reply_markup=build_city_buttons())
            user_states.pop(chat_id, None)
            return jsonify({"ok": True})

        if chat_id in user_states:
            city = user_states[chat_id]["city"]
            query = f"{city} {text}"
            results, last_update = search_csv(query)
            if results:
                reply = f"نتایج جستجو برای <b>{query}</b>:\n"
                reply += f"آخرین آپدیت ساعات خاموشی: {last_update}\n\n"
                for r in results:
                    reply += (f"تاریخ: {r['تاریخ']}\n"
                              f"ساعت: {r['شروع']} تا {r['پایان']}\n"
                              f"شهر: {r['شهر']}\n"
                              f"آدرس: {r['آدرس']}\n\n")
                send_message(chat_id, reply)
            else:
                send_message(chat_id, f"هیچ خاموشی‌ای مطابق '{query}' پیدا نشد.\nآخرین آپدیت: {last_update}")

            send_message(chat_id, "برای دریافت آخرین آپدیت دیتابیس، لطفاً دوباره /start را بزنید.")
            return jsonify({"ok": True})

        else:
            send_message(chat_id, "سلام! لطفاً ابتدا با دستور /start شهر خود را انتخاب کنید.")
            return jsonify({"ok": True})

    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        if data.startswith("city_"):
            city = data[len("city_"):]
            user_states[chat_id] = {"city": city}
            send_message(chat_id, f"شهر <b>{city}</b> انتخاب شد.\nحالا لطفا آدرس خود را ارسال کنید.")
            answer_url = f"{TELEGRAM_API}/answerCallbackQuery"
            callback_id = callback["id"]
            try:
                requests.post(answer_url, json={"callback_query_id": callback_id})
            except:
                pass
            return jsonify({"ok": True})

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
