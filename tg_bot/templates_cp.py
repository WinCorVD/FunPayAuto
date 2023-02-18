"""
В данном модуле описаны функции для ПУ шаблонами ответа.
Модуль реализован в виде плагина.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from tg_bot import utils, keyboards, CBT

from telebot.types import InlineKeyboardButton as Button
from telebot import types
import logging

logger = logging.getLogger("TGBot")


def init_templates_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    def check_template_exists(template_index: int, message_obj: types.Message) -> bool:
        """
        Проверяет, существует ли команда с переданным индексом.
        Если команда не существует - отправляет сообщение с кнопкой обновления списка команд.

        :param template_index: индекс шаблона.

        :param message_obj: экземпляр Telegram-сообщения.

        :return: True, если команда существует, False, если нет.
        """
        if template_index > len(cardinal.telegram.answer_templates) - 1:
            update_button = types.InlineKeyboardMarkup().add(Button("🔄 Обновить",
                                                                    callback_data=f"{CBT.TMPLT_LIST}:0"))
            bot.edit_message_text(f"❌ Не удалось обнаружить команду с индексом <code>{template_index}</code>.",
                                  message_obj.chat.id, message_obj.id,
                                  parse_mode="HTML", reply_markup=update_button)
            return False
        return True

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
        """
        Открывает список существующих шаблонов ответов (answer_mode).
        """
        bot.answer_callback_query(c.id)

    def open_edit_template_cp(c: types.CallbackQuery):
        split = c.data.split(":")
        template_index, offset = int(split[1]), int(split[2])
        if not check_template_exists(template_index, c.message):
            bot.answer_callback_query(c.id)
            return

        keyboard = keyboards.edit_template(cardinal, template_index, offset)
        template = cardinal.telegram.answer_templates[template_index]

        message = f"""<code>{utils.escape(template)}</code>"""
        bot.edit_message_text(message, c.message.chat.id, c.message.id, reply_markup=keyboard, parse_mode="HTML")
        bot.answer_callback_query(c.id)

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

    def del_template(c: types.CallbackQuery):
        split = c.data.split(":")
        template_index, offset = int(split[1]), int(split[2])
        if not check_template_exists(template_index, c.message):
            bot.answer_callback_query(c.id)
            return

        tg.answer_templates.pop(template_index)
        utils.save_answer_templates(tg.answer_templates)
        bot.edit_message_text(f"Здесь вы можете добавлять и удалять заготовки для ответа.",
                              c.message.chat.id, c.message.id,
                              reply_markup=keyboards.templates_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def send_template(c: types.CallbackQuery):
        pass

    tg.cbq_handler(open_templates_list, lambda c: c.data.startswith(f"{CBT.TMPLT_LIST}:"))
    tg.cbq_handler(open_templates_list_in_ans_mode, lambda c: c.data.startswith(f"{CBT.TMPLT_LIST_ANS_MODE}:"))
    tg.cbq_handler(open_edit_template_cp, lambda c: c.data.startswith(f"{CBT.EDIT_TMPLT}:"))
    tg.cbq_handler(act_add_template, lambda c: c.data == CBT.ADD_TMPLT)
    tg.msg_handler(add_template, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.ADD_TMPLT))
    tg.cbq_handler(del_template, lambda c: c.data.startswith(f"{CBT.DEL_TMPLT}:"))


BIND_TO_PRE_INIT = [init_templates_cp]