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
        """
        Активирует режим добавления нового шаблона ответа.
        """
        result = bot.send_message(c.message.chat.id,
                                  "Введите новый шаблон ответа.\n\nДоступные переменные:\n<code>$username</code> "
                                  "- <i>никнейм написавшего пользователя.</i>",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.ADD_TMPLT)
        bot.answer_callback_query(c.id)

    def add_template(m: types.Message):
        # todo: добавить правильные offset'ы.
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        template = m.text.strip()

        if template in tg.answer_templates:
            error_keyboard = types.InlineKeyboardMarkup() \
                .row(Button("◀️ Назад", callback_data=f"{CBT.TMPLT_LIST}:0"),
                     Button("➕ Добавить другую", callback_data=CBT.ADD_TMPLT))
            bot.reply_to(m, f"❌ Такая заготовка уже существует.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=error_keyboard)
            return

        tg.answer_templates.append(template)
        utils.save_answer_templates(tg.answer_templates)

        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.TMPLT_LIST}:0"),
                 Button("➕ Добавить еще", callback_data=CBT.ADD_TMPLT))

        bot.reply_to(m, f"✅ Добавлена заготовка:\n"
                        f"<code>{utils.escape(template)}</code>.",
                     allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    def remove_template(c: types.CallbackQuery):
        pass

    def send_template(c: types.CallbackQuery):
        pass

    tg.cbq_handler(open_templates_list, lambda c: c.data.startswith(f"{CBT.TMPLT_LIST}:"))
    tg.cbq_handler(act_add_template, lambda c: c.data == CBT.ADD_TMPLT)
    tg.msg_handler(add_template, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.ADD_TMPLT))


BIND_TO_PRE_INIT = [init_templates_cp]