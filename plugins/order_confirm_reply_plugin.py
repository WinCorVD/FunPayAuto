"""
Данный плагин отправляет сообщение пользователю, после того как последний подтвердит выполнение заказа.
Так же бот отправляет уведомление в Telegram.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

import os
import json
import shutil
import logging
from FunPayAPI.types import OrderStatusChangedEvent, OrderStatuses, Message
import telebot
import datetime
from tg_bot import keyboards, utils, CBT

NAME = "Order Confirm Plugin"
VERSION = "0.0.3"
DESCRIPTION = "После подтверждения заказа данный плагин отправляет ответное сообщение пользователю, а так же " \
              "уведомляет вас об этом в Telegram-чате."
CREDITS = "@woopertail"
UUID = "0358c4a2-b1e0-4302-b58e-0f1b39bd4697"
SETTINGS_PAGE = True

logger = logging.getLogger(f"FPC.{__name__}")


def load_settings():
    if not os.path.exists(f"storage/plugins/{UUID}/settings.json"):
        return {
            "send_ans": True,
            "send_notification": True,
            "message": """$username, спасибо за подтверждение заказа $order_id!

Если не сложно, оставь, пожалуйста, отзыв."""
        }

    with open(f"storage/plugins/{UUID}/settings.json", "r", encoding="utf-8") as f:
        return json.loads(f.read())


SETTINGS = load_settings()


def save_settings():
    global SETTINGS
    if not os.path.exists(f"storage/plugins/{UUID}"):
        os.makedirs(f"storage/plugins/{UUID}")
    with open(f"storage/plugins/{UUID}/settings.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(SETTINGS, ensure_ascii=False))


def delete_plugin_folder(c, call):
    """
    Хэндлер на удаление плагина.
    """
    if not os.path.exists(f"storage/plugins/{UUID}"):
        return
    try:
        shutil.rmtree(f"storage/plugins/{UUID}")
    except:
        pass


def send_thank_u_message_handler(cardinal: Cardinal, event: OrderStatusChangedEvent):
    """
    Отправляет сообщение в чат FunPay.
    """
    global SETTINGS
    if not SETTINGS["send_ans"]:
        return
    if not event.order.status == OrderStatuses.COMPLETED:
        return

    node_id = cardinal.account.get_node_id_by_username(event.order.buyer_username)
    text = SETTINGS["message"].replace("$username", event.order.buyer_username)\
        .replace("$order_name", event.order.title)\
        .replace("$order_id", event.order.id)
    logger.info(f"Пользователь %YELLOW{event.order.buyer_username}$RESET подтвердил выполнение заказа "
                f"$YELLOW{event.order.id}.$RESET")
    logger.info(f"Отправляю ответное сообщение ...")
    msg = Message(text, node_id, None, False)
    cardinal.send_message(msg)


def send_notification_handler(cardinal: Cardinal, event: OrderStatusChangedEvent):
    """
    Отправляет уведомление в Telegram.
    """
    global SETTINGS
    if not cardinal.telegram or not SETTINGS["send_notification"]:
        return
    if not event.order.status == OrderStatuses.COMPLETED:
        return

    tg = cardinal.telegram
    node_id = cardinal.account.get_node_id_by_username(event.order.buyer_username)
    tg.send_notification(f"""🪙 Пользователь <a href="https://funpay.com/chat/?node={node_id}">{event.order.buyer_username}</a> """
                         f"""подтвердил выполнение заказа <code>{event.order.id}</code>.""",
                         inline_keyboard=keyboards.new_order(event.order.id[1:], event.order.buyer_username, node_id))


def generate_settings_keyboard(offset: int):
    keyboard = telebot.types.InlineKeyboardMarkup()\
        .add(telebot.types.InlineKeyboardButton(f"Отправлять ответ {utils.bool_to_text(SETTINGS['send_ans'])}",
                                                callback_data=f"OCRP:send_ans:{offset}"))\
        .add(telebot.types.InlineKeyboardButton(f"Отправлять уведомление {utils.bool_to_text(SETTINGS['send_notification'])}",
                                                callback_data=f"OCRP:send_notification:{offset}"))\
        .add(telebot.types.InlineKeyboardButton(f"✏️ Изменить текст ответа",
                                                callback_data=f"OCRP:edit_msg:{offset}"))\
        .add(telebot.types.InlineKeyboardButton(f"◀️ Назад",
                                                callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:{offset}"))
    return keyboard


def telegram_settings_cp(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return

    tg = cardinal.telegram
    bot = tg.bot
    global SETTINGS

    def open_settings_menu(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        uuid, offset = split[1], int(split[2])

        text = f"""Настройки плагина <b><i>{utils.escape(NAME)}</i></b>.

<b><i>Текст ответа на подтверждение заказа:</i></b>
<code>{utils.escape(SETTINGS['message'])}</code>

<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
        bot.edit_message_text(text, c.message.chat.id, c.message.id,
                              parse_mode="HTML", reply_markup=generate_settings_keyboard(offset))

    def toggle_msg(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        offset = int(split[2])

        SETTINGS["send_ans"] = not SETTINGS["send_ans"]
        save_settings()
        c.data = f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"
        open_settings_menu(c)

    def toggle_notification(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        offset = int(split[2])

        SETTINGS["send_notification"] = not SETTINGS["send_notification"]
        save_settings()
        c.data = f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"
        open_settings_menu(c)

    def act_edit_message(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        offset = int(split[2])
        result = bot.send_message(c.message.chat.id,
                                  "Введите новый текст ответа на подтверждение заказа."
                                  "\n\nСписок переменных:"
                                  "\n<code>$username</code> - никнейм пользователя."
                                  "\n<code>$order_id</code> - ID заказа.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)

        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "OCRP:edit_msg",
                          {"offset": offset})
        bot.answer_callback_query(c.id)

    def edit_message(m: telebot.types.Message):
        user_state = tg.get_user_state(m.chat.id, m.from_user.id)
        offset = user_state["data"]["offset"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)

        SETTINGS["message"] = m.text
        save_settings()

        keyboard = telebot.types.InlineKeyboardMarkup()\
            .row(telebot.types.InlineKeyboardButton("◀️ Назад",
                                                    callback_data=f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"),
                 telebot.types.InlineKeyboardButton("✏️ Изменить",
                                                    callback_data=f"OCRP:edit_msg:{offset}"))

        bot.reply_to(m, "✅ Текст ответа на подтверждение заказа изменен.",
                     allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)


    tg.cbq_handler(open_settings_menu, lambda c: c.data.startswith(f"{CBT.PLUGIN_SETTINGS}:{UUID}:"))
    tg.cbq_handler(toggle_msg, lambda c: c.data.startswith(f"OCRP:send_ans:"))
    tg.cbq_handler(toggle_notification, lambda c: c.data.startswith(f"OCRP:send_notification:"))
    tg.cbq_handler(act_edit_message, lambda c: c.data.startswith("OCRP:edit_msg:"))
    tg.msg_handler(edit_message, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "OCRP:edit_msg"))


BIND_TO_PRE_INIT = [telegram_settings_cp]
BIND_TO_ORDER_STATUS_CHANGED = [send_thank_u_message_handler, send_notification_handler]
BIND_TO_DELETE = delete_plugin_folder
