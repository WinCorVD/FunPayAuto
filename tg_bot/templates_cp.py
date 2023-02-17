"""
В данном модуле описаны функции для ПУ шаблонами ответа.
Модуль реализован в виде плагина.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from tg_bot import utils, keyboards, CBT, MENU_CFG

from telebot.types import InlineKeyboardButton as Button
from telebot import types
import datetime
import logging

logger = logging.getLogger("TGBot")


def init_templates_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    def open_templates_list(c: types.CallbackQuery):
        """
        Открывает список существующих шаблонов ответов.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"Здесь вы можете добавлять и удалять заготовки для ответа.",
                              c.message.chat.id, c.message.id,
                              reply_markup=keyboards.templates_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def open_templates_list_in_ans_mode(c: types.CallbackQuery):
        pass

    def act_add_template(c: types.CallbackQuery):
        pass

    def add_template(c: types.CallbackQuery):
        pass

    def remove_template(c: types.CallbackQuery):
        pass

    def send_template(c: types.CallbackQuery):
        pass

    tg.cbq_handler(open_templates_list, lambda c: c.data.startswith(f"{CBT.TMPLT_LIST}:"))


BIND_TO_PRE_INIT = [init_templates_cp]