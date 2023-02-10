"""
В данном модуле написаны инструменты, которыми пользуется Telegram бот.
"""

import configparser
import datetime
import os.path
import json

import Utils.cardinal_tools

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
    Сохраняет ID авторизированных пользователей в кэш.

    :param users: список id авторизированных пользователей.
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")

    with open("storage/cache/tg_authorized_users.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(users))


def save_chat_ids(chat_ids: list[int]) -> None:
    """
    Сохраняет id чатов для уведомлений в кэш.

    :param chat_ids: список id чатов для уведомлений.
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")

    with open("storage/cache/tg_chat_ids.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(chat_ids))


def escape(text: str) -> str:
    """
    Форматирует текст под HTML разметку.

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


def bool_to_text(value: bool | int | str | None, on: str = "🟢", off: str = "🔴"):
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


def get_offset(element_index: int, max_elements_on_page: int) -> int:
    """
    Возвращает смещение списка элементов таким образом, чтобы элемент с индексом element_index оказался в конце списка.
    """
    elements_amount = element_index + 1
    elements_on_page = elements_amount % max_elements_on_page
    elements_on_page = elements_on_page if elements_on_page else max_elements_on_page
    if not elements_amount - elements_on_page:  # если это первая группа команд:
        return 0
    else:
        return element_index - elements_on_page + 1


def generate_lot_info_text(lot_name: str, lot_obj: configparser.SectionProxy) -> str:
    """
    Генерирует текст с информацией о лоте.

    :param lot_name: название лота.

    :param lot_obj: секция лота в конфиге авто-выдачи.

    :return: сгенерированный текст с информацией о лоте.
    """
    if lot_obj.get("productsFileName") is None:
        file_path = "<b><u>не привязан.</u></b>"
        products_amount = "<code>∞</code>"
    else:
        file_path = f"<code>storage/products/{lot_obj.get('productsFileName')}</code>"
        if not os.path.exists(f"storage/products/{lot_obj.get('productsFileName')}"):
            with open(f"storage/products/{lot_obj.get('productsFileName')}", "w", encoding="utf-8"):
                pass
        products_amount = Utils.cardinal_tools.count_products(f"storage/products/{lot_obj.get('productsFileName')}")
        products_amount = f"<code>{products_amount}</code>"

    message = f"""<b>[{escape(lot_name)}]</b>\n
<b><i>Текст выдачи:</i></b> <code>{escape(lot_obj["response"])}</code>\n
<b><i>Кол-во товаров: </i></b> {products_amount}\n
<b><i>Файл с товарами: </i></b>{file_path}\n
<b><i>Выдача принуд. отключена: </i></b> {bool_to_text(lot_obj.get("disable"), "<b><u>Да.</u></b>", "<b><u>Нет.</u></b>")}

<b><i>Мульти-выдача принуд. отключена: </i></b> {bool_to_text(lot_obj.get("disableMultiDelivery"), "<b><u>Да.</u></b>", "<b><u>Нет.</u></b>")}

<b><i>Восстановление принуд. отключено: </i></b> {bool_to_text(lot_obj.get("disableAutoRestore"), 
                                                            "<b><u>Да.</u></b>", "<b><u>Нет.</u></b>")}\n
<b><i>Деактивация принуд. отключена: </i></b> {bool_to_text(lot_obj.get("disableAutoDisable"), 
                                                            "<b><u>Да.</u></b>", "<b><u>Нет.</u></b>")}\n
<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
    return message
