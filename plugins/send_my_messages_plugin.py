from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

import os
import telebot
from tg_bot import utils, keyboards
from FunPayAPI.types import NewMessageEvent, SystemMessageTypes
from threading import Thread


NAME = "Send My Messages Plugin"
VERSION = "0.0.2"
DESCRIPTION = "Данный плагин позволяет получать уведомления о новых сообщениях в переписках, " \
              "даже если эти сообщения отправили вы."
CREDITS = "@woopertail"
UUID = "081d6abb-9da0-4c93-a3bf-346d27ad234e"
SETTINGS_PAGE = False


def load_state():
    if not os.path.exists(f"storage/plugins/{UUID}/state.txt"):
        return 0
    with open(f"storage/plugins/{UUID}/state.txt", "r", encoding="utf-8") as f:
        data = f.read()
    if data == "1":
        return 1
    return 0


ENABLED = load_state()


def save_state():
    """
    Сохранить состояние (вкл / выкл) в кэш.
    """
    global ENABLED
    if not os.path.exists(f"storage/plugins/{UUID}"):
        os.makedirs(f"storage/plugins/{UUID}")
    with open(f"storage/plugins/{UUID}/state.txt", "w", encoding="utf-8") as f:
        f.write(str(ENABLED))


def send_my_message_notification_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Отправляет уведомление о новом сообщении от вас в телеграм.
    """
    if not ENABLED or cardinal.telegram is None:
        return
    if event.message.unread:
        return
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockNewMessageNotification"]):
        return
    if event.message.text.strip().lower() in cardinal.AR_CFG.sections():
        return
    if event.message.text.startswith("!автовыдача"):
        return
    if event.message.sys_type is not SystemMessageTypes.NON_SYSTEM:
        return

    text = f"""Сообщение в переписке <a href="https://funpay.com/chat/?node={event.message.node_id}">{event.message.chat_with}</a>.

<b><i>Вы:</i></b> <code>{utils.escape(event.message.text)}</code>"""

    button = keyboards.reply(event.message.node_id, event.message.chat_with)
    Thread(target=cardinal.telegram.send_notification, args=(text, button, utils.NotificationTypes.new_message),
           daemon=True).start()


def add_commands(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return

    tg = cardinal.telegram
    bot = tg.bot

    def toggle_state(msg: telebot.types.Message):
        global ENABLED
        ENABLED = int(not ENABLED)
        save_state()
        if ENABLED:
            bot.send_message(msg.chat.id, "✅ Уведомления о своих сообщениях включены.")
        else:
            bot.send_message(msg.chat.id, "✅ Уведомления о своих сообщениях выключены.")

    cardinal.add_commands(UUID, [
        ("mymessages", "вкл / выкл уведомления об отправленных вами сообщениях", True)
    ])
    tg.msg_handler(toggle_state, commands=["MyMessages", "mymessages"])


BIND_TO_NEW_MESSAGE = [send_my_message_notification_handler]
BIND_TO_PRE_INIT = [add_commands]
