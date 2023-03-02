from __future__ import annotations
from typing import TYPE_CHECKING, Callable

import Utils.exceptions

if TYPE_CHECKING:
    from configparser import ConfigParser

from tg_bot import auto_response_cp, config_loader_cp, auto_delivery_cp, templates_cp, plugins_cp, file_uploader
from types import ModuleType
from uuid import UUID
import importlib.util
import configparser
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


def check_proxy(proxy: dict) -> bool:
    logger.info("Выполняю проверку прокси...")
    try:
        response = requests.get("http://ip-api.com/json/?fields=61439", proxies=proxy, timeout=10.0)
    except KeyboardInterrupt:
        return False
    except:
        logger.error("Не удалось подключиться к прокси. Убедитесь, что данные введены верно.")
        logger.debug("------TRACEBACK------", exc_info=True)
        return False
    logger.info(f"Прокси успешно проверен! Запросы к FunPay будут отправлять с "
                f"IP-адреса $YELLOW{response.json()['query']}")
    return True


def get_cardinal() -> None | Cardinal:
    """
    Возвращает существующий экземпляр кардинала.
    """
    if hasattr(Cardinal, "instance"):
        return getattr(Cardinal, "instance")


class PluginData:
    def __init__(self, name: str, version: str, desc: str, credentials: str, uuid: str,
                 path: str, plugin: ModuleType, settings_page: bool, enabled: bool):
        self.name = name
        self.version = version
        self.description = desc
        self.credits = credentials
        self.uuid = uuid

        self.path = path
        self.plugin = plugin
        self.settings_page = settings_page
        self.commands = {}
        self.enabled = enabled


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

        self.instance_id = random.randint(0, 999999999)

        self.delivery_tests = {}  # Одноразовые ключи для тестов автовыдачи. {"ключ": "название лота"}

        # Конфиги
        self.MAIN_CFG = main_config
        self.AD_CFG = auto_delivery_config
        self.AR_CFG = auto_response_config
        self.RAW_AR_CFG = raw_auto_response_config

        self.proxy = {}
        if self.MAIN_CFG["Proxy"].getboolean("enable"):
            if self.MAIN_CFG["Proxy"]["ip"] and self.MAIN_CFG["Proxy"]["port"].isnumeric():
                logger.info("Обнаружен прокси.")

                ip, port = self.MAIN_CFG["Proxy"]["ip"], self.MAIN_CFG["Proxy"]["port"]
                login, password = self.MAIN_CFG["Proxy"]["login"], self.MAIN_CFG["Proxy"]["password"]
                self.proxy = {
                    "https": f"http://{f'{login}:{password}@' if login and password else ''}{ip}:{port}"
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
        self.start_time = int(time.time())

        self.raise_time = {}  # Временные метки поднятия категорий {id игры: след. время поднятия}
        self.lots: list[FunPayAPI.types.Lot] = []  # Список лотов (при запуске FPC) (для восстановления / деактивации)
        self.categories: list[FunPayAPI.types.Category] = []  # Список категорий (при запуске FPC)
        self.telegram_lots: list[FunPayAPI.types.Lot] = []  # Список лотов (для Telegram-ПУ)
        self.last_telegram_lots_update = datetime.datetime.now()  # Последнее время обновления списка лотов для TG-ПУ
        self.current_lots: list[FunPayAPI.types.Lot] = []  # Текущий список лотов (для восстановления / деактивации)
        # Тег последнего event'а, после которого обновлялся self.current_lots
        self.current_lots_last_tag: str | None = None
        # Тег последнего event'а, после которого обновлялось состояние лотов.
        self.last_state_change_tag: str | None = None
        self.block_list: list[str] = []  # ЧС.

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

        self.plugins: dict[str, PluginData] = {}
        self.disabled_plugins = cardinal_tools.load_disabled_plugins()

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
            except (FunPayAPI.exceptions.StatusCodeIsNot200, FunPayAPI.exceptions.AccountDataNotfound) as e:
                logger.error(e)
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных аккаута. "
                             "Подробнее а файле logs/log.log")
                logger.debug("------TRACEBACK------", exc_info=True)
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
                user_lots_info = self.account.get_user(self.account.id)
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
                logger.debug("------TRACEBACK------", exc_info=True)
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
                if not infinite_polling:
                    count -= 1
        else:
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
                    logger.debug("------TRACEBACK------", exc_info=True)
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
                        f"Изменения применены к автовосстановлению и автодеактивации.")
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

    # Прочее
    def raise_lots(self) -> int:
        """
        Пытается поднять лоты.

        :return: предположительное время, когда нужно снова запустить данную функцию.
        """
        # Время следующего вызова функции (по умолчанию - бесконечность).
        next_call = float("inf")

        for cat in self.categories:
            if cat.game_id is None:
                continue

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
                    logger.debug("------TRACEBACK------", exc_info=True)
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
                    logger.debug("------TRACEBACK------", exc_info=True)
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

    def update_session(self, attempts: int = 3) -> bool:
        """
        Обновляет данные аккаунта (баланс, токены и т.д.)

        :param attempts: кол-во попыток.

        :return: True, если удалось обновить данные, False - если нет.
        """
        while attempts:
            try:
                self.account.get(update_session_id=True)
                logger.info("Данные аккаунта обновлены.")
                return True
            except TimeoutError:
                logger.warning("Не удалось загрузить данные об аккаунте: превышен тайм-аут ожидания.")
            except (FunPayAPI.exceptions.StatusCodeIsNot200, FunPayAPI.exceptions.AccountDataNotfound) as e:
                logger.error(e)
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных аккаута. "
                             "Подробнее а файле logs/log.log")
                logger.debug("------TRACEBACK------", exc_info=True)
            attempts -= 1
            logger.warning("Повторю попытку через 2 секунды...")
            time.sleep(2)
        else:
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
        if not self.categories:
            logger.info("$CYAN Цикл автоподнятия не был запущен, т.к. на аккаунте не обнаружен лотов.")
            return

        logger.info("$CYANЦикл автоподнятия лотов запущен (это не значит, что автоподнятие лотов включено).")
        while True:
            if not self.MAIN_CFG["FunPay"].getboolean("autoRaise"):
                time.sleep(10)
                continue
            next_time = self.raise_lots()
            delay = next_time - int(time.time())
            if delay <= 0:
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
        self.add_handlers_from_plugin(handlers)
        self.load_plugins()
        self.add_handlers()

        self.block_list = cardinal_tools.load_block_list()

        if self.MAIN_CFG["Telegram"].getboolean("enabled"):
            self.__init_telegram()
            for module in [auto_response_cp, auto_delivery_cp, config_loader_cp, templates_cp, plugins_cp,
                           file_uploader]:
                self.add_handlers_from_plugin(module)

        self.run_handlers(self.pre_init_handlers, (self, ))

        if self.MAIN_CFG["Telegram"].getboolean("enabled"):
            self.telegram.setup_commands()
            Thread(target=self.telegram.run, daemon=True).start()

        self.__init_account()
        self.__init_lots_and_categories()
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
    def save_config(config: configparser.ConfigParser, file_path: str) -> None:
        """
        Сохраняет конфиг в указанный файл.

        :param config: объект конфига.

        :param file_path: путь до файла, в который нужно сохранить конфиг.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            config.write(f)

    # Загрузка плагинов
    @staticmethod
    def is_uuid_valid(uuid: str):
        try:
            uuid_obj = UUID(uuid, version=4)
        except ValueError:
            return False
        return str(uuid_obj) == uuid

    @staticmethod
    def load_plugin(from_file: str) -> tuple:
        spec = importlib.util.spec_from_file_location(f"plugins.{from_file[:-3]}", f"plugins/{from_file}")
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)

        fields = ["NAME", "VERSION", "DESCRIPTION", "CREDITS", "SETTINGS_PAGE", "UUID"]
        result = {}

        for i in fields:
            try:
                if i == "SETTINGS_PAGE":
                    value = bool(getattr(plugin, i))
                else:
                    value = str(getattr(plugin, i))
            except AttributeError:
                raise Utils.exceptions.FieldNotExistsError(i, from_file)
            result[i] = value

        return plugin, result

    def load_plugins(self):
        if not os.path.exists("plugins"):
            logger.warning("Папка с плагинами не обнаружена.")
            return
        plugins = [file for file in os.listdir("plugins") if file.endswith(".py")]
        if not plugins:
            logger.info("Плагины не обнаружены.")
            return

        sys.path.append("plugins")
        for file in plugins:
            try:
                plugin, data = self.load_plugin(file)
            except:
                logger.error(f"Не удалось загрузить плагин {file}. Подробнее в файле logs/log.log.")
                logger.debug("------TRACEBACK------", exc_info=True)
                continue

            if not self.is_uuid_valid(data["UUID"]):
                logger.error(f"Не удалось загрузить плагин {file}. Невалидный UUID.")
                continue

            if data["UUID"] in self.plugins:
                logger.error(f"UUID {data['UUID']} ({data['NAME']}) уже зарегистрирован.")
                continue

            plugin_data = PluginData(data["NAME"], data["VERSION"], data["DESCRIPTION"], data["CREDITS"], data["UUID"],
                                     f"plugins/{file}", plugin, data["SETTINGS_PAGE"],
                                     False if data["UUID"] in self.disabled_plugins else True)

            self.plugins[data["UUID"]] = plugin_data

    def add_handlers_from_plugin(self, plugin, uuid: str | None = None):
        """
        Добавляет хэндлеры из плагина.

        :param plugin: модуль (плагин).

        :param uuid: UUID плагина (None для встроенных хэндлеров).
        """
        for name in self.handler_bind_var_names:
            try:
                functions = getattr(plugin, name)
            except AttributeError:
                continue
            for func in functions:
                func.plugin_uuid = uuid
            self.handler_bind_var_names[name].extend(functions)
        logger.info(f"Хэндлеры из $YELLOW{plugin.__name__}.py$RESET зарегистрированы.")

    def add_handlers(self):
        for i in self.plugins:
            plugin = self.plugins[i].plugin
            self.add_handlers_from_plugin(plugin, i)

    def run_handlers(self, handlers_list: list[Callable], args) -> None:
        """
        Выполняет функции из списка handlers.

        :param handlers_list: Список функций.

        :param args: аргументы для функций.
        """
        for func in handlers_list:
            try:
                if getattr(func, "plugin_uuid") is None or self.plugins[getattr(func, "plugin_uuid")].enabled:
                    func(*args)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера. Подробнее в файле logs/log.log.")
                logger.debug("------TRACEBACK------", exc_info=True)

    def add_commands(self, uuid: str, commands: list[tuple[str, str, bool]]):
        """
        Добавляет команды в список команд плагина.
        [
            ("команда1", "описание команды", Добавлять ли в меню команд (True / False)),
            ("команда2", "описание команды", Добавлять ли в меню команд (True / False))
        ]

        :param uuid: UUID плагина.
        :param commands: список команд (без "/")
        """
        if uuid not in self.plugins:
            return

        for i in commands:
            self.plugins[uuid].commands[i[0]] = i[1]
            if i[2] and self.telegram:
                self.telegram.add_command_to_menu(i[0], i[1])

    def toggle_plugin(self, uuid):
        self.plugins[uuid].enabled = not self.plugins[uuid].enabled
        if self.plugins[uuid].enabled and uuid in self.disabled_plugins:
            self.disabled_plugins.remove(uuid)
        elif not self.plugins[uuid].enabled and uuid not in self.disabled_plugins:
            self.disabled_plugins.append(uuid)
        cardinal_tools.cache_disabled_plugins(self.disabled_plugins)
