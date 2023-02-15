from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from configparser import ConfigParser

from tg_bot import auto_response_cp, config_loader_cp, auto_delivery_cp, file_uploader
import importlib.util
import configparser
import traceback
import requests
import datetime
import logging
import random
import time
import sys
import os

import FunPayAPI
import handlers

from Utils import cardinal_tools
import tg_bot.bot

from threading import Thread


logger = logging.getLogger("FPC")


def check_proxy(proxy: dict):
    logger.info("Выполняю проверку прокси...")
    try:
        response = requests.get("https://api.myip.com", proxies=proxy, timeout=10.0)
        print(response.status_code)
    except KeyboardInterrupt:
        return False
    except:
        logger.error("Не удалось подключиться к прокси. Убедитесь, данные веедены верно.")
        logger.debug(traceback.format_exc())
        return False
    logger.info(f"Прокси успешно проверен! Запросы к FunPay будут отправлять с "
                f"IP-адреса $YELLOW{response.json()['ip']}")
    return True


def get_cardinal() -> None | Cardinal:
    """
    Возвращает существующий экземпляр кардинала (или None, если такового нет).
    """
    if not hasattr(Cardinal, "instance"):
        return None
    return getattr(Cardinal, "instance")


class Cardinal(object):
    def __new__(cls, *args, **kwargs):
        # Singleton
        if not hasattr(cls, "instance"):
            cls.instance = super(Cardinal, cls).__new__(cls)
        return getattr(cls, "instance")

    def __init__(self, main_config: ConfigParser,
                 auto_delivery_config: ConfigParser,
                 auto_response_config: ConfigParser,
                 raw_auto_response_config: ConfigParser):

        self.instance_id = random.randint(0, 999999)

        # {"key": "lot_name"}
        self.delivery_tests = {}

        # Конфиги
        self.MAIN_CFG = main_config
        self.AD_CFG = auto_delivery_config
        self.AR_CFG = auto_response_config
        self.RAW_AR_CFG = raw_auto_response_config

        self.proxy = {}
        if self.MAIN_CFG["Proxy"].getboolean("enable"):
            if self.MAIN_CFG["Proxy"]["ip"] and self.MAIN_CFG["Proxy"]["port"].isnumeric():
                logger.info("Обнаружен прокси в основном конфиге.")

                ip, port = self.MAIN_CFG["Proxy"]["ip"], self.MAIN_CFG["Proxy"]["port"]
                self.proxy = {
                    "https": f"http://{ip}:{port}"
                }

                if self.MAIN_CFG["Proxy"]["login"] and self.MAIN_CFG["Proxy"]["password"]:
                    login, password = self.MAIN_CFG["Proxy"]["login"], self.MAIN_CFG["Proxy"]["password"]
                    self.proxy = {
                        "https": f"http://{login}:{password}@{ip}:{port}"
                    }

                if self.MAIN_CFG["Proxy"].getboolean("check"):
                    if not check_proxy(self.proxy):
                        sys.exit()

        self.account = FunPayAPI.account.Account(self.MAIN_CFG["FunPay"]["golden_key"],
                                                 self.MAIN_CFG["FunPay"]["user_agent"],
                                                 proxy=self.proxy)
        self.runner = FunPayAPI.runner.Runner(self.account)
        self.telegram: tg_bot.bot.TGBot | None = None

        self.running = False
        self.run_id = 0
        self.start_time = 0

        # В данном свойстве хранятся интервалы до следующего поднятия категорий игры.
        # формат хранения: {id игры: следующее время поднятия}
        self.raise_time = {}
        self.lots: list[FunPayAPI.types.Lot] = []
        self.categories: list[FunPayAPI.types.Category] = []
        self.telegram_lots: list[FunPayAPI.types.Lot] = []  # Для Telegram-ПУ.
        self.last_telegram_lots_update = datetime.datetime.now()
        self.current_lots: list[FunPayAPI.types.Lot] = []  # Для хэндлеров (авто-восстановление, авто-деактивация)
        self.current_lots_last_tag: str | None = None
        self.last_state_change_tag: str | None = None
        self.block_list: list[str] = []

        # Хэндлеры
        self.pre_init_handlers = []
        self.post_init_handlers = []
        self.pre_start_handlers = []
        self.post_start_handlers = []
        self.pre_stop_handlers = []
        self.post_stop_handlers = []

        self.init_message_handlers = []
        self.messages_list_changed_handlers = []
        self.new_message_handlers = []
        self.init_order_handlers = []
        self.orders_list_changed_handlers = []
        self.new_order_handlers = []
        self.order_status_changed_handlers = []

        self.pre_delivery_handlers = []
        self.post_delivery_handlers = []

        self.pre_lots_raise_handlers = []
        self.post_lots_raise_handlers = []

        self.handler_bind_var_names = {
            "BIND_TO_PRE_INIT": self.pre_init_handlers,
            "BIND_TO_POST_INIT": self.post_init_handlers,
            "BIND_TO_PRE_START": self.pre_start_handlers,
            "BIND_TO_POST_START": self.post_start_handlers,
            "BIND_TO_PRE_STOP": self.pre_stop_handlers,
            "BIND_TO_POST_STOP": self.post_stop_handlers,
            "BIND_TO_INIT_MESSAGE": self.init_message_handlers,
            "BIND_TO_MESSAGES_LIST_CHANGED": self.messages_list_changed_handlers,
            "BIND_TO_NEW_MESSAGE": self.new_message_handlers,
            "BIND_TO_INIT_ORDER": self.init_order_handlers,
            "BIND_TO_NEW_ORDER": self.new_order_handlers,
            "BIND_TO_ORDERS_LIST_CHANGED": self.orders_list_changed_handlers,
            "BIND_TO_ORDER_STATUS_CHANGED": self.order_status_changed_handlers,
            "BIND_TO_PRE_DELIVERY": self.pre_delivery_handlers,
            "BIND_TO_POST_DELIVERY": self.post_delivery_handlers,
            "BIND_TO_PRE_LOTS_RAISE": self.pre_lots_raise_handlers,
            "BIND_TO_POST_LOTS_RAISE": self.post_lots_raise_handlers,
        }

    def __init_account(self) -> None:
        """
        Инициализирует класс аккаунта (self.account)
        """
        while True:
            try:
                self.account.get()
                greeting_text = cardinal_tools.create_greetings(self.account)
                for line in greeting_text.split("\n"):
                    logger.info(line)
                break
            except TimeoutError:
                logger.error("Не удалось загрузить данные об аккаунте: превышен тайм-аут ожидания.")
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
            except (FunPayAPI.exceptions.StatusCodeIsNot200, FunPayAPI.exceptions.AccountDataNotfound) as e:
                logger.error(e)
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных аккаута. "
                             "Подробнее а файле logs/log.log")
                logger.debug(traceback.format_exc())
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)

    def __init_lots_and_categories(self, infinite_polling: bool = True, attempts: int = 0,
                                   update_telegram_lots: bool = True,
                                   update_cardinal_lots: bool = True) -> bool:
        """
        Загружает данные о лотах категориях аккаунта + восстанавливает game_id каждой категории из кэша, либо
        отправляет дополнительные запросы к FunPay. (self.categories)

        :param infinite_polling: бесконечно посылать запросы, пока не будет получен ответ (игнорировать макс. кол-во
        попыток)

        :param attempts: максимальное кол-во попыток.

        :param update_telegram_lots: обновить информацию о лотах для TG ПУ.

        :param update_cardinal_lots: обновить информацию о лотах и категориях для всего кардинала (+ хэндлеров).

        :return: True, если информация обновлена, False, если превышено макс. кол-во попыток.
        """
        logger.info("Получаю данные о лотах и категориях...")
        if infinite_polling:
            count = 1
        else:
            count = attempts
        # Получаем категории аккаунта.
        while count:
            try:
                user_lots_info = FunPayAPI.users.get_user(self.account.id,
                                                          user_agent=self.MAIN_CFG["FunPay"]["user_agent"],
                                                          proxy=self.proxy)
                categories = user_lots_info.categories
                lots = user_lots_info.lots
                logger.info(f"$MAGENTAПолучил информацию о лотах аккаунта. Всего категорий: $YELLOW{len(categories)}.")
                logger.info(f"$MAGENTAВсего лотов: $YELLOW{len(lots)}")
                break
            except TimeoutError:
                logger.error("Не удалось загрузить данные о категориях аккаунта: превышен тайм-аут ожидания.")
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                if not infinite_polling:
                    count -= 1
            except FunPayAPI.exceptions.StatusCodeIsNot200 as e:
                logger.error(e)
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                if not infinite_polling:
                    count -= 1
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных о лотах и категориях. "
                             "Подробнее а файле logs/log.log")
                logger.debug(traceback.format_exc())
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                if not infinite_polling:
                    count -= 1

        if not count:
            logger.error(f"Произошло ошибка при получении данных о лотах и категориях: "
                         f"превышено кол-во попыток ({attempts}).")
            return False

        # Привязываем к каждой категории её game_id. Если категория кэширована - берем game_id из кэша,
        # если нет - делаем запрос к FunPay.
        # Присваиваем каждому лоту game_id
        # Так же добавляем game_id категории в self.game_ids
        logger.info("Получаю ID игр, к которым относятся лоты и категории...")
        cached_categories = cardinal_tools.load_cached_categories()
        for index, cat in enumerate(categories):
            cached_category_name = f"{cat.id}_{cat.type.value}"
            if cached_category_name in cached_categories:
                categories[index].game_id = cached_categories[cached_category_name]
                # Присваиваем game_id каждому лоту это категории.
                category_lots = [(ind, lot) for ind, lot in enumerate(lots) if lot.category_id == cat.id]
                for lot_tuple in category_lots:
                    lots[lot_tuple[0]].game_id = cat.game_id
                logger.info(f"Доп. данные о категории \"{cat.title}\" найдены в кэше.")
                continue

            logger.warning(f"Доп. данные о категории \"{cat.title}\" не найдены в кэше.")
            logger.info("Отправляю запрос к FunPay...")
            if infinite_polling:
                count = 1
            else:
                count = attempts
            while count:
                try:
                    game_id = self.account.get_category_game_id(cat)
                    categories[index].game_id = game_id
                    # Присваиваем game_id каждому лоту этой категории.
                    category_lots = [(ind, lot) for ind, lot in enumerate(lots) if lot.category_id == cat.id]
                    for lot_tuple in category_lots:
                        lots[lot_tuple[0]].game_id = game_id
                    logger.info(f"Доп. данные о категории \"{cat.title}\" получены!")
                    time.sleep(0.2)
                    break
                except TimeoutError:
                    logger.error(f"Не удалось получить ID игры, к которой относится категория \"{cat.title}\": "
                                 f"превышен тайм-аут ожидания.")
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)
                    if not infinite_polling:
                        count -= 1
                except FunPayAPI.exceptions.StatusCodeIsNot200 as e:
                    logger.error(e)
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)
                    if not infinite_polling:
                        count -= 1
                except:
                    logger.error(f"Не удалось получить ID игры, к которой относится категория \"{cat.title}\": "
                                 f"неизвестная ошибка.")
                    logger.debug(traceback.format_exc())
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)
                    if not infinite_polling:
                        count -= 1

            if not count:
                logger.error(f"Не удалось получить ID игры, к которой относится категория \"{cat.title}\": "
                             f"превышено кол-во попыток ({attempts}).")
                return False

        if update_cardinal_lots:
            self.categories = categories
            self.lots = lots
            self.current_lots = lots
            self.lots_ids = [i.id for i in self.lots]
            logger.info(f"Кардинал обновил информацию об активных лотах "
                        f"$YELLOW({len(lots)})$RESET и категориях $YELLOW({len(categories)})$RESET. "
                        f"Изменения применены к авто-восстановлению и авто-деактивации.")
        if update_telegram_lots:
            self.telegram_lots = lots
            self.last_telegram_lots_update = datetime.datetime.now()
            logger.info(f"Обновлена информация об активных лотах $YELLOW({len(lots)})$RESET для ПУ TG.")
        logger.info("Кэширую данные о категориях...")
        cardinal_tools.cache_categories(self.categories, cached_categories)
        return True

    def __init_telegram(self) -> None:
        """
        Инициализирует Telegram бота.
        """
        self.telegram = tg_bot.bot.TGBot(self)
        self.telegram.init()

    def __add_handlers(self, plugin) -> None:
        """
        Добавляет хэндлеры из плагина.

        :param plugin: модуль (плагин)
        """
        for name in self.handler_bind_var_names:
            try:
                functions = getattr(plugin, name)
            except AttributeError:
                continue
            self.handler_bind_var_names[name].extend(functions)

        logger.info(f"Хэндлеры из $YELLOW{plugin.__name__}.py$RESET зарегистрированы.")

    def __load_plugins(self) -> None:
        """
        Загружает плагины из папки plugins.
        """
        if not os.path.exists("plugins"):
            logger.warning("Папка с плагинами не обнаружена.")
            return
        plugins = [file for file in os.listdir("plugins") if file.endswith(".py")]
        if not len(plugins):
            logger.info("Плагины не обнаружены.")
            return

        sys.path.append("plugins")
        for file in plugins:
            try:
                spec = importlib.util.spec_from_file_location(f"plugins.{file[:-3]}", f"plugins/{file}")
                plugin = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin)
                logger.info(f"Плагин $YELLOW{file}$RESET загружен.")
            except:
                logger.error(f"Не удалось загрузить плагин {file}. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())
                continue
            self.__add_handlers(plugin)

    # Прочее
    def raise_lots(self) -> int:
        """
        Пытается поднять лоты.

        :return: предположительное время, когда нужно снова запустить данную функцию.
        """
        # Время следующего вызова функции (по умолчанию - бесконечность).
        next_call = float("inf")

        for cat in self.categories:
            # Если game_id данной категории уже находится в self.game_ids, но время поднятия категорий
            # данной игры еще не настало - пропускам эту категорию.
            if cat.game_id in self.raise_time and self.raise_time[cat.game_id] > int(time.time()):
                # Если записанное в self.game_ids время меньше текущего next_call'а
                # обновляем время next_call'a на записанное время.
                if self.raise_time[cat.game_id] < next_call:
                    next_call = self.raise_time[cat.game_id]
                continue

            # В любом другом случае пытаемся поднять лоты всех категорий, относящихся к игре cat.game_id
            try:
                time.sleep(0.5)
                result = self.account.raise_game_categories(cat)
            except Exception as e:
                if isinstance(e, FunPayAPI.exceptions.StatusCodeIsNot200) and e.status_code == 429:
                    logger.warning(f"Ошибка 429 при поднятии категории \"{cat.title}\". Пауза на 10 сек...")
                    time.sleep(10)
                    next_time = int(time.time()) + 1
                else:
                    logger.error(f"Произошла непредвиденная ошибка при попытке поднять категорию \"{cat.title}. "
                                 f"Подробнее в файле logs/log.log. "
                                 f"(следующая попытка для данной категории через 10 секунд.)")
                    logger.debug(traceback.format_exc())
                    next_time = int(time.time()) + 10
                if next_time < next_call:
                    next_call = next_time
                continue

            if not result.complete:
                logger.warning(f"Не удалось поднять категорию \"{cat.title}\". "
                               f"FunPay говорит подождать еще {cardinal_tools.time_to_str(result.wait)}.")
                logger.debug(f"Ответ FunPay: {result.funpay_response}")
                next_time = int(time.time()) + result.wait
            else:
                for category_name in result.raised_category_names:
                    logger.info(f"Поднял категорию \"{category_name}\". ")
                logger.info(f"Все категории, относящиеся к игре с ID {cat.game_id} подняты!")
                logger.info(f"Попробую еще раз через  {cardinal_tools.time_to_str(result.wait)}.")
                next_time = int(time.time()) + result.wait
                self.run_handlers(self.post_lots_raise_handlers, (self, cat.game_id, result))

            self.raise_time[cat.game_id] = next_time
            if next_time < next_call:
                next_call = next_time
        return next_call

    def send_message(self, msg: FunPayAPI.types.Message, attempts: int = 3) -> bool:
        """
        Отправляет сообщение в чат FunPay.

        :param msg: объект MessageEvent.

        :param attempts: кол-во попыток на отправку сообщения.

        :return: True, если сообщение доставлено, False, если нет.
        """
        if self.MAIN_CFG["Other"].get("watermark"):
            msg.text = f"{self.MAIN_CFG['Other']['watermark']}\n" + msg.text

        lines = [i.strip() for i in msg.text.split("\n")]
        msg.text = "\n".join(lines)
        while "\n\n" in msg.text:
            msg.text = msg.text.replace("\n\n", "\n[a][/a]\n")
        lines = msg.text.split("\n")

        split_messages = []
        while lines:
            text = "\n".join(lines[:20])
            if text.strip() == "[a][/a]":
                continue
            msg_obj = FunPayAPI.types.Message(text, msg.node_id, msg.chat_with, msg.unread)
            split_messages.append(msg_obj)
            lines = lines[20:]

        for mes in split_messages:
            current_attempts = attempts
            while current_attempts:
                try:
                    response = self.account.send_message(mes)
                    if response.get("response") and response.get("response").get("error") is None:
                        self.runner.update_saved_message(mes)
                        logger.info(f"Отправил сообщение в чат $YELLOW{msg.node_id}.")
                        break
                except:
                    logger.debug(traceback.format_exc())
                # if error in response
                logger.warning(f"Произошла ошибка при отправке сообщения в чат $YELLOW{msg.node_id}.$RESET "
                               f"Подробнее в файле logs/log.log")
                logger.info(f"Осталось попыток: {current_attempts}.")
                current_attempts -= 1
                time.sleep(1)
            else:
                logger.error(f"Не удалось отправить сообщение в чат $YELLOW{msg.node_id}$RESET: "
                             f"превышено кол-во попыток.")
                return False
        return True

    def update_session(self):
        """
        Обновляет данные аккаунта (баланс, токены и т.д.)
        """
        attempts = 3
        while attempts:
            try:
                self.account.get(update_session_id=True)
                logger.info("Данные аккаунта обновлены.")
                return True
            except TimeoutError:
                attempts -= 1
                logger.warning("Не удалось загрузить данные об аккаунте: превышен тайм-аут ожидания.")
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                continue
            except (FunPayAPI.exceptions.StatusCodeIsNot200, FunPayAPI.exceptions.AccountDataNotfound) as e:
                attempts -= 1
                logger.error(e)
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                continue
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных аккаута. "
                             "Подробнее а файле logs/log.log")
                logger.debug(traceback.format_exc())
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                continue
        logger.error("Не удалось обновить данные об аккаунте: превышено кол-во попыток.")
        return False

    # Бесконечные циклы
    def process_events(self):
        """
        Запускает хэндлеры, привязанные к тому или иному событию.
        """
        instance_id = self.run_id
        events_handlers = {
            FunPayAPI.types.EventTypes.INITIAL_MESSAGE: self.init_message_handlers,
            FunPayAPI.types.EventTypes.MESSAGES_LIST_CHANGED: self.messages_list_changed_handlers,
            FunPayAPI.types.EventTypes.NEW_MESSAGE: self.new_message_handlers,

            FunPayAPI.types.EventTypes.INITIAL_ORDER: self.init_order_handlers,
            FunPayAPI.types.EventTypes.ORDERS_LIST_CHANGED: self.orders_list_changed_handlers,
            FunPayAPI.types.EventTypes.NEW_ORDER: self.new_order_handlers,
            FunPayAPI.types.EventTypes.ORDER_STATUS_CHANGED: self.order_status_changed_handlers,
        }

        for event in self.runner.listen(delay=int(self.MAIN_CFG["Other"]["requestsDelay"])):
            if instance_id != self.run_id:
                break
            self.run_handlers(events_handlers[event.type], (self, event))

    def lots_raise_loop(self):
        """
        Запускает бесконечный цикл поднятия категорий (если autoRaise в _main.cfg == 1)
        """
        logger.info("$CYANЦикл авто-поднятия лотов запущен (это не значит, что авто-поднятие лотов включено).")
        while True:
            if not self.MAIN_CFG["FunPay"].getboolean("autoRaise") or not self.categories:
                time.sleep(10)
                continue
            try:
                next_time = self.raise_lots()
                time.sleep(0.3)
            except not KeyboardInterrupt:
                logger.error("При попытке поднять лоты произошла непредвиденная ошибка. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())
                logger.warning("Попробую через 10 секунд.")
                time.sleep(10)
                continue
            delay = next_time - int(time.time())
            if delay < 0:
                continue
            time.sleep(delay)

    def update_session_loop(self):
        """
        Запускает бесконечный цикл обновления данных о пользователе.
        """
        logger.info("$CYANЦикл обновления данных аккаунта запущен.")
        sleep_time = 3600
        while True:
            time.sleep(sleep_time)
            result = self.update_session()
            sleep_time = 60 if not result else 3600

    # Управление процессом
    def init(self):
        self.block_list = cardinal_tools.load_block_list()

        if int(self.MAIN_CFG["Telegram"]["enabled"]):
            self.__init_telegram()
            self.__add_handlers(auto_response_cp)
            self.__add_handlers(auto_delivery_cp)
            self.__add_handlers(config_loader_cp)
            self.__add_handlers(file_uploader)

        self.run_handlers(self.pre_init_handlers, (self, ))

        if self.MAIN_CFG["Telegram"].getboolean("enabled"):
            Thread(target=self.telegram.run, daemon=True).start()

        self.__init_account()
        self.__init_lots_and_categories()

        self.__add_handlers(handlers)
        self.__load_plugins()

        self.run_handlers(self.post_init_handlers, (self, ))

    def run(self):
        self.run_id += 1
        self.start_time = int(time.time())
        self.run_handlers(self.pre_start_handlers, (self,))
        self.run_handlers(self.post_start_handlers, (self,))

        Thread(target=self.lots_raise_loop, daemon=True).start()
        Thread(target=self.update_session_loop, daemon=True).start()
        self.process_events()

    def start(self):
        self.run_id += 1
        self.run_handlers(self.pre_start_handlers, (self, ))
        self.run_handlers(self.post_start_handlers, (self, ))
        self.process_events()

    def stop(self):
        self.run_id += 1
        self.run_handlers(self.pre_start_handlers, (self, ))
        self.run_handlers(self.post_stop_handlers, (self, ))

    def update_lots_and_categories(self):
        """
        Парсит лоты (для ПУ TG).
        """
        result = self.__init_lots_and_categories(infinite_polling=False, attempts=3, update_cardinal_lots=False)
        return result

    @staticmethod
    def run_handlers(handlers_list: list[Callable], args) -> None:
        """
        Выполняет функции из списка handlers.

        :param handlers_list: Список функций.
        :param args: аргументы для функций.
        """
        for func in handlers_list:
            try:
                func(*args)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    @staticmethod
    def save_config(config: configparser.ConfigParser, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            config.write(f)
