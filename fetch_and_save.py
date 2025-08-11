import requests
from bs4 import BeautifulSoup
import csv
import os

cities = [
    "آمل", "بابل", "بابلسر", "بهشهر", "جویبار", "ساري",
    "سوادکوه شمالي", "سوادکوه", "سیمرغ", "فریدون کنار",
    "قائمشهر", "میاندرود", "نکا", "گلوگاه"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_PATH = "blackouts.csv"

def scrape_city(city):
    print(f"دریافت داده‌های خاموشی برای شهر {city}...")
    city_url = f"https://baboliha.ir/?city={city}"
    try:
        r = requests.get(city_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"خطا در دریافت صفحه برای شهر {city}:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    outage_list = soup.find("ul", class_="outage-card-list")
    if outage_list:
        items = outage_list.find_all("li", class_="outage-card")
    else:
        items = soup.find_all("li", class_="outage-card")

    rows = []
    for it in items:
        date = it.find("div", class_="card-date")
        meta = it.find("div", class_="card-meta")
        address = it.find("div", class_="card-address")

        date_text = date.get_text(strip=True) if date else ""
        addr_text = address.get_text(strip=True).replace("آدرس:", "").strip() if address else ""

        start, end = "", ""
        if meta:
            for span in meta.find_all("span"):
                t = span.get_text(strip=True)
                if "از ساعت:" in t:
                    start = t.replace("از ساعت:", "").strip()
                elif "تا ساعت:" in t:
                    end = t.replace("تا ساعت:", "").strip()

        rows.append({"تاریخ": date_text, "شروع": start, "پایان": end, "شهر": city, "آدرس": addr_text})

    return rows

def scrape():
    all_rows = []
    for city in cities:
        city_rows = scrape_city(city)
        all_rows.extend(city_rows)
    # آخرین تاریخ را می‌توان از آخرین داده‌ها یا جداگانه استخراج کرد
    last_update = "نامشخص"  # یا مقدار واقعی اگر دارید
    print(f"فایل CSV با {len(all_rows)} ردیف ذخیره شد.")
    return all_rows, last_update

def save_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["تاریخ", "شروع", "پایان", "شهر", "آدرس"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
