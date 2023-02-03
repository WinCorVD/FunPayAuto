"""
В данном модуле описаны функции для ПУ конфига авто-ответчика.
Модуль реализован в виде плагина.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from telegram import telegram_tools as tg_tools, keyboards

from telebot.types import InlineKeyboardButton as Button
from telebot import types
import datetime
import logging


logger = logging.getLogger("TGBot")


def init_auto_response_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    def open_commands_list(c: types.CallbackQuery):
        """
        Открывает список существующих команд.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"Выберите интересующую вас команду.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.commands_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def act_add_command(c: types.CallbackQuery):
        """
        Активирует режим добавления новой команды.
        """
        result = bot.send_message(c.message.chat.id,
                                  "Введите новую команду (или несколько команд через знак <code>|</code>).",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "add_command")
        bot.answer_callback_query(c.id)

    def add_command(m: types.Message):
        """
        Добавляет новую команду в конфиг.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        raw_command = m.text.strip()
        commands = [i.strip() for i in raw_command.split("|") if i.strip()]
        applied_commands = []
        for cmd in commands:
            if cmd in applied_commands:
                bot.send_message(m.chat.id, f"❌ Дубликат команды <code>{tg_tools.format_text(cmd)}</code>.",
                                 parse_mode="HTML")
                return
            if cmd in cardinal.AR_CFG.sections():
                bot.send_message(m.chat.id, f"❌ Команда <code>{tg_tools.format_text(cmd)}</code> уже существует.",
                                 parse_mode="HTML")
                return
            applied_commands.append(cmd)

        cardinal.RAW_AR_CFG.add_section(raw_command)
        cardinal.RAW_AR_CFG.set(raw_command, "response", "Данной команде необходимо настроить текст ответа :(")
        cardinal.RAW_AR_CFG.set(raw_command, "telegramNotification", "0")

        for cmd in applied_commands:
            cardinal.AR_CFG.add_section(cmd)
            cardinal.AR_CFG.set(cmd, "response", "Данной команде необходимо настроить текст ответа :(")
            cardinal.AR_CFG.set(cmd, "telegramNotification", "0")

        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")

        command_number = len(cardinal.RAW_AR_CFG.sections())-1
        offset = command_number - 4 if command_number - 4 > 0 else 0

        keyboard = types.InlineKeyboardMarkup()\
            .add(Button("✏️ Редактировать команду", callback_data=f"edit_command:{command_number}:{offset}"))
        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET добавил секцию "
                    f"$YELLOW[{raw_command}]$RESET в конфиг авто-ответчика.")
        bot.send_message(m.chat.id, f"✅ Добавлена новая секция "
                                    f"<code>[{tg_tools.format_text(raw_command)}]</code> в конфиг авто-ответчика.",
                         parse_mode="HTML", reply_markup=keyboard)

    def open_edit_command_cp(c: types.CallbackQuery):
        """
        Открывает панель редактирования команды.
        """
        command_number = int(c.data.split(":")[1])
        offset = int(c.data.split(":")[2])
        keyboard = keyboards.edit_command(cardinal, command_number, offset)
        if not keyboard:
            bot.edit_message_text("❌ Не удалось обнаружить искомую команду. Обновите меню команд.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        command = cardinal.RAW_AR_CFG.sections()[command_number]
        command_obj = cardinal.RAW_AR_CFG[command]

        if command_obj.get("telegramNotification") == "1":
            telegram_notification_text = "Да."
        else:
            telegram_notification_text = "Нет."
        notification_text = command_obj.get("notificationText")
        notification_text = notification_text if notification_text else "Пользователь $username ввел команду $message_text."

        message = f"""<b>[{tg_tools.format_text(command)}]</b>

<b><i>Ответ:</i></b> <code>{tg_tools.format_text(command_obj["response"])}</code>

<b><i>Отправлять уведомления в Telegram:</i></b> <b><u>{telegram_notification_text}</u></b>

<b><i>Текст уведомления:</i></b> <code>{tg_tools.format_text(notification_text)}</code>

<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
        bot.edit_message_text(message, c.message.chat.id, c.message.id, reply_markup=keyboard, parse_mode="HTML")
        bot.answer_callback_query(c.id)

    def act_edit_command_response(c: types.CallbackQuery):
        """
        Активирует режим изменения текста ответа команды.
        """
        result = bot.send_message(c.message.chat.id, "Введите новый текст ответа.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        commands_number = c.data.split(":")[1]
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "edit_commands_response",
                          {"commands_number": int(commands_number)})
        bot.answer_callback_query(c.id)

    def edit_command_response(m: types.Message):
        """
        Изменяет текст ответа команды.
        """
        command_number = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["commands_number"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        response_text = m.text.strip()

        if command_number > len(cardinal.RAW_AR_CFG.sections()) - 1:
            bot.send_message(m.chat.id, "❌ Не удалось обнаружить искомую команду. Обновите меню команд.")
            return

        command = cardinal.RAW_AR_CFG.sections()[command_number]
        commands = [i.strip() for i in command.split("|") if i.strip()]
        cardinal.RAW_AR_CFG.set(command, "response", response_text)
        for cmd in commands:
            cardinal.AR_CFG.set(cmd, "response", response_text)
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET изменил текст ответа "
                    f"команды $YELLOW[{command}]$RESET на $YELLOW\"{response_text}\"$RESET.")
        bot.send_message(m.chat.id, f"✅ Ответ команды / сета команд <code>[{tg_tools.format_text(command)}]</code> "
                                    f"изменен на <code>{tg_tools.format_text(response_text)}</code>"
                                    "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ КОМАНДЫ!</u></b>",
                         parse_mode="HTML")

    def act_edit_command_notification(c: types.CallbackQuery):
        """
        Активирует режим изменения уведомления о вводе команды.
        """
        result = bot.send_message(c.message.chat.id, "Введите новый текст уведомления.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        commands_number = c.data.split(":")[1]
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "edit_commands_notification",
                          {"commands_number": int(commands_number)})
        bot.answer_callback_query(c.id)

    def edit_command_notification(m: types.Message):
        """
        Изменяет текст уведомления о вводе команды.
        """
        command_number = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["commands_number"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        notification_text = m.text.strip()

        if command_number > len(cardinal.RAW_AR_CFG.sections()) - 1:
            bot.send_message(m.chat.id, "❌ Не удалось обнаружить искомую команду. Обновите меню команд.")
            return

        command = cardinal.RAW_AR_CFG.sections()[command_number]
        commands = [i.strip() for i in command.split("|") if i.strip()]
        cardinal.RAW_AR_CFG.set(command, "notificationText", notification_text)
        for cmd in commands:
            cardinal.AR_CFG.set(cmd, "response", notification_text)
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET изменил текст "
                    f"уведомления команды $YELLOW[{command}]$RESET на $YELLOW\"{notification_text}\"$RESET.")
        bot.send_message(m.chat.id, f"✅ Текст уведомления команды <code>[{tg_tools.format_text(command)}]</code> "
                                    f"изменен на <code>{tg_tools.format_text(notification_text)}</code>"
                                    "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ КОМАНДЫ!</u></b>",
                         parse_mode="HTML")

    def switch_notification(c: types.CallbackQuery):
        """
        Вкл / Выкл уведомление о вводе команды.
        """
        command_number = int(c.data.split(":")[1])
        if command_number > len(cardinal.RAW_AR_CFG.sections()) - 1:
            bot.edit_message_text("❌ Не удалось обнаружить искомую команду. Обновите меню команд.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        command = cardinal.RAW_AR_CFG.sections()[command_number]
        commands = [i.strip() for i in command.split("|") if i.strip()]
        command_obj = cardinal.RAW_AR_CFG[command]
        if command_obj.get("telegramNotification") in [None, "0"]:
            value = "1"
        else:
            value = "0"
        cardinal.RAW_AR_CFG.set(command, "telegramNotification", value)
        for cmd in commands:
            cardinal.AR_CFG.set(cmd, "telegramNotification", value)
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")
        logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET изменил параметр "
                    f"$CYANtelegramNotification$RESET команды $YELLOW[{command}]$RESET на $YELLOW{value}$RESET.")
        open_edit_command_cp(c)

    def del_command(c: types.CallbackQuery):
        """
        Удаляет команду из конфига.
        """
        command_number = int(c.data.split(":")[1])
        offset = int(c.data.split(":")[2])
        if command_number > len(cardinal.RAW_AR_CFG.sections()) - 1:
            bot.edit_message_text("❌ Не удалось обнаружить искомую команду. Обновите меню команд.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        command = cardinal.RAW_AR_CFG.sections()[command_number]
        commands = [i.strip() for i in command.split("|") if i.strip()]
        cardinal.RAW_AR_CFG.remove_section(command)
        for cmd in commands:
            cardinal.AR_CFG.remove_section(cmd)
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")
        logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET удалил команду "
                    f"$YELLOW[{command}]$RESET.")
        bot.edit_message_text(f"Выберите интересующую вас команду.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.commands_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    # Регистрируем хэндлеры
    tg.cbq_handler(open_commands_list, func=lambda c: c.data.startswith("command_list:"))

    tg.cbq_handler(act_add_command, func=lambda c: c.data == "add_command")
    tg.msg_handler(add_command, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "add_command"))

    tg.cbq_handler(open_edit_command_cp, func=lambda c: c.data.startswith("edit_command:"))

    tg.cbq_handler(act_edit_command_response, func=lambda c: c.data.startswith("edit_commands_response:"))
    tg.msg_handler(edit_command_response,
                   func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "edit_commands_response"))

    tg.cbq_handler(act_edit_command_notification, func=lambda c: c.data.startswith("edit_commands_notification:"))
    tg.msg_handler(edit_command_notification,
                   func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "edit_commands_notification"))

    tg.cbq_handler(switch_notification, func=lambda c: c.data.startswith("switch_telegram_notification:"))
    tg.cbq_handler(del_command, func=lambda c: c.data.startswith("del_command:"))


REGISTER_TO_POST_INIT = [init_auto_response_cp]
