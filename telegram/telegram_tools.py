"""
В данном модуле написаны инструменты, которыми пользуется Telegram бот.
"""
import configparser
import json
import os.path


ABOUT_TEXT = """FunPay Cardinal - это продвинутый бот для автоматизации рутинных действий.
Разработчик:
    TG: @woopertail
    VK: https://vk.com/woopertail
    GitHub: https://github.com/woopertail

Скачать бота:
https://github.com/woopertail/FunPayCardinal"""


def load_authorized_users() -> list[int]:
    """
    Загружает авторизированных пользователей из кэша.

    :return: список из id авторизированных пользователей.
    """
    if not os.path.exists("storage/cache/tg_authorized_users.json"):
        return []
    with open("storage/cache/tg_authorized_users.json", "r", encoding="utf-8") as f:
        data = f.read()
    return json.loads(data)


def load_chat_ids() -> list[int]:
    """
    Загружает список чатов для уведомлений из кэша.

    :return: список из id чатов для уведомлений.
    """
    if not os.path.exists("storage/cache/tg_chat_ids.json"):
        return []
    with open("storage/cache/tg_chat_ids.json", "r", encoding="utf-8") as f:
        data = f.read()
    return json.loads(data)


def save_authorized_users(users: list[int]) -> None:
    """
    Сохраняет id авторизированных пользователей в кэш.

    :param users: список id авторизированных пользователей.
    :return:
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")

    with open("storage/cache/tg_authorized_users.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(users))


def save_chat_ids(chat_ids: list[int]) -> None:
    """
    Сохраняет id чатов для уведомлений в кэш.

    :param chat_ids: список id чатов для уведомлений.
    :return:
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")

    with open("storage/cache/tg_chat_ids.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(chat_ids))


def format_text(text: str) -> str:
    """
    Форматирует текст под HTML.

    :param text: текст.
    :return: форматированный текст.
    """
    escape_characters = {
        "<": "&lt;",
        ">": "&gt;",
        "&": "&amp;"
    }
    for char in escape_characters:
        text = text.replace(char, escape_characters[char])
    return text


def get_on_off_text(value: bool | int | str | None, on: str = "🟢", off: str = "🔴"):
    if value is not None and int(value):
        return on
    return off


def generate_help_text(commands_json: dict) -> str:
    """
    Генерирует текст справки.

    :return: текст справки.
    """
    text = ""
    for module in commands_json:
        if not len(commands_json[module]):
            continue

        text += f"\n{module}\n"
        for command in commands_json[module]:
            text += f"    /{command} - {commands_json[module][command]}\n"
    return text.strip()


def generate_lot_info_text(lot_name: str, lot_obj: configparser.SectionProxy) -> str:
    if lot_obj.get("productsFileName") is None:
        file_path = "<b><u>не привязан.</u></b>"
    else:
        file_path = f"<code>storage/products/{lot_obj.get('productsFileName')}</code>"

    message = f"""<b>[{format_text(lot_name)}]</b>

<b><i>Ответ:</i></b> <code>{format_text(lot_obj["response"])}</code>

<b><i>Файл с товарами: </i></b>{file_path}

<b><i>Авто-выдача отключена: </i></b> {"<b><u>Нет.</u></b>" if lot_obj.get("disable") in [None, "0"]
                                       else "<b><u>Да.</u></b>"}

<b><i>Авто-восстановление отключено: </i></b> {"<b><u>Нет.</u></b>" if lot_obj.get("disableAutoRestore") in [None, "0"]
                                               else "<b><u>Да.</u></b>"}

<b><i>Авто-деактивация отключена: </i></b> {"<b><u>Нет.</u></b>" if lot_obj.get("disableAutoDisable") in [None, "0"]
                                            else "<b><u>Да.</u></b>"}"""
    return message
