"""
Функции генерации клавиатур для суб-панелей управления.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from telebot.types import InlineKeyboardButton as Button
from telebot import types

from tg_bot import utils, CBT, MENU_CFG

import logging
import random
import os


logger = logging.getLogger("TGBot")

CLEAR_STATE_BTN = types.InlineKeyboardMarkup().add(Button("❌ Отмена", callback_data=CBT.CLEAR_USER_STATE))

UPDATE_PROFILE_BTN = types.InlineKeyboardMarkup().add(Button("🔄 Обновить", callback_data=CBT.UPDATE_PROFILE))


def power_off(instance_id: int, state: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру выключения бота.

    :param instance_id: ID запуска бота.

    :param state: текущей этап клавиатуры.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    if state == 0:
        keyboard.row(Button("✅ Да", callback_data=f"{CBT.SHUT_DOWN}:1:{instance_id}"),
                     Button("❌ Нет", callback_data=CBT.CANCEL_SHUTTING_DOWN))
    elif state == 1:
        keyboard.row(Button("❌ Нет", callback_data=CBT.CANCEL_SHUTTING_DOWN),
                     Button("✅ Да", callback_data=f"{CBT.SHUT_DOWN}:2:{instance_id}"))
    elif state == 2:
        max_buttons = 10
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("✅ Да", callback_data=f"{CBT.SHUT_DOWN}:3:{instance_id}")
        no_button = Button("❌ Нет", callback_data=CBT.CANCEL_SHUTTING_DOWN)
        buttons = [*[no_button]*(yes_button_num-1), yes_button, *[no_button]*(max_buttons-yes_button_num)]
        keyboard.add(*buttons, row_width=2)
    elif state == 3:
        max_buttons = 30
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("✅ Да", callback_data=f"{CBT.SHUT_DOWN}:4:{instance_id}")
        no_button = Button("❌ Нет", callback_data=CBT.CANCEL_SHUTTING_DOWN)
        buttons = [*[no_button] * (yes_button_num - 1), yes_button, *[no_button] * (max_buttons - yes_button_num)]
        keyboard.add(*buttons, row_width=5)
    elif state == 4:
        max_buttons = 40
        yes_button_num = random.randint(1, max_buttons)
        yes_button = Button("❌ Нет", callback_data=f"{CBT.SHUT_DOWN}:5:{instance_id}")
        no_button = Button("✅ Да", callback_data=CBT.CANCEL_SHUTTING_DOWN)
        buttons = [*[yes_button] * (yes_button_num - 1), no_button, *[yes_button] * (max_buttons - yes_button_num)]
        keyboard.add(*buttons, row_width=7)
    elif state == 5:
        keyboard.add(Button("✅ Дэ", callback_data=f"{CBT.SHUT_DOWN}:6:{instance_id}"))
    return keyboard


def settings_sections() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру разделов настроек (CBT.MAIN).

    :return: экземпляр основной клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("⚙️ Основные настройки", callback_data=f"{CBT.CATEGORY}:main"))\
        .add(Button("🔔 Настройки уведомлений", callback_data=f"{CBT.CATEGORY}:telegram"))\
        .add(Button("🤖 Настройки автоответчика", callback_data=f"{CBT.CATEGORY}:autoResponse"))\
        .add(Button("📦 Настройки автовыдачи", callback_data=f"{CBT.CATEGORY}:autoDelivery"))\
        .add(Button("🚫 Настройки черного списка",  callback_data=f"{CBT.CATEGORY}:blockList"))\
        .add(Button("📝 Заготовки ответов", callback_data=f"{CBT.TMPLT_LIST}:0"))\
        .add(Button("🧩 Управление плагинами", callback_data=f"{CBT.PLUGINS_LIST}:0"))\
        .add(Button("📁 Управление конфиг-файлами", callback_data="config_loader"))
    return keyboard


def main_settings(cardinal: Cardinal) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру основных переключателей (CBT.CATEGORY:main).

    :param cardinal: экземпляр кардинала.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .row(Button(f"Автоподнятие {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoRaise']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:FunPay:autoRaise"),
             Button(f"Автоответчик {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoResponse']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:FunPay:autoResponse"))\
        .row(Button(f"Автовыдача {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoDelivery']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:FunPay:autoDelivery"),
             Button(f"Мульти-выдача {utils.bool_to_text(cardinal.MAIN_CFG['FunPay'].getboolean('multiDelivery'))}",
                    callback_data=f"{CBT.SWITCH}:FunPay:multiDelivery"))\
        .row(Button(f"Активация лотов {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoRestore']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:FunPay:autoRestore"),
             Button(f"Деактивация лотов {'🟢' if int(cardinal.MAIN_CFG['FunPay']['autoDisable']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:FunPay:autoDisable"))\
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


def notifications_settings(cardinal: Cardinal, chat_id: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек уведомлений (CBT.CATEGORY:telegram).

    :param cardinal: экземпляр кардинала.

    :param chat_id: ID чата, в котором вызвана данная клавиатура.

    :return: экземпляр клавиатуры.
    """
    tg = cardinal.telegram
    keyboard = types.InlineKeyboardMarkup()\
        .row(Button(f"Новое сообщение "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.new_message) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.new_message}"),
             Button(f"Введена команда "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.command) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.command}"))\
        .row(Button(f"Новый заказ "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.new_order) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.new_order}"),
             Button(f"Выдача товара "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.delivery) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.delivery}"))\
        .row(Button(f"Активация лота "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.lots_restore) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.lots_restore}"),
             Button("Деактивация лота "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.lots_deactivate) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.lots_deactivate}"))\
        .add(Button(f"Поднятие лотов "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.lots_raise) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.lots_raise}"))\
        .add(Button(f"Запуск бота "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.bot_start) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.bot_start}"))\
        .add(Button(f"Прочее (плагины) "
                    f"{'🔔' if tg.is_notification_enabled(chat_id, utils.NotificationTypes.other) else '🔕'}",
                    callback_data=f"{CBT.SWITCH_TG_NOTIFICATIONS}:{chat_id}:{utils.NotificationTypes.other}")) \
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


def ar_settings() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек автоответчика (CBT.CATEGORY:autoResponse).

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("✏️ Редактировать существующие команды", callback_data=f"{CBT.CMD_LIST}:0"))\
        .add(Button("➕ Добавить команду / сет команд", callback_data=CBT.ADD_CMD))\
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


def ad_settings() -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек автовыдачи (CBT.CATEGORY:autoDelivery).

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup() \
        .add(Button("🗳️ Редактировать автовыдачу лотов", callback_data=f"{CBT.AD_LOTS_LIST}:0")) \
        .add(Button("➕ Добавить автовыдачу лоту", callback_data=f"{CBT.FP_LOTS_LIST}:0"))\
        .add(Button("📋 Редактировать товарные файлы", callback_data=f"{CBT.PRODUCTS_FILES_LIST}:0"))\
        .row(Button("⤴️ Выгрузить товарный файл", callback_data=CBT.UPLOAD_PRODUCTS_FILE),
             Button("➕ Новый товарный файл", callback_data=CBT.CREATE_PRODUCTS_FILE))\
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


def block_list_settings(cardinal: Cardinal) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек черного списка (CBT.CATEGORY:blockList).

    :param cardinal: экземпляр кардинала.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button(f"Блокировать автовыдачу "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockDelivery']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:BlockList:blockDelivery"))\
        .add(Button(f"Блокировать автоответ "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockResponse']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:BlockList:blockResponse"))\
        .add(Button(f"Не уведомлять о новых сообщениях "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockNewMessageNotification']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:BlockList:blockNewMessageNotification"))\
        .add(Button(f"Не уведомлять о новых заказах "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockNewOrderNotification']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:BlockList:blockNewOrderNotification"))\
        .add(Button(f"Не уведомлять о введенных командах "
                    f"{'🟢' if int(cardinal.MAIN_CFG['BlockList']['blockCommandNotification']) else '🔴'}",
                    callback_data=f"{CBT.SWITCH}:BlockList:blockCommandNotification"))\
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


def commands_list(cardinal: Cardinal, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком команд (CBT.CMD_LIST:<offset>).

    :param cardinal: экземпляр кардинала.

    :param offset: смещение списка команд.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    commands = cardinal.RAW_AR_CFG.sections()[offset: offset + MENU_CFG.AR_BTNS_AMOUNT]
    if not commands and offset != 0:
        offset = 0
        commands = cardinal.RAW_AR_CFG.sections()[offset: offset + MENU_CFG.AR_BTNS_AMOUNT]

    for index, cmd in enumerate(commands):
        #  CBT.EDIT_CMD:номер команды:смещение (для кнопки назад)
        keyboard.add(Button(cmd, callback_data=f"{CBT.EDIT_CMD}:{offset + index}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.AR_BTNS_AMOUNT, len(commands),
                                            len(cardinal.RAW_AR_CFG.sections()), CBT.CMD_LIST)

    keyboard.add(Button("🤖 В настройки автоответчика", callback_data=f"{CBT.CATEGORY}:autoResponse"))\
        .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def edit_command(cardinal: Cardinal, command_index: int, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру изменения параметров команды (CBT.EDIT_CMD:<command_num>:<offset>).

    :param cardinal: экземпляр кардинала.

    :param command_index: номер команды.

    :param offset: смещение списка команд.

    :return: экземпляр клавиатуры.
    """
    command = cardinal.RAW_AR_CFG.sections()[command_index]
    command_obj = cardinal.RAW_AR_CFG[command]
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button(f"✏️ Редактировать ответ",
                    callback_data=f"{CBT.EDIT_CMD_RESPONSE_TEXT}:{command_index}:{offset}"))\
        .add(Button(f"✏️ Редактировать уведомление",
                    callback_data=f"{CBT.EDIT_CMD_NOTIFICATION_TEXT}:{command_index}:{offset}"))\
        .add(Button(f"Уведомление в Telegram "
                    f"{utils.bool_to_text(command_obj.get('telegramNotification'), on='🔔', off='🔕')}",
                    callback_data=f"{CBT.SWITCH_CMD_NOTIFICATION}:{command_index}:{offset}"))\
        .add(Button("🗑️ Удалить команду / сет команд", callback_data=f"{CBT.DEL_CMD}:{command_index}:{offset}"))\
        .row(Button("◀️ Назад", callback_data=f"{CBT.CMD_LIST}:{offset}"),
             Button("🔄 Обновить", callback_data=f"{CBT.EDIT_CMD}:{command_index}:{offset}"))
    return keyboard


def products_files_list(offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком файлов с товарами (CBT.PRODUCTS_FILES_LIST:<offset>).

    :param offset: смещение списка файлов.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    files = os.listdir("storage/products")[offset:offset + MENU_CFG.PF_BTNS_AMOUNT]
    if not files and offset != 0:
        offset = 0
        files = os.listdir("storage/products")[offset:offset + 5]

    for index, name in enumerate(files):
        keyboard.add(Button(name, callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{offset + index}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.PF_BTNS_AMOUNT, len(files),
                                            len(os.listdir("storage/products")), CBT.PRODUCTS_FILES_LIST)

    keyboard.add(Button("📦 В настройки автовыдачи", callback_data=f"{CBT.CATEGORY}:autoDelivery"))\
        .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def products_file_edit(file_number: int, offset: int, confirmation: bool = False) \
        -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру изменения файла с товарами (CBT.EDIT_PRODUCTS_FILE:<file_index>:<offset>).

    :param file_number: номер файла.

    :param offset: смещение списка файлов с товарами.

    :param confirmation: включить ли в клавиатуру подтверждение удаления файла.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("➕ Добавить товары",
                    callback_data=f"{CBT.ADD_PRODUCTS_TO_FILE}:{file_number}:{file_number}:{offset}:0"))\
        .add(Button("⤵️ Скачать файл с товарами.", callback_data=f"download_products_file:{file_number}:{offset}"))
    if not confirmation:
        keyboard.add(Button("🗑️ Удалить файл с товарами", callback_data=f"del_products_file:{file_number}:{offset}"))
    else:
        keyboard.row(Button("✅ Да", callback_data=f"confirm_del_products_file:{file_number}:{offset}"),
                     Button("❌ Нет", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_number}:{offset}"))
    keyboard.row(Button("◀️ Назад", callback_data=f"{CBT.PRODUCTS_FILES_LIST}:{offset}"),
                 Button("🔄 Обновить", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_number}:{offset}"))
    return keyboard


def lots_list(cardinal: Cardinal, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком лотов (lots:<offset>).

    :param cardinal: экземпляр кардинала.

    :param offset: смещение списка лотов.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    lots = cardinal.AD_CFG.sections()[offset: offset + MENU_CFG.AD_BTNS_AMOUNT]
    if not lots and offset != 0:
        offset = 0
        lots = cardinal.AD_CFG.sections()[offset: offset + MENU_CFG.AD_BTNS_AMOUNT]

    for index, lot in enumerate(lots):
        keyboard.add(Button(lot, callback_data=f"{CBT.EDIT_AD_LOT}:{offset + index}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.AD_BTNS_AMOUNT, len(lots),
                                            len(cardinal.AD_CFG.sections()), CBT.AD_LOTS_LIST)

    keyboard.add(Button("📦 В настройки автовыдачи", callback_data=f"{CBT.CATEGORY}:autoDelivery")) \
        .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def funpay_lots_list(cardinal: Cardinal, offset: int):
    """
    Создает клавиатуру со списком лотов с FunPay (funpay_lots:<offset>).
    """
    keyboard = types.InlineKeyboardMarkup()
    lots = cardinal.telegram_lots[offset: offset + MENU_CFG.FP_LOTS_BTNS_AMOUNT]
    if not lots and offset != 0:
        offset = 0
        lots = cardinal.telegram_lots[offset: offset + MENU_CFG.FP_LOTS_BTNS_AMOUNT]

    for index, lot in enumerate(lots):
        keyboard.add(Button(lot.title, callback_data=f"{CBT.ADD_AD_TO_LOT}:{offset + index}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.FP_LOTS_BTNS_AMOUNT, len(lots),
                                            len(cardinal.telegram_lots), CBT.FP_LOTS_LIST)

    keyboard.row(Button("➕ Ввести вручную", callback_data=f"{CBT.ADD_AD_TO_LOT_MANUALLY}:{offset}"),
                 Button("🔄 Сканировать FunPay", callback_data=f"update_funpay_lots:{offset}"))\
        .add(Button("📦 В настройки автовыдачи", callback_data=f"{CBT.CATEGORY}:autoDelivery"))\
        .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def edit_lot(cardinal: Cardinal, lot_number: int, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру изменения лота (CBT.EDIT_AD_LOT:<lot_num>:<offset>).

    :param cardinal: экземпляр кардинала.

    :param lot_number: номер лота.

    :param offset: смещение списка слотов.

    :return: экземпляр клавиатуры.
    """

    lot = cardinal.AD_CFG.sections()[lot_number]
    lot_obj = cardinal.AD_CFG[lot]
    file_name = lot_obj.get("productsFileName")
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("✏️ Редактировать текст выдачи",
                    callback_data=f"{CBT.EDIT_LOT_DELIVERY_TEXT}:{lot_number}:{offset}"))
    if not file_name:
        keyboard.add(Button("⛓️ Привязать файл с товарами",
                            callback_data=f"{CBT.BIND_PRODUCTS_FILE}:{lot_number}:{offset}"))
    else:
        if file_name not in os.listdir("storage/products"):
            with open(f"storage/products/{file_name}", "w", encoding="utf-8"):
                pass
        file_number = os.listdir("storage/products").index(file_name)

        keyboard.row(Button("⛓️ Привязать файл с товарами",
                            callback_data=f"{CBT.BIND_PRODUCTS_FILE}:{lot_number}:{offset}"),
                     Button("➕ Добавить товары",
                            callback_data=f"{CBT.ADD_PRODUCTS_TO_FILE}:{file_number}:{lot_number}:{offset}:1"))
    keyboard.row(Button(f"Выдача {utils.bool_to_text(lot_obj.get('disable'), '🔴', '🟢')}",
                        callback_data=f"switch_lot:disable:{lot_number}:{offset}"),
                 Button(f"Мульти-выдача {utils.bool_to_text(lot_obj.get('disableMultiDelivery'), '🔴', '🟢')}",
                        callback_data=f"switch_lot:disableMultiDelivery:{lot_number}:{offset}"))\
            .row(Button(f"Восст. {utils.bool_to_text(lot_obj.get('disableAutoRestore'), '🔴', '🟢')}",
                        callback_data=f"switch_lot:disableAutoRestore:{lot_number}:{offset}"),
                 Button(f"Деакт. {utils.bool_to_text(lot_obj.get('disableAutoDisable'), '🔴', '🟢')}",
                        callback_data=f"switch_lot:disableAutoDisable:{lot_number}:{offset}"))\
        .row(Button("👾 Тест автовыдачи", callback_data=f"test_auto_delivery:{lot_number}:{offset}"),
             Button("🗑️ Удалить лот", callback_data=f"{CBT.DEL_AD_LOT}:{lot_number}:{offset}"))\
        .row(Button("◀️ Назад", callback_data=f"{CBT.AD_LOTS_LIST}:{offset}"),
             Button("🔄 Обновить", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_number}:{offset}"))
    return keyboard


def configs() -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру загрузки / выгрузки конфигов.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup() \
        .add(Button("⤵️ Загрузить основной конфиг", callback_data=f"{CBT.DOWNLOAD_CFG}:main")) \
        .add(Button("⤵️ Загрузить конфиг автоответа", callback_data=f"{CBT.DOWNLOAD_CFG}:autoResponse")) \
        .add(Button("⤵️ Загрузить конфиг автовыдачи", callback_data=f"{CBT.DOWNLOAD_CFG}:autoDelivery")) \
        .add(Button("⤴️ Выгрузить основной конфиг", callback_data="upload_main_config")) \
        .add(Button("⤴️ Выгрузить конфиг автоответа", callback_data="upload_auto_response_config")) \
        .add(Button("⤴️ Выгрузить конфиг автовыдачи", callback_data="upload_auto_delivery_config")) \
        .add(Button("◀️ Назад", callback_data=CBT.MAIN))
    return keyboard


# Прочее
def new_order(order_id: str, username: str, node_id: int,
              confirmation: bool = False, no_refund: bool = False) -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для сообщения о новом заказе.

    :param order_id: ID заказа (без #).

    :param username: никнейм покупателя.

    :param node_id: ID чата с покупателем.

    :param confirmation: заменить ли кнопку "Вернуть деньги" на подтверждение "Да" / "Нет"?

    :param no_refund: убрать ли кнопки, связанные с возвратом денег?

    :return: экземпляр кнопки (клавиатуры).
    """
    keyboard = types.InlineKeyboardMarkup()
    if not no_refund:
        if confirmation:
            keyboard.row(Button(text="✅ Да", callback_data=f"{CBT.REFUND_CONFIRMED}:{order_id}:{node_id}:{username}"),
                         Button(text="❌ Нет", callback_data=f"{CBT.REFUND_CANCELLED}:{order_id}:{node_id}:{username}"))
        else:
            keyboard.add(Button(text="💸 Вернуть деньги",
                                callback_data=f"{CBT.REQUEST_REFUND}:{order_id}:{node_id}:{username}"))

    keyboard.add(Button(text="🌐 Открыть страницу заказа", url=f"https://funpay.com/orders/{order_id}/")) \
        .row(Button(text="📨 Ответить", callback_data=f"{CBT.SEND_FP_MESSAGE}:{node_id}:{username}"),
             Button(text="📝 Заготовки", callback_data=f"{CBT.TMPLT_LIST_ANS_MODE}:0:{node_id}:{username}:2:{order_id}:"
                                                      f"{1 if no_refund else 0}"))
    return keyboard


def reply(node_id: int, username: str, again: bool = False) -> types.InlineKeyboardMarkup:
    """
    Генерирует кнопку для отправки сообщения из Telegram в ЛС пользователю FunPay.

    :param node_id: ID переписки, в которую нужно отправить сообщение.

    :param username: никнейм пользователя, с которым ведется переписка.

    :param again: заменить текст "Отправить" на "Отправить еще"?

    :return: экземпляр кнопки (клавиатуры).
    """
    keyboard = types.InlineKeyboardMarkup()\
        .row(Button(text=f"{'📨 Ответить' if not again else '📨 Отправить еще'}",
                    callback_data=f"{CBT.SEND_FP_MESSAGE}:{node_id}:{username}"),
             Button(text="📝 Заготовки", callback_data=f"{CBT.TMPLT_LIST_ANS_MODE}:0:{node_id}:{username}:"
                                                      f"{0 if not again else 1}"))
    return keyboard


def templates_list(cardinal: Cardinal, offset: int) \
        -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком шаблонов ответов. (CBT.TMPLT_LIST:<offset>).

    :param cardinal: экземпляр кардинала.

    :param offset: смещение списка шаблонов.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    templates = cardinal.telegram.answer_templates[offset: offset + MENU_CFG.TMPLT_BTNS_AMOUNT]
    if not templates and offset != 0:
        offset = 0
        templates = cardinal.telegram.answer_templates[offset: offset + MENU_CFG.TMPLT_BTNS_AMOUNT]

    for index, tmplt in enumerate(templates):
        keyboard.add(Button(tmplt, callback_data=f"{CBT.EDIT_TMPLT}:{offset + index}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.TMPLT_BTNS_AMOUNT, len(templates),
                                            len(cardinal.telegram.answer_templates), CBT.TMPLT_LIST)
    keyboard.add(Button("➕ Добавить заготовку", callback_data=f"{CBT.ADD_TMPLT}:{offset}"))\
            .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def edit_template(cardinal: Cardinal, template_index: int, offset: int) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру изменения шаблона ответа (CBT.EDIT_TMPLT:<template_index>:<offset>).

    :param cardinal: экземпляр кардинала.

    :param template_index: числовой индекс шаблона ответа.

    :param offset: смещение списка шаблонов ответа.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()\
        .add(Button("◀️ Назад", callback_data=f"{CBT.TMPLT_LIST}:{offset}"))\
        .add(Button("🗑️ Удалить", callback_data=f"{CBT.DEL_TMPLT}:{template_index}:{offset}"))
    return keyboard


def templates_list_ans_mode(cardinal: Cardinal, offset: int, node_id: int, username: str, prev_page: int,
                            extra: list | None = None):
    """
    Создает клавиатуру со списком шаблонов ответов.
    (CBT.TMPLT_LIST_ANS_MODE:{offset}:{node_id}:{username}:{prev_page}:{extra}).


    :param cardinal: экземпляр кардинала.

    :param offset: смещение списка шаблонов ответа.

    :param node_id: ID чата, в который нужно отправить шаблон.

    :param username: никнейм пользователя, с которым ведется переписка.

    :param prev_page: предыдущая страница.

    :param extra: доп данные для пред. страницы.

    :return: экземпляр клавиатуры.
    """

    keyboard = types.InlineKeyboardMarkup()
    templates = cardinal.telegram.answer_templates[offset: offset + MENU_CFG.TMPLT_BTNS_AMOUNT]
    extra_str = ":" + ":".join(str(i) for i in extra) if extra else ""

    if not templates and offset != 0:
        offset = 0
        templates = cardinal.telegram.answer_templates[offset: offset + MENU_CFG.TMPLT_BTNS_AMOUNT]

    for index, tmplt in enumerate(templates):
        keyboard.add(Button(tmplt.replace("$username", username),
                            callback_data=f"{CBT.SEND_TMPLT}:{offset + index}:{node_id}:{username}:{prev_page}{extra_str}"))

    extra_list = [node_id, username, prev_page]
    extra_list.extend(extra)
    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.TMPLT_BTNS_AMOUNT, len(templates),
                                            len(cardinal.telegram.answer_templates), CBT.TMPLT_LIST_ANS_MODE,
                                            extra_list)

    if prev_page == 0:
        keyboard.add(Button("◀️ Назад", callback_data=f"{CBT.BACK_TO_REPLY_KB}:{node_id}:{username}:0"))
    elif prev_page == 1:
        keyboard.add(Button("◀️ Назад", callback_data=f"{CBT.BACK_TO_REPLY_KB}:{node_id}:{username}:1"))
    elif prev_page == 2:
        keyboard.add(Button("◀️ Назад", callback_data=f"{CBT.BACK_TO_ORDER_KB}:{node_id}:{username}{extra_str}"))
    return keyboard


def plugins_list(cardinal: Cardinal, offset: int):
    """
    Создает клавиатуру со списком плагинов (CBT.PLUGINS_LIST:<offset>).

    :param cardinal: экземпляр кардинала.

    :param offset: смещение списка плагинов.

    :return: экземпляр клавиатуры.
    """
    keyboard = types.InlineKeyboardMarkup()
    plugins = list(cardinal.plugins.keys())[offset: offset + MENU_CFG.PLUGINS_BTNS_AMOUNT]
    if not plugins and offset != 0:
        offset = 0
        plugins = list(cardinal.plugins.keys())[offset: offset + MENU_CFG.PLUGINS_BTNS_AMOUNT]

    for uuid in plugins:
        #  CBT.EDIT_CMD:номер команды:смещение (для кнопки назад)
        keyboard.add(Button(f"{cardinal.plugins[uuid].name} {utils.bool_to_text(cardinal.plugins[uuid].enabled)}",
                            callback_data=f"{CBT.EDIT_PLUGIN}:{uuid}:{offset}"))

    keyboard = utils.add_navigation_buttons(keyboard, offset, MENU_CFG.PLUGINS_BTNS_AMOUNT, len(plugins),
                                            len(list(cardinal.plugins.keys())), CBT.PLUGINS_LIST)

    keyboard.add(Button("➕ Добавить плагин", callback_data=f"{CBT.UPLOAD_PLUGIN}:{offset}"))\
        .add(Button("📋 В главное меню", callback_data=CBT.MAIN))
    return keyboard


def edit_plugin(cardinal: Cardinal, uuid: str, offset: int, ask_to_delete: bool = False):
    """
    Создает клавиатуру управления плагином.

    :param cardinal: экземпляр кардинала.

    :param uuid: UUID плагина.

    :param offset: смещение списка плагинов.

    :param ask_to_delete: вставить ли подтверждение удаления плагина?

    :return: экземпляр клавиатуры.
    """
    plugin_obj = cardinal.plugins[uuid]
    keyboard = types.InlineKeyboardMarkup()
    active_text = "Деактивировать" if cardinal.plugins[uuid].enabled else "Активировать"
    keyboard.add(Button(active_text, callback_data=f"{CBT.TOGGLE_PLUGIN}:{uuid}:{offset}"))

    if plugin_obj.commands:
        keyboard.add(Button("⌨️ Команды", callback_data=f"{CBT.PLUGIN_COMMANDS}:{uuid}:{offset}"))
    if plugin_obj.settings_page:
        keyboard.add(Button("⚙️ Настройки", callback_data=f"{CBT.PLUGIN_SETTINGS}:{uuid}:{offset}"))

    if not ask_to_delete:
        keyboard.add(Button("🗑️ Удалить", callback_data=f"{CBT.DELETE_PLUGIN}:{uuid}:{offset}"))
    else:
        keyboard.row(Button("✅ Да", callback_data=f"{CBT.CONFIRM_DELETE_PLUGIN}:{uuid}:{offset}"),
                     Button("❌ Нет", callback_data=f"{CBT.CANCEL_DELETE_PLUGIN}:{uuid}:{offset}"))
    keyboard.add(Button("◀️ Назад", callback_data=f"{CBT.PLUGINS_LIST}:{offset}"))

    return keyboard
