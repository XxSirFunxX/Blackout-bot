from fetch_and_save import scrape, save_csv

if __name__ == "__main__":
    data = scrape()
    if data:
        save_csv(data)
        print("CSV با موفقیت به‌روزرسانی شد.")
    else:
        print("داده‌ای دریافت نشد.")
