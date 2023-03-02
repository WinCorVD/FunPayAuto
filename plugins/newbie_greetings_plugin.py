from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

import os
import json
import logging
from tg_bot import utils, keyboards, CBT
import telebot
import datetime
from telebot.types import InlineKeyboardButton as Button, InlineKeyboardMarkup as Keyboard
from FunPayAPI.types import NewMessageEvent, InitialMessageEvent, Message, SystemMessageTypes


NAME = "Newbie Greetings Plugin"
VERSION = "0.0.3"
DESCRIPTION = "Данный плагин отправляет приветственное сообщение пользователю, " \
              "если тот написал впервые + отправляет уведомление в Telegram."
CREDITS = "@woopertail"
UUID = "30438ea4-da7f-44e8-8e94-b243c6100e53"
SETTINGS_PAGE = True


logger = logging.getLogger(f"FPC.{__name__}")


def load_settings():
    if not os.path.exists(f"storage/plugins/{UUID}/settings.json"):
        return {
            "add_initial_chats": True,
            "send_answer": True,
            "send_notification": True,
            "message": """Привет, $username!
Я вижу тебя впервые!
К сожалению, мой хозяин не настроил текст приветствия,
потому, давай подождем его вместе."""
        }

    with open(f"storage/plugins/{UUID}/settings.json", "r", encoding="utf-8") as f:
        return json.loads(f.read())


def save_settings():
    global SETTINGS
    if not os.path.exists(f"storage/plugins/{UUID}"):
        os.makedirs(f"storage/plugins/{UUID}")
    with open(f"storage/plugins/{UUID}/settings.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(SETTINGS, ensure_ascii=False))


def load_old_users() -> list[str]:
    """
    Загружает из кэша список пользователей, которые уже писали на аккаунт.

    :return: список никнеймов пользователей.
    """
    if not os.path.exists(f"storage/plugins/{UUID}/old_users.json"):
        return []
    with open("storage/cache/newbie_detect_plugin_cache.json", "r", encoding="utf-8") as f:
        users = f.read()

    try:
        users = json.loads(users)
        return users
    except json.decoder.JSONDecodeError:
        return []


def cache_old_users():
    """
    Сохраняет в кэш список пользователей, которые уже писали на аккаунт.
    """
    if not os.path.exists(f"storage/plugins/{UUID}/"):
        os.makedirs(f"storage/plugins/{UUID}/")
    with open("storage/cache/newbie_detect_plugin_cache.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(OLD_USERS, ensure_ascii=False))


def save_already_exists_chat(cardinal: Cardinal, event: InitialMessageEvent):
    """
    Добавляет пользователя в список "не первых", если его чат уже есть на аккаунте.
    """
    if not SETTINGS["add_initial_chats"]:
        return
    if event.message.chat_with not in OLD_USERS:
        OLD_USERS.append(event.message.chat_with)
        cache_old_users()


def send_newbie_notification(cardinal: Cardinal, event: NewMessageEvent):
    if cardinal.telegram and SETTINGS["send_notification"]:
        cardinal.telegram.send_notification(
            f"""Пользователь <a href="https://funpay.com/chat/?node={event.message.node_id}">{event.message.chat_with}</a> написал впервые!

{utils.escape(event.message.text)}""",
            inline_keyboard=keyboards.reply(event.message.node_id, event.message.chat_with))


def send_newbie_message(cardinal: Cardinal, event: NewMessageEvent, *args) -> None:
    """
    Отправляет приветственное сообщение пользователю, если он написал впервые.
    """
    if event.message.chat_with in OLD_USERS:
        return

    OLD_USERS.append(event.message.chat_with)
    cache_old_users()

    if not event.message.unread:
        return
    if event.message.sys_type is not SystemMessageTypes.NON_SYSTEM:
        return

    logger.info(f"Пользователь {event.message.chat_with} пишет впервые. Отправляю приветственное сообщение.")
    send_newbie_notification(cardinal, event)

    if SETTINGS["send_answer"]:
        text = SETTINGS["message"].replace("$username", event.message.chat_with)
        new_message = Message(text, event.message.node_id, event.message.chat_with)
        cardinal.send_message(new_message)


def generate_settings_keyboard(offset: int):
    keyboard = Keyboard()\
        .add(Button(f"Отправлять приветственное сообщение {utils.bool_to_text(SETTINGS['send_answer'])}",
                    callback_data=f"NGP:toggle:send_answer:{offset}"))\
        .add(Button(f"Отправлять уведомление {utils.bool_to_text(SETTINGS['send_notification'])}",
                    callback_data=f"NGP:toggle:send_notification:{offset}"))\
        .add(Button(f"Игнорировать существующие чаты {utils.bool_to_text(SETTINGS['add_initial_chats'])}",
                    callback_data=f"NGP:toggle:add_initial_chats:{offset}"))\
        .add(Button(f"✏️ Изменить текст приветственного сообщения",
                    callback_data=f"NGP:edit_msg:{offset}"))\
        .add(Button(f"◀️ Назад",
                    callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:{offset}"))
    return keyboard


def init_settings_menu(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return

    tg = cardinal.telegram
    bot = tg.bot
    global SETTINGS

    def open_settings_menu(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        uuid, offset = split[1], int(split[2])

        text = f"""Настройки плагина <b><i>{utils.escape(NAME)}</i></b>.

<b><i>Текст приветственного сообщения:</i></b>
<code>{utils.escape(SETTINGS['message'])}</code>

<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
        bot.edit_message_text(text, c.message.chat.id, c.message.id,
                              parse_mode="HTML", reply_markup=generate_settings_keyboard(offset))

    def toggle_param(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        param, offset = split[2], int(split[3])

        SETTINGS[param] = not SETTINGS[param]
        save_settings()
        c.data = f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"
        open_settings_menu(c)

    def act_edit_message(c: telebot.types.CallbackQuery):
        split = c.data.split(":")
        offset = int(split[2])
        result = bot.send_message(c.message.chat.id,
                                  "Введите новый текст приветственного сообщения."
                                  "\n\nСписок переменных:"
                                  "\n<code>$username</code> - никнейм пользователя.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)

        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "NGP:edit_msg",
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
                                                    callback_data=f"NGP:edit_msg:{offset}"))

        bot.reply_to(m, "✅ Текст приветственного сообщения изменен.",
                     allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    tg.cbq_handler(open_settings_menu, lambda c: c.data.startswith(f"{CBT.PLUGIN_SETTINGS}:{UUID}:"))
    tg.cbq_handler(toggle_param, lambda c: c.data.startswith("NGP:toggle:"))
    tg.cbq_handler(act_edit_message, lambda c: c.data.startswith("NGP:edit_msg:"))

    tg.msg_handler(edit_message, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "NGP:edit_msg"))


SETTINGS = load_settings()
OLD_USERS = load_old_users()
logger.info("Загрузил пользователей, которые уже писали мне.")


BIND_TO_PRE_INIT = [init_settings_menu]
BIND_TO_NEW_MESSAGE = [send_newbie_message]
BIND_TO_INIT_MESSAGE = [save_already_exists_chat]
