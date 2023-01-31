"""
В данном модуле написаны хэндлеры для разных эвентов.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from FunPayAPI.types import NewMessageEvent, NewOrderEvent, RaiseResponse, Message, Order
import FunPayAPI.users

from Utils import cardinal_tools
import configparser
import time
import logging
import traceback
from threading import Thread

import telebot.types
from telebot.types import InlineKeyboardButton as Button
from telegram import telegram_tools as tg_tools


logger = logging.getLogger("FPC.handlers")


ORDER_HTML_TEMPLATE = """<a href="https://funpay.com/orders/DELIVERY_TEST/" class="tc-item info">
    <div class="tc-date">
        <div class="tc-date-time">сегодня, 00:00</div>
        <div class="tc-date-left">1 минуту назад</div>
    </div>

    <div class="tc-order">#DELIVERY_TEST</div>
    <div class="order-desc">
        <div>ТЕСТ АВТОВЫДАЧИ</div>
        <div class="text-muted">$lot_name</div>
    </div>

    <div class="tc-user">
        <div class="media media-user mt0 offline">
        <div class="media-left">
            <div class="avatar-photo pseudo-a" tabindex="0" data-href="https://funpay.com/users/000000/" style="background-image: url(https://s.funpay.com/s/avatar/6d/h3/6dh3m89zv8k90kwlj9bg.jpg);"></div>
        </div>
        <div class="media-body">
            <div class="media-user-name">
                <span class="pseudo-a" tabindex="0" data-href="https://funpay.com/users/000000/">$username</span>
            </div>
            <div class="media-user-status">был миллион лет назад</div>
        </div>
    </div>
        <div class="tc-status text-primary">Оплачен</div>
        <div class="tc-price text-nowrap tc-seller-sum">999999.0<span class="unit">₽</span></div>
</a>"""


def create_reply_button(node_id: int) -> telebot.types.InlineKeyboardMarkup:
    """
    Генерирует кнопку для отправки сообщения из Telegram в ЛС пользователю FunPay.
    :param node_id: ID переписки, в которую нужно отправить сообщение.
    :return: экземпляр кнопки (клавиатуры).
    """
    keyboard = telebot.types.InlineKeyboardMarkup()
    reply_button = telebot.types.InlineKeyboardButton(text="📨 Ответить", callback_data=f"to_node:{node_id}")
    keyboard.add(reply_button)
    return keyboard


def create_new_order_keyboard(order_id: str) -> telebot.types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для сообщения о новом оредере.
    :param order_id: ID оредра.
    :return: экземпляр кнопки (клавиатуры).
    """
    keyboard = telebot.types.InlineKeyboardMarkup()\
        .add(Button(text="💸 Вернуть деньги", callback_data=f"refund_request:{order_id[1:]}")) \
        .add(Button(text="🌐 Открыть страницу заказа", url=f"https://funpay.com/orders/{order_id[1:]}/"))
    return keyboard


# Новое сообщение (REGISTER_TO_NEW_MESSAGE)
def log_msg_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Логирует полученное сообщение.
    """
    logger.info(f"$MAGENTA┌──$RESET Новое сообщение в переписке с пользователем $YELLOW{event.message.chat_with}"
                f" (node: {event.message.node_id}):")

    for index, line in enumerate(event.message.text.split("\n")):
        if not index:
            logger.info(f"$MAGENTA└───> $CYAN{line}")
        else:
            logger.info(f"      $CYAN{line}")


def send_response_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Проверяет, является ли сообщение командой, и если да, отправляет ответ на данную команду.
    """
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockResponse"]):
        return

    command = event.message.text.strip().lower()
    if not int(cardinal.MAIN_CFG["FunPay"]["autoResponse"]):
        return
    if command not in cardinal.AR_CFG:
        return

    logger.info(f"Получена команда $YELLOW{command}$RESET "
                f"в переписке с пользователем $YELLOW{event.message.chat_with} (node: {event.message.node_id}).")
    attempts = 3
    response_text = cardinal_tools.format_msg_text(cardinal.AR_CFG[command]["response"], event.message)
    new_msg_obj = FunPayAPI.types.Message(response_text, event.message.node_id, event.message.chat_with)
    while attempts:
        try:
            result = cardinal.send_message(new_msg_obj)
        except:
            logger.error(f"Произошла непредвиденная ошибка при отправке ответа пользователю {event.message.chat_with}.")
            logger.debug(traceback.format_exc())
            logger.info("Следующая попытка через секунду.")
            attempts -= 1
            time.sleep(1)
            continue
        if not result:
            attempts -= 1
            logger.info("Следующая попытка через секунду.")
            time.sleep(1)
            continue
        return
    logger.error("Не удалось отправить ответ пользователю: превышено кол-во попыток.")
    return


def send_new_message_notification_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Отправляет уведомление о новом сообщении в телеграм.
    """
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockNewMessageNotification"]):
        return
    if cardinal.telegram is None or not int(cardinal.MAIN_CFG["Telegram"]["newMessageNotification"]):
        return
    if event.message.text.strip().lower() in cardinal.AR_CFG.sections():
        return

    if event.message.text.startswith("!автовыдача"):
        return

    if any(i in event.message.text for i in ["Покупатель", "Продавец"]):
        if any(i in event.message.text for i in ["вернул деньги", "оплатил заказ", "написал отзыв",
                                                 "подтвердил успешное выполнение заказа"]):
            return
    text = f"""Новое сообщение в переписке с пользователем <a href="https://funpay.com/chat/?node={event.message.node_id}">{event.message.chat_with}</a>.

{tg_tools.format_text(event.message.text)}"""

    button = create_reply_button(event.message.node_id)
    Thread(target=cardinal.telegram.send_notification, args=(text, button), daemon=True).start()


def send_command_notification_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Отправляет уведомление о введенной комманде в телеграм.
    """
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockCommandNotification"]):
        return
    command = event.message.text.strip().lower()
    if cardinal.telegram is None or command not in cardinal.AR_CFG:
        return

    if cardinal.AR_CFG[command].get("telegramNotification") is None:
        return
    if not int(cardinal.AR_CFG[command]["telegramNotification"]):
        return

    if cardinal.AR_CFG[command].get("notificationText") is None:
        text = f"Пользователь {event.message.chat_with} ввел команду \"{tg_tools.format_text(command)}\"."
    else:
        text = cardinal_tools.format_msg_text(cardinal.AR_CFG[command]["notificationText"], event.message)

    Thread(target=cardinal.telegram.send_notification, args=(text, ), daemon=True).start()


def test_auto_delivery_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    if not event.message.text.startswith("!автовыдача"):
        return
    split = event.message.text.split(" ")
    if len(split) < 2:
        logger.warning("Не обнаружен секретный код.")
        return

    key = event.message.text.split(" ")[1].strip()
    if not key.isnumeric() or int(key) != cardinal.secret_key:
        logger.warning("Неверный секретный код.")
        return

    cardinal.update_secret_key()
    logger.warning("Секретный код обновлен.")

    split = event.message.text.split(" ", 2)
    if len(split) < 3 or not split[2].strip():
        logger.warning("Название лота не обнаружено.")
        return

    lot_name = split[2].strip()

    fake_order = Order(ORDER_HTML_TEMPLATE.replace("$username", event.message.chat_with).replace("$lot_name", lot_name),
                       "#DELIVERY_TEST", lot_name, 999999.0, event.message.chat_with, 000000,
                       FunPayAPI.types.OrderStatuses.OUTSTANDING)

    fake_event = NewOrderEvent(fake_order, event.tag)
    cardinal.run_handlers(cardinal.new_order_handlers, (cardinal, fake_event,))


def send_categories_raised_notification_handler(cardinal: Cardinal, game_id: int, response: RaiseResponse) -> None:
    """
    Отправляет уведомление о поднятии лотов в Telegram.
    """
    if cardinal.telegram is None or not int(cardinal.MAIN_CFG["Telegram"]["lotsRaiseNotification"]):
        return

    cats_text = "".join(f"\"{i}\", " for i in response.raised_category_names).strip()[:-1]
    Thread(target=cardinal.telegram.send_notification,
           args=(f"Поднял категории: {cats_text}. (ID игры: {game_id})\n"
                 f"Ответ FunPay: {response.funpay_response}"
                 f"Попробую еще раз через {cardinal_tools.time_to_str(response.wait)}.", ), daemon=True).start()


# Новый ордер (REGISTER_TO_NEW_ORDER)
def send_new_order_notification_handler(cardinal: Cardinal, event: NewOrderEvent, *args):
    """
    Отправляет уведомления о новом заказе в телеграм.
    """
    if event.order.buyer_username in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockNewOrderNotification"]):
        return
    if cardinal.telegram is None:
        return
    if not int(cardinal.MAIN_CFG["Telegram"]["newOrderNotification"]):
        return

    node_id = cardinal.account.get_node_id_by_username(event.order.buyer_username)

    text = f"""<b>Новый заказ</b>  <code>{event.order.id}</code>

<b><i>Покупатель:</i></b>  <code>{event.order.buyer_username}</code>
<b><i>Сумма:</i></b>  <code>{event.order.price}</code>
<b><i>Лот:</i></b>  <code>{tg_tools.format_text(event.order.title)}</code>"""

    keyboard = create_new_order_keyboard(event.order.id)
    Thread(target=cardinal.telegram.send_notification, args=(text, keyboard), daemon=True).start()


def send_product_text(node_id: int, text: str, order_id: str, cardinal: Cardinal, *args) -> bool:
    """
    Отправляет сообщение с товаром в чат node_id.

    :param node_id: ID чата.
    :param text: текст сообщения.
    :param order_id: ID ордера.
    :param cardinal: экземпляр Кардинала.
    :return: результат отправки.
    """
    new_msg_obj = Message(text, node_id, None)
    attempts = 3
    while attempts:
        try:
            result = cardinal.send_message(new_msg_obj)
        except:
            logger.error(f"Произошла непредвиденная ошибка при отправке товара для ордера {order_id}. "
                         f"Подробнее в файле logs/log.log.")
            logger.debug(traceback.format_exc())
            logger.info("Следующая попытка через секунду.")
            attempts -= 1
            time.sleep(1)
            continue
        if not result:
            attempts -= 1
            logger.info("Следующая попытка через секунду.")
            time.sleep(1)
            continue
        return True
    return False


def deliver_product(cardinal: Cardinal, event: NewOrderEvent, delivery_obj: configparser.SectionProxy,
                    *args) -> tuple[bool, str, int] | None:
    """
    Форматирует текст товара и отправляет его покупателю.
    :return: результат выполнения. None - если лота нет в конфиге.
    [Результат выполнения, текст товара, оставшееся кол-во товара] - в любом другом случае.
    """
    node_id = cardinal.account.get_node_id_by_username(event.order.buyer_username)
    response_text = cardinal_tools.format_order_text(delivery_obj["response"], event.order)

    # Проверяем, есть ли у лота файл с товарами. Если нет, то просто отправляем response лота.
    if delivery_obj.get("productsFileName") is None:
        result = send_product_text(node_id, response_text, event.order.id, cardinal)
        return result, response_text, -1

    # Получаем товар.
    file_name = delivery_obj.get("productsFileName")
    product = cardinal_tools.get_product(f"storage/products/{file_name}")
    product_text = product[0].replace("\\n", "\n")
    response_text = response_text.replace("$product", product_text)

    # Отправляем товар.
    result = send_product_text(node_id, response_text, event.order.id, cardinal)

    # Если произошла какая-либо ошибка при отправлении товара, возвращаем товар обратно в файл с товарами.
    if not result:
        cardinal_tools.add_products(f"storage/products/{file_name}", [product_text])
    return result, response_text, -1


def deliver_product_handler(cardinal: Cardinal, event: NewOrderEvent, *args) -> None:
    """
    Обертка для deliver_product(), обрабатывающая ошибки.
    """
    # Ищем название лота в конфиге.
    delivery_obj = None
    config_lot_name = ""
    for lot_name in cardinal.AD_CFG:
        if lot_name in event.order.title:
            delivery_obj = cardinal.AD_CFG[lot_name]
            config_lot_name = lot_name
            break
    if delivery_obj is None:
        return None

    if delivery_obj.get("disable") is not None and delivery_obj.getboolean("disable"):
        return

    cardinal.run_handlers(cardinal.pre_delivery_handlers, (cardinal, event, config_lot_name))
    try:
        result = deliver_product(cardinal, event, delivery_obj, *args)
        if result is None:
            logger.info(f"Лот \"{event.order.title}\" не обнаружен в конфиге авто-выдачи.")
        elif not result[0]:
            logger.error(f"Ошибка при выдаче товара для ордера {event.order.id}: превышено кол-во попыток.")
            cardinal.run_handlers(cardinal.post_delivery_handlers,
                                  (cardinal, event, config_lot_name, "Превышено кол-во попыток.", True))
        else:
            logger.info(f"Товар для ордера {event.order.id} выдан.")
            cardinal.run_handlers(cardinal.post_delivery_handlers,
                                  (cardinal, event, config_lot_name, result[1], False))
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка при обработке заказа {event.order.id}.")
        logger.debug(traceback.format_exc())
        cardinal.run_handlers(cardinal.post_delivery_handlers,
                              (cardinal, event, config_lot_name, str(e), True))


# REGISTER_TO_POST_DELIVERY
def send_delivery_notification_handler(cardinal: Cardinal, event: NewOrderEvent, config_lot_name: str,
                                       delivery_text: str, errored: bool = False, *args):
    """
    Отправляет уведомление в телеграм об отправке товара.
    """
    if cardinal.telegram is None:
        return
    if not int(cardinal.MAIN_CFG["Telegram"]["productsDeliveryNotification"]):
        return

    if errored:
        text = f"""Произошла ошибка при выдаче товара для ордера <code>{event.order.id}</code>.
Ошибка: {delivery_text}"""
    else:
        text = f"""Успешно выдал товар для ордера <code>{event.order.id}</code>.

----- ТОВАР -----
{tg_tools.format_text(delivery_text)}"""

    Thread(target=cardinal.telegram.send_notification, args=(text, ), daemon=True).start()


def change_lot_state_handler(cardinal: Cardinal, event: NewOrderEvent, config_lot_name: str,
                             delivery_text: str, errored: bool = False, *args):
    delivery_obj = cardinal.AD_CFG[config_lot_name]
    if delivery_obj.get("productsFileName"):
        # получить кол-во товара
        file_name = delivery_obj.get("productsFileName")
        products_count = cardinal_tools.get_products_count(f"storage/products/{file_name}")
        if products_count:
            if int(cardinal.MAIN_CFG["FunPay"]["autoRestore"]):
                # restore
                pass
                return
            return
        else:
            if int(cardinal.MAIN_CFG["FunPay"]["autoDisable"]):
                # disable
                pass
                return
            return
    else:
        if int(cardinal.MAIN_CFG["FunPay"]["autoRestore"]):
            if cardinal.AD_CFG[config_lot_name].get("disableAutoRestore") is not None and int(cardinal.AD_CFG[config_lot_name].get("disableAutoRestore")):
                return
            else:
                # todo
                return


'''def activate_lots_handler(cardinal: Cardinal, event: NewOrderEvent, delivery_obj: configparser.SectionProxy):
    """
    Активирует деактивированные лоты.
    """
    logger.info("Обновляю информацию о лотах...")
    attempts = 3
    lots_info = []
    while attempts:
        try:
            lots_info = FunPayAPI.users.get_user_lots_info(cardinal.account.id)["lots"]
            break
        except:
            logger.error("Произошла пошибка при получении информации о лотах.")
            logger.debug(traceback.format_exc())
            attempts -= 1
    if not attempts:
        logger.error("Не удалось получить информацию о лотах: превышено кол-во попыток.")
        return

    lots_ids = [i.id for i in lots_info]
    for lot in cardinal.lots:
        if lot.id not in lots_ids:
            try:
                cardinal.account.change_lot_state(lot.id, lot.game_id)
                logger.info(f"Активировал лот {lot.id}.")
            except:
                logger.error(f"Не удалось активировать лот {lot.id}.")
                logger.debug(traceback.format_exc())'''


# REGISTER_TO_POST_START
def send_bot_started_notification_handler(cardinal: Cardinal, *args) -> None:
    """
    Отправляет уведомление о запуске бота в телеграм.
    """
    if cardinal.telegram is None:
        return

    if cardinal.account.currency is None:
        curr = ""
    else:
        curr = cardinal.account.currency
    text = f"""<b><u>Бот запущен!</u></b>

<b><i>Аккаунт:</i></b>  <code>{cardinal.account.username}</code> | <code>{cardinal.account.id}</code>
<b><i>Баланс:</i></b> <code>{cardinal.account.balance}{curr}</code>
<b><i>Незавершенных ордеров:</i></b>  <code>{cardinal.account.active_orders}</code>"""
    cardinal.telegram.send_notification(text)


REGISTER_TO_NEW_MESSAGE = [log_msg_handler,
                           send_response_handler,
                           send_new_message_notification_handler,
                           send_command_notification_handler,
                           test_auto_delivery_handler]

REGISTER_TO_POST_LOTS_RAISE = [send_categories_raised_notification_handler]

REGISTER_TO_NEW_ORDER = [send_new_order_notification_handler, deliver_product_handler]

REGISTER_TO_POST_DELIVERY = [send_delivery_notification_handler]

REGISTER_TO_POST_START = [send_bot_started_notification_handler]

