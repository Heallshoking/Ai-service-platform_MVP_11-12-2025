"""
Telegram Folders Integration для BALT-SET.RU
Автоматическое создание папок в Telegram для клиентов и мастеров
"""

# ========== КОНФИГУРАЦИЯ ПАПОК ==========

# Папка для клиентов: "Электрик БАЛТСЕТЬ"
CLIENT_FOLDER_CONFIG = {
    "folder_name": "⚡ Электрик БАЛТСЕТЬ",
    "description": "Все важные уведомления по вашей заявке",
    "channels": [
        "@ai_service_client_bot",  # Главный бот клиента
        "@konigkomfort",            # Инженерные сети (если нужно)
        # Добавьте канал с новостями/акциями если будет
    ]
}

# Папка для мастеров: "Заказы БАЛТСЕТЬ"
MASTER_FOLDER_CONFIG = {
    "folder_name": "🔧 Заказы БАЛТСЕТЬ",
    "description": "Все новые заказы и уведомления",
    "channels": [
        "@ai_service_master_bot",  # Главный бот мастера
        # Можно добавить канал с инструкциями для мастеров
    ]
}


def generate_folder_invite_link(bot_username: str, folder_name: str, channels: list) -> str:
    """
    Генерирует пригласительную ссылку с автоматическим добавлением в папку
    
    Args:
        bot_username: Username бота (например: @ai_service_client_bot)
        folder_name: Название папки (например: "⚡ Электрик БАЛТСЕТЬ")
        channels: Список username'ов каналов/ботов для добавления в папку
    
    Returns:
        Пригласительная ссылка с параметром addlist
    
    Пример:
        https://t.me/ai_service_client_bot?start=welcome&addlist=channel1,channel2
    """
    # Убираем @ из username'ов
    clean_channels = [ch.replace('@', '') for ch in channels]
    
    # Формируем параметр addlist
    addlist_param = ','.join(clean_channels)
    
    # Генерируем ссылку
    clean_bot = bot_username.replace('@', '')
    invite_link = f"https://t.me/{clean_bot}?start=welcome&addlist={addlist_param}"
    
    return invite_link


def get_client_folder_invite() -> dict:
    """
    Получить данные для папки клиента
    
    Returns:
        {
            "link": "https://t.me/...",
            "folder_name": "⚡ Электрик БАЛТСЕТЬ",
            "description": "...",
            "message": "Текст для клиента"
        }
    """
    link = generate_folder_invite_link(
        bot_username="@ai_service_client_bot",
        folder_name=CLIENT_FOLDER_CONFIG["folder_name"],
        channels=CLIENT_FOLDER_CONFIG["channels"]
    )
    
    message = f"""
📁 **Добавьте папку "{CLIENT_FOLDER_CONFIG["folder_name"]}"**

Чтобы не потерять важные уведомления о вашей заявке, добавьте специальную папку в Telegram.

👉 **Нажмите на ссылку:** {link}

✅ Все чаты по вашему заказу будут в одной папке
✅ Быстрый доступ к мастеру и поддержке
✅ Уведомления всегда под рукой

_Это займет 1 секунду!_
    """
    
    return {
        "link": link,
        "folder_name": CLIENT_FOLDER_CONFIG["folder_name"],
        "description": CLIENT_FOLDER_CONFIG["description"],
        "message": message.strip()
    }


def get_master_folder_invite() -> dict:
    """
    Получить данные для папки мастера
    
    Returns:
        {
            "link": "https://t.me/...",
            "folder_name": "🔧 Заказы БАЛТСЕТЬ",
            "description": "...",
            "message": "Текст для мастера"
        }
    """
    link = generate_folder_invite_link(
        bot_username="@ai_service_master_bot",
        folder_name=MASTER_FOLDER_CONFIG["folder_name"],
        channels=MASTER_FOLDER_CONFIG["channels"]
    )
    
    message = f"""
📁 **Добавьте рабочую папку "{MASTER_FOLDER_CONFIG["folder_name"]}"**

Для удобной работы с заказами создайте отдельную папку в Telegram.

👉 **Нажмите на ссылку:** {link}

✅ Все новые заказы в одном месте
✅ Быстрый доступ к клиентам
✅ Удобное управление заявками

_Организуйте свою работу за 1 клик!_
    """
    
    return {
        "link": link,
        "folder_name": MASTER_FOLDER_CONFIG["folder_name"],
        "description": MASTER_FOLDER_CONFIG["description"],
        "message": message.strip()
    }


# ========== ИСПОЛЬЗОВАНИЕ В БОТЕ ==========

def send_folder_invite_to_client(update, context, order_id: int):
    """
    Отправить приглашение в папку клиенту после создания заявки
    
    Использовать в telegram_client_bot.py в функции confirm()
    """
    folder_data = get_client_folder_invite()
    
    # Создаем кнопку с InlineKeyboard
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(
            f"📁 Добавить папку \"{folder_data['folder_name']}\"",
            url=folder_data['link']
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение
    message = f"""
✅ **Заявка #{order_id} создана!**

📞 Мастер свяжется с вами в течение 15 минут.

💡 **Совет:** Добавьте нашу папку в Telegram, чтобы не пропустить важные уведомления!
    """
    
    update.message.reply_text(
        message.strip(),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


def send_folder_invite_to_master(bot, master_telegram_id: int, order_id: int):
    """
    Отправить приглашение в папку мастеру после назначения на заказ
    
    Использовать когда мастер принимает заказ
    """
    folder_data = get_master_folder_invite()
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(
            f"📁 Добавить папку \"{folder_data['folder_name']}\"",
            url=folder_data['link']
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
✅ **Вы назначены на заказ #{order_id}!**

📋 Детали заказа доступны в боте.

💡 **Совет для мастеров:** Добавьте рабочую папку, чтобы все заказы были в одном месте!
    """
    
    bot.send_message(
        chat_id=master_telegram_id,
        text=message.strip(),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ========== АЛЬТЕРНАТИВА: Deep Links ==========

def create_folder_deeplink(folder_name: str, channels: list) -> str:
    """
    Создает deep link для добавления папки (альтернативный метод)
    
    Формат: tg://addlist?name=FolderName&include=channel1,channel2
    """
    import urllib.parse
    
    clean_channels = [ch.replace('@', '') for ch in channels]
    encoded_name = urllib.parse.quote(folder_name)
    include_param = ','.join(clean_channels)
    
    deeplink = f"tg://addlist?name={encoded_name}&include={include_param}"
    
    return deeplink


# ========== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========

if __name__ == "__main__":
    print("📁 TELEGRAM FOLDERS INTEGRATION\n")
    
    # Для клиента
    print("=" * 60)
    print("КЛИЕНТ:")
    print("=" * 60)
    client_data = get_client_folder_invite()
    print(f"Папка: {client_data['folder_name']}")
    print(f"Ссылка: {client_data['link']}")
    print(f"\nСообщение:\n{client_data['message']}")
    
    print("\n\n")
    
    # Для мастера
    print("=" * 60)
    print("МАСТЕР:")
    print("=" * 60)
    master_data = get_master_folder_invite()
    print(f"Папка: {master_data['folder_name']}")
    print(f"Ссылка: {master_data['link']}")
    print(f"\nСообщение:\n{master_data['message']}")
