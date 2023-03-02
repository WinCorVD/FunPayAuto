from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from bs4 import BeautifulSoup
from FunPayAPI import exceptions
from FunPayAPI.account import Account

import telebot
import requests
from tg_bot import utils


NAME = "List Old Orders Plugin"
VERSION = "0.0.1"
DESCRIPTION = "Данный плагин добавляет команду /old_orders, " \
              "благодаря которой можно получить список открытых заказов, которым более 24 часов."
CREDITS = "@woopertail"
UUID = "a31cfa24-5ac8-4efb-8c61-7dec3544aa32"
SETTINGS_PAGE = False


def get_orders(acc: Account) -> list[str]:
    """
    Получает список ордеров на аккаунте.

    :return: Список с заказами.
    """
    headers = {"cookie": f"golden_key={acc.golden_key}; PHPSESSID={acc.session_id};",
               "user-agent": acc.user_agent}
    response = requests.get("https://funpay.com/orders/trade?id=&buyer=&state=paid&game=",
                            headers=headers, timeout=acc.timeout, proxies=acc.proxy)
    if response.status_code != 200:
        raise exceptions.StatusCodeIsNot200(response.status_code)

    html_response = response.content.decode()
    soup = BeautifulSoup(html_response, "html.parser")

    check_user = soup.find("div", {"class": "user-link-name"})
    if check_user is None:
        raise exceptions.AccountDataNotfound()

    order_divs = soup.find_all("a", {"class": "tc-item"})
    if order_divs is None:
        return []
    orders_list = []

    for div in order_divs:
        time = div.find("div", {"class": "tc-date-left"}).text
        if any(map(time.__contains__, ["сек", "мин", "час", "тол"])):
            continue
        orders_list.append(div.find("div", {"class": "tc-order"}).text)
    return orders_list


def init_commands(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot
    acc = cardinal.account

    def send_orders(m: telebot.types.Message):
        try:
            orders = get_orders(acc)
        except:
            bot.send_message(m.chat.id, "❌ Не удалось получить список заказов.")
            return

        if not orders:
            bot.send_message(m.chat.id, "❌ Просроченных заказов нет.")
            return

        orders_text = ", ".join(orders)
        text = f"Здравствуйте!\n\nПрошу подтвердить выполнение следующих заказов:\n{orders_text}"
        bot.send_message(m.chat.id, f"<code>{utils.escape(text)}</code>", parse_mode="HTML")

    tg.msg_handler(send_orders, commands=["old_orders"])
    cardinal.add_telegram_commands(UUID, [
        ("old_orders", "отправляет список открытых заказов, которым более 24 часов", True)
    ])


BIND_TO_PRE_INIT = [init_commands]
BIND_TO_DELETE = None
