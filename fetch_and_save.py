import requests
from bs4 import BeautifulSoup
import csv
import os

URL = "https://baboliha.ir/?city=%D8%A8%D8%A7%D8%A8%D9%84"
CSV_PATH = "blackouts.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("خطا در دریافت صفحه:", e)
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

        start, end, city = "", "", ""
        if meta:
            for span in meta.find_all("span"):
                t = span.get_text(strip=True)
                if "از ساعت:" in t:
                    start = t.replace("از ساعت:", "").strip()
                elif "تا ساعت:" in t:
                    end = t.replace("تا ساعت:", "").strip()
                elif "شهر:" in t:
                    city = t.replace("شهر:", "").strip()

        rows.append({"تاریخ": date_text, "شروع": start, "پایان": end, "شهر": city, "آدرس": addr_text})

    return rows

def save_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["تاریخ", "شروع", "پایان", "شهر", "آدرس"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"فایل CSV با {len(rows)} ردیف ذخیره شد.")

if __name__ == "__main__":
    data = scrape()
    if data:
        save_csv(data)
    else:
        print("داده‌ای دریافت نشد.")