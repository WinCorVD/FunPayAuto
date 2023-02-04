"""
В данном модуле описаны функции для ПУ конфига авто-выдачи.
Модуль реализован в виде плагина.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from telegram import telegram_tools as tg_tools, keyboards
from telebot.types import InlineKeyboardButton as Button
from telebot import types

from Utils import cardinal_tools

import traceback
import itertools
import random
import string
import logging
import os


logger = logging.getLogger("TGBot")


def init_auto_delivery_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    # Основное меню настроек авто-выдачи.
    def open_lots_list(c: types.CallbackQuery):
        """
        Открывает список лотов с авто-выдачей.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"Выберите интересующий вас лот.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.lots_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def open_funpay_lots_list(c: types.CallbackQuery):
        """
        Открывает список лотов FunPay.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"""Выберите интересующий вас лот (все лоты получена напрямую с вашей страницы FunPay).

Учтите, что при обновлении списка лотов, <b><u>информация о лотах и категориях обновляется во всем Кардинале</u></b> """
                              """(это повлияет на авто-поднятие, авто-восстановление и авто-деактивацию).

"""
                              f"""Время последнего обновления: """
                              f"""<code>{cardinal.last_info_update.strftime("%d.%m.%Y %H:%M:%S")}</code>""",
                              c.message.chat.id, c.message.id,
                              parse_mode="HTML", reply_markup=keyboards.funpay_lots_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def act_add_lot(c: types.CallbackQuery):
        """
        Активирует режим добавления нового лота для авто-выдачи.
        """
        result = bot.send_message(c.message.chat.id, "Скопируйте название лота с FunPay и отправьте его мне.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "add_lot")
        bot.answer_callback_query(c.id)

    def add_lot(m: types.Message):
        """
        Добавляет новый лот для авто-выдачи.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        lot = m.text.strip()
        if lot in cardinal.AD_CFG.sections():
            bot.send_message(m.chat.id,
                             f"❌ Лот <code>{tg_tools.format_text(lot)}</code> уже есть в конфиге авто-выдачи.",
                             parse_mode="HTML")
            return

        cardinal.AD_CFG.add_section(lot)
        cardinal.AD_CFG.set(lot, "response", """Спасибо за покупку, $username!

Вот твой товар:
$product""")
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        lot_number = len(cardinal.AD_CFG.sections()) - 1
        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("✏️ Редактировать лот", callback_data=f"edit_lot:{lot_number}:0"))

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET добавил секцию "
                    f"$YELLOW[{lot}]$RESET в конфиг авто-выдачи.")
        bot.send_message(m.chat.id, f"✅ Добавлена новая секция <code>{tg_tools.format_text(lot)}</code> в конфиг "
                                    f"авто-выдачи.", parse_mode="HTML", reply_markup=keyboard)

    def open_products_files_list(c: types.CallbackQuery):
        """
        Открывает список файлов с товарами.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text("Выберите интересующий вас файл с товарами.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.products_files_list(offset))
        bot.answer_callback_query(c.id)

    def act_create_product_file(c: types.CallbackQuery):
        """
        Активирует режим создания нового файла для товаров.
        """
        result = bot.send_message(c.message.chat.id, "Введите название для нового файла с товарами "
                                                     "(можно без <code>.txt</code>).\n\n",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "create_products_file")
        bot.answer_callback_query(c.id)

    def create_products_file(m: types.Message):
        """
        Создает новый файл для товаров.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        file_name = m.text.strip()
        if not file_name:
            bot.send_message(m.chat.id, "❌ Необходимо ввести название файла.")
            return
        if not file_name.endswith(".txt"):
            file_name += ".txt"

        if os.path.exists(f"storage/products/{file_name}"):
            file_number = os.listdir("storage/products").index(file_name)
            keyboard = types.InlineKeyboardMarkup()\
                .add(Button("✏️ Редактировать файл", callback_data=f"products_file:{file_number}:0"))
            bot.send_message(m.chat.id,
                             f"❌ Файл <code>storage/products/{tg_tools.format_text(file_name)}</code> уже существует.",
                             parse_mode="HTML", reply_markup=keyboard)
            return

        with open(f"storage/products/{file_name}", "w", encoding="utf-8"):
            pass
        file_number = os.listdir("storage/products").index(file_name)
        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("✏️ Редактировать файл", callback_data=f"products_file:{file_number}:0"))
        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET создал файл для товаров "
                    f"$YELLOWstorage/products/{file_name}$RESET.")
        bot.send_message(m.chat.id, f"✅ Файл <code>storage/products/{tg_tools.format_text(file_name)}</code> создан.",
                         parse_mode="HTML", reply_markup=keyboard)

    # Меню настройки лотов.
    def open_edit_lot_cp(c: types.CallbackQuery):
        """
        Открывает панель редактирования авто-выдачи лота.
        """
        split = c.data.split(":")
        lot_number, offset = int(split[1]), int(split[2])
        keyboard = keyboards.edit_lot(cardinal, lot_number, offset)
        if not keyboard:
            bot.edit_message_text("❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        lot_obj = cardinal.AD_CFG[lot]

        bot.edit_message_text(tg_tools.generate_lot_info_text(lot, lot_obj),
                              c.message.chat.id, c.message.id, parse_mode="HTML",
                              reply_markup=keyboards.edit_lot(cardinal, lot_number, offset))
        bot.answer_callback_query(c.id)

    def act_edit_lot_response(c: types.CallbackQuery):
        """
        Активирует режим изменения текста выдачи.
        """
        result = bot.send_message(c.message.chat.id, "Введите новый текст выдачи товара.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        lot_number = c.data.split(":")[1]
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "edit_lot_response",
                          {"lot_number": int(lot_number)})
        bot.answer_callback_query(c.id)

    def edit_lot_response(m: types.Message):
        """
        Изменяет текст выдачи.
        """
        lot_number = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["lot_number"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if lot_number > len(cardinal.AD_CFG.sections()) - 1:
            bot.send_message(m.chat.id, "❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.")
            return

        new_response = m.text.strip()
        lot = cardinal.AD_CFG.sections()[lot_number]
        lot_obj = cardinal.AD_CFG[lot]

        if lot_obj.get("productsFileName") is not None and "$product" not in new_response:
            bot.send_message(m.chat.id, f"❌ К лоту <code>[{tg_tools.format_text(lot)}]</code> привязан файл с "
                                        f"товарами, однако в тексте ответа нет переменной <code>$product</code>.",
                             parse_mode="HTML")
            return

        cardinal.AD_CFG.set(lot, "response", new_response)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET изменил текст выдачи "
                    f"лота $YELLOW[{lot}]$RESET на $YELLOW\"{new_response}\"$RESET.")
        bot.send_message(m.chat.id, f"✅ Ответ для лота <code>{tg_tools.format_text(lot)}</code> изменен на "
                                    f"<code>{tg_tools.format_text(new_response)}</code>"
                                    "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ ЛОТА!</u></b>", parse_mode="HTML")

    def act_link_products_file(c: types.CallbackQuery):
        """
        Активирует режим привязки файла с товарами к лоту.
        """
        result = bot.send_message(c.message.chat.id, "Введите название файла с товарами.\nЕсли вы хотите отвязать файл "
                                                     "с товарами, отправьте <code>-</code>\n\n"
                                                     "Если файла не существует, он будет создан автоматически.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        lot_number = c.data.split(":")[1]
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "link_products_file",
                          {"lot_number": int(lot_number)})
        bot.answer_callback_query(c.id)

    def link_products_file(m: types.Message):
        """
        Привязывает файл с товарами к лоту.
        """
        lot_number = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["lot_number"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if lot_number > len(cardinal.AD_CFG.sections()) - 1:
            bot.send_message(m.chat.id, "❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.")
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        lot_obj = cardinal.AD_CFG[lot]
        file_name = m.text.strip()
        exists = 1

        if "$product" not in lot_obj.get("response") and file_name != "":
            bot.send_message(m.chat.id, "❌ Невозможно привязать файл с товарами, т.к. в тексте ответа "
                                        "отсутствует переменная <code>$product</code>.", parse_mode="HTML")
            return

        if file_name == "-":
            cardinal.AD_CFG.remove_option(lot, "productsFileName")
            cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET отвязал файл с товарами от "
                f"лота $YELLOW[{lot}]$RESET.")
            bot.send_message(m.chat.id, f"✅ Файл с товарами "
                                        f"успешно отвязан от лота <code>{tg_tools.format_text(lot)}</code>."
                                        "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ ЛОТА!</u></b>",
                             parse_mode="HTML")
            return
        if not file_name.endswith(".txt"):
            file_name += ".txt"

        if not os.path.exists(f"storage/products/{file_name}"):
            exists = 0
            with open(f"storage/products/{file_name}", "w", encoding="utf-8") as f:
                pass

        cardinal.AD_CFG.set(lot, "productsFileName", file_name)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        if exists:
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET привязал файл с товарами "
                f"$YELLOWstorage/products/{file_name}$RESET к лоту $YELLOW[{lot}]$RESET.")
            bot.send_message(m.chat.id, f"✅ Файл с товарами "
                                        f"<code>storage/products/{tg_tools.format_text(file_name)}</code> "
                                        f"успешно привязан к лоту <code>{tg_tools.format_text(lot)}</code>."
                                        "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ ЛОТА!</u></b>",
                             parse_mode="HTML")
        else:
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET создал и привязал файл с "
                f"товарами $YELLOWstorage/products/{file_name}$RESET к лоту $YELLOW[{lot}]$RESET.")
            bot.send_message(m.chat.id, f"✅ Файл с товарами "
                                        f"<code>storage/products/{tg_tools.format_text(file_name)}</code> "
                                        f"успешно <b><u>создан</u></b> и привязан к лоту "
                                        f"<code>{tg_tools.format_text(lot)}</code>."
                                        "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ ЛОТА!</u></b>",
                             parse_mode="HTML")

    def switch_lot_setting(c: types.CallbackQuery):
        """
        Переключает переключаемые параметры лота.
        """
        split = c.data.split(":")
        param, lot_number, offset = split[1], int(split[2]), int(split[3])
        if lot_number > len(cardinal.AD_CFG.sections()) - 1:
            bot.edit_message_text("❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        lot_obj = cardinal.AD_CFG[lot]
        if lot_obj.get(param) in [None, "0"]:
            value = "1"
        else:
            value = "0"
        cardinal.AD_CFG.set(lot, param, value)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET изменил параметр $CYAN{param}$RESET "
            f"секции $YELLOW[{lot}]$RESET на $YELLOW{value}$RESET.")
        bot.edit_message_text(tg_tools.generate_lot_info_text(lot, lot_obj),
                              c.message.chat.id, c.message.id, parse_mode="HTML",
                              reply_markup=keyboards.edit_lot(cardinal, lot_number, offset))
        bot.answer_callback_query(c.id)

    def create_lot_delivery_test(c: types.CallbackQuery):
        """
        Создает комбинацию [ключ: название лота] для теста авто-выдачи.
        :param c:
        :return:
        """
        lot_number = int(c.data.split(":")[1])

        if lot_number > len(cardinal.AD_CFG.sections()) - 1:
            bot.edit_message_text("❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        lot_name = cardinal.AD_CFG.sections()[lot_number]

        simbols = string.ascii_letters + "0123456789"
        key = "".join(random.choice(simbols) for _ in range(50))

        cardinal.delivery_tests[key] = lot_name

        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET создал одноразовый ключ для "
            f"авто-выдачи лота $YELLOW[{lot_name}]$RESET: $CYAN{key}$RESET.")
        bot.send_message(c.message.chat.id, f"✅ Одноразовый ключ для теста авто-выдачи лота "
                                            f"<b>[</b><code>{tg_tools.format_text(lot_name)}</code><b>]</b> "
                                            f"успешно создан. \n\n"
                                            f"Для теста авто-выдачи введите команду снизу в любой чат FunPay (ЛС).\n\n"
                                            f"<code>!автовыдача {key}</code>", parse_mode="HTML")
        bot.answer_callback_query(c.id)

    def del_lot(c: types.CallbackQuery):
        """
        Удаляет лот из конфига.
        """
        split = c.data.split(":")
        lot_number, offset = int(split[1]), int(split[2])

        if lot_number > len(cardinal.AD_CFG.sections()) - 1:
            bot.edit_message_text("❌ Не удалось обнаружить искомый лот. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id)
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        cardinal.AD_CFG.remove_section(lot)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET удалил секцию "
            f"$YELLOW[{lot}]$RESET из конфига авто-выдачи.")
        bot.edit_message_text(f"Выберите интересующий вас лот.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.lots_list(cardinal, 0))
        bot.answer_callback_query(c.id)

    # Меню добавления лота с FunPay
    def update_funpay_lots_list(c: types.CallbackQuery):
        offset = int(c.data.split(":")[1])
        new_msg = bot.send_message(c.message.chat.id,
                                   "Обновляю данные о лотах и категориях (это может занять некоторое время)...")
        bot.answer_callback_query(c.id)
        result = cardinal.update_lots_and_categories()
        if not result:
            bot.edit_message_text("❌ Не удалось обновить данные о лотах и категориях. "
                                  "Подробнее в файле <code>logs/log.log</code>.", new_msg.chat.id, new_msg.id,
                                  parse_mode="HTML")
            return
        bot.delete_message(new_msg.chat.id, new_msg.id)
        bot.edit_message_text(f"""Выберите интересующий вас лот (все лоты получена напрямую с вашей страницы FunPay).

Учтите, что при обновлении списка лотов, <b><u>информация о лотах и категориях обновляется во всем Кардинале</u></b> """
                              """(это повлияет на авто-поднятие, авто-восстановление и авто-деактивацию).

"""
                              f"""Время последнего обновления: """
                              f"""<code>{cardinal.last_info_update.strftime("%d.%m.%Y %H:%M:%S")}</code>""",
                              c.message.chat.id, c.message.id,
                              parse_mode="HTML", reply_markup=keyboards.funpay_lots_list(cardinal, offset))

    def add_funpay_lot(c: types.CallbackQuery):
        lot_number = int(c.data.split(":")[1])

        if lot_number > len(cardinal.telegram_lots) - 1:
            bot.send_message("❌ Не удалось обнаружить искомый лот в памяти Кардинала. Обновите список лотов.",
                             c.message.chat.id)
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.telegram_lots[lot_number]
        if lot.title in cardinal.AD_CFG.sections():
            bot.send_message(c.message.chat.id,
                             f"❌ Лот <code>{tg_tools.format_text(lot.title)}</code> уже есть в конфиге авто-выдачи.",
                             parse_mode="HTML")
            bot.answer_callback_query(c.id)
            return

        cardinal.AD_CFG.add_section(lot.title)
        cardinal.AD_CFG.set(lot.title, "response", """Спасибо за покупку, $username!

Вот твой товар:
$product""")
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        lot_number = len(cardinal.AD_CFG.sections()) - 1
        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("✏️ Редактировать лот", callback_data=f"edit_lot:{lot_number}:0"))

        logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET добавил секцию "
                    f"$YELLOW[{lot.title}]$RESET в конфиг авто-выдачи.")
        bot.send_message(c.message.chat.id,
                         f"✅ Добавлена новая секция <code>{tg_tools.format_text(lot.title)}</code> в конфиг "
                         f"авто-выдачи.", parse_mode="HTML", reply_markup=keyboard)
        bot.answer_callback_query(c.id)

    # Меню управления файлов с товарами.
    def open_products_file_action(c: types.CallbackQuery):
        """
        Открывает панель управления файлом с товарами.
        """
        split = c.data.split(":")
        file_number, offset = int(split[1]), int(split[2])
        files = os.listdir("storage/products")
        files = [i for i in files if i.endswith(".txt")]
        if file_number > len(files)-1:
            bot.edit_message_text(f"❌ Искомый файл не обнаружен. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id, parse_mode="HTML")
            bot.answer_callback_query(c.id)
            return
        file_name = files[file_number]

        products_amount = cardinal_tools.get_products_count(f"storage/products/{file_name}")
        delivery_objs = [i for i in cardinal.AD_CFG.sections() if
                         cardinal.AD_CFG[i].get("productsFileName") == file_name]

        text = f"""<b><u>{file_name}</u></b>
        
<b><i>Товаров в файле:</i></b>  <code>{products_amount}</code>

<b><i>Используется в лотах:</i></b> {", ".join(f"<code>{tg_tools.format_text(i)}</code>" for i in delivery_objs)}

<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
        bot.edit_message_text(text, c.message.chat.id, c.message.id,
                              reply_markup=keyboards.products_file_edit(file_number, offset),
                              parse_mode="HTML")
        bot.answer_callback_query(c.id)

    def act_add_products_to_file(c: types.CallbackQuery):
        """
        Активирует режим добавления товаров в файл с товарами.
        """
        result = bot.send_message(c.message.chat.id, "Отправьте товары, которые вы хотите "
                                  "добавить. Каждый товар должен быть с новой строки",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        file_number = int(c.data.split(":")[1])
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "add_products_to_file",
                          {"file_number": file_number})
        bot.answer_callback_query(c.id)

    def add_products_to_file(m: types.Message):
        """
        Добавляет товары в файл с товарами.
        """
        file_number = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["file_number"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        products = m.text.strip()

        files = os.listdir("storage/products")
        files = [i for i in files if i.endswith(".txt")]
        if file_number > len(files) - 1:
            bot.edit_message_text(f"❌ Искомый файл не обнаружен. Обновите меню авто-выдачи.",
                                  m.chat.id, m.id, parse_mode="HTML")
            return
        file_name = files[file_number]

        products = list(itertools.filterfalse(lambda el: not el, products.split("\n")))
        if not products:
            bot.send_message(m.chat.id, "❌ Товары не обнаружены.")
            return
        products_text = "\n".join(products)
        with open(f"storage/products/{file_name}", "a", encoding="utf-8") as f:
            f.write("\n")
            f.write(products_text)

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET добавил "
                    f"$CYAN{len(products)}$RESET товар(-a, -oв) в файл $YELLOWstorage/products/{file_name}$RESET.")
        bot.send_message(m.chat.id,
                         f"✅ В файл <code>storage/products/{file_name}</code> добавлен(-о) "
                         f"<code>{len(products)}</code> товар(-а / -ов)."
                         "\n\n<b><u>ОБНОВИТЕ СООБЩЕНИЕ С НАСТРОЙКАМИ ФАЙЛА С ТОВАРАМИ!</u></b>",
                         parse_mode="HTML")

    def send_products_file(c: types.CallbackQuery):
        """
        Отправляет файл с товарами.
        """
        file_number = int(c.data.split(":")[1])
        files = os.listdir("storage/products")
        files = [i for i in files if i.endswith(".txt")]
        if file_number > len(files) - 1:
            bot.send_message(c.message.chat.id, f"❌ Искомый файл не обнаружен. Обновите меню авто-выдачи.")
            return
        file_name = files[file_number]

        with open(f"storage/products/{file_name}", "r", encoding="utf-8") as f:
            logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET запросил "
                        f"файл с товарами $YELLOWstorage/products/{file_name}$RESET.")
            bot.send_document(c.message.chat.id, f)
            bot.answer_callback_query(c.id)

    def ask_del_products_file(c: types.CallbackQuery):
        """
        Открывает суб-панель подтверждения удаления файла с товарами.
        """
        split = c.data.split(":")
        file_number, offset = int(split[1]), int(split[2])
        files = os.listdir("storage/products")
        files = [i for i in files if i.endswith(".txt")]
        if file_number > len(files) - 1:
            bot.edit_message_text(f"❌ Искомый файл не обнаружен. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id, parse_mode="HTML")
            tg.answer_callback_query(c.id)
            return
        bot.edit_message_reply_markup(c.message.chat.id, c.message.id,
                                      reply_markup=keyboards.products_file_edit(file_number, offset, True))
        bot.answer_callback_query(c.id)

    def del_products_file(c: types.CallbackQuery):
        """
        Удаляет файл с товарами.
        """
        split = c.data.split(":")
        file_number, offset = int(split[1]), int(split[2])
        files = os.listdir("storage/products")
        files = [i for i in files if i.endswith(".txt")]
        if file_number > len(files) - 1:
            bot.edit_message_text(f"❌ Искомый файл не обнаружен. Обновите меню авто-выдачи.",
                                  c.message.chat.id, c.message.id, parse_mode="HTML")
            tg.answer_callback_query(c.id)
            return
        file_name = files[file_number]

        delivery_objs = [i for i in cardinal.AD_CFG.sections() if
                         cardinal.AD_CFG[i].get("productsFileName") == file_name]

        if delivery_objs:
            bot.send_message(c.message.chat.id,
                             f"❌ Файл <code>storage/products/{file_name}</code> используется в конфиге авто-выдачи.\n"
                             "Для начала необходимо удалить все лоты, которые используют этот файл с товарами, "
                             "из конфига авто-выдачи.", parse_mode="HTML")
            bot.answer_callback_query(c.id)
            return
        try:
            os.remove(f"storage/products/{file_name}")
            bot.edit_message_text(f"Выберите интересующий вас файл с товарами.",
                                  c.message.chat.id, c.message.id,
                                  reply_markup=keyboards.products_files_list(offset))
            logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET удалил "
                        f"файл с товарами $YELLOWstorage/products/{file_name}$RESET.")
            bot.answer_callback_query(c.id)
        except:
            bot.send_message(f"❌ Не удалось удалить файл <code>storage/products/{file_name}</code>. "
                             f"Подробнее в файле logs/log.log.")
            bot.answer_callback_query(c.id)
            logger.debug(traceback.format_exc())
            return

    # Основное меню настроек авто-выдачи.
    tg.cbq_handler(open_lots_list, func=lambda c: c.data.startswith("lots:"))
    tg.cbq_handler(open_funpay_lots_list, func=lambda c: c.data.startswith("funpay_lots:"))
    tg.cbq_handler(act_add_lot, func=lambda c: c.data == "add_lot")
    tg.msg_handler(add_lot, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "add_lot"))

    tg.cbq_handler(open_products_files_list, func=lambda c: c.data.startswith("products_files:"))

    tg.cbq_handler(act_create_product_file, func=lambda c: c.data == "create_products_file")
    tg.msg_handler(create_products_file, func=lambda m: tg.check_state(m.chat.id, m.from_user.id,
                                                                       "create_products_file"))

    # Меню настройки лотов.
    tg.cbq_handler(open_edit_lot_cp, func=lambda c: c.data.startswith("edit_lot:"))

    tg.cbq_handler(act_edit_lot_response, func=lambda c: c.data.startswith("edit_lot_response:"))
    tg.msg_handler(edit_lot_response, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "edit_lot_response"))

    tg.cbq_handler(act_link_products_file, func=lambda c: c.data.startswith("link_products_file:"))
    tg.msg_handler(link_products_file, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "link_products_file"))

    tg.cbq_handler(switch_lot_setting, func=lambda c: c.data.startswith("switch_lot:"))
    tg.cbq_handler(create_lot_delivery_test, func=lambda c: c.data.startswith("test_auto_delivery:"))
    tg.cbq_handler(del_lot, func=lambda c: c.data.startswith("del_lot:"))

    # Меню добавления лота с FunPay
    tg.cbq_handler(add_funpay_lot, func=lambda c: c.data.startswith("add_funpay_lot:"))
    tg.cbq_handler(update_funpay_lots_list, func=lambda c: c.data.startswith("update_funpay_lots:"))

    # Меню управления файлов с товарами.
    tg.cbq_handler(open_products_file_action, func=lambda c: c.data.startswith("products_file:"))

    tg.cbq_handler(act_add_products_to_file, func=lambda c: c.data.startswith("add_products_to_file:"))
    tg.msg_handler(add_products_to_file,
                   func=lambda m: tg.check_state(m.chat.id, m.from_user.id, "add_products_to_file"))

    tg.cbq_handler(send_products_file, func=lambda c: c.data.startswith("download_products_file:"))
    tg.cbq_handler(ask_del_products_file, func=lambda c: c.data.startswith("del_products_file:"))
    tg.cbq_handler(del_products_file, func=lambda c: c.data.startswith("confirm_del_products_file:"))


REGISTER_TO_POST_INIT = [init_auto_delivery_cp]
