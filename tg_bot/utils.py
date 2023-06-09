"""
В данном модуле написаны инструменты, которыми пользуется Telegram бот.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from FunPayAPI.account import Account

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton as Button
import configparser
import datetime
import os.path
import json
import time

import Utils.cardinal_tools


class NotificationTypes:
    """
    Класс с типами Telegram уведомлений.
    """
    bot_start = "init"
    new_message = "newmsg"
    command = "command"
    new_order = "neworder"
    lots_restore = "lots_restore"
    lots_deactivate = "lots_deactivate"
    delivery = "delivery"
    lots_raise = "raise"
    other = "other"


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


def load_notifications_settings() -> dict:
    """
    Загружает настройки Telegram уведомлений из кэша.

    :return: настройки Telegram уведомлений.
    """
    if not os.path.exists("storage/cache/notifications_settings.json"):
        return {}
    with open("storage/cache/notifications_settings.json", "r", encoding="utf-8") as f:
        return json.loads(f.read())


def load_answer_templates() -> list[str]:
    """
    Загружает шаблоны ответов из кэша.

    :return: шаблоны ответов из кэша.
    """
    if not os.path.exists("storage/cache/answer_templates.json"):
        return []
    with open("storage/cache/answer_templates.json", "r", encoding="utf-8") as f:
        return json.loads(f.read())


def save_authorized_users(users: list[int]) -> None:
    """
    Сохраняет ID авторизированных пользователей.

    :param users: список id авторизированных пользователей.
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")
    with open("storage/cache/tg_authorized_users.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(users))


def save_notifications_settings(settings: dict) -> None:
    """
    Сохраняет настройки Telegram-уведомлений.

    :param settings: настройки Telegram-уведомлений.
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache/")
    with open("storage/cache/notifications_settings.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(settings))


def save_answer_templates(templates: list[str]) -> None:
    """
    Сохраняет шаблоны ответов.

    :param templates: список шаблонов.
    """
    if not os.path.exists("storage/cache/"):
        os.makedirs("storage/cache")
    with open("storage/cache/answer_templates.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(templates))


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


def add_navigation_buttons(keyboard_obj: InlineKeyboardMarkup, curr_offset: int,
                           max_buttons_amount: int,
                           curr_elements_amount: int, elements_amount: int,
                           callback_text: str,
                           extra: list | None = None) -> InlineKeyboardMarkup:
    """
    Добавляет к переданной клавиатуре кнопки след. / пред. страница.

    :param keyboard_obj: экземпляр клавиатуры.

    :param curr_offset: текущее смещение списка.

    :param max_buttons_amount: максимальное кол-во кнопок на 1 странице.

    :param curr_elements_amount: текущее кол-во элементов на странице.

    :param elements_amount: общее кол-во элементов.

    :param callback_text: текст callback'а.

    :param extra: доп. данные (будут перечислены через ":")
    """
    extra = ":" + ":".join(str(i) for i in extra) if extra else ""
    navigation_buttons = []
    if curr_offset > 0:
        back_offset = curr_offset - max_buttons_amount if curr_offset > max_buttons_amount else 0
        back_button = Button("◀️ Пред. страница", callback_data=f"{callback_text}:{back_offset}{extra}")
        navigation_buttons.append(back_button)
    if curr_offset + curr_elements_amount < elements_amount:
        forward_offset = curr_offset + curr_elements_amount
        forward_button = Button("След. страница ▶️", callback_data=f"{callback_text}:{forward_offset}{extra}")
        navigation_buttons.append(forward_button)

    keyboard_obj.row(*navigation_buttons)
    return keyboard_obj


def generate_profile_text(account: Account) -> str:
    return f"""Статистика аккаунта <b><i>{account.username}</i></b>

<b>ID:</b> <code>{account.id}</code>
<b>Баланс:</b> <code>{account.balance} {account.currency}</code>
<b>Незавершенных заказов:</b> <code>{account.active_orders}</code>

<i>Обновлено:</i>  <code>{time.strftime('%H:%M:%S', time.localtime(account.last_update))}</code>"""


def generate_lot_info_text(lot_obj: configparser.SectionProxy) -> str:
    """
    Генерирует текст с информацией о лоте.

    :param lot_obj: секция лота в конфиге автовыдачи.

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

    message = f"""<b>[{escape(lot_obj.name)}]</b>\n
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
