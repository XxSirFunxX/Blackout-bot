import requests
from bs4 import BeautifulSoup
import csv

URL_TEMPLATE = "https://baboliha.ir/?city={city}"
CSV_PATH = "blackouts.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_city(city):
    url = URL_TEMPLATE.format(city=city)
    print(f"دریافت داده‌های خاموشی برای شهر {city}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"خطا در دریافت صفحه برای شهر {city}: {e}")
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

        rows.append({"تاریخ": date_text, "شروع": start, "پایان": end, "شهر": city_name, "آدرس": addr_text})

    return rows

def scrape_all_cities(cities):
    all_rows = []
    for city in cities:
        city_rows = scrape_city(city)
        all_rows.extend(city_rows)
    return all_rows

def get_last_update():
    url = URL_TEMPLATE.format(city="بابل")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("خطا در دریافت صفحه برای آخرین آپدیت:", e)
        return "نامشخص"

    soup = BeautifulSoup(r.text, "html.parser")
    last_update_span = soup.find("span", id="last-update-time")
    if last_update_span:
        return last_update_span.get_text(strip=True)
    return "نامشخص"

def save_csv(rows, last_update):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["تاریخ", "شروع", "پایان", "شهر", "آدرس"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        # اضافه کردن ردیف آخر برای آخرین آپدیت
        writer.writerow({"تاریخ": "آخرین آپدیت", "شروع": last_update})

    print(f"فایل CSV با {len(rows)} ردیف ذخیره شد. آخرین آپدیت: {last_update}")
