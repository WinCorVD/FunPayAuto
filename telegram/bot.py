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

from telegram import telegram_tools as tg_tools, keyboards
from Utils import cardinal_tools


logger = logging.getLogger("TGBot")


class TGBot:
    def __init__(self, cardinal: Cardinal):
        self.cardinal = cardinal
        self.bot = telebot.TeleBot(self.cardinal.MAIN_CFG["Telegram"]["token"])

        self.authorized_users = tg_tools.load_authorized_users()
        self.chat_ids = tg_tools.load_chat_ids()

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
                "commands": "получить справку по командам",
                "test_lot": "создать ключ для теста авто-выдачи",
                "add_chat": "вкл. уведомления в этом чате",
                "remove_chat": "выкл. уведомления в этот чат",
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

    def msg_handler(self, handler, **args):
        """
        Регистрирует хэндлер, срабатывающий при новом сообщении.

        :param handler: хэндлер.

        :param args: аргументы для хэндлера.
        """
        bot_instance = self.bot

        @bot_instance.message_handler(**args)
        def run_handler(message: types.Message):
            try:
                handler(message)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера Telegram бота. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    def cbq_handler(self, handler, **args):
        """
        Регистрирует хэндлер, срабатывающий при новом callback'е.

        :param handler: хэндлер.

        :param args: аргументы для хэндлера.
        """
        bot_instance = self.bot

        @bot_instance.callback_query_handler(**args)
        def run_handler(call: types.CallbackQuery):
            try:
                handler(call)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера Telegram бота. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    # Команды бота
    def reg_admin(self, message: types.Message):
        """
        Проверяет, есть ли пользователь в списке пользователей с доступом к ПУ TG.
        """
        if message.chat.type != "private":
            return
        if message.text == self.cardinal.MAIN_CFG["Telegram"]["secretKey"]:
            self.authorized_users.append(message.from_user.id)
            tg_tools.save_authorized_users(self.authorized_users)
            text = f"""⭐️ Та-даааам! Теперь я тебе доверяю.

Учти, что пока что я никуда <b><u>не отправляю уведомления</u></b>.
Если нужно, что бы я присылал уведомления в этот чат, <b><u>введи команду</u></b> /add_chat."""
            logger.warning(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                           "ПОЛУЧИЛ ДОСТУП К ПУ TG!")

        else:
            text = f"""👋 Привет, <b><i>{message.from_user.username}</i></b>!
🫤 Похоже, ты неавторизованный пользователь.

🔑 Отправь мне <u><b>секретный пароль</b></u> который ты ввел в моих настройках, что бы начать работу 🙂"""
            logger.warning(f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET "
                           f"попытался получить доступ к ПУ TG. Сдерживаю его как могу!")
        self.bot.send_message(message.chat.id, text, parse_mode="HTML")

    @staticmethod
    def ignore_unauthorized_users(call: types.CallbackQuery):
        """
        Игнорирует callback'и от не авторизированных пользователей.
        :param call:
        :return:
        """
        logger.warning(f"Пользователь $MAGENTA{call.from_user.username} (id {call.from_user.id})$RESET "
                       f"тыкает кнопки ПУ в чате $MAGENTA@{call.message.chat.username}"
                       f" (id {call.message.chat.id})$RESET. Сдерживаю его как могу!")
        return

    # Комманды
    def add_chat(self, message: types.Message):
        """
        Добавляет чат в список чатов для уведомлений.
        """
        if message.chat.id in self.chat_ids:
            self.bot.send_message(message.chat.id,  "❌ Данный чат уже находится в списке чатов для уведомлений.")
        else:
            self.chat_ids.append(message.chat.id)
            tg_tools.save_chat_ids(self.chat_ids)
            self.bot.send_message(message.chat.id, "🔔 Теперь в этот чат будут приходить уведомления.")

    def remove_chat(self, message: types.Message):
        """
        Удаляет чат из списка чатов для уведомлений.
        """
        if message.chat.id not in self.chat_ids:
            self.bot.send_message(message.chat.id, "❌ Данного чата нет в списке чатов для уведомлений.")
        else:
            self.chat_ids.remove(message.chat.id)
            tg_tools.save_chat_ids(self.chat_ids)
            self.bot.send_message(message.chat.id, "🔕 Теперь в этот чат не будут приходить уведомления.")

    def send_about_text(self, message: types.Message):
        """
        Отправляет текст о боте.
        """
        self.bot.send_message(message.chat.id, tg_tools.ABOUT_TEXT)

    def send_logs(self, message: types.Message):
        """
        Отправляет файл логов.
        """
        if not os.path.exists("logs/log.log"):
            self.bot.send_message(message.chat.id, "❌ Лог файл не обнаружен.")
        else:
            with open("logs/log.log", "r", encoding="utf-8") as f:
                self.bot.send_document(message.chat.id, f)

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
        keyboard = keyboards.power_off(self.cardinal.instance_id, 0)
        self.bot.send_message(msg.chat.id, """<b><u>Вы уверены, что хотите меня отключить?</u></b>

Включить бота через ПУ TG <b><u>НЕ ПОЛУЧИТСЯ!</u></b>""", reply_markup=keyboard, parse_mode="HTML")

    def power_off(self, call: types.CallbackQuery):
        """
        Отключает FPC.
        """
        split = call.data.split(":")
        state = int(split[1])
        instance_id = int(split[2])

        if instance_id != self.cardinal.instance_id:
            self.bot.edit_message_text("❌ Данная кнопка не принадлежит этому запуску бота.\nВызовите данное меню снова.",
                                       call.message.chat.id, call.message.id)
            self.bot.answer_callback_query(call.id)
            return

        if state == 6:
            self.bot.edit_message_text("Ладно, ладно, выключаюсь...", call.message.chat.id, call.message.id)
            cardinal_tools.shut_down()
            self.bot.answer_callback_query(call.id)

        texts = ["""На всякий случай спрошу еще раз.
        
<b><u>Вы точно уверены?</u></b>""",
                 """Просто для протокола.
                  
Вам придется логиниться на ваш дедик или подходить к компьютеру (или где еще я там у вас) и запускать меня вручную!""",

                 """Не то что бы я навязываюсь, но если вы хотите применить изменения в конфигах, вы можете 
просто перезапустить меня (кнопка так же есть в ПУ)...""",

                 """Вы вообще читаете мои сообщения? Проверим ка вас на внимательность. Да = Нет, а Нет = да. 
Уверен, вы даже не читаете мои сообщения, а ведь я дело говорю :(""",

                 "Ну то есть твердо и четко, дэ?"]

        self.bot.edit_message_text(texts[state - 1], call.message.chat.id, call.message.id,
                                   reply_markup=keyboards.power_off(instance_id, state), parse_mode="HTML")
        self.bot.answer_callback_query(call.id)

    def cancel_power_off(self, call: types.CallbackQuery):
        """
        Отменяет выключение (удаляет клавиатуру с кнопками подтверждения).
        :param call:
        :return:
        """
        self.bot.edit_message_text("Вот и славненько.", call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id)

    def send_commands_text(self, message: types.Message):
        try:
            self.bot.send_message(message.chat.id, self.generate_help_text())
        except:
            logger.error("Произошла ошибка в работе Telegram бота.")
            logger.debug(traceback.format_exc())

    def act_add_to_block_list(self, message: types.Message):
        """
        Активирует режим ввода никнейма пользователя, которого нужно добавить в ЧС.
        """
        result = self.bot.send_message(message.chat.id, "Введите имя пользователя, которого хотите внести в ЧС.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, "ban")

    def add_to_block_list(self, message: types.Message):
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

    def act_remove_from_block_list(self, message: types.Message):
        """
        Активирует режим ввода никнейма пользователя, которого нужно удалить из ЧС.
        """
        result = self.bot.send_message(message.chat.id, "Введите имя пользователя, которого хотите удалить в ЧС.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, "unban")

    def remove_from_block_list(self, message: types.Message):
        """
        Удаляет пользователя из ЧС.
        :param message:
        :return:
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

    def send_block_list(self, message: types.Message):
        """
        Отправляет ЧС.
        """
        if not self.cardinal.block_list:
            self.bot.send_message(message.chat.id, "❌ Черный список пуст.")
            return
        block_list = ", ".join(f"<code>{nickname}</code>" for nickname in self.cardinal.block_list)
        self.bot.send_message(message.chat.id, block_list, parse_mode="HTML")

    def act_create_lot_delivery_test_manual(self, message: types.Message):
        """
        Активирует режим ввода названия лота для ручной генерации ключа теста авто-выдачи.
        """
        result = self.bot.send_message(message.chat.id, "Введите название лота, тест авто-выдачи которого вы хотите "
                                                        "провести.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(message.chat.id, result.id, message.from_user.id, "test_auto_delivery_manual")

    def create_lot_delivery_test_manual(self, message: types.Message):
        """
        Генерирует ключ теста авто-выдачи (вручную).
        """
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        lot_name = message.text.strip()
        simbols = string.ascii_letters + "0123456789"
        key = "".join(random.choice(simbols) for _ in range(50))

        self.cardinal.delivery_tests[key] = lot_name

        logger.info(
            f"Пользователь $MAGENTA{message.from_user.username} (id: {message.from_user.id})$RESET создал "
            f"одноразовый ключ для авто-выдачи лота $YELLOW[{lot_name}]$RESET: $CYAN{key}$RESET.")

        self.bot.send_message(message.chat.id, f"✅ Одноразовый ключ для теста авто-выдачи лота "
                                               f"<b>[</b><code>{tg_tools.format_text(lot_name)}</code><b>]</b> "
                                               f"успешно создан. \n\n"
                                               f"Для теста авто-выдачи введите команду снизу в любой чат FunPay (ЛС)."
                                               f"\n\n<code>!автовыдача {key}</code>", parse_mode="HTML")

    # Чат FunPay
    def act_send_funpay_message(self, call: types.CallbackQuery):
        """
        Активирует режим ввода ссобщения для отправки его в чат FunPay.
        """
        node_id = int(call.data.split(":")[1])
        result = self.bot.send_message(call.message.chat.id, "Введите текст сообщения.",
                                       reply_markup=keyboards.CLEAR_STATE_BTN)
        self.set_user_state(call.message.chat.id, result.id, call.from_user.id,
                            "to_node", {"node": node_id})
        self.bot.answer_callback_query(call.id)

    def send_funpay_message(self, message: types.Message):
        """
        Отправляет сообщение в чат FunPay.
        """
        node_id = self.user_states[message.chat.id][message.from_user.id]["data"]["node"]
        self.clear_user_state(message.chat.id, message.from_user.id, True)
        response_text = message.text.strip()
        new_msg_obj = FunPayAPI.types.Message(response_text, node_id, None)
        try:
            result = self.cardinal.send_message(new_msg_obj)
            if result:
                self.bot.send_message(message.chat.id, "✅ Сообщение отправлено.")
            else:
                self.bot.send_message(message.chat.id, "❌ Не удалось отправить сообщение. Подробнее в файле logs/log.log")
        except:
            self.bot.send_message(message.chat.id, "❌ Не удалось отправить сообщение. Подробнее в файле logs/log.log")

    # Ордер
    def confirm_refund(self, call: types.CallbackQuery):
        """
        Просит подтвердить возврат денег.
        """
        order_id = call.data.split(":")[1]
        keyboard = types.InlineKeyboardMarkup()
        accept_button = Button(text="✅ Да", callback_data=f"refund_confirm:{order_id}")
        decline_button = Button(text="❌ Нет", callback_data=f"refund_cancel:{order_id}")
        open_order_button = Button(text="🌐 Открыть страницу заказа", url=f"https://funpay.com/orders/{order_id}/")

        keyboard.row(accept_button, decline_button)
        keyboard.add(open_order_button)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
        self.bot.answer_callback_query(call.id)

    def cancel_refund(self, call: types.CallbackQuery):
        """
        Отменяет возврат.
        """
        order_id = call.data.split(":")[1]
        keyboard = types.InlineKeyboardMarkup()
        refund_button = Button(text="💸 Вернуть деньги", callback_data=f"refund_request:{order_id}")
        open_order_button = Button(text="🌐 Открыть страницу заказа", url=f"https://funpay.com/orders/{order_id}/")

        keyboard.add(refund_button)
        keyboard.add(open_order_button)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
        self.bot.answer_callback_query(call.id)

    def refund(self, call: types.CallbackQuery):
        """
        Оформляет возврат за заказ.
        """
        order_id = call.data.split(":")[1]
        open_order_button = Button(text="🌐 Открыть страницу заказа", url=f"https://funpay.com/orders/{order_id}/")
        attempts = 3
        while attempts:
            try:
                self.cardinal.account.refund_order(order_id)
            except:
                logger.error(f"❌ Не удалось вернуть средства по заказу #{order_id}. Следующая попытка через 1 сек.")
                time.sleep(1)
                continue

            self.bot.send_message(call.message.chat.id, f"✅ Средства по заказу </code>#{order_id}</code> возвращены.",
                                  parse_mode="HTML")
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(open_order_button)
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
            self.bot.answer_callback_query(call.id)
            return

        self.bot.send_message(call.message.chat.id, f"❌ Не удалось вернуть средства по заказу <code>#{order_id}</code>.",
                              parse_mode="HTML")

        refund_button = Button(text="💸 Вернуть деньги", callback_data=f"refund_request:{order_id}")
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(refund_button).add(open_order_button)
        self.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)

    # Панель управления
    def switch_setting(self, call: types.CallbackQuery):
        """
        Переключает переключаемые настройки FPC.
        """
        split = call.data.split(":")
        section = split[1]
        option = split[2]
        value = int(self.cardinal.MAIN_CFG[section][option])
        new_value = "0" if value else "1"
        self.cardinal.MAIN_CFG[section][option] = new_value

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
                    f"основного конфига на $YELLOW{new_value}$RESET.")
        self.bot.answer_callback_query(call.id)

    def send_cp(self, message: types.Message):
        """
        Отправляет основное меню настроек (новым сообщением).
        """
        self.bot.send_message(message.chat.id, "Добро пожаловать в панель управления. Выберите категорию настроек.",
                              reply_markup=keyboards.settings_sections())

    def open_cp(self, call: types.CallbackQuery):
        """
        Открывает основное меню настроек (редактирует сообщение).
        """
        self.bot.edit_message_text("Добро пожаловать в панель управления. Выберите категорию настроек.",
                                   call.message.chat.id, call.message.id, reply_markup=keyboards.settings_sections())
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

    def send_system_info(self, msg: types.Message):
        """
        Отправляет информацию о нагрузке на систему.
        """
        current_time = int(time.time())
        run_time = current_time - self.cardinal.start_time
        days = int(run_time / 86400)
        hours = int((run_time - days * 86400) / 3600)
        minutes = int((run_time - days * 86400 - hours * 3600) / 60)
        seconds = run_time - days * 86400 - hours * 3600 - minutes * 60

        ram = psutil.virtual_memory()
        cpu_usage = "\n".join(f"    CPU {i}:  <code>{l}%</code>" for i, l in enumerate(psutil.cpu_percent(percpu=True)))
        self.bot.send_message(msg.chat.id, f"""<b><u>Сводка данных</u></b>
    
<b>ЦП:</b>
{cpu_usage}
    Используется ботом: <code>{psutil.Process().cpu_percent()}%</code>

<b>ОЗУ:</b>
    Всего:  <code>{int(ram.total / 1048576)} MB</code>
    Использовано:  <code>{int(ram.used / 1048576)} MB</code>
    Свободно:  <code>{int(ram.free / 1048576)} MB</code>
    Используется ботом:  <code>{int(psutil.Process().memory_info().rss / 1048576)} MB</code>

<b>Бот:</b>
    Аптайм:  <code>{days}д {hours}ч {minutes}мин {seconds}сек</code>
    Чат:  <code>{msg.chat.id}</code>""", parse_mode="HTML")

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
                         func=lambda call: call.from_user.id not in self.authorized_users)

        self.msg_handler(self.send_cp, commands=["menu"])
        self.msg_handler(self.send_commands_text, commands=["commands"])
        self.msg_handler(self.act_create_lot_delivery_test_manual, commands=["test_lot"])
        self.msg_handler(self.create_lot_delivery_test_manual,
                         func=lambda m: self.check_state(m.chat.id, m.from_user.id, "test_auto_delivery_manual"))
        self.msg_handler(self.add_chat, commands=["add_chat"])
        self.msg_handler(self.remove_chat, commands=["remove_chat"])
        self.msg_handler(self.act_add_to_block_list, commands=["ban"])
        self.msg_handler(self.add_to_block_list, func=lambda m: self.check_state(m.chat.id, m.from_user.id, "ban"))
        self.msg_handler(self.act_remove_from_block_list, commands=["unban"])
        self.msg_handler(self.remove_from_block_list,
                         func=lambda m: self.check_state(m.chat.id, m.from_user.id, "unban"))
        self.msg_handler(self.send_block_list, commands=["block_list"])
        self.msg_handler(self.send_logs, commands=["logs"])
        self.msg_handler(self.send_about_text, commands=["about"])
        self.msg_handler(self.send_system_info, commands=["sys"])
        self.msg_handler(self.restart_cardinal, commands=["restart"])
        self.msg_handler(self.ask_power_off, commands=["power_off"])

        self.cbq_handler(self.act_send_funpay_message, func=lambda c: c.data.startswith("to_node:"))
        self.msg_handler(self.send_funpay_message,
                         func=lambda m: self.check_state(m.chat.id, m.from_user.id, "to_node"))

        self.cbq_handler(self.confirm_refund, func=lambda call: call.data.startswith("refund_request:"))
        self.cbq_handler(self.cancel_refund, func=lambda call: call.data.startswith("refund_cancel:"))
        self.cbq_handler(self.refund, func=lambda call: call.data.startswith("refund_confirm:"))

        self.cbq_handler(self.open_cp, func=lambda call: call.data == "main_settings_page")
        self.cbq_handler(self.open_settings_section, func=lambda call: call.data.startswith("settings:"))
        self.cbq_handler(self.switch_setting, func=lambda call: call.data.startswith("switch:"))

        self.cbq_handler(self.power_off, func=lambda call: call.data.startswith("power_off:"))
        self.cbq_handler(self.cancel_power_off, func=lambda call: call.data.startswith("cancel_power_off"))

        self.cbq_handler(self.cancel_action, func=lambda c: c.data == "clear_state")

    def send_notification(self, text: str, inline_keyboard=None):
        """
        Отправляет сообщение во все чаты для уведомлений из self.chat_ids.

        :param text: текст уведомления.

        :param inline_keyboard: экземпляр клавиатуры.
        """
        for chat_id in self.chat_ids:
            try:
                if inline_keyboard is None:
                    self.bot.send_message(chat_id, text, parse_mode='HTML')
                else:
                    self.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=inline_keyboard)
            except:
                logger.error("Произошла ошибка при отправке уведомления в Telegram.")
                logger.debug(traceback.format_exc())

    def add_command_help(self, plugin_name: str, command: str, help_text: str) -> None:
        """
        Добавляет справку о команде.

        :param plugin_name: имя плагина (лучше всего использовать переменную __name__).

        :param command: текст команды.

        :param help_text: текст справки.
        """
        if self.commands.get(plugin_name) is None:
            self.commands[plugin_name] = {}

        self.commands[plugin_name][command] = help_text

    def generate_help_text(self) -> str:
        """
        Генерирует текст справки.
        :return: текст справки.
        """
        text = ""
        for module in self.commands:
            if not len(self.commands[module]):
                continue

            text += f"\n{module}\n"
            for command in self.commands[module]:
                text += f"    /{command} - {self.commands[module][command]}\n"

        return text.strip()

    def set_commands(self):
        """
        Устанавливает меню команд.
        """
        commands = []
        for module in self.commands:
            for command in self.commands[module]:
                commands.append(types.BotCommand(f"/{command}", self.commands[module][command]))
        self.bot.set_my_commands(commands)

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

    def init(self):
        self.__init_commands()
        self.set_commands()
        logger.info("$MAGENTATelegram бот инициализирован.")

    def run(self):
        """
        Запускает поллинг.
        """
        try:
            logger.info(f"$CYANTelegram бот $YELLOW@{self.bot.user.username} $CYANзапущен.")
            self.bot.infinity_polling(logger_level=logging.DEBUG)
        except:
            logger.error("Произошла ошибка при получении обновлений Telegram (введен некорректный токен?).")
            logger.debug(traceback.format_exc())
