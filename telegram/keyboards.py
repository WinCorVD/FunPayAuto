"""
Функции генерации клавиатур для суб-панелей управления.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from telebot.types import InlineKeyboardButton as Button
from telebot import types

from telegram import telegram_tools as tg_tools

import logging
import random
import os


logger = logging.getLogger("TGBot")

CLEAR_STATE_BTN = types.InlineKeyboardMarkup().add(Button("❌ Отмена", callback_data="clear_state"))


def power_off(instance_id: int, state: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру выключения бота.

    :param instance_id: ID запуска бота.
    :param state: текущей этап клавиатуры.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    if state == 0:
        keyboard.row(Button("✅ Да", callback_data=f"power_off:1:{instance_id}"),
                     Button("❌ Нет", callback_data="cancel_power_off"))
    elif state == 1:
        keyboard.row(Button("❌ Нет", callback_data="cancel_power_off"),
                     Button("✅ Да", callback_data=f"power_off:2:{instance_id}"))
    elif state == 2:
        max_buttons = 10
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("✅ Да", callback_data=f"power_off:3:{instance_id}")
        no_button = Button("❌ Нет", callback_data="cancel_power_off")
        buttons = [*[no_button]*(yes_button_num-1), yes_button, *[no_button]*(max_buttons-yes_button_num)]
        keyboard.add(*buttons, row_width=2)
    elif state == 3:
        max_buttons = 30
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("✅ Да", callback_data=f"power_off:4:{instance_id}")
        no_button = Button("❌ Нет", callback_data="cancel_power_off")
        buttons = [*[no_button] * (yes_button_num - 1), yes_button, *[no_button] * (max_buttons - yes_button_num)]
        keyboard.add(*buttons, row_width=5)
    elif state == 4:
        max_buttons = 40
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("❌ Нет", callback_data=f"power_off:5:{instance_id}")
        no_button = Button("✅ Да", callback_data="cancel_power_off")
        buttons = [*[yes_button] * (yes_button_num - 1), no_button, *[yes_button] * (max_buttons - yes_button_num)]
        keyboard.add(*buttons, row_width=7)
    elif state == 5:
        keyboard.add(Button("✅ Дэ", callback_data=f"power_off:6:{instance_id}"))
    return keyboard


def main_menu() -> types.ReplyKeyboardMarkup:
    """
    Создает клавиатуру основного меню (команда /menu).

    :return: экземпляр клавиатуры.
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)\
        .row("🤖 О боте 🤖", "📟 Команды 📟")\
        .row("⚙️ Настройки ⚙️", "📋 Логи 📋")\
        .row("📈 Система 📈")\
        .row("🔄 Перезапуск 🔄", "🔌 Отключение 🔌")
    return keyboard


def settings_sections() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру разделов настроек (сообщение: "⚙️ Настройки ⚙️", callback: "main_settings_page").

    :return: экземпляр основной клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("⚙️ Основные настройки", callback_data="settings:main"))\
        .add(Button("🔔 Настройки уведомлений", callback_data="settings:telegram"))\
        .add(Button("🤖 Настройки авто-ответчика", callback_data="settings:autoResponse"))\
        .add(Button("📦 Настройки авто-выдачи", callback_data="settings:autoDelivery"))\
        .add(Button("🚫 Настройки черного списка",  callback_data="settings:blockList"))\
        .add(Button("📁 Управление конфиг-файлами", callback_data="config_loader"))
    return keyboard


def main_settings(cardinal: Cardinal) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру основных переключателей (settings:main).

    :param cardinal: экземпляр кардинала.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .row(Button(f"Авто-поднятие {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoRaise']) else '🔴'}",
                    callback_data="switch:FunPay:autoRaise"),
             Button(f"Авто-ответчик {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoResponse']) else '🔴'}",
                    callback_data="switch:FunPay:autoResponse"))\
        .row(Button(f"Авто-выдача {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoDelivery']) else '🔴'}",
                    callback_data="switch:FunPay:autoDelivery"),
             Button(f"Активация лотов {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoRestore']) else '🔴'}",
                    callback_data="switch:FunPay:autoRestore"))\
        .add(Button(f"Деактивация лотов {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoDisable']) else '🔴'}",
                    callback_data="switch:FunPay:autoDisable"))\
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard


def notifications_settings(cardinal: Cardinal) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек уведомлений (settings:telegram).

    :param cardinal: экземпляр кардинала.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button(f"Уведомления о поднятии лотов "
                    f"{'🔔' if int(cardinal.MAIN_CFG['Telegram']['lotsRaiseNotification']) else '🔕'}",
                    callback_data="switch:Telegram:lotsRaiseNotification"))\
        .add(Button(f"Уведомления о новых сообщениях "
                    f"{'🔔' if int(cardinal.MAIN_CFG['Telegram']['newMessageNotification']) else '🔕'}",
                    callback_data="switch:Telegram:newMessageNotification"))\
        .add(Button(f"Уведомления о новых заказах "
                    f"{'🔔' if int(cardinal.MAIN_CFG['Telegram']['newOrderNotification']) else '🔕'}",
                    callback_data="switch:Telegram:newOrderNotification"))\
        .add(Button(f"Уведомления о выдаче товара "
                    f"{'🔔' if int(cardinal.MAIN_CFG['Telegram']['productsDeliveryNotification']) else '🔕'}",
                    callback_data="switch:Telegram:productsDeliveryNotification"))\
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard


def ar_settings() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек авто-ответчика (settings:autoResponse).

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("✏️ Редактировать существующие команды", callback_data="command_list:0"))\
        .add(Button("➕ Добавить команду / сет команд", callback_data="add_command"))\
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard


def ad_settings() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек авто-выдачи (settings:autoDelivery).

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup() \
        .add(Button("✏️ Редактировать существующие лоты", callback_data="lots:0")) \
        .add(Button("➕ Добавить лот", callback_data="add_lot"))\
        .add(Button("✏️ Редактировать существующие файлы с товарами", callback_data="products_files:0"))\
        .add(Button("⤴️ Выгрузить файл с товарами", callback_data="upload_products_file"))\
        .add(Button("➕ Создать файл с товарами", callback_data="create_products_file"))\
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard


def block_list_settings(cardinal: Cardinal) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек черного списка (settings:blockList).

    :param cardinal: экземпляр кардинала.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button(f"Блокировать авто-выдачу "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockDelivery']) else '🔴'}",
                    callback_data="switch:BlockList:blockDelivery"))\
        .add(Button(f"Блокировать авто-ответ "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockResponse']) else '🔴'}",
                    callback_data="switch:BlockList:blockResponse"))\
        .add(Button(f"Не уведомлять о новых сообщениях "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockNewMessageNotification']) else '🔴'}",
                    callback_data="switch:BlockList:blockNewMessageNotification"))\
        .add(Button(f"Не уведомлять о новых заказах "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockNewOrderNotification']) else '🔴'}",
                    callback_data="switch:BlockList:blockNewOrderNotification"))\
        .add(Button(f"Не уведомлять о введенных командах "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockCommandNotification']) else '🔴'}",
                    callback_data="switch:BlockList:blockCommandNotification"))\
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard


def commands_list(cardinal: Cardinal, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком команд (command_list:<offset>).

    :param cardinal: экземпляр кардинала.
    :param offset: оффсет списка команд.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    commands = cardinal.RAW_AR_CFG.sections()[offset: offset + 5]
    if not commands and offset != 0:
        offset = 0
        commands = cardinal.RAW_AR_CFG.sections()[offset: offset + 5]

    btn_number = 0
    for i in commands:
        #  edit_command:номер команды:оффсет (для кнопки назад)
        keyboard.add(Button(i, callback_data=f"edit_command:{offset + btn_number}:{offset}"))
        btn_number += 1

    navigation_buttons = []
    if offset > 0:
        back_offset = offset-5 if offset > 5 else 0
        back_button = Button("◀️ Пред. страница", callback_data=f"command_list:{back_offset}")
        navigation_buttons.append(back_button)
    if offset + len(commands) < len(cardinal.RAW_AR_CFG.sections()):
        forward_offset = offset + len(commands)
        forward_button = Button("След. страница ▶️", callback_data=f"command_list:{forward_offset}")
        navigation_buttons.append(forward_button)

    keyboard.add(Button("🤖 В настройки авто-ответчика", callback_data="settings:autoResponse"))\
        .add(Button("📋 В главное меню", callback_data="main_settings_page"))\
        .row(*navigation_buttons)
    return keyboard


def edit_command(cardinal: Cardinal, command_number: int, offset: int) -> types.InlineKeyboardMarkup | None:
    """
    Создает клавиатуру изменения параметров команды (edit_command:<command_num>:<offset>).

    :param cardinal: экземпляр кардинала.
    :param command_number: номер команды.
    :param offset: оффсет списка команд.
    :return: экземпляр клавиатуры.
    """
    if command_number > len(cardinal.RAW_AR_CFG.sections())-1:
        return None

    command = cardinal.RAW_AR_CFG.sections()[command_number]
    command_obj = cardinal.RAW_AR_CFG[command]
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button(f"✏️ Редактировать ответ", callback_data=f"edit_commands_response:{command_number}"))\
        .add(Button(f"✏️ Редактировать уведомление", callback_data=f"edit_commands_notification:{command_number}"))\
        .add(Button(f"Уведомление в Telegram "
                    f"{tg_tools.get_on_off_text(command_obj.get('telegramNotification'), on='🔔', off='🔕')}",
                    callback_data=f"switch_telegram_notification:{command_number}:{offset}"))\
        .add(Button("🗑️ Удалить команду / сет команд", callback_data=f"del_command:{command_number}:{offset}"))\
        .add(Button("🔄 Обновить", callback_data=f"edit_command:{command_number}:{offset}"))\
        .add(Button("◀️ Назад", callback_data=f"command_list:{offset}"))
    return keyboard


def products_file_list(offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком файлов с товарами (products_files:<offset>).

    :param offset: оффсет списка файлов.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    files = os.listdir("storage/products")[offset:offset + 5]
    if not files and offset != 0:
        offset = 0
        files = os.listdir("storage/products")[offset:offset + 5]

    for i in files:
        keyboard.add(Button(i, callback_data=f"products_file:{i}:{offset}"))

    navigation_buttons = []
    if offset > 0:
        back_offset = offset-5 if offset > 5 else 0
        back_button = Button("◀️ Пред. страница", callback_data=f"products_files:{back_offset}")
        navigation_buttons.append(back_button)
    if offset + len(files) < len(os.listdir("storage/products")):
        forward_offset = offset + len(files)
        forward_button = Button("След. страница ▶️", callback_data=f"products_files:{forward_offset}")
        navigation_buttons.append(forward_button)

    keyboard.add(Button("📦 В настройки авто-выдачи", callback_data="settings:autoDelivery"))\
        .add(Button("📋 В главное меню", callback_data="main_settings_page"))\
        .row(*navigation_buttons)
    return keyboard


def products_file_edit(file_name: str, offset: int, confirmation: bool = False) \
        -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру изменения файла с товарами (products_file:<file_name>:<offset>).

    :param file_name: название файла с товарами.
    :param offset: оффсет списка файлов с товарами.
    :param confirmation: включить ли в клавиатуру подтверждение удаления файла.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("➕ Добавить товары в файл с товарами.", callback_data=f"add_products_to_file:{file_name}"))\
        .add(Button("⤵️ Скачать файл с товарами.", callback_data=f"download_products_file:{file_name}"))
    if not confirmation:
        keyboard.add(Button("🗑️ Удалить файл с товарами", callback_data=f"del_products_file:{file_name}:{offset}"))
    else:
        keyboard.row(Button("✅ Да", callback_data=f"confirm_del_products_file:{file_name}:{offset}"),
                     Button("❌ Нет", callback_data=f"products_file:{file_name}:{offset}"))
    keyboard.add(Button("🔄 Обновить", callback_data=f"products_file:{file_name}:{offset}"))\
            .add(Button("◀️ Назад", callback_data=f"products_files:{offset}"))
    return keyboard


def lots_list(cardinal: Cardinal, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком лотов (lots:<offset>).

    :param cardinal: экземпляр кардинала.
    :param offset: оффсет списка лотов.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    lots = cardinal.AD_CFG.sections()[offset: offset + 5]
    if not lots and offset != 0:
        offset = 0
        lots = cardinal.AD_CFG.sections()[offset: offset + 5]

    btn_number = 0
    for i in lots:
        keyboard.add(Button(i, callback_data=f"edit_lot:{offset + btn_number}:{offset}"))
        btn_number += 1

    navigation_buttons = []
    if offset > 0:
        back_offset = offset - 5 if offset > 5 else 0
        back_button = Button("◀️ Пред. страница", callback_data=f"lots:{back_offset}")
        navigation_buttons.append(back_button)
    if offset + len(lots) < len(cardinal.AD_CFG.sections()):
        forward_offset = offset + len(lots)
        forward_button = Button("След. страница ▶️", callback_data=f"lots:{forward_offset}")
        navigation_buttons.append(forward_button)

    keyboard.add(Button("📦 В настройки авто-выдачи", callback_data="settings:autoDelivery")) \
        .add(Button("📋 В главное меню", callback_data="main_settings_page")) \
        .row(*navigation_buttons)
    return keyboard


def edit_lot(cardinal: Cardinal, lot_number: int, offset: int) -> types.InlineKeyboardMarkup | None:
    """
    Создает клавиатуру изменения лота (edit_lot:<lot_num>:<offset>).

    :param cardinal: экземпляр кардинала.
    :param lot_number: номер лота.
    :param offset: оффсет списка слотов.
    :return: экземпляр клавиатуры.
    """
    if lot_number > len(cardinal.AD_CFG.sections()) - 1:
        return None

    lot = cardinal.AD_CFG.sections()[lot_number]
    lot_obj = cardinal.AD_CFG[lot]
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("✏️ Редактировать текст выдачи", callback_data=f"edit_lot_response:{lot_number}"))\
        .add(Button("⛓️ Привязать файл с товарами", callback_data=f"link_products_file:{lot_number}"))\
        .add(Button("Выключить авто-выдачу" if lot_obj.get("disable") in [None, "0"] else "Включить авто-выдачу",
                    callback_data=f"switch_lot:disable:{lot_number}:{offset}"))\
        .add(Button("Выключить авто-восстановление" if lot_obj.get("disableAutoRestore") in [None, "0"] else
                    "Включить авто-восстановление",
                    callback_data=f"switch_lot:disableAutoRestore:{lot_number}:{offset}"))\
        .add(Button("Выключить авто-деактивацию" if lot_obj.get("disableAutoDisable") in [None, "0"] else
                    "Включить авто-деактивацию",
                    callback_data=f"switch_lot:disableAutoDisable:{lot_number}:{offset}"))\
        .add(Button("🗑️ Удалить лот", callback_data=f"del_lot:{lot_number}:{offset}"))\
        .add(Button("🔄 Обновить", callback_data=f"edit_lot:{lot_number}:{offset}"))\
        .add(Button("◀️ Назад", callback_data=f"lots:{offset}"))
    return keyboard


def configs() -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру загрузки / выгрузки конфигов.
    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup() \
        .add(Button("⤵️ Загрузить основной конфиг", callback_data="download_config:main")) \
        .add(Button("⤵️ Загрузить конфиг авто-ответа", callback_data="download_config:auto_response")) \
        .add(Button("⤵️ Загрузить конфиг авто-выдачи", callback_data="download_config:auto_delivery")) \
        .add(Button("⤴️ Выгрузить основной конфиг", callback_data="upload_main_config")) \
        .add(Button("⤴️ Выгрузить конфиг авто-ответа", callback_data="upload_auto_response_config")) \
        .add(Button("⤴️ Выгрузить конфиг авто-выдачи", callback_data="upload_auto_delivery_config")) \
        .add(Button("◀️ Назад", callback_data="main_settings_page"))
    return keyboard

