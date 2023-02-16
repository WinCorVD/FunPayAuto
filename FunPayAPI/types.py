"""
В данном модуле описаны все типы пакета FunPayAPI.
"""
from __future__ import annotations

from enum import Enum
import time
import re


class Links:
    """
    Основные ссылки для работы с FunPay API.
    """
    BASE_URL = "https://funpay.com"
    ORDERS = "https://funpay.com/orders/trade"
    USER = "https://funpay.com/users"
    RAISE = "https://funpay.com/lots/raise"
    RUNNER = "https://funpay.com/runner/"
    REFUND = "https://funpay.com/orders/refund"


class EventTypes(Enum):
    """
    Типы событий.
    """
    INITIAL_MESSAGE = 0
    """Обнаружено новое сообщение (при первом запросе Runner'а)."""

    MESSAGES_LIST_CHANGED = 1
    """Список чатов и/или содержимое одного/нескольких чатов изменилось."""

    NEW_MESSAGE = 2
    """В чате обнаружено новое сообщение."""

    INITIAL_ORDER = 3
    """Обнаружен новый заказ (при первом запросе Runner'а)."""

    ORDERS_LIST_CHANGED = 4
    """Список заказов и/или статус одного/нескольких заказов изменился."""

    NEW_ORDER = 5
    """В списке заказов обнаружен новый заказ."""

    ORDER_STATUS_CHANGED = 6
    """Статус заказа изменился."""


class SystemMessageTypes(Enum):
    """
    Типы системных сообщений.
    """
    NON_SYSTEM = 0
    """Не системное сообщение."""

    ORDER_PURCHASED = 1
    """Покупатель [buyer] оплатил заказ #[order_id]. [lot_name]. [buyer], не забудьте потом нажать кнопку «Подтвердить выполнение заказа»."""

    ORDER_CONFIRMED = 2
    """Покупатель [buyer] подтвердил успешное выполнение заказа #[order_id] и отправил деньги продавцу [seller]."""

    NEW_FEEDBACK = 3
    """Покупатель [buyer] написал отзыв к заказу #[order_id]."""

    FEEDBACK_CHANGED = 4
    """Покупатель [buyer] изменил отзыв к заказу #[order_id]."""

    FEEDBACK_DELETED = 5
    """Покупатель [buyer] удалил отзыв к заказу #[order_id]."""

    NEW_FEEDBACK_ANSWER = 6
    """Продавец [seller] ответил на отзыв к заказу #[order_id]."""

    FEEDBACK_ANSWER_CHANGED = 7
    """Продавец [seller] изменил ответ на отзыв к заказу #[order_id]."""

    FEEDBACK_ANSWER_DELETED = 8
    """Продавец [seller] удалил ответ на отзыв к заказу #[order_id]."""

    ORDER_REOPENED = 9
    """Заказ #[order_id] открыт повторно."""

    REFUND = 10
    """Продавец [seller] вернул деньги покупателю [buyer] по заказу #[order_id]."""

    PARTIAL_REFUND = 11
    """Часть средств по заказу #[order_id] возвращена покупателю."""

    ORDER_CONFIRMED_BY_ADMIN = 12
    """Администратор [admin] подтвердил успешное выполнение заказа #[order_id] и отправил деньги продавцу [seller]."""

    DISCORD = 13
    """Вы можете перейти в Discord. Внимание: общение за пределами сервера FunPay считается нарушением правил."""


class SystemMessageRes(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(SystemMessageRes, cls).__new__(cls)
        return getattr(cls, "instance")

    def __init__(self):
        self.ORDER_PURCHASED_RE_1 = re.compile(r"Покупатель [a-zA-Z0-9]+ оплатил заказ #[A-Z0-9]{8}\.")

        self.ORDER_PURCHASED_RE_2 = re.compile(r"[a-zA-Z0-9]+, не забудьте потом нажать кнопку "
                                               r"«Подтвердить выполнение заказа»\.")

        self.ORDER_CONFIRMED_RE = re.compile(r"Покупатель [a-zA-Z0-9]+ подтвердил успешное выполнение "
                                             r"заказа #[A-Z0-9]{8} и отправил деньги продавцу [a-zA-Z0-9]+\.")

        self.NEW_FEEDBACK_RE = re.compile(r"Покупатель [a-zA-Z0-9]+ написал отзыв к заказу #[A-Z0-9]{8}\.")

        self.FEEDBACK_CHANGED_RE = re.compile(r"Покупатель [a-zA-Z0-9]+ изменил отзыв к заказу #[A-Z0-9]{8}\.")

        self.FEEDBACK_DELETED_RE = re.compile(r"Покупатель [a-zA-Z0-9]+ удалил отзыв к заказу #[A-Z0-9]{8}\.")

        self.NEW_FEEDBACK_ANSWER_RE = re.compile(r"Продавец [a-zA-Z0-9]+ ответил на отзыв к заказу #[A-Z0-9]{8}\.")

        self.FEEDBACK_ANSWER_CHANGED_RE = re.compile(r"Продавец [a-zA-Z0-9]+ изменил ответ на отзыв к "
                                                     r"заказу #[A-Z0-9]{8}\.")

        self.FEEDBACK_ANSWER_DELETED_RE = re.compile(r"Продавец [a-zA-Z0-9]+ удалил ответ на отзыв к заказу "
                                                     r"#[A-Z0-9]{8}\.")

        self.ORDER_REOPENED_RE = re.compile(r"Заказ #[A-Z0-9]{8} открыт повторно\.")

        self.REFUND_RE = re.compile(r"Продавец [a-zA-Z0-9]+ вернул деньги покупателю [a-zA-Z0-9]+ "
                                    r"по заказу #[A-Z0-9]{8}\.")

        self.PARTIAL_REFUND_RE = re.compile(r"Часть средств по заказу #[A-Z0-9]{8} возвращена покупателю\.")

        self.ORDER_CONFIRMED_BY_ADMIN_RE = re.compile(r"Администратор [a-zA-Z0-9]+ подтвердил успешное выполнение "
                                                      r"заказа #[A-Z0-9]{8} и отправил деньги продавцу [a-zA-Z0-9]+\.")

        self.DISCORD = "Вы можете перейти в Discord. " \
                       "Внимание: общение за пределами сервера FunPay считается нарушением правил."

        self.ORDER_ID_RE = re.compile(r"#[A-Z0-9]{8}")


class CategoryTypes(Enum):
    """
    Типы категорий FunPay.
    """
    LOT = 0
    """Стандартный лот."""

    CURRENCY = 1
    """лот с игровой валютой (их нельзя поднимать)."""


class OrderStatuses(Enum):
    """
    Состояния заказов.
    """
    OUTSTANDING = 0
    """Заказ ожидает выполнения."""

    COMPLETED = 1
    """Заказ выполнен."""

    REFUND = 2
    """Запрошен возврат средств."""


class Order:
    """
    Класс, хранящий информацию о заказе.
    """
    def __init__(self, html: str,
                 id_: str,
                 title: str,
                 price: float,
                 buyer_username: str,
                 buyer_id: int,
                 status: OrderStatuses):
        """
        :param html: HTML код заказа.

        :param id_: ID заказа.

        :param title: Краткое описание заказа.

        :param price: Оплаченная сумма за заказ.

        :param buyer_username: Никнейм покупателя.

        :param buyer_id: ID покупателя.

        :param status: статус заказа.
        """
        self.html = html
        self.id = id_
        self.title = title
        self.price = price
        self.buyer_username = buyer_username
        self.buyer_id = buyer_id
        self.status = status


class Message:
    """
    Класс, хранящий информацию о сообщении.
    """
    def __init__(self, text: str, node_id: int, chat_with: str | None, unread: bool = False,
                 set_sys_type: bool = False):
        """
        :param text: текст сообщения.

        :param node_id: ID чата.

        :param chat_with: никнейм пользователя, из чата с которым получено сообщение.

        :param unread: установлен ли флаг "unread" у чата, в котором получено сообщение (на момент получения сообщения)

        :param set_sys_type: устанавливать ли тип системного сообщения (не нужно, если сообщение отправляется ботом)
        """
        self.node_id: int = node_id
        self.text: str = text
        self.chat_with: str = chat_with
        self.unread: bool = unread
        self.sys_type: SystemMessageTypes | None = self.get_system_type() if set_sys_type else None

    def get_system_type(self) -> SystemMessageTypes:
        """
        Определяет тип системного сообщения.
        """
        res = SystemMessageRes()
        if self.text == res.DISCORD:
            return SystemMessageTypes.DISCORD

        if res.ORDER_PURCHASED_RE_1.findall(self.text) and res.ORDER_PURCHASED_RE_2.findall(self.text):
            return SystemMessageTypes.ORDER_PURCHASED

        if res.ORDER_ID_RE.search(self.text) is None:
            return SystemMessageTypes.NON_SYSTEM

        # регулярки выставлены в порядке от самых часто-используемых до самых редко-используемых
        sys_msg_types = {
            SystemMessageTypes.ORDER_CONFIRMED: res.ORDER_CONFIRMED_RE,
            SystemMessageTypes.NEW_FEEDBACK: res.NEW_FEEDBACK_RE,
            SystemMessageTypes.NEW_FEEDBACK_ANSWER: res.NEW_FEEDBACK_ANSWER_RE,
            SystemMessageTypes.FEEDBACK_CHANGED: res.FEEDBACK_CHANGED_RE,
            SystemMessageTypes.FEEDBACK_DELETED: res.FEEDBACK_DELETED_RE,
            SystemMessageTypes.REFUND: res.REFUND_RE,
            SystemMessageTypes.FEEDBACK_ANSWER_CHANGED: res.FEEDBACK_ANSWER_CHANGED_RE,
            SystemMessageTypes.FEEDBACK_ANSWER_DELETED: res.FEEDBACK_ANSWER_DELETED_RE,
            SystemMessageTypes.ORDER_CONFIRMED_BY_ADMIN: res.ORDER_CONFIRMED_BY_ADMIN_RE,
            SystemMessageTypes.PARTIAL_REFUND: res.PARTIAL_REFUND_RE,
            SystemMessageTypes.ORDER_REOPENED: res.ORDER_REOPENED_RE
        }

        for i in sys_msg_types:
            if sys_msg_types[i].search(self.text):
                return i
        else:
            return SystemMessageTypes.NON_SYSTEM


class Lot:
    """
    Класс, описывающий лот.
    """
    def __init__(self,
                 category_id: int,
                 game_id: int | None,
                 id_: int,
                 title: str,
                 price: str):
        """
        :param category_id: ID категории, к которой относится лот.

        :param game_id: ID игры, к которой относится лот.

        :param id_: ID лота.

        :param title: название лота.

        :param price: цена лота.
        """
        # todo: добавить html-код лота.
        self.category_id = category_id
        self.game_id = game_id
        self.id = id_
        self.title = title
        self.price = price


class Category:
    """
    Класс, описывающий категорию.
    """
    def __init__(self, id_: int, game_id: int | None, title: str, edit_lots_link: str, public_link: str,
                 type_: CategoryTypes):
        """
        :param id_: ID категории.

        :param game_id: ID игры, к которой относится категория.

        :param title: название категории.

        :param edit_lots_link: ссылка на страницу редактирования лотов данной категории.

        :param public_link: ссылка на все лоты всех пользователей в данной категории.

        :param type_: тип категории.
        """
        self.id = id_
        self.game_id = game_id
        self.title = title
        self.edit_lots_link = edit_lots_link
        self.public_link = public_link
        self.type = type_


class Event:
    """
    Базовый класс события.
    """
    def __init__(self, event_type: EventTypes, event_time: int, tag: str | None):
        """
        :param event_type: тип события.

        :param event_time: время события.

        :param tag: тег runner'а.
        """
        self.type = event_type
        self.time = event_time
        self.tag = tag


class InitialMessageEvent(Event):
    """
    Класс события: обнаружено новое сообщение (при первом запросе Runner'а).
    """
    def __init__(self, message_obj: Message, tag: str):
        """
        :param message_obj: экземпляр класса, описывающий сообщение.

        :param tag: тег runner'а.
        """
        super(InitialMessageEvent, self).__init__(EventTypes.INITIAL_MESSAGE, int(time.time()), tag)
        self.message = message_obj


class MessagesListChangedEvent(Event):
    """
    Класс события: список чатов и/или содержимое одного/нескольких чатов изменилось.
    """
    def __init__(self, tag: str):
        """
        :param tag: тэг runner'а.
        """
        super(MessagesListChangedEvent, self).__init__(EventTypes.MESSAGES_LIST_CHANGED, int(time.time()), tag)


class NewMessageEvent(Event):
    """
    Класс события: в чате обнаружено новое сообщение.
    """
    def __init__(self, message_obj: Message, tag: str | None):
        """
        :param message_obj: экземпляр класса, описывающий сообщение.

        :param tag: тег runner'а.
        """
        super(NewMessageEvent, self).__init__(EventTypes.NEW_MESSAGE, int(time.time()), tag)
        self.message = message_obj


class InitialOrderEvent(Event):
    """
    Класс события: обнаружен новый заказ (при первом запросе Runner'а).
    """
    def __init__(self, order_obj: Order, tag: str):
        """
        :param order_obj: экземпляр класса, описывающий заказ.

        :param tag: тег runner'а.
        """
        super(InitialOrderEvent, self).__init__(EventTypes.INITIAL_ORDER, int(time.time()), tag)
        self.order = order_obj


class OrdersListChangedEvent(Event):
    """
    Класс события: список заказов и/или статус одного/нескольких заказов изменился.
    """
    def __init__(self, buyer: int, seller: int, tag: str):
        """
        :param buyer: кол-во активных покупок.

        :param seller: кол-во активных продаж.

        :param tag: тэг runner'а.
        """
        super(OrdersListChangedEvent, self).__init__(EventTypes.ORDERS_LIST_CHANGED, int(time.time()), tag)
        self.buyer = buyer
        self.seller = seller


class NewOrderEvent(Event):
    """
    Класс события: в списке заказов обнаружен новый заказ.
    """
    def __init__(self, order_obj: Order, tag: str | None):
        """
        :param order_obj: экземпляр класса, описывающий заказ.

        :param tag: тег runner'а.
        """
        super(NewOrderEvent, self).__init__(EventTypes.NEW_ORDER, int(time.time()), tag)
        self.order = order_obj


class OrderStatusChangedEvent(Event):
    """
    Класс события: статус заказа изменился.
    """
    def __init__(self, order_obj: Order, tag: str | None):
        """
        :param order_obj: экземпляр класса, описывающий заказ.

        :param tag: тег runner'а.
        """
        super(OrderStatusChangedEvent, self).__init__(EventTypes.ORDER_STATUS_CHANGED, int(time.time()), tag)
        self.order = order_obj


class RaiseResponse:
    """
    Класс, описывающий ответ FunPay на запрос о поднятии лотов.
    """
    def __init__(self, complete: bool, wait: int,
                 raised_category_names: list[str], raised_category_ids: list[int],
                 funpay_response: dict):
        """
        :param complete: удалось ли поднять лоты.

        :param wait: примерное время ожидания до следующего поднятия.

        :param raised_category_names: названия поднятых категорий (из modal-формы).

        :param raised_category_ids: ID поднятых категорий (из modal-формы).

        :param funpay_response: полный ответ Funpay.
        """
        self.complete = complete
        self.wait = wait
        self.raised_category_names = raised_category_names
        self.raised_category_ids = raised_category_ids
        self.funpay_response = funpay_response


class UserInfo:
    """
    Класс, хранящий информацию о лотах и категориях пользователя.
    """
    def __init__(self, lots: list[Lot], categories: list[Category]):
        """
        :param lots: список лотов пользователя.

        :param categories: список категорий пользователя.
        """
        self.lots = lots
        self.categories = categories
