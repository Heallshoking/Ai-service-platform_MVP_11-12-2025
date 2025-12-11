# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from utils.sheets_client import SheetsClient

load_dotenv()

TEST_RECORDS = [
    {'title': 'The Dark Side of the Moon', 'artist': 'Pink Floyd', 'genre': 'Прогрессивный рок', 'year': 1973, 'label': 'Harvest Records', 'country': 'Великобритания', 'condition': 'Near Mint', 'price': 3500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Abbey Road', 'artist': 'The Beatles', 'genre': 'Рок', 'year': 1969, 'label': 'Apple Records', 'country': 'Великобритания', 'condition': 'VG+', 'price': 4200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Thriller', 'artist': 'Michael Jackson', 'genre': 'Поп', 'year': 1982, 'label': 'Epic Records', 'country': 'США', 'condition': 'Mint', 'price': 2800, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Led Zeppelin IV', 'artist': 'Led Zeppelin', 'genre': 'Хард-рок', 'year': 1971, 'label': 'Atlantic Records', 'country': 'Великобритания', 'condition': 'VG', 'price': 3200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Группа крови', 'artist': 'Кино', 'genre': 'Рок', 'year': 1988, 'label': 'Мелодия', 'country': 'СССР', 'condition': 'Near Mint', 'price': 2200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'The Wall', 'artist': 'Pink Floyd', 'genre': 'Прогрессивный рок', 'year': 1979, 'label': 'Harvest Records', 'country': 'Великобритания', 'condition': 'VG+', 'price': 4500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Back in Black', 'artist': 'AC/DC', 'genre': 'Хард-рок', 'year': 1980, 'label': 'Atlantic Records', 'country': 'Австралия', 'condition': 'Near Mint', 'price': 2900, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Kind of Blue', 'artist': 'Miles Davis', 'genre': 'Джаз', 'year': 1959, 'label': 'Columbia Records', 'country': 'США', 'condition': 'VG', 'price': 3800, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Nevermind', 'artist': 'Nirvana', 'genre': 'Гранж', 'year': 1991, 'label': 'DGC Records', 'country': 'США', 'condition': 'Near Mint', 'price': 2600, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Hotel California', 'artist': 'Eagles', 'genre': 'Рок', 'year': 1976, 'label': 'Asylum Records', 'country': 'США', 'condition': 'Near Mint', 'price': 2400, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': "Sgt. Pepper's Lonely Hearts Club Band", 'artist': 'The Beatles', 'genre': 'Рок', 'year': 1967, 'label': 'Parlophone', 'country': 'Великобритания', 'condition': 'VG+', 'price': 5500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Rumours', 'artist': 'Fleetwood Mac', 'genre': 'Рок', 'year': 1977, 'label': 'Warner Bros.', 'country': 'США', 'condition': 'Near Mint', 'price': 2500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'OK Computer', 'artist': 'Radiohead', 'genre': 'Альтернативный рок', 'year': 1997, 'label': 'Parlophone', 'country': 'Великобритания', 'condition': 'VG+', 'price': 4200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Exile on Main St.', 'artist': 'The Rolling Stones', 'genre': 'Рок', 'year': 1972, 'label': 'Rolling Stones Records', 'country': 'Великобритания', 'condition': 'VG', 'price': 3900, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Ziggy Stardust', 'artist': 'David Bowie', 'genre': 'Глэм-рок', 'year': 1972, 'label': 'RCA', 'country': 'Великобритания', 'condition': 'VG+', 'price': 4300, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Unknown Pleasures', 'artist': 'Joy Division', 'genre': 'Пост-панк', 'year': 1979, 'label': 'Factory', 'country': 'Великобритания', 'condition': 'VG+', 'price': 4100, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'A Night at the Opera', 'artist': 'Queen', 'genre': 'Рок', 'year': 1975, 'label': 'EMI', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3600, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Paranoid', 'artist': 'Black Sabbath', 'genre': 'Хеви-метал', 'year': 1970, 'label': 'Vertigo', 'country': 'Великобритания', 'condition': 'VG', 'price': 3700, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Highway 61 Revisited', 'artist': 'Bob Dylan', 'genre': 'Фолк-рок', 'year': 1965, 'label': 'Columbia', 'country': 'США', 'condition': 'VG', 'price': 3400, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'London Calling', 'artist': 'The Clash', 'genre': 'Панк-рок', 'year': 1979, 'label': 'CBS', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3600, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Born to Run', 'artist': 'Bruce Springsteen', 'genre': 'Рок', 'year': 1975, 'label': 'Columbia', 'country': 'США', 'condition': 'VG+', 'price': 3300, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'The Velvet Underground & Nico', 'artist': 'The Velvet Underground', 'genre': 'Арт-рок', 'year': 1967, 'label': 'Verve', 'country': 'США', 'condition': 'VG+', 'price': 4200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Master of Puppets', 'artist': 'Metallica', 'genre': 'Трэш-метал', 'year': 1986, 'label': 'Elektra', 'country': 'США', 'condition': 'VG+', 'price': 3000, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Purple Rain', 'artist': 'Prince', 'genre': 'Поп-фанк', 'year': 1984, 'label': 'Warner Bros.', 'country': 'США', 'condition': 'VG+', 'price': 3100, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'The Joshua Tree', 'artist': 'U2', 'genre': 'Альтернативный рок', 'year': 1987, 'label': 'Island', 'country': 'Ирландия', 'condition': 'VG+', 'price': 3200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'The Queen Is Dead', 'artist': 'The Smiths', 'genre': 'Инди-рок', 'year': 1986, 'label': 'Rough Trade', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': "(What's the Story) Morning Glory?", 'artist': 'Oasis', 'genre': 'Брит-поп', 'year': 1995, 'label': 'Creation', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3000, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Violator', 'artist': 'Depeche Mode', 'genre': 'Синти-поп', 'year': 1990, 'label': 'Mute', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3200, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'Disintegration', 'artist': 'The Cure', 'genre': 'Пост-панк', 'year': 1989, 'label': 'Fiction', 'country': 'Великобритания', 'condition': 'VG+', 'price': 3300, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'To Pimp a Butterfly', 'artist': 'Kendrick Lamar', 'genre': 'Хип-хоп', 'year': 2015, 'label': 'Top Dawg', 'country': 'США', 'condition': 'VG+', 'price': 4500, 'photo_url': '', 'seller_tg_id': 123456789},
    {'title': 'My Beautiful Dark Twisted Fantasy', 'artist': 'Kanye West', 'genre': 'Хип-хоп', 'year': 2010, 'label': 'Def Jam', 'country': 'США', 'condition': 'VG+', 'price': 4300, 'photo_url': '', 'seller_tg_id': 123456789}
]

def main():
    print("🎵 Заполняю каталог тестовыми данными...")
    sheets_client = SheetsClient()
    added = 0
    for record in TEST_RECORDS:
        try:
            sheets_client.add_record(record)
            added += 1
            print(f"✅ {added}. {record['artist']} - {record['title']}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    print(f"\n🎉 Добавлено {added} записей!")

if __name__ == "__main__":
    main()
