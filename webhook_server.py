import os
import csv
import requests
from flask import Flask, request, jsonify

BOT_TOKEN = os.environ.get("454808876:AAFxTfB-dTFgWZQ_JecVVLJIPIVo6GZo_6M")
CSV_PATH = "blackouts.csv"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

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

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    message = update.get("message")
    if not message:
        return jsonify({"ok": True})

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        send_message(chat_id, "سلام! یه کلمه یا آدرس بفرست تا خاموشی‌ها رو جستجو کنم.")
    else:
        results = search_csv(text)
        if results:
            reply = ""
            for r in results:
                reply += f"تاریخ: {r['تاریخ']}\nساعت: {r['شروع']} تا {r['پایان']}\nشهر: {r['شهر']}\nآدرس: {r['آدرس']}\n\n"
            send_message(chat_id, reply)
        else:
            send_message(chat_id, f"هیچ خاموشی‌ای مطابق '{text}' پیدا نشد.")
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))