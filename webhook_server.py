import os
import csv
import requests
from flask import Flask, request, jsonify
from fetch_and_save import scrape_city, save_csv  # توجه کنید تابع scrape_city از فایل fetch_and_save

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است!")

CSV_PATH = "blackouts.csv"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

cities = [
    "آمل", "بابل", "بابلسر", "بهشهر", "جویبار",
    "ساري", "سوادکوه شمالي", "سوادکوه", "سیمرغ",
    "فریدون کنار", "قائمشهر", "میاندرود", "نکا", "گلوگاه"
]

def create_city_keyboard():
    row_size = 3
    keyboard = [cities[i:i+row_size] for i in range(0, len(cities), row_size)]
    reply_markup = {
        "keyboard": keyboard,
        "one_time_keyboard": True,
        "resize_keyboard": True
    }
    return reply_markup

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        import json
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("خطا در ارسال پیام:", e, resp.text if 'resp' in locals() else "")

def search_csv(keyword, limit=10):
    keyword = keyword.strip().lower()
    results = []
    if not os.path.exists(CSV_PATH):
        return results
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            addr = row.get("آدرس", "").lower()
            city = row.get("شهر", "").lower()
            if keyword in addr or keyword in city:
                results.append(row)
                if len(results) >= limit:
                    break
    return results

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

    if text == "/start":
        keyboard = create_city_keyboard()
        send_message(chat_id, "سلام! لطفا یکی از شهرهای زیر را انتخاب کنید:", reply_markup=keyboard)
        return jsonify({"ok": True})

    if text in cities:
        # درخواست scrape بر اساس شهر انتخابی
        data, last_update = scrape_city(text)
        if data:
            save_csv(data)
            results = search_csv(text)
            if results:
                reply = f"آخرین آپدیت: {last_update}\n\n"
                for r in results:
                    reply += (f"تاریخ: {r['تاریخ']}\n"
                              f"ساعت: {r['شروع']} تا {r['پایان']}\n"
                              f"شهر: {r['شهر']}\n"
                              f"آدرس: {r['آدرس']}\n\n")
                send_message(chat_id, reply)
            else:
                send_message(chat_id, f"هیچ خاموشی‌ای مطابق '{text}' پیدا نشد.\nآخرین آپدیت: {last_update}")
        else:
            send_message(chat_id, "در دریافت داده‌ها مشکلی پیش آمد، لطفا بعدا تلاش کنید.")
    else:
        send_message(chat_id, "لطفاً یکی از شهرهای موجود را از کلیدهای زیر انتخاب کنید یا /start را ارسال کنید.")

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
