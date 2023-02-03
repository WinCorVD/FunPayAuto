"""
В данном модуле описаны функции для ПУ загрузки / выгрузки конфиг-файлов.
Модуль реализован в виде плагина.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from telebot import types
from telegram import keyboards
import logging

import os


logger = logging.getLogger("TGBot")


def init_config_loader_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    def open_config_loader(c: types.CallbackQuery):
        bot.edit_message_text("Здесь вы можете загрузить и выгрузить конфиги.", c.message.chat.id,
                              c.message.id, reply_markup=keyboards.configs())

    def send_config(c: types.CallbackQuery):
        """
        Отправляет файл конфига.
        """
        config_type = c.data.split(":")[1]
        if config_type == "main":
            path = "configs/_main.cfg"
        elif config_type == "auto_response":
            path = "configs/auto_response.cfg"
        elif config_type == "auto_delivery":
            path = "configs/auto_delivery.cfg"
        else:
            return
        if not os.path.exists(path):
            bot.send_message(c.message.chat.id, f"❌ Конфиг {path} не обнаружен.")
            bot.answer_callback_query(c.id)
        else:
            with open(path, "r", encoding="utf-8") as f:
                bot.send_document(c.message.chat.id, f)
            logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET запросил "
                        f"конфиг $YELLOW{path}$RESET.")
            bot.answer_callback_query(c.id)

    tg.cbq_handler(open_config_loader, func=lambda c: c.data == "config_loader")
    tg.cbq_handler(send_config, func=lambda c: c.data.startswith("download_config:"))


REGISTER_TO_POST_INIT = [init_config_loader_cp]
