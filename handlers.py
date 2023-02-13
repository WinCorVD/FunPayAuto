"""
В данном модуле написаны хэндлеры для разных эвентов.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from FunPayAPI.types import NewMessageEvent, NewOrderEvent, OrdersListChangedEvent, RaiseResponse, Message, Order
import FunPayAPI.users

from Utils import cardinal_tools
import configparser
import time
import logging
import traceback
from threading import Thread

import re
from tg_bot import utils, keyboards


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


AMOUNT_EXPRESSION = re.compile(r'[\d]+ шт\.')


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
    response_text = cardinal_tools.format_msg_text(cardinal.AR_CFG[command]["response"], event.message)
    new_msg_obj = FunPayAPI.types.Message(response_text, event.message.node_id, event.message.chat_with)
    result = cardinal.send_message(new_msg_obj)
    if not result:
        logger.error(f"Не удалось отправить ответ на команду пользователю $YELLOW{event.message.chat_with}$RESET.")


def send_new_message_notification_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Отправляет уведомление о новом сообщении в телеграм.
    """
    if not cardinal.telegram or not event.message.unread:
        return
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockNewMessageNotification"]):
        return
    if event.message.text.strip().lower() in cardinal.AR_CFG.sections():
        return
    if event.message.text.startswith("!автовыдача"):
        return
    if any(i in event.message.text for i in ["Покупатель", "Продавец"]):
        if any(i in event.message.text for i in ["вернул деньги", "оплатил заказ", "написал отзыв",
                                                 "подтвердил успешное выполнение заказа"]):
            return

    text = f"""Сообщение в переписке <a href="https://funpay.com/chat/?node={event.message.node_id}">{event.message.chat_with}</a>.

<b><i>{event.message.chat_with}:</i></b> <code>{utils.escape(event.message.text)}</code>"""

    button = keyboards.reply(event.message.node_id, event.message.chat_with)
    Thread(target=cardinal.telegram.send_notification, args=(text, button, utils.NotificationTypes.new_message),
           daemon=True).start()


def send_command_notification_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """
    Отправляет уведомление о введенной комманде в телеграм.
    """
    if event.message.chat_with in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockCommandNotification"]):
        return
    command = event.message.text.strip().lower()
    if not cardinal.telegram or command not in cardinal.AR_CFG:
        return

    if cardinal.AR_CFG[command].getboolean("telegramNotification") is None:
        return

    if cardinal.AR_CFG[command].get("notificationText") is None:
        text = f"Пользователь {event.message.chat_with} ввел команду \"{utils.escape(command)}\"."
    else:
        text = cardinal_tools.format_msg_text(cardinal.AR_CFG[command]["notificationText"], event.message)

    Thread(target=cardinal.telegram.send_notification, args=(text,),
           kwargs={"notification_type": utils.NotificationTypes.command}, daemon=True).start()


def test_auto_delivery_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    if not event.message.text.startswith("!автовыдача"):
        return
    split = event.message.text.split(" ")
    if len(split) < 2:
        logger.warning("Одноразовый ключ авто-выдачи не обнаружен.")
        return

    key = event.message.text.split(" ")[1].strip()
    if key not in cardinal.delivery_tests:
        logger.warning("Невалидный одноразовый ключ.")
        return

    lot_name = cardinal.delivery_tests[key]
    del cardinal.delivery_tests[key]
    logger.info(f"Одноразовый ключ $YELLOW{key}$RESET удален.")

    fake_order = Order(ORDER_HTML_TEMPLATE.replace("$username", event.message.chat_with).replace("$lot_name", lot_name),
                       "#DELIVERY_TEST", lot_name, 999999.0, event.message.chat_with, 000000,
                       FunPayAPI.types.OrderStatuses.OUTSTANDING)

    fake_event = NewOrderEvent(fake_order, event.tag)
    cardinal.run_handlers(cardinal.new_order_handlers, (cardinal, fake_event,))


def send_categories_raised_notification_handler(cardinal: Cardinal, game_id: int, response: RaiseResponse) -> None:
    """
    Отправляет уведомление о поднятии лотов в Telegram.
    """
    if not cardinal.telegram:
        return

    cats_text = "".join(f"\"{i}\", " for i in response.raised_category_names).strip()[:-1]

    Thread(target=cardinal.telegram.send_notification,
           args=(f"Поднял категории: {cats_text}. (ID игры: {game_id})\n"
                 f"Ответ FunPay: {response.funpay_response}"
                 f"Попробую еще раз через {cardinal_tools.time_to_str(response.wait)}.", ),
           kwargs={"notification_type": utils.NotificationTypes.lots_raise}, daemon=True).start()


# Изменен список ордеров (REGISTER_TO_ORDERS_LIST_CHANGED)
def get_lot_config_by_name(cardinal: Cardinal, name: str) -> configparser.SectionProxy | None:
    """
    Ищет секцию лота в конфиге авто-выдачи.

    :param cardinal: экземпляр кардинала.

    :param name: название лота.

    :return: секцию конфига или None.
    """
    for i in cardinal.AD_CFG.sections():
        if i in name:
            return cardinal.AD_CFG[i]
    return None


def check_lot_products_count(config_obj: configparser.SectionProxy) -> int:
    file_name = config_obj.get("productsFileName")
    if file_name is None:
        return 1

    return cardinal_tools.count_products(f"storage/products/{file_name}")


def update_current_lots_handler(cardinal: Cardinal, event: OrdersListChangedEvent):
    logger.info("Получаю информацию о лотах...")
    attempts = 3
    while attempts:
        try:
            cardinal.current_lots = FunPayAPI.users.get_user(cardinal.account.id,
                                                             user_agent=cardinal.MAIN_CFG["FunPay"]["user_agent"],
                                                             proxy=cardinal.proxy).lots
            cardinal.current_lots_last_tag = event.tag
            break
        except:
            logger.error("Произошла ошибка при получении информации о лотах.")
            logger.debug(traceback.format_exc())
            attempts -= 1
            time.sleep(2)
    if not attempts:
        logger.error("Не удалось получить информацию о лотах: превышено кол-во попыток.")
        return


# Новый ордер (REGISTER_TO_NEW_ORDER)
def log_new_order_handler(cardinal: Cardinal, event: NewOrderEvent, *args):
    """
    Логирует новый заказ.
    """
    logger.info(f"Новый заказ! ID: $YELLOW{event.order.id}$RESET")


def send_new_order_notification_handler(cardinal: Cardinal, event: NewOrderEvent, *args):
    """
    Отправляет уведомления о новом заказе в телеграм.
    """
    if event.order.buyer_username in cardinal.block_list and int(cardinal.MAIN_CFG["BlockList"]["blockNewOrderNotification"]):
        return
    if not cardinal.telegram:
        return

    text = f"""<b>Новый заказ</b>  <code>{event.order.id}</code>

<b><i>Покупатель:</i></b>  <code>{event.order.buyer_username}</code>
<b><i>Сумма:</i></b>  <code>{event.order.price}</code>
<b><i>Лот:</i></b>  <code>{utils.escape(event.order.title)}</code>"""

    keyboard = keyboards.new_order(event.order.id[1:])
    Thread(target=cardinal.telegram.send_notification, args=(text, keyboard, utils.NotificationTypes.new_order),
           daemon=True).start()


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
        new_msg_obj = Message(response_text, node_id, None)
        result = cardinal.send_message(new_msg_obj)
        if not result:
            logger.error(f"Не удалось отправить товар для ордера $YELLOW{event.order.id}$RESET. ")
        return result, response_text, -1

    # Получаем товар.
    file_name = delivery_obj.get("productsFileName")
    products = []
    if cardinal.MAIN_CFG["FunPay"].getboolean("multiDelivery") and not delivery_obj.getboolean("disableMultiDelivery"):
        result = AMOUNT_EXPRESSION.findall(event.order.title)
        if result:
            amount = int(result[0].split(" ")[0])
            products = cardinal_tools.get_product(f"storage/products/{file_name}", amount)
    if not products:
        products = cardinal_tools.get_product(f"storage/products/{file_name}")

    product_text = "\n".join(products[0]).replace("\\n", "\n")
    response_text = response_text.replace("$product", product_text)

    # Отправляем товар.
    new_msg_obj = Message(response_text, node_id, None)
    result = cardinal.send_message(new_msg_obj)

    # Если произошла какая-либо ошибка при отправлении товара, возвращаем товар обратно в файл с товарами.
    if not result:
        cardinal_tools.add_products(f"storage/products/{file_name}", [product_text])
        logger.error(f"Не удалось отправить товар для ордера $YELLOW{event.order.id}$RESET. ")
    return result, response_text, -1


def deliver_product_handler(cardinal: Cardinal, event: NewOrderEvent, *args) -> None:
    """
    Обертка для deliver_product(), обрабатывающая ошибки.
    """
    if event.order.buyer_username in cardinal.block_list and cardinal.MAIN_CFG["BlockList"].getboolean("blockDelivery"):
        logger.info(f"Пользователь {event.order.buyer_username} находится в ЧС и включена блокировка авто-выдачи. "
                    f"$YELLOW(ID: {event.order.id})$RESET")
        if cardinal.telegram:
            text = f"Пользователь {event.order.buyer_username} находится в ЧС и включена блокировка авто-выдачи."
            Thread(target=cardinal.telegram.send_notification, args=(text, ),
                   kwargs={"notification_type": utils.NotificationTypes.delivery}, daemon=True).start()
        return

    # Ищем название лота в конфиге.
    delivery_obj = None
    config_lot_name = ""
    for lot_name in cardinal.AD_CFG:
        if lot_name in event.order.title:
            delivery_obj = cardinal.AD_CFG[lot_name]
            config_lot_name = lot_name
            break

    if delivery_obj is None:
        logger.info(f"Лот \"{event.order.title}\" не обнаружен в конфиге авто-выдачи.")
        return

    if delivery_obj.get("disable") is not None and delivery_obj.getboolean("disable"):
        logger.info(f"Для данного лота отключена авто-выдача. $YELLOW(ID: {event.order.id})$RESET")
        return

    cardinal.run_handlers(cardinal.pre_delivery_handlers, (cardinal, event, config_lot_name))
    try:
        result = deliver_product(cardinal, event, delivery_obj, *args)
        if not result[0]:
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

    if errored:
        text = f"""Произошла ошибка при выдаче товара для ордера <code>{event.order.id}</code>.
Ошибка: {delivery_text}"""
    else:
        text = f"""Успешно выдал товар для ордера <code>{event.order.id}</code>.

----- ТОВАР -----
{utils.escape(delivery_text)}"""

    Thread(target=cardinal.telegram.send_notification, args=(text, ),
           kwargs={"notification_type": utils.NotificationTypes.delivery}, daemon=True).start()


def update_lot_state(cardinal: Cardinal, lot: FunPayAPI.types.Lot, task: int):
    """
    Обновляет состояние лота

    :param task: -1 - деактивировать лот. 1 - активировать лот.
    """
    attempts = 3
    while attempts:
        try:
            lot_info = cardinal.account.get_lot_info(lot.id, lot.game_id)
            if task == 1:
                cardinal.account.save_lot(lot_info, active=True)
                logger.info(f"Восстановил лот $YELLOW{lot.title}$RESET.")
            elif task == -1:
                cardinal.account.save_lot(lot_info, active=False)
                logger.info(f"Деактивировал лот $YELLOW{lot.title}$RESET.")
            return
        except:
            logger.error(f"Произошла ошибка при изменении состояния лота $YELLOW{lot.title}$RESET."
                         "Подробнее в файле logs/log.log")
            logger.debug(traceback.format_exc())
            attempts -= 1
            time.sleep(2)
    logger.error(f"Не удалось изменить состояние лота $YELLOW{lot.title}$RESET: превышено кол-во попыток.")


def update_lots_states(cardinal: Cardinal, event: NewOrderEvent):
    if not any([cardinal.MAIN_CFG["FunPay"].getboolean("autoRestore"),
                cardinal.MAIN_CFG["FunPay"].getboolean("autoDisable")]):
        return
    if cardinal.current_lots_last_tag != event.tag or cardinal.last_state_change_tag == event.tag:
        return

    lots_ids = [i.id for i in cardinal.current_lots]

    for lot in cardinal.lots:
        # -1 - деактивировать
        # 0 - ничего не делать
        # 1 - восстановить
        current_task = 0
        config_obj = get_lot_config_by_name(cardinal, lot.title)

        # Если лот уже деактивирован
        if lot.id not in lots_ids:
            # и не найден в конфиге авто-выдачи (глобальное авто-восстановление включено)
            if config_obj is None:
                if cardinal.MAIN_CFG["FunPay"].getboolean("autoRestore"):
                    current_task = 1

            # и найден в конфиге авто-выдачи
            else:
                # и глобальное авто-восстановление вкл. + не выключено в самом лоте в конфиге авто-выдачи
                if cardinal.MAIN_CFG["FunPay"].getboolean("autoRestore") and \
                        config_obj.get("disableAutoRestore") in ["0", None]:
                    # если глобальная авто-деактивация выключена - восстанавливаем.
                    if not cardinal.MAIN_CFG["FunPay"].getboolean("autoDisable"):
                        current_task = 1
                    # если глобальная авто-деактивация включена - восстанавливаем только если есть товары.
                    else:
                        if check_lot_products_count(config_obj):
                            current_task = 1

        # Если же лот активен
        else:
            # и найден в конфиге авто-выдачи
            if config_obj:
                products_count = check_lot_products_count(config_obj)
                # и все условия выполнены: нет товаров + включено глобальная авто-деактивация + она не выключена в
                # самом лоте в конфига авто-выдачи - отключаем.
                if all((not products_count, cardinal.MAIN_CFG["FunPay"].getboolean("autoDisable"),
                        config_obj.get("disableAutoDisable") in ["0", None])):
                    current_task = -1

        if current_task:
            update_lot_state(cardinal, lot, current_task)
            time.sleep(0.5)

    cardinal.last_state_change_tag = event.tag


def update_lots_state_handler(cardinal: Cardinal, event: NewOrderEvent, *args):
    Thread(target=update_lots_states, args=(cardinal, event), daemon=True).start()


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
    text = f"""✅ <b><u>FunPay Cardinal запущен!</u></b>

👑 <b><i>Аккаунт:</i></b>  <code>{cardinal.account.username}</code> | <code>{cardinal.account.id}</code>
💰 <b><i>Баланс:</i></b> <code>{cardinal.account.balance}{curr}</code>
📊 <b><i>Незавершенных ордеров:</i></b>  <code>{cardinal.account.active_orders}</code>"""

    for i in cardinal.telegram.init_messages:
        try:
            cardinal.telegram.bot.edit_message_text(text, i[0], i[1], parse_mode="HTML")
        except:
            continue


BIND_TO_NEW_MESSAGE = [log_msg_handler,
                       send_response_handler,
                       send_new_message_notification_handler,
                       send_command_notification_handler,
                       test_auto_delivery_handler]

BIND_TO_POST_LOTS_RAISE = [send_categories_raised_notification_handler]

BIND_TO_ORDERS_LIST_CHANGED = [update_current_lots_handler]

BIND_TO_NEW_ORDER = [log_new_order_handler, send_new_order_notification_handler, deliver_product_handler,
                     update_lots_state_handler]

BIND_TO_POST_DELIVERY = [send_delivery_notification_handler]

BIND_TO_POST_START = [send_bot_started_notification_handler]
