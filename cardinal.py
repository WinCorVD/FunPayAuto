from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from configparser import ConfigParser

import importlib.util
import configparser
import traceback
import logging
import random
import time
import sys
import os

import FunPayAPI
import handlers

from Utils import cardinal_tools
import telegram.bot

from threading import Thread

from telegram import auto_response_cp, config_loader_cp, auto_delivery_cp, file_uploader


logger = logging.getLogger("FPC")


class Cardinal:
    def __init__(self, main_config: ConfigParser,
                 auto_delivery_config: ConfigParser,
                 auto_response_config: ConfigParser,
                 raw_auto_response_config: ConfigParser):

        self.instance_id = random.randint(0, 999999)
        self.secret_key = random.randint(10000000, 999999999)

        # Конфиги
        self.MAIN_CFG = main_config
        self.AD_CFG = auto_delivery_config
        self.AR_CFG = auto_response_config
        self.RAW_AR_CFG = raw_auto_response_config

        self.account = FunPayAPI.account.Account(self.MAIN_CFG["FunPay"]["golden_key"],
                                                 self.MAIN_CFG["FunPay"]["user_agent"])
        self.runner = FunPayAPI.runner.Runner(self.account)
        self.telegram: telegram.bot.TGBot | None = None

        self.running = False
        self.run_id = 0
        self.start_time = 0

        # В данном свойстве хранятся интервалы до следующего поднятия категорий игры.
        # формат хранения: {id игры: следующее время поднятия}
        self.raise_time = {}
        self.block_list = []

        # Хэндлеры
        self.post_init_handlers = []
        self.pre_start_handlers = []
        self.post_start_handlers = []
        self.pre_stop_handlers = []
        self.post_stop_handlers = []

        self.new_message_handlers = []
        self.new_order_handlers = []
        self.order_status_changed_handlers = []

        self.pre_delivery_handlers = []
        self.post_delivery_handlers = []

        self.pre_lots_raise_handlers = []
        self.post_lots_raise_handlers = []

        self.handler_reg_var_names = {
            "REGISTER_TO_POST_INIT": self.post_init_handlers,
            "REGISTER_TO_PRE_START": self.pre_start_handlers,
            "REGISTER_TO_POST_START": self.post_start_handlers,
            "REGISTER_TO_PRE_STOP": self.pre_stop_handlers,
            "REGISTER_TO_POST_STOP": self.post_stop_handlers,
            "REGISTER_TO_NEW_MESSAGE": self.new_message_handlers,
            "REGISTER_TO_NEW_ORDER": self.new_order_handlers,
            "REGISTER_TO_ORDER_STATUS_CHANGED": self.order_status_changed_handlers,
            "REGISTER_TO_PRE_DELIVERY": self.pre_delivery_handlers,
            "REGISTER_TO_POST_DELIVERY": self.post_delivery_handlers,
            "REGISTER_TO_PRE_LOTS_RAISE": self.pre_lots_raise_handlers,
            "REGISTER_TO_POST_LOTS_RAISE": self.post_lots_raise_handlers
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
                logger.warning("Не удалось загрузить данные об аккаунте: превышен тайм-аут ожидания.")
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

    def __init_lots_and_categories(self) -> None:
        """
        Загружает данные о лотах категориях аккаунта + восстанавливает game_id каждой категории из кэша, либо
        отправляет дополнительные запросы к FunPay. (self.categories)

        :return: None
        """
        logger.info("Получаю данные о лотах и категориях...")
        # Получаем категории аккаунта.
        while True:
            try:
                user_lots_info = FunPayAPI.users.get_user(self.account.id,
                                                          user_agent=self.MAIN_CFG["FunPay"]["user_agent"])
                categories = user_lots_info.categories
                lots = user_lots_info.lots
                logger.info(f"$MAGENTAПолучил информацию о лотах аккаунта. Всего категорий: $YELLOW{len(categories)}.")
                logger.info(f"$MAGENTAВсего лотов: $YELLOW{len(lots)}")
                break
            except TimeoutError:
                logger.error("Не удалось загрузить данные о категориях аккаунта: превышен тайм-аут ожидания.")
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
            except FunPayAPI.exceptions.StatusCodeIsNot200 as e:
                logger.error(e)
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)
            except:
                logger.error("Произошла непредвиденная ошибка при получении данных о лотах и категориях. "
                             "Подробнее а файле logs/log.log")
                logger.debug(traceback.format_exc())
                logger.warning("Повторю попытку через 2 секунды...")
                time.sleep(2)

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
            while True:
                try:
                    game_id = self.account.get_category_game_id(cat)
                    categories[index].game_id = game_id
                    # Присваиваем game_id каждому лоту этой категории.
                    category_lots = [(ind, lot) for ind, lot in enumerate(lots) if lot.category_id == cat.id]
                    for lot_tuple in category_lots:
                        lots[lot_tuple[0]].game_id = game_id
                    logger.info(f"Доп. данные о категории \"{cat.title}\" получены!")
                    break
                except TimeoutError:
                    logger.error(f"Не удалось получить ID игры, к которой относится категория \"{cat.title}\": "
                                 f"превышен тайм-аут ожидания.")
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)
                except FunPayAPI.exceptions.StatusCodeIsNot200 as e:
                    logger.error(e)
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)
                except:
                    logger.error(f"Не удалось получить ID игры, к которой относится категория \"{cat.title}\": "
                                 f"неизвестная ошибка.")
                    logger.debug(traceback.format_exc())
                    logger.warning("Повторю попытку через 2 секунды...")
                    time.sleep(2)

        self.categories = categories
        self.lots = lots
        logger.info("Кэширую данные о категориях...")
        cardinal_tools.cache_categories(self.categories)

    def __init_telegram(self) -> None:
        """
        Инициализирует Telegram бота.
        :return:
        """
        self.telegram = telegram.bot.TGBot(self)
        self.telegram.init()

    def __add_handlers(self, plugin) -> None:
        """
        Добавляет хэндлеры из плагина.

        :param plugin: модуль (плагин)
        """
        for name in self.handler_reg_var_names:
            try:
                functions = getattr(plugin, name)
            except AttributeError:
                continue
            self.handler_reg_var_names[name].extend(functions)

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
        # Минимальное время до следующего вызова данной функции.
        min_next_time = -1
        if not self.categories:
            time.sleep(10)
        for cat in self.categories:
            # Если game_id данной категории уже находится в self.game_ids, но время поднятия категорий
            # данной игры еще не настало - пропускам эту категорию.
            if cat.game_id in self.raise_time and self.raise_time[cat.game_id] > int(time.time()):
                if min_next_time == -1 or self.raise_time[cat.game_id] < min_next_time:
                    min_next_time = self.raise_time[cat.game_id]
                continue

            # В любом другом случае пытаемся поднять лоты всех категорий, относящихся к игре cat.game_id
            try:
                response = self.account.raise_game_categories(cat)
            except:
                logger.error(f"Произошла непредвиденная ошибка при попытке поднять категорию \"{cat.title}. "
                             f"Подробнее в файле logs/log.log. (следующая попытка для данной категории через 10 секунд.)")
                logger.debug(traceback.format_exc())
                next_time = int(time.time()) + 10
                if min_next_time == -1 or next_time < min_next_time:
                    min_next_time = next_time
                continue
            if not response.complete:
                logger.warning(f"Не удалось поднять категорию \"{cat.title}\".")
                logger.warning(f"Ответ FunPay: {response.funpay_response}")
                logger.warning(f"Попробую еще раз через {cardinal_tools.time_to_str(response.wait)}.")
                next_time = int(time.time()) + response.wait
                self.raise_time[cat.game_id] = next_time
                if min_next_time == -1 or next_time < min_next_time:
                    min_next_time = next_time
            else:
                for category_name in response.raised_category_names:
                    logger.info(f"Поднял категорию \"{category_name}\". ")
                logger.info(f"Все категории, относящиеся к игре с ID {cat.game_id} подняты!")
                logger.info(f"Попробую еще раз через  {cardinal_tools.time_to_str(response.wait)}.")
                next_time = int(time.time()) + response.wait
                self.raise_time[cat.game_id] = next_time
                if min_next_time == -1 or next_time < min_next_time:
                    min_next_time = next_time
                self.run_handlers(self.post_lots_raise_handlers, (self, cat.game_id, response))
        return min_next_time

    def send_message(self, msg: FunPayAPI.types.Message):
        """
        Отправляет сообщение в чат c ID node_id. Если сообщение доставлено - добавляет его в список последних сообщений
        в runner.

        :param msg: объект MessageEvent.
        :return:
        """
        if self.MAIN_CFG["Other"]["watermark"]:
            msg.text = f"{self.MAIN_CFG['Other']['watermark']}\n" + msg.text

        response = self.account.send_message(msg)
        if response.get("response") and response.get("response").get("error") is None:
            self.runner.update_saved_message(msg)
            logger.info(f"Отправил сообщение в чат $YELLOW{msg.node_id}.")
            return True
        else:
            logger.warning(f"Произошла ошибка при отправке сообщения в чат $YELLOW{msg.node_id}.$RESET Подробнее "
                           f"в файле logs/log.log")
            return False

    def update_session(self):
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
        instance_id = self.run_id
        for event in self.runner.listen():
            if instance_id != self.run_id:
                break
            if event.type == FunPayAPI.types.EventTypes.NEW_MESSAGE:
                self.run_handlers(self.new_message_handlers, (self, event))
            elif event.type == FunPayAPI.types.EventTypes.NEW_ORDER:
                self.run_handlers(self.new_order_handlers, (self, event))
            elif event.type == FunPayAPI.types.EventTypes.ORDER_STATUS_CHANGED:
                self.run_handlers(self.order_status_changed_handlers, (self, event))

    def lots_raise_loop(self):
        """
        Запускает бесконечный цикл поднятия категорий (если autoRaise в _main.cfg == 1)
        """
        logger.info("$CYANЦикл авто-поднятия лотов запущен (это не значит, что авто-поднятие лотов включено).")
        while True:
            if not self.MAIN_CFG["FunPay"].getboolean("autoRaise"):
                time.sleep(10)
                continue
            try:
                next_time = self.raise_lots()
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
        logger.info("$CYANЦикл обновления данных аккаунта запущен.")
        sleep_time = 3600
        while True:
            time.sleep(sleep_time)
            result = self.update_session()
            sleep_time = 60 if not result else 3600

    # Управление процессом
    def init(self):
        self.block_list = cardinal_tools.load_block_list()
        self.__init_account()
        self.__init_lots_and_categories()

        self.__add_handlers(handlers)
        self.__load_plugins()

        if int(self.MAIN_CFG["Telegram"]["enabled"]):
            self.__init_telegram()
            self.__add_handlers(auto_response_cp)
            self.__add_handlers(auto_delivery_cp)
            self.__add_handlers(config_loader_cp)
            self.__add_handlers(file_uploader)

        self.run_handlers(self.post_init_handlers, (self, ))

    def run(self):
        self.run_id += 1
        self.start_time = int(time.time())
        self.run_handlers(self.pre_start_handlers, (self,))
        self.run_handlers(self.post_start_handlers, (self,))

        if self.telegram:
            Thread(target=self.telegram.run, daemon=True).start()
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

    def run_handlers(self, handlers: list[Callable], args) -> None:
        """
        Выполняет функции из списка handlers.

        :param handlers: Список функций.
        :param args: аргументы для функций.
        """
        for func in handlers:
            try:
                func(*args)
            except:
                logger.error("Произошла ошибка при выполнении хэндлера. Подробнее в файле logs/log.log.")
                logger.debug(traceback.format_exc())

    def save_config(self, config: configparser.ConfigParser, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            config.write(f)

    def update_secret_key(self):
        self.secret_key = random.randint(10000000, 999999999)