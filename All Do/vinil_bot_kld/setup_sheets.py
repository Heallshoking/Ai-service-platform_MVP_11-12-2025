"""Настройка структуры Google Sheets"""
import os
from dotenv import load_dotenv
from utils.sheets_client import SheetsClient
import gspread

load_dotenv()

def setup_sheets():
    print("📊 Настройка структуры Google Sheets...")
    
    # Подключение
    sheets_client = SheetsClient()
    spreadsheet = sheets_client.spreadsheet
    
    # 1. Создаем/обновляем лист "Справочник"
    try:
        worksheet = spreadsheet.worksheet("Справочник")
        print("✅ Лист 'Справочник' существует, очищаем...")
        worksheet.clear()
    except:
        print("📝 Создаём лист 'Справочник'...")
        worksheet = spreadsheet.add_worksheet(title="Справочник", rows=100, cols=20)
    
    # Заголовки для каталога
    headers = [
        "Название", "Исполнитель", "Жанр", "Год", "Лейбл",
        "Страна", "Состояние", "Цена", "ФОТО_URL",
        "Продавец_TG_ID", "Статус", "Описание",
        "Минимум_складчиков", "Складчина_участников", "Цена_ориентир", "Последний_интерес"
    ]
    worksheet.update([headers], 'A1:P1')
    
    # Тестовые данные
    test_data = [
        ["The Dark Side of the Moon", "Pink Floyd", "Progressive Rock", 1973, "Harvest Records", "UK", "Near Mint", 3500, "", 123456789, "🟢 Доступна", ""],
        ["Abbey Road", "The Beatles", "Rock", 1969, "Apple Records", "UK", "Very Good+", 4200, "", 123456789, "🟢 Доступна", ""],
        ["Thriller", "Michael Jackson", "Pop", 1982, "Epic Records", "USA", "Mint", 2800, "", 123456789, "🟢 Доступна", ""],
        ["Led Zeppelin IV", "Led Zeppelin", "Hard Rock", 1971, "Atlantic Records", "UK", "Very Good", 3200, "", 123456789, "🟢 Доступна", ""],
        ["Группа крови", "Кино", "Рок", 1988, "Мелодия", "СССР", "Near Mint", 2200, "", 123456789, "🟢 Доступна", ""],
        ["The Wall", "Pink Floyd", "Progressive Rock", 1979, "Harvest Records", "UK", "Very Good+", 4500, "", 123456789, "🟢 Доступна", ""],
        ["Back in Black", "AC/DC", "Hard Rock", 1980, "Atlantic Records", "Australia", "Near Mint", 2900, "", 123456789, "🟢 Доступна", ""],
        ["Kind of Blue", "Miles Davis", "Jazz", 1959, "Columbia Records", "USA", "Very Good", 3800, "", 123456789, "🟢 Доступна", ""],
        ["Nevermind", "Nirvana", "Grunge", 1991, "DGC Records", "USA", "Near Mint", 2600, "", 123456789, "🟢 Доступна", ""],
        ["Hotel California", "Eagles", "Rock", 1976, "Asylum Records", "USA", "Near Mint", 2400, "", 123456789, "🟢 Доступна", ""]
    ]
    
    worksheet.update(test_data, 'A2:P11')
    print(f"✅ Добавлено {len(test_data)} тестовых записей в 'Справочник'")
    
    # 2. Создаем лист "Балансы"
    try:
        balances = spreadsheet.worksheet("Балансы")
        balances.clear()
    except:
        balances = spreadsheet.add_worksheet(title="Балансы", rows=50, cols=5)
    
    balances.update('A1:E1', [["TG ID", "Имя", "Добавлено записей", "Продано записей", "Дата регистрации"]])
    print("✅ Лист 'Балансы' готов")
    
    # 3. Создаем лист "Отчёты"
    try:
        reports = spreadsheet.worksheet("Отчёты")
        reports.clear()
    except:
        reports = spreadsheet.add_worksheet(title="Отчёты", rows=100, cols=6)
    
    reports.update('A1:F1', [["Дата/Время", "ID записи", "Действие", "Продавец TG ID", "Покупатель TG ID", "Сумма"]])
    print("✅ Лист 'Отчёты' готов")
    
    # 4. Создаем лист "photo_hashes"
    try:
        hashes = spreadsheet.worksheet("photo_hashes")
        hashes.clear()
    except:
        hashes = spreadsheet.add_worksheet(title="photo_hashes", rows=100, cols=3)
    
    hashes.update([["Photo Hash", "Record ID", "Timestamp"]], 'A1:C1')
    print("✅ Лист 'photo_hashes' готов")
    
    # 5. Создаем лист "Предзаказы"
    try:
        preorders = spreadsheet.worksheet("Предзаказы")
        preorders.clear()
    except:
        preorders = spreadsheet.add_worksheet(title="Предзаказы", rows=200, cols=8)
    
    preorders.update([["Дата/Время", "Название", "Исполнитель", "Пользователь TG", "Контакт", "Тип", "Комментарий", "Статус"]], 'A1:H1')
    print("✅ Лист 'Предзаказы' готов")
    
    # 6. Создаем лист "Оповещения_админу"
    try:
        admin_notes = spreadsheet.worksheet("Оповещения_админу")
        admin_notes.clear()
    except:
        admin_notes = spreadsheet.add_worksheet(title="Оповещения_админу", rows=200, cols=5)
    
    admin_notes.update([["Дата/Время", "Событие", "Пластинка", "Детали", "Ссылка"]], 'A1:E1')
    print("✅ Лист 'Оповещения_админу' готов")
    
    print("\n🎉 Таблица готова к работе!")
    print(f"📋 Ссылка: {spreadsheet.url}")

if __name__ == "__main__":
    setup_sheets()
