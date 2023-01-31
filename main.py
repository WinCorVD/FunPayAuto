import logging.config
import os
import sys
import colorama
from colorama import Fore, Style
import traceback
import Utils.config_loader as cfg_loader
from Utils.logger import CONFIG
import Utils.exceptions as excs

from cardinal import Cardinal


# Инициируем цветной текст и логгер.
colorama.init()
if not os.path.exists("logs"):
    os.mkdir("logs")
logging.config.dictConfig(CONFIG)
logging.raiseExceptions = False
logger = logging.getLogger("main")
logger.debug("-------------------Новый запуск.-------------------")

print(f"""{Fore.MAGENTA}{Style.BRIGHT}█▀▀ █░█ █▄░█ █▀█ ▄▀█ █▄█  {Fore.CYAN} █▀▀ ▄▀█ █▀█ █▀▄ █ █▄░█ ▄▀█ █░░{Style.RESET_ALL}
{Fore.MAGENTA}{Style.BRIGHT}█▀░ █▄█ █░▀█ █▀▀ █▀█ ░█░  {Fore.CYAN} █▄▄ █▀█ █▀▄ █▄▀ █ █░▀█ █▀█ █▄▄{Style.RESET_ALL}""")
print(f"{Fore.RED}{Style.BRIGHT}v0.0.5b{Style.RESET_ALL}")
print("\n")
print(f"{Fore.MAGENTA}{Style.BRIGHT}By {Fore.BLUE}{Style.BRIGHT}Woopertail{Style.RESET_ALL}\n")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * GitHub: {Fore.BLUE}{Style.BRIGHT}github.com/woopertail/FunPayCardinal{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * Telegram: {Fore.BLUE}{Style.BRIGHT}t.me/funpay_cardinal")
print(f"{Fore.MAGENTA}{Style.BRIGHT} * VK: {Fore.BLUE}{Style.BRIGHT}vk.com/woopertail")
print("\n\n")


# Загружаем конфиги
e = None
try:
    logger.info("$MAGENTAЗагружаю конфиг _main.cfg...")
    MAIN_CONFIG = cfg_loader.load_main_config("configs/_main.cfg")

    logger.info("$MAGENTAЗагружаю конфиг auto_response.cfg...")
    AUTO_RESPONSE_CONFIG = cfg_loader.load_auto_response_config("configs/auto_response.cfg")
    RAW_AUTO_RESPONSE_CONFIG = cfg_loader.load_raw_auto_response_config("configs/auto_response.cfg")

    logger.info("$MAGENTAЗагружаю конфиг auto_delivery.cfg...")
    AUTO_DELIVERY_CONFIG = cfg_loader.load_auto_delivery_config("configs/auto_delivery.cfg")

except excs.ConfigParseError as e:
    logger.error(e)
    logger.error("Завершаю программу...")
    sys.exit()

except UnicodeDecodeError:
    logger.error("Произошла ошибка при расшифровке UTF-8. Убедитесь, что кодировка файла = UTF-8, "
                 "а формат конца строк = LF.")
    logger.error("Завершаю программу...")
    sys.exit()

except Exception as e:
    logger.critical("Произошла непредвиденная ошибка. Подробнее в файле logs/log.log.")
    logger.debug(traceback.format_exc())
    logger.error("Завершаю программу...")
    sys.exit()

# Запускаем основную программу Cardinal
if __name__ == '__main__':
    try:
        main_program = Cardinal(
            MAIN_CONFIG,
            AUTO_DELIVERY_CONFIG,
            AUTO_RESPONSE_CONFIG,
            RAW_AUTO_RESPONSE_CONFIG
        )
        main_program.init()
        main_program.run()
    except KeyboardInterrupt:
        logger.info("Завершаю программу...")
        sys.exit()
    except:
        logger.critical("При работе Кардинала произошла необработанная ошибка. Подробнее в файле logs/log.log")
        logger.debug(traceback.format_exc())
        logger.critical("Завершаю программу...")
        sys.exit()
