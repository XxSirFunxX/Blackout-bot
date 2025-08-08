import os
import csv
import requests
from flask import Flask, request, jsonify

from fetch_and_save import scrape, save_csv

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است!")

CSV_PATH = "blackouts.csv"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
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

    # دریافت داده‌ها و تاریخ آخرین بروزرسانی
    data, last_update = scrape()
    if data:
        save_csv(data)
    else:
        print("داده‌ای دریافت نشد برای به‌روزرسانی فایل CSV.")

    if text == "/start":
        send_message(chat_id, "سلام! یه کلمه از آدرس خودت رو بفرست تا خاموشی‌ها رو جستجو کنم.")
    else:
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

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
