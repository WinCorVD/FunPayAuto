"""
В данном модуле реализован загрузчик файлов из телеграм чата.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal
    from telegram.bot import TGBot

from telegram import telegram_tools as tg_tools, keyboards
from telebot.types import InlineKeyboardButton as Button
from Utils import config_loader as cfg_loader
from Utils import cardinal_tools
import Utils.exceptions as excs
from telebot import types
import traceback
import logging
import os


logger = logging.getLogger("TGBot")


def check_file(tg: TGBot, msg: types.Message) -> bool:
    """
    Проверяет выгруженный файл. Чистит состояние пользователя. Отправляет сообщение в TG в зависимости от ошибки.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :return: True, если все ок, False, если файл проверку не прошел.
    """
    tg.clear_user_state(msg.chat.id, msg.from_user.id, True)
    if not msg.document:
        tg.bot.send_message(msg.chat.id, "❌ Файл не обнаружен.")
        return False
    if not msg.document.mime_type == "text/plain":
        tg.bot.send_message(msg.chat.id, "❌ Файл должен быть текстовым.")
        return False
    if msg.document.file_size >= 20971520:
        tg.bot.send_message(msg.chat.id, "❌ Размер файла не должен превышать 20МБ.")
        return False
    return True


def download_file(tg: TGBot, msg: types.Message, file_name: str = "temp_file.txt") -> bool:
    """
    Скачивает выгруженный файл и сохраняет его в папку storage/cache/.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :param file_name: название сохраненного файла.

    :return: True, если все ок, False, при ошибке.
    """
    tg.bot.send_message(msg.chat.id, "⏬ Загружаю файл...")
    try:
        file_info = tg.bot.get_file(msg.document.file_id)
        file = tg.bot.download_file(file_info.file_path)
    except:
        tg.bot.send_message(msg.chat.id, "❌ Произошла ошибка при загрузке файла. Подробнее в файле "
                                         "<code>logs/log.log</code>.", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return False

    with open(f"storage/cache/{file_name}", "wb") as new_file:
        new_file.write(file)
    return True


def upload_products_file(cardinal: Cardinal, msg: types.Message):
    """
    Загружает файл с товарами.

    :param cardinal: экземпляр кардинала.

    :param msg: экземпляр сообщения.
    """
    tg = cardinal.telegram
    bot = tg.bot
    if not check_file(tg, msg):
        return
    if not download_file(tg, msg, "temp_products_file.txt"):
        return

    bot.send_message(msg.chat.id, "🔁 Проверяю валидность файла...")
    try:
        with open("storage/cache/temp_products_file.txt", "r", encoding="utf-8") as f:
            text = f.read()
    except:
        bot.send_message(msg.chat.id,
                         "❌ Произошла ошибка при обработке файла с товарами. Подробнее в файле "
                         "<code>logs/log.log</code>.", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return

    try:
        products_count = cardinal_tools.get_products_count("storage/cache/temp_products_file.txt")
        file_name = msg.document.file_name
        with open(f"storage/products/{file_name}", "w", encoding="utf-8") as f:
            f.write(text)
    except:
        bot.send_message(msg.chat.id,
                         "❌ Произошла ошибка при сохранении файла с товарами. Подробнее в файле "
                         "<code>logs/log.log</code>.", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return
    file_number = os.listdir("storage/products").index(file_name)
    keyboard = types.InlineKeyboardMarkup() \
        .add(Button("✏️ Редактировать файл", callback_data=f"products_file:{file_number}:0"))
    logger.info(f"Пользователь $MAGENTA{msg.from_user.username} (id: {msg.from_user.id})$RESET "
                f"загрузил в бота файл с товарами $YELLOWstorage/products/{file_name}$RESET.")
    bot.send_message(msg.chat.id,
                     f"✅ Файл с товарами <code>storage/products/{file_name}</code> успешно загружен. "
                     f"Товаров в файле: <code>{products_count}.</code>",
                     parse_mode="HTML", reply_markup=keyboard)


def upload_auto_response_config(cardinal: Cardinal, msg: types.Message):
    """
    Загружает, проверяет и устанавливает конфиг авто-выдачи.

    :param cardinal: экземпляр кардинала.

    :param msg: экземпляр сообщения.
    """
    tg = cardinal.telegram
    bot = tg.bot
    if not check_file(tg, msg):
        return
    if not download_file(tg, msg, "temp_auto_response.cfg"):
        return

    bot.send_message(msg.chat.id, "🔁 Проверяю валидность файла...")
    try:
        new_config = cfg_loader.load_auto_response_config("storage/cache/temp_auto_response.cfg")
        raw_new_config = cfg_loader.load_raw_auto_response_config("storage/cache/temp_auto_response.cfg")
    except excs.ConfigParseError as e:
        bot.send_message(msg.chat.id, f"❌ Произошла ошибка при обработке конфига авто-выдачи: "
                                      f"<code>{tg_tools.format_text(str(e))}</code>", parse_mode="HTML")
        return
    except UnicodeDecodeError:
        bot.send_message(msg.chat.id, "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                                      "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                         parse_mode="HTML")
        return
    except:
        bot.send_message(msg.chat.id,
                         "❌ Произошла ошибка при проверке конфига авто-выдачи. Подробнее в файле "
                         "<code>logs/log.log</code>", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return

    cardinal.RAW_AR_CFG = raw_new_config
    cardinal.AR_CFG = new_config
    cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")
    logger.info(f"Пользователь $MAGENTA{msg.from_user.username} (id: {msg.from_user.id})$RESET "
                f"загрузил в бота и установил конфиг авто-ответчика.")
    bot.send_message(msg.chat.id, "✅ Конфиг авто-ответчика успешно применен.")


def upload_auto_delivery_config(cardinal: Cardinal, msg: types.Message):
    """
    Загружает, проверяет и устанавливает конфиг авто-выдачи.

    :param cardinal: экземпляр кардинала.

    :param msg: экземпляр сообщения.
    """
    tg = cardinal.telegram
    bot = tg.bot
    if not check_file(tg, msg):
        return
    if not download_file(tg, msg, "temp_auto_delivery.cfg"):
        return

    bot.send_message(msg.chat.id, "🔁 Проверяю валидность файла...")
    try:
        new_config = cfg_loader.load_auto_delivery_config("storage/cache/temp_auto_delivery.cfg")
    except excs.ConfigParseError as e:
        bot.send_message(msg.chat.id, f"❌ Произошла ошибка при обработке конфига авто-выдачи: "
                                      f"<code>{tg_tools.format_text(str(e))}</code>", parse_mode="HTML")
        return
    except UnicodeDecodeError:
        bot.send_message(msg.chat.id, "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                                      "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                         parse_mode="HTML")
        return
    except:
        bot.send_message(msg.chat.id,
                         "❌ Произошла ошибка при проверке конфига авто-выдачи. Подробнее в файле "
                         "<code>logs/log.log</code>", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return

    cardinal.AD_CFG = new_config
    cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
    logger.info(f"Пользователь $MAGENTA{msg.from_user.username} (id: {msg.from_user.id})$RESET "
                f"загрузил в бота и установил конфиг авто-выдачи.")
    bot.send_message(msg.chat.id, "✅ Конфиг авто-выдачи успешно применен.")


def upload_main_config(cardinal: Cardinal, msg: types.Message):
    """
    Загружает и проверяет основной конфиг.

    :param cardinal: экземпляр кардинала.

    :param msg: экземпляр сообщения.
    """
    tg = cardinal.telegram
    bot = tg.bot
    if not check_file(tg, msg):
        return
    if not download_file(tg, msg, "temp_main.cfg"):
        return

    bot.send_message(msg.chat.id, "🔁 Проверяю валидность файла...")
    try:
        new_config = cfg_loader.load_main_config("storage/cache/temp_main.cfg")
    except excs.ConfigParseError as e:
        bot.send_message(msg.chat.id, f"❌ Произошла ошибка при обработке конфига авто-выдачи: "
                                      f"<code>{tg_tools.format_text(str(e))}</code>", parse_mode="HTML")
        return
    except UnicodeDecodeError:
        bot.send_message(msg.chat.id, "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                                      "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                         parse_mode="HTML")
        return
    except:
        bot.send_message(msg.chat.id,
                         "❌ Произошла ошибка при проверке конфига авто-выдачи. Подробнее в файле "
                         "<code>logs/log.log</code>", parse_mode="HTML")
        logger.debug(traceback.format_exc())
        return

    cardinal.save_config(new_config, "configs/_main.cfg")
    logger.info(f"Пользователь $MAGENTA{msg.from_user.username} (id: {msg.from_user.id})$RESET "
                f"загрузил в бота основной конфиг.")
    bot.send_message(msg.chat.id, "✅ Основной конфиг успешно загружен. \n"
                                  "Необходимо перезагрузить бота, что бы применить изменения. \n"
                                  "Любое изменение основного конфига через переключатели на ПУ отменит все изменения.")


def init_uploader(cardinal: Cardinal):
    tg = cardinal.telegram
    bot = tg.bot

    def main(msg: types.Message):
        if tg.check_state(msg.chat.id, msg.from_user.id, "upload_products_file"):
            upload_products_file(cardinal, msg)
        elif tg.check_state(msg.chat.id, msg.from_user.id, "upload_auto_response_config"):
            upload_auto_response_config(cardinal, msg)
        elif tg.check_state(msg.chat.id, msg.from_user.id, "upload_auto_delivery_config"):
            upload_auto_delivery_config(cardinal, msg)
        elif tg.check_state(msg.chat.id, msg.from_user.id, "upload_main_config"):
            upload_main_config(cardinal, msg)

    def act_upload_products_file(call: types.CallbackQuery):
        result = bot.send_message(call.message.chat.id, "Отправьте мне файл с товарами.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(call.message.chat.id, result.id, call.from_user.id, "upload_products_file")
        bot.answer_callback_query(call.id)

    def act_upload_main_config(call: types.CallbackQuery):
        result = bot.send_message(call.message.chat.id, "Отправьте мне основной конфиг.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(call.message.chat.id, result.id, call.from_user.id, "upload_main_config")
        bot.answer_callback_query(call.id)

    def act_upload_auto_response_config(call: types.CallbackQuery):
        result = bot.send_message(call.message.chat.id, "Отправьте мне конфиг авто-ответчика.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(call.message.chat.id, result.id, call.from_user.id, "upload_auto_response_config")
        bot.answer_callback_query(call.id)

    def act_upload_auto_delivery_config(call: types.CallbackQuery):
        result = bot.send_message(call.message.chat.id, "Отправьте мне конфиг авто-выдачи.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(call.message.chat.id, result.id, call.from_user.id, "upload_auto_delivery_config")
        bot.answer_callback_query(call.id)

    tg.msg_handler(main, content_types=["document"])
    tg.cbq_handler(act_upload_products_file, func=lambda c: c.data == "upload_products_file")
    tg.cbq_handler(act_upload_auto_response_config, func=lambda c: c.data == "upload_auto_response_config")
    tg.cbq_handler(act_upload_auto_delivery_config, func=lambda c: c.data == "upload_auto_delivery_config")
    tg.cbq_handler(act_upload_main_config, func=lambda c: c.data == "upload_main_config")


REGISTER_TO_POST_INIT = [init_uploader]

