"""
В данном модуле написан Telegram бот.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import FunPayAPI.types

if TYPE_CHECKING:
    from cardinal import Cardinal

import os
import time
import random
import string
import psutil
import telebot
import logging
import traceback

from telebot import types
from telebot.types import InlineKeyboardButton as Button

from tg_bot import utils, keyboards, CBT
from Utils import cardinal_tools


logger = logging.getLogger("TGBot")


class TGBot:
    def __init__(self, cardinal: Cardinal):
        self.cardinal = cardinal
        self.bot = telebot.TeleBot(self.cardinal.MAIN_CFG["Telegram"]["token"])

        self.authorized_users = utils.load_authorized_users()
        self.chat_ids = utils.load_chat_ids()

        # [(chat_id, message_id)]
        self.init_messages = []

        # {
        #     chat_id: {
        #         user_id: {
        #            "status": None | "statusText",
        #             "data": { ... },
        #             "msg_id": int
        #         }
        #     }
        # }
        self.user_states = {}

        self.commands = {
            "FunPayCardinal": {
                "menu": "открыть панель настроек",
                "notifications": "вкл / выкл уведомления в этом чате",
                "commands": "получить справку по командам",
                "test_lot": "создать ключ для теста авто-выдачи",
                "ban": "добавить пользователя в ЧС",
                "unban": "удалить пользователя из ЧС",
                "block_list": "получить ЧС",
                "logs": "получить лог-файл",
                "about": "информация о боте",
                "sys": "информация о нагрузке на систему",
                "restart": "перезагрузить бота",
                "power_off": "выключить бота"
            }
        }

    # User states
    def get_user_state(self, chat_id: int, user_id: int) -> dict | None:
        """
        Получает текущее состояние пользователя.

        :param chat_id: id чата.

        :param user_id: id пользователя.

        :return: состояние + доп. данные.
        """
        if chat_id not in self.user_states:
            return None
        if user_id not in self.user_states[chat_id]:
            return None
        if self.user_states[chat_id][user_id].get("state") is None:
            return None
        else:
            return self.user_states[chat_id][user_id]

    def set_user_state(self, chat_id: int, message_id: int, user_id: int,
                       state: str, data: dict | None = None) -> None:
        """
        Устанавливает состояние для пользователя.

        :param chat_id: id чата.

        :param message_id: id сообщения, после которого устанавливается данное состояние.

        :param user_id: id пользователя.

        :param state: состояние.

        :param data: доп. данные.
        """
        if chat_id not in self.user_states:
            self.user_states[chat_id] = {}
        if user_id not in self.user_states[chat_id]:
            self.user_states[chat_id][user_id] = {}
        if self.user_states[chat_id][user_id].get("state") is None and state is None:
            return None
        self.user_states[chat_id][user_id]["state"] = state
        self.user_states[chat_id][user_id]["data"] = {} if data is None else data
        self.user_states[chat_id][user_id]["msg_id"] = message_id

    def clear_user_state(self, chat_id: int, user_id: int, del_msg: bool = False) -> int | None:
        """
        Очищает состояние пользователя.

        :param chat_id: id чата.

        :param user_id: id пользователя.

        :param del_msg: удалять ли сообщение, после которого было обозначено текущее состояние.

        :return: ID сообщения | None, если состояние уже было пустое.
        """
        if chat_id not in self.user_states:
            self.user_states[chat_id] = {}
        if user_id not in self.user_states[chat_id]:
            self.user_states[chat_id][user_id] = {}
        if self.user_states[chat_id][user_id].get("state") is None:
            return None

        msg_id = self.user_states[chat_id][user_id]["msg_id"]
        self.user_states[chat_id][user_id]["state"] = None
        self.user_states[chat_id][user_id]["data"] = {}
        self.user_states[chat_id][user_id]["msg_id"] = None

        if del_msg:
            self.bot.delete_message(chat_id, msg_id)

        return msg_id

    def check_state(self, chat_id: int, user_id: int, state: str) -> bool:
        """
        Проверяет, является ли состояние указанным.

        :param chat_id: id чата.

        :param user_id: id пользователя.

        :param state: состояние.

        :return: True / False
        """
        if chat_id not in self.user_states:
            return False
        if user_id not in self.user_states[chat_id]:
            return False
        if self.user_states[chat_id][user_id].get("state") != state:
            return False
        return True

    # handler binders
    def msg_handler(self, handler, **kwargs):
        """
        Регистрирует хэндлер, срабатывающий при новом сообщении.

        :param handler: хэндлер.

        :param kwargs: аргументы для хэндлера.
        """
        bot_instance = self.bot

        @bot_instance.message_handler(**kwargs)
        def run_handler(message: types.Message):
            try:
                handler(message)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера Telegram бота. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    def cbq_handler(self, handler, func, **kwargs):
        """
        Регистрирует хэндлер, срабатывающий при новом callback'е.

        :param handler: хэндлер.

        :param func: функция-фильтр.

        :param kwargs: аргументы для хэндлера.
        """
        bot_instance = self.bot

        @bot_instance.callback_query_handler(func, **kwargs)
        def run_handler(call: types.CallbackQuery):
            try:
                handler(call)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера Telegram бота. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    # Система свой-чужой 0_0
    def reg_admin(self, message: types.Message):
        """
        Проверяет, есть ли пользователь в списке пользователей с доступом к ПУ TG.
        """
        if message.chat.type != "private":
            return
        if message.text == self.cardinal.MAIN_CFG["Telegram"]["secretKey"]:
            self.authorized_users.append(message.from_user.id)
            utils.save_authorized_users(self.authorized_users)
            text = f"""🔓 Доступ к ПУ предоставлен!

🔕 Учти, что сейчас я <b><u>не отправляю никакие уведомления в этот чат</u></b>.

🔔 Ты можешь включить / выключить отправку уведомлений <b><u>в этот чат</u></b> с помощью команды /notifications.

⚙️ Чтобы открыть меню настроек <i>FunPay Cardinal</i>, введи команду /menu."""
            logger.warning(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                           "ПОЛУЧИЛ ДОСТУП К ПУ TG!")

        else:
            text = f"""👋 Привет, <b><i>{message.from_user.username}</i></b>!\n\n❌ Ты неавторизованный пользователь.\n
🔑 Отправь мне <u><b>секретный пароль</b></u> (<code>[Telegram]</code> <b>→</b> <code>secretKey</code>) """ \
                   """который ты ввел в моих настройках, чтобы начать работу."""
            logger.warning(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                           f"попытался получить доступ к ПУ TG. Сдерживаю его как могу!")
        self.bot.send_message(message.chat.id, text, parse_mode="HTML")

    @staticmethod
    def ignore_unauthorized_users(call: types.CallbackQuery):
        """
        Игнорирует callback'и от не авторизированных пользователей.
        """
        logger.warning(f"Пользователь $MAGENTA{call.from_user.username} (id {call.from_user.id})$RESET "
                       f"тыкает кнопки ПУ в чате $MAGENTA@{call.message.chat.username}"
                       f" (id {call.message.chat.id})$RESET. Сдерживаю его как могу!")
        return

    # Команды
    def send_settings_menu(self, message: types.Message):
        """
        Отправляет основное меню настроек (новым сообщением).
        """
        self.bot.send_message(message.chat.id, "Добро пожаловать в панель управления. Выберите категорию настроек.",
                              reply_markup=keyboards.settings_sections())

    def switch_notifications(self, message: types.Message):
        """
        Включает / отключает уведомления в чате.
        """
        if message.chat.id in self.chat_ids:
            self.chat_ids.remove(message.chat.id)
            utils.save_chat_ids(self.chat_ids)
            logger.info(
                f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET выключил "
                f"уведомления в чате $MAGENTA@{message.chat.username} (id {message.chat.id})$RESET.")
            self.bot.send_message(message.chat.id, "🔕 Теперь в этот чат не будут приходить уведомления.")
        else:
            self.chat_ids.append(message.chat.id)
            utils.save_chat_ids(self.chat_ids)
            logger.info(
                f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET включил "
                f"уведомления в чате $MAGENTA@{message.chat.username} (id {message.chat.id})$RESET.")
            self.bot.send_message(message.chat.id, "🔔 Теперь в этот чат будут приходить уведомления.")

    def send_commands_help(self, message: types.Message):
        """
        Отправляет справку по командам.
        """
        self.bot.send_message(message.chat.id, utils.generate_help_text(self.commands), parse_mode="HTML")

    def act_manual_delivery_test(self, message: types.Message):
        """
        Активирует режим ввода названия лота для ручной генерации ключа теста авто-выдачи.
        """
        result = self.bot.send_message(message.chat.id, "Введите название лота, тест авто-выдачи которого вы хотите "
                                                        "провести.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, CBT.MANUAL_AD_TEST)

    def manual_delivery_text(self, message: types.Message):
        """
        Генерирует ключ теста авто-выдачи (ручной режим).
        """
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        lot_name = message.text.strip()
        simbols = string.ascii_letters + "0123456789"
        key = "".join(random.sample(simbols, 50))

        self.cardinal.delivery_tests[key] = lot_name

        logger.info(
            f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET создал "
            f"одноразовый ключ для авто-выдачи лота $YELLOW[{lot_name}]$RESET: $CYAN{key}$RESET.")

        self.bot.send_message(message.chat.id,
                              f"✅ Одноразовый ключ для теста авто-выдачи лота "
                              f"<b>[</b><code>{utils.escape(lot_name)}</code><b>]</b> успешно создан. \n\n"
                              f"Для теста авто-выдачи введите команду снизу в любой чат FunPay (ЛС)."
                              f"\n\n<code>!автовыдача {key}</code>", parse_mode="HTML")

    def act_ban(self, message: types.Message):
        """
        Активирует режим ввода никнейма пользователя, которого нужно добавить в ЧС.
        """
        result = self.bot.send_message(message.chat.id, "Введите имя пользователя, которого хотите внести в ЧС.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, CBT.BAN)

    def ban(self, message: types.Message):
        """
        Добавляет пользователя в ЧС.
        """
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        nickname = message.text.strip()

        if nickname in self.cardinal.block_list:
            self.bot.send_message(message.chat.id, f"❌ Пользователь <code>{nickname}</code> уже находится в ЧС.",
                                  parse_mode="HTML")
            return
        self.cardinal.block_list.append(nickname)
        cardinal_tools.cache_block_list(self.cardinal.block_list)
        logger.info(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                    f"добавил пользователя $YELLOW{nickname}$RESET в ЧС.")
        self.bot.send_message(message.chat.id, f"✅ Пользователь <code>{nickname}</code> добавлен в ЧС.",
                              parse_mode="HTML")

    def act_unban(self, message: types.Message):
        """
        Активирует режим ввода никнейма пользователя, которого нужно удалить из ЧС.
        """
        result = self.bot.send_message(message.chat.id, "Введите имя пользователя, которого хотите удалить в ЧС.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, CBT.UNBAN)

    def unban(self, message: types.Message):
        """
        Удаляет пользователя из ЧС.
        """
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        nickname = message.text.strip()
        if nickname not in self.cardinal.block_list:
            self.bot.send_message(message.chat.id, f"❌ Пользователя <code>{nickname}</code> нет в ЧС.",
                                  parse_mode="HTML")
            return
        self.cardinal.block_list.remove(nickname)
        cardinal_tools.cache_block_list(self.cardinal.block_list)
        logger.info(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                    f"удалил пользователя $YELLOW{nickname}$RESET из ЧС.")
        self.bot.send_message(message.chat.id, f"✅ Пользователь <code>{nickname}</code> удален из ЧС.",
                              parse_mode="HTML")

    def send_ban_list(self, message: types.Message):
        """
        Отправляет ЧС.
        """
        if not self.cardinal.block_list:
            self.bot.send_message(message.chat.id, "❌ Черный список пуст.")
            return
        block_list = ", ".join(f"<code>{nickname}</code>" for nickname in self.cardinal.block_list)
        self.bot.send_message(message.chat.id, block_list, parse_mode="HTML")

    def send_logs(self, message: types.Message):
        """
        Отправляет файл логов.
        """
        if not os.path.exists("logs/log.log"):
            self.bot.send_message(message.chat.id, "❌ Лог файл не обнаружен.")
        else:
            with open("logs/log.log", "r", encoding="utf-8") as f:
                self.bot.send_document(message.chat.id, f)

    def send_about_text(self, message: types.Message):
        """
        Отправляет текст о боте.
        """
        self.bot.send_message(message.chat.id, utils.ABOUT_TEXT)

    def send_system_info(self, msg: types.Message):
        """
        Отправляет информацию о нагрузке на систему.
        """
        current_time = int(time.time())
        run_time = current_time - self.cardinal.start_time

        ram = psutil.virtual_memory()
        cpu_usage = "\n".join(
            f"    CPU {i}:  <code>{l}%</code>" for i, l in enumerate(psutil.cpu_percent(percpu=True)))
        self.bot.send_message(msg.chat.id, f"""<b><u>Сводка данных</u></b>

<b>ЦП:</b>
{cpu_usage}
    Используется ботом: <code>{psutil.Process().cpu_percent()}%</code>

<b>ОЗУ:</b>
    Всего:  <code>{ram.total // 1048576} MB</code>
    Использовано:  <code>{ram.used // 1048576} MB</code>
    Свободно:  <code>{ram.free // 1048576} MB</code>
    Используется ботом:  <code>{psutil.Process().memory_info().rss // 1048576} MB</code>

<b>Бот:</b>
    Аптайм:  <code>{cardinal_tools.time_to_str(run_time)}</code>
    Чат:  <code>{msg.chat.id}</code>""", parse_mode="HTML")

    def restart_cardinal(self, msg: types.Message):
        """
        Перезапускает кардинал.
        """
        self.bot.send_message(msg.chat.id, "Перезагружаюсь...")
        cardinal_tools.restart_program()

    def ask_power_off(self, msg: types.Message):
        """
        Просит подтверждение на отключение FPC.
        """
        self.bot.send_message(msg.chat.id, """<b><u>Вы уверены, что хотите выключить меня?</u></b>\n
Включить меня через <i>Telegram</i>-ПУ <b><u>не получится!</u></b>""",
                              reply_markup=keyboards.power_off(self.cardinal.instance_id, 0), parse_mode="HTML")

    def cancel_power_off(self, call: types.CallbackQuery):
        """
        Отменяет выключение (удаляет клавиатуру с кнопками подтверждения).
        """
        self.bot.edit_message_text("Выключение отменено.", call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id)

    def power_off(self, call: types.CallbackQuery):
        """
        Отключает FPC.
        """
        split = call.data.split(":")
        state = int(split[1])
        instance_id = int(split[2])

        if instance_id != self.cardinal.instance_id:
            self.bot.edit_message_text("❌ Данная кнопка не принадлежит этому запуску.\nВызовите это меню снова.",
                                       call.message.chat.id, call.message.id)
            self.bot.answer_callback_query(call.id)
            return

        if state == 6:
            self.bot.edit_message_text("Ладно, ладно, выключаюсь...", call.message.chat.id, call.message.id)
            self.bot.answer_callback_query(call.id)
            cardinal_tools.shut_down()
            return

        texts = ["На всякий случай спрошу еще раз.\n\n<b><u>Вы точно уверены?</u></b>",

                 """Просто для протокола:\n             
вам придется заходить на ваш сервер или подходить к компьютеру (ну или где я там у вас) и запускать меня вручную!""",

                 """Не то чтобы я навязываюсь, но если вы хотите применить изменения основного конфига, вы можете 
просто перезапустить меня командой /restart.""",

                 """Вы вообще читаете мои сообщения? Проверим ка вас на внимательность: да = нет, нет = да. """ +
                 """Уверен, вы даже не читаете мои сообщения, а ведь важную инфу тут пишу.""",

                 "Ну то есть твердо и четко, дэ?"]

        self.bot.edit_message_text(texts[state - 1], call.message.chat.id, call.message.id,
                                   reply_markup=keyboards.power_off(instance_id, state), parse_mode="HTML")
        self.bot.answer_callback_query(call.id)

    # Чат FunPay
    def act_send_funpay_message(self, call: types.CallbackQuery):
        """
        Активирует режим ввода ссобщения для отправки его в чат FunPay.
        """
        split = call.data.split(":")
        node_id = int(split[1])
        try:
            username = split[2]
        except IndexError:
            username = None
        result = self.bot.send_message(call.message.chat.id, "Введите текст сообщения.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(call.message.chat.id, result.id, call.from_user.id,
                            CBT.SEND_FP_MESSAGE, {"node_id": node_id, "username": username})
        self.bot.answer_callback_query(call.id)

    def send_funpay_message(self, message: types.Message):
        """
        Отправляет сообщение в чат FunPay.
        """
        data = self.get_user_state(message.chat.id, message.from_user.id)["data"]
        node_id, username = data["node_id"], data["username"]
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        response_text = message.text.strip()
        new_msg_obj = FunPayAPI.types.Message(response_text, node_id, None)
        result = self.cardinal.send_message(new_msg_obj)
        if result:
            keyboard = types.InlineKeyboardMarkup() \
                .add(Button("📨 Отправить еще", callback_data=f"{CBT.SEND_FP_MESSAGE}:{node_id}:{username}"))
            self.bot.reply_to(message, f'✅ Сообщение отправлено в переписку '
                                       f'<a href="https://funpay.com/chat/?node={node_id}">{username}</a>.',
                              allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup() \
                .add(Button("📨 Попробовать еще раз", callback_data=f"{CBT.SEND_FP_MESSAGE}:{node_id}:{username}"))
            self.bot.reply_to(message, f'❌ Не удалось отправить сообщение в переписку '
                                       f'<a href="https://funpay.com/chat/?node={node_id}">{username}</a>. '
                                       f'Подробнее в файле <code>logs/log.log</code>',
                              allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    # Ордер
    def ask_to_confirm_refund(self, call: types.CallbackQuery):
        """
        Просит подтвердить возврат денег.
        """
        order_id = call.data.split(":")[1]
        keyboard = keyboards.new_order(order_id, confirmation=True)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
        self.bot.answer_callback_query(call.id)

    def cancel_refund(self, call: types.CallbackQuery):
        """
        Отменяет возврат.
        """
        order_id = call.data.split(":")[1]
        keyboard = keyboards.new_order(order_id)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
        self.bot.answer_callback_query(call.id)

    def refund(self, call: types.CallbackQuery):
        """
        Оформляет возврат за заказ.
        """
        order_id = call.data.split(":")[1]
        new_msg = False
        attempts = 3
        while attempts:
            try:
                self.cardinal.account.refund_order(order_id)
                break
            except:
                if not new_msg:
                    new_msg = self.bot.send_message(call.message.chat.id,
                                                    f"❌ Не удалось вернуть средства по заказу <code>#{order_id}</code>."
                                                    f"\nОсталось попыток: <code>{attempts}</code>.",
                                                    parse_mode="HTML")
                else:
                    self.bot.edit_message_text(f"❌ Не удалось вернуть средства по заказу <code>#{order_id}</code>."
                                               f"\nОсталось попыток: <code>{attempts}</code>.",
                                               new_msg.chat.id, new_msg.id, parse_mode="HTML")
                attempts -= 1
                time.sleep(1)
                continue

        if attempts:
            if not new_msg:
                self.bot.send_message(call.message.chat.id,
                                      f"✅ Средства по заказу <code>#{order_id}</code> возвращены.", parse_mode="HTML")
            else:
                self.bot.edit_message_text(f"✅ Средства по заказу <code>#{order_id}</code> возвращены.",
                                           new_msg.chat.id, new_msg.id, parse_mode="HTML")

            keyboard = keyboards.new_order(order_id, no_refund=True)
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
            self.bot.answer_callback_query(call.id)
            return

        self.bot.edit_message_text(f"❌ Не удалось вернуть средства по заказу <code>#{order_id}</code>.",
                                   new_msg.chat.id, new_msg.id, parse_mode="HTML")

        keyboard = keyboards.new_order(order_id)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
        self.bot.answer_callback_query(call.id)

    # Панель управления
    def open_cp(self, call: types.CallbackQuery):
        """
        Открывает основное меню настроек (редактирует сообщение).
        """
        self.bot.edit_message_text("Добро пожаловать в панель управления. Выберите категорию настроек.",
                                   call.message.chat.id, call.message.id, reply_markup=keyboards.settings_sections())
        self.bot.answer_callback_query(call.id)

    def switch_param(self, call: types.CallbackQuery):
        """
        Переключает переключаемые настройки FPC.
        """
        split = call.data.split(":")
        section, option = split[1], split[2]
        self.cardinal.MAIN_CFG[section][option] = "0" if self.cardinal.MAIN_CFG[section].getboolean(option) else "1"

        self.cardinal.save_config(self.cardinal.MAIN_CFG, "configs/_main.cfg")
        if section == "FunPay":
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                               reply_markup=keyboards.main_settings(self.cardinal))
        elif section == "Telegram":
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                               reply_markup=keyboards.notifications_settings(self.cardinal))
        elif section == "BlockList":
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                               reply_markup=keyboards.block_list_settings(self.cardinal))
        logger.info(f"Пользователь $MAGENTA{call.from_user.username} (id: {call.from_user.id})$RESET изменил параметр "
                    f"$CYAN{option}$RESET секции $YELLOW[{section}]$RESET "
                    f"основного конфига на $YELLOW{self.cardinal.MAIN_CFG[section][option]}$RESET.")
        self.bot.answer_callback_query(call.id)

    def open_settings_section(self, call: types.CallbackQuery):
        """
        Открывает выбранную категорию настроек.
        """
        section = call.data.split(":")[1]
        if section == "main":
            self.bot.edit_message_text("Здесь вы можете включить и отключать основные функции FPC.",
                                       call.message.chat.id, call.message.id,
                                       reply_markup=keyboards.main_settings(self.cardinal))
        elif section == "telegram":
            self.bot.edit_message_text("Здесь вы можете включить и отключать уведомления в Telegram.",
                                       call.message.chat.id, call.message.id,
                                       reply_markup=keyboards.notifications_settings(self.cardinal))
        elif section == "blockList":
            self.bot.edit_message_text("Здесь вы можете изменить настройки черного списка. "
                                       "Все ограничения, представленные ниже, "
                                       "применяются только к пользователям из ЧС.",
                                       call.message.chat.id, call.message.id,
                                       reply_markup=keyboards.block_list_settings(self.cardinal))
        elif section == "autoResponse":
            self.bot.edit_message_text("В данном разделе вы можете изменить существующие команды или добавить новые.",
                                       call.message.chat.id, call.message.id, reply_markup=keyboards.ar_settings())
        elif section == "autoDelivery":
            self.bot.edit_message_text("В данном разделе вы можете изменить настройки авто-выдачи, "
                                       "загрузить файлы с товарами и т.д.",
                                       call.message.chat.id, call.message.id, reply_markup=keyboards.ad_settings())
        self.bot.answer_callback_query(call.id)

    # Прочее
    def cancel_action(self, call: types.CallbackQuery):
        """
        Обнуляет состояние пользователя, удаляет сообщение, являющийся источником состояния.
        """
        result = self.clear_user_state(call.message.chat.id, call.from_user.id)
        if result is None:
            self.bot.answer_callback_query(call.id)
            return
        else:
            self.bot.delete_message(call.message.chat.id, call.message.id)
            self.bot.answer_callback_query(call.id)

    def __init_commands(self):
        """
        Регистрирует хэндлеры всех команд.
        """
        self.msg_handler(self.reg_admin, func=lambda msg: msg.from_user.id not in self.authorized_users)
        self.cbq_handler(self.ignore_unauthorized_users,
                         lambda call: call.from_user.id not in self.authorized_users)

        self.msg_handler(self.send_settings_menu, commands=["menu"])
        self.msg_handler(self.send_commands_help, commands=["commands"])
        self.msg_handler(self.act_manual_delivery_test, commands=["test_lot"])
        self.msg_handler(self.manual_delivery_text,
                         func=lambda m: self.check_state(m.chat.id, m.from_user.id, CBT.MANUAL_AD_TEST))
        self.msg_handler(self.switch_notifications, commands=["notifications"])
        self.msg_handler(self.act_ban, commands=["ban"])
        self.msg_handler(self.ban, func=lambda m: self.check_state(m.chat.id, m.from_user.id, CBT.BAN))
        self.msg_handler(self.act_unban, commands=["unban"])
        self.msg_handler(self.unban, func=lambda m: self.check_state(m.chat.id, m.from_user.id, CBT.UNBAN))
        self.msg_handler(self.send_ban_list, commands=["block_list"])
        self.msg_handler(self.send_logs, commands=["logs"])
        self.msg_handler(self.send_about_text, commands=["about"])
        self.msg_handler(self.send_system_info, commands=["sys"])
        self.msg_handler(self.restart_cardinal, commands=["restart"])
        self.msg_handler(self.ask_power_off, commands=["power_off"])

        self.cbq_handler(self.act_send_funpay_message, lambda c: c.data.startswith(f"{CBT.SEND_FP_MESSAGE}:"))
        self.msg_handler(self.send_funpay_message,
                         func=lambda m: self.check_state(m.chat.id, m.from_user.id, CBT.SEND_FP_MESSAGE))
        self.cbq_handler(self.ask_to_confirm_refund, lambda call: call.data.startswith(f"{CBT.REQUEST_REFUND}:"))
        self.cbq_handler(self.cancel_refund, lambda call: call.data.startswith(f"{CBT.REFUND_CANCELLED}:"))
        self.cbq_handler(self.refund, lambda call: call.data.startswith(f"{CBT.REFUND_CONFIRMED}:"))
        self.cbq_handler(self.open_cp, lambda call: call.data == CBT.MAIN)
        self.cbq_handler(self.open_settings_section, lambda call: call.data.startswith(f"{CBT.CATEGORY}:"))
        self.cbq_handler(self.switch_param, lambda call: call.data.startswith(f"{CBT.SWITCH}:"))
        self.cbq_handler(self.power_off, lambda call: call.data.startswith(f"{CBT.SHUT_DOWN}:"))
        self.cbq_handler(self.cancel_power_off, lambda call: call.data == CBT.CANCEL_SHUTTING_DOWN)
        self.cbq_handler(self.cancel_action, lambda c: c.data == CBT.CLEAR_USER_STATE)

    def send_notification(self, text: str, inline_keyboard=None, init_notification=False):
        """
        Отправляет сообщение во все чаты для уведомлений из self.chat_ids.

        :param text: текст уведомления.

        :param inline_keyboard: экземпляр клавиатуры.

        :param init_notification: это уведомление о старте Telegram-бота?
        """
        for chat_id in self.chat_ids:
            try:
                if inline_keyboard is None:
                    new_msg = self.bot.send_message(chat_id, text, parse_mode='HTML')
                else:
                    new_msg = self.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=inline_keyboard)

                if init_notification:
                    self.init_messages.append((new_msg.chat.id, new_msg.id))
            except:
                logger.error("Произошла ошибка при отправке уведомления в Telegram.")
                logger.debug(traceback.format_exc())
                continue

    def add_command(self, plugin_name: str, command: str, help_text: str) -> None:
        """
        Добавляет команду в список команд.

        :param plugin_name: имя плагина (лучше всего использовать переменную __name__).

        :param command: текст команды.

        :param help_text: текст справки.
        """
        if self.commands.get(plugin_name) is None:
            self.commands[plugin_name] = {}

        self.commands[plugin_name][command] = help_text

    def setup(self):
        """
        Устанавливает меню команд.
        """
        commands = []

        for module in self.commands:
            for command in self.commands[module]:
                commands.append(types.BotCommand(f"/{command}", self.commands[module][command]))
        self.bot.set_my_commands(commands)

    def init(self):
        self.__init_commands()
        self.setup()
        logger.info("$MAGENTATelegram бот инициализирован.")

    def run(self):
        """
        Запускает поллинг.
        """
        self.send_notification("""✅ Telegram-бот запущен!

✅ Сейчас вы уже <b><u>можете настраивать конфиги</u></b> и полностью <b><u>использовать функционал <i>Telegram</i>-бота</u></b>.

❌ Учтите, что <i>FunPay Cardinal</i> еще <b><u>не инициализирован</u></b> и <b><u>никакие функции не работают</u></b>.

🔃 Как только <i>FunPay Cardinal</i> инициализируется - данное сообщение изменится.

📋 Если <i>FPC</i> долго не инициализируется - проверьте логи с помощью команды /logs""", init_notification=True)
        try:
            logger.info(f"$CYANTelegram бот $YELLOW@{self.bot.user.username} $CYANзапущен.")
            self.bot.infinity_polling(logger_level=logging.DEBUG)
        except:
            logger.error("Произошла ошибка при получении обновлений Telegram (введен некорректный токен?).")
            logger.debug(traceback.format_exc())
