import asyncio
from telethon import TelegramClient, events, Button
from datetime import datetime

# Замените значения ниже на ваши API ID, API Hash и телефон
api_id = "your_api_id"
api_hash = 'your_api_hash'
bot_token = 'your_bot_token'
register_file_path = './accs_for_register.txt'  # Путь к файлу для регистрации
accs_like_file_path = './accs_like.txt'  # Путь к файлу для записи использованных аккаунтов

# Создаем клиент Telethon
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Глобальная переменная для хранения текущего аккаунта
current_account = None
current_account_index = None


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    # Отправка пользователю клавиатуры с кнопками
    buttons = [
        [Button.inline("Я хочу зарегистрировать", b"register")],
        [Button.inline("Я хочу использовать", b"use")]
    ]
    await event.respond("Выберите действие:", buttons=buttons)


@client.on(events.CallbackQuery(data=b"register"))
async def handle_register(event):
    global current_account
    # Обработка выбора "Я хочу зарегистрировать"
    with open(register_file_path, 'r') as file:
        lines = file.readlines()

    if lines:
        # Получаем первую строку и делим её на username и password
        first_line = lines[0].strip()
        username, password = first_line.split(':')

        # Сохраняем текущий аккаунт
        current_account = first_line

        # Отправляем username и password в двух разных сообщениях
        await event.respond(username)
        await event.respond(password)

        # Отправка пользователю клавиатуры с кнопками после вывода строки
        buttons = [
            [Button.inline("Использовал", b"register_used")],
            [Button.inline("Пропустил", b"register_skipped")],
            [Button.inline("Не работает", b"register_not_working")]
        ]
        await event.respond("Выберите действие:", buttons=buttons)
    else:
        await event.respond("Файл регистрации пуст или произошла ошибка при чтении файла.")


@client.on(events.CallbackQuery(data=b"register_used"))
async def register_used(event):
    global current_account
    if current_account:
        # Добавляем строку в файл accs_like.txt с текущей датой
        with open(accs_like_file_path, 'a') as file:
            tg_user_name = event.sender.username if event.sender.username else "tg_user_name"
            current_date = datetime.now().strftime("%Y-%m-%d")
            file.write(f"{current_account}:false:tg_user_name:{current_date}\n")

        # Удаляем строку из файла accs_for_register.txt
        with open(register_file_path, 'r') as file:
            lines = file.readlines()

        if lines:
            lines = [line for line in lines if line.strip() != current_account]

            with open(register_file_path, 'w') as file:
                file.writelines(lines)

        await event.respond("Аккаунт сохранен как использованный и удален из списка регистрации.")
        current_account = None
        # Возвращаем пользователя к начальному меню
        await start(event)
    else:
        await event.respond("Ошибка: нет текущего аккаунта.")


@client.on(events.CallbackQuery(data=b"register_skipped"))
async def register_skipped(event):
    global current_account
    await event.respond("Вы пропустили аккаунт.")
    current_account = None
    # Возвращаем пользователя к начальному меню
    await start(event)


@client.on(events.CallbackQuery(data=b"register_not_working"))
async def register_not_working(event):
    global current_account
    if current_account:
        # Удаляем первую строку из файла accs_for_register.txt
        with open(register_file_path, 'r') as file:
            lines = file.readlines()

        if lines:
            first_line = lines[0].strip()
            if first_line == current_account:
                lines.pop(0)
                with open(register_file_path, 'w') as file:
                    file.writelines(lines)

        await event.respond("Аккаунт удален.")
        current_account = None
        # Возвращаем пользователя к начальному меню
        await start(event)
    else:
        await event.respond("Ошибка: нет текущего аккаунта.")


@client.on(events.CallbackQuery(data=b"use"))
async def handle_use(event):
    global current_account, current_account_index
    # Обработка выбора "Я хочу использовать"
    with open(accs_like_file_path, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        parts = line.strip().split(':')
        if len(parts) >= 3 and parts[2] == 'false':
            username, password, status, tg_user, register_date = parts[0], parts[1], parts[2], parts[3], parts[4]
            current_account = line.strip()
            current_account_index = i

            await event.respond("В формате логин/номер телефона/эмейл \n пароль")
            await event.respond(username)
            await event.respond(password)
            await event.respond(f"Дата регистрации: {register_date}")

            buttons = [
                [Button.inline("Использовал", b"use_used")],
                [Button.inline("Пропустил", b"use_skipped")],
                [Button.inline("Не работает", b"use_not_working")]
            ]
            await event.respond("Выберите действие:", buttons=buttons)
            return

    await event.respond("Нет доступных аккаунтов для использования.")


@client.on(events.CallbackQuery(data=b"use_used"))
async def use_used(event):
    global current_account, current_account_index
    if current_account and current_account_index is not None:
        with open(accs_like_file_path, 'r') as file:
            lines = file.readlines()

        if lines:
            parts = current_account.split(':')
            tg_user_name = event.sender.username if event.sender.username else "tg_user_name"
            lines[current_account_index] = f"{parts[0]}:{parts[1]}:used:{tg_user_name}\n"

            with open(accs_like_file_path, 'w') as file:
                file.writelines(lines)

        await event.respond("Аккаунт обновлен как использованный.")
        current_account = None
        current_account_index = None
        # Возвращаем пользователя к начальному меню
        await start(event)
    else:
        await event.respond("Ошибка: нет текущего аккаунта.")


@client.on(events.CallbackQuery(data=b"use_skipped"))
async def use_skipped(event):
    global current_account, current_account_index
    await event.respond("Вы пропустили аккаунт.")
    current_account = None
    current_account_index = None
    # Возвращаем пользователя к начальному меню
    await start(event)


@client.on(events.CallbackQuery(data=b"use_not_working"))
async def use_not_working(event):
    global current_account, current_account_index
    if current_account and current_account_index is not None:
        with open(accs_like_file_path, 'r') as file:
            lines = file.readlines()

        if lines:
            parts = current_account.split(':')
            tg_user_name = event.sender.username if event.sender.username else "tg_user_name"
            lines[current_account_index] = f"{parts[0]}:{parts[1]}:not_working:{tg_user_name}\n"

            with open(accs_like_file_path, 'w') as file:
                file.writelines(lines)

        await event.respond("Аккаунт обновлен как не работающий. Ищем следующий...")
        current_account = None
        current_account_index = None
        # Ищем следующий аккаунт
        await handle_use(event)
    else:
        await event.respond("Ошибка: нет текущего аккаунта.")

# Запуск клиента
print("Бот запущен...")
client.run_until_disconnected()
