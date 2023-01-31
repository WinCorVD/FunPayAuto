from enum import Enum
import time


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
    NEW_MESSAGE = 0
    NEW_ORDER = 1
    ORDER_STATUS_CHANGED = 2


class CategoryTypes(Enum):
    """
    Типы категорий FunPay.

    CategoryTypes.LOT - стандартный лот.
    CategoryTypes.CURRENCY - лот с игровой валютой (их нельзя поднимать).
    """
    LOT = 0
    CURRENCY = 1


class OrderStatuses(Enum):
    """
    Состояния ордеров.

    OrderStatuses.OUTSTANDING - ожидает выполнения.
    OrderStatuses.COMPLETED - выполнен.
    OrderStatuses.REFUND - запрошен возврат средств.
    """
    OUTSTANDING = 0
    COMPLETED = 1
    REFUND = 2


class Order:
    """
    Класс, описывающий ордер.
    """
    def __init__(self, html: str,
                 id_: str,
                 title: str,
                 price: float,
                 buyer_username: str,
                 buyer_id: int,
                 status: OrderStatuses):
        """
        :param html: HTML код ордера.
        :param id_: ID ордера.
        :param title: Краткое описание ордера.
        :param price: Оплаченная сумма за ордер.
        :param buyer_username: Псевдоним покупателя.
        :param buyer_id: ID покупателя.
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
    Класс, описывающий сообщение.
    """
    def __init__(self, text: str, node_id: int, chat_with: str | None):
        """
        :param node_id: ID чата.
        :param text: текст сообщения.
        :param chat_with: никнейм пользователя, из переписки с которым получено сообщение.
        """
        self.node_id = node_id
        self.text = text
        self.chat_with = chat_with


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
    Базовый класс, описывающий событие.
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


class NewMessageEvent(Event):
    """
    Класс, описывающий событие: новое сообщение.
    """
    def __init__(self, message_obj: Message, tag: str | None):
        """
        :param message_obj: объект ордера.
        :param tag: тег runner'а.
        """
        super(NewMessageEvent, self).__init__(EventTypes.NEW_MESSAGE, int(time.time()), tag)
        self.message = message_obj


class NewOrderEvent(Event):
    """
    Класс, описывающий событие: новый ордер.
    """
    def __init__(self, order_obj: Order, tag: str | None):
        """
        :param order_obj: объект ордера.
        :param tag: тег runner'а.
        """
        super(NewOrderEvent, self).__init__(EventTypes.NEW_ORDER, int(time.time()), tag)
        self.order = order_obj


class OrderStatusChangedEvent(Event):
    """
    Класс, описывающий событие: изменение статуса ордера.
    """
    def __init__(self, order_obj: Order, tag: str | None):
        """
        :param order_obj: объект ордера.
        :param tag: тег runner'а.
        """
        super(OrderStatusChangedEvent, self).__init__(EventTypes.ORDER_STATUS_CHANGED, int(time.time()), tag)
        self.order = order_obj


class RaiseResponse:
    """
    Класс, описывающий ответ FunPay на запрос о поднятии лотов.
    """
    def __init__(self, complete: bool, wait: int, raised_category_names: list[str], funpay_response: dict):
        """
        :param complete: удалось ли поднять лоты.
        :param wait: примерное время ожидания до следующего поднятия.
        :param raised_category_names: названия поднятых категорий (из modal-формы)
        :param funpay_response: полный ответ Funpay.
        """
        self.complete = complete
        self.wait = wait
        self.raised_category_names = raised_category_names
        self.funpay_response = funpay_response


class UserInfo:
    def __init__(self, lots: list[Lot], categories: list[Category]):
        self.lots = lots
        self.categories = categories
