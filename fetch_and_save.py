import requests
from bs4 import BeautifulSoup
import csv
import os
import urllib.parse

BASE_URL = "https://baboliha.ir/?city="
CSV_PATH = "blackouts.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

CITIES = [
    "آمل", "بابل", "بابلسر", "بهشهر", "جویبار", "ساري", 
    "سوادکوه شمالي", "سوادکوه", "سیمرغ", "فریدون کنار", 
    "قائمشهر", "میاندرود", "نکا", "گلوگاه"
]

def scrape_city(city):
    city_encoded = urllib.parse.quote(city)
    url = BASE_URL + city_encoded
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"خطا در دریافت صفحه برای شهر {city}: {e}")
        return [], ""

    soup = BeautifulSoup(r.text, "html.parser")

    # استخراج تاریخ آخرین بروزرسانی
    last_update_span = soup.find("span", id="last-update-time")
    last_update = last_update_span.get_text(strip=True) if last_update_span else "نامشخص"

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

        start, end, city_name = "", "", ""
        if meta:
            for span in meta.find_all("span"):
                t = span.get_text(strip=True)
                if "از ساعت:" in t:
                    start = t.replace("از ساعت:", "").strip()
                elif "تا ساعت:" in t:
                    end = t.replace("تا ساعت:", "").strip()
                elif "شهر:" in t:
                    city_name = t.replace("شهر:", "").strip()

        rows.append({
            "تاریخ": date_text,
            "شروع": start,
            "پایان": end,
            "شهر": city_name or city,
            "آدرس": addr_text
        })

    return rows, last_update

def scrape_all_cities():
    all_rows = []
    last_updates = []
    for city in CITIES:
        print(f"دریافت داده‌های خاموشی برای شهر {city}...")
        rows, last_update = scrape_city(city)
        if rows:
            all_rows.extend(rows)
        if last_update != "نامشخص":
            last_updates.append(last_update)
    # آخرین زمان آپدیت رو از همه بگیر
    last_update_final = max(last_updates) if last_updates else "نامشخص"
    return all_rows, last_update_final

def save_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["تاریخ", "شروع", "پایان", "شهر", "آدرس"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"فایل CSV با {len(rows)} ردیف ذخیره شد.")

if __name__ == "__main__":
    data, last_update = scrape_all_cities()
    if data:
        save_csv(data)
        print(f"CSV updated with {len(data)} rows, last update: {last_update}")
    else:
        print("داده‌ای دریافت نشد.")
