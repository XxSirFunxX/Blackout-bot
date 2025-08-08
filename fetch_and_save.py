import requests
from bs4 import BeautifulSoup
import csv

CSV_PATH = "blackouts.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_city(city_name):
    """
    دریافت داده خاموشی‌ها برای شهری مشخص
    city_name: نام شهر به زبان فارسی، مثل 'بابل' یا 'بابلسر'
    """
    # کد شهر را URL ای encode میکنیم (مثلاً فضای خالی به %20 تبدیل می‌شود)
    import urllib.parse
    encoded_city = urllib.parse.quote(city_name)
    URL = f"https://baboliha.ir/?city={encoded_city}"

    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"خطا در دریافت صفحه برای شهر {city_name}:", e)
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

        rows.append({
            "تاریخ": date_text,
            "شروع": start,
            "پایان": end,
            "شهر": city,
            "آدرس": addr_text,
        })

    return rows, last_update


def save_csv(rows, path=CSV_PATH):
    """
    ذخیره داده‌ها در فایل CSV
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["تاریخ", "شروع", "پایان", "شهر", "آدرس"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"فایل CSV با {len(rows)} ردیف ذخیره شد.")

# اگر بخواهید به صورت standalone فایل را تست کنید:
if __name__ == "__main__":
    city = input("نام شهر را وارد کنید: ")
    data, last_update = scrape_city(city)
    if data:
        save_csv(data)
        print(f"CSV به روز شد با {len(data)} ردیف. آخرین بروزرسانی: {last_update}")
    else:
        print("داده‌ای دریافت نشد.")
