from configparser import ConfigParser, SectionProxy
import itertools
import codecs
import os

from Utils.exceptions import (ParamNotFoundError, EmptyValueError, ValueNotValidError, SectionNotFoundError,
                              ConfigParseError, ProductsFileNotFoundError, NoProductsError, NoProductVarError,
                              SubCommandAlreadyExists)


def check_param(param_name: str, section: SectionProxy, valid_values: list[str | None] | None = None,
                raise_if_not_exists: bool = True) -> str | None:
    """
    Проверяет, существует ли в переданной секции указанный параметр и если да, валидно ли его значение.
    :param param_name: название параметра.
    :param section: объект секции.
    :param valid_values: валидные значения. Если None - любая строка - валидное значение.
    :param raise_if_not_exists: райзить ли исключение, если параметр не найден.
    :return: Значение ключа, если ключ найден и его значение валидно. Если ключ не найден и
    raise_ex_if_not_exists == False - возвращает None. В любом другом случае райзит исключения.
    """
    if param_name not in list(section.keys()):
        if raise_if_not_exists:
            raise ParamNotFoundError(param_name)
        return None

    value = section[param_name].strip()

    # Если значение пустое ("", оно не может быть None)
    if not value:
        if valid_values and None in valid_values:
            return value
        raise EmptyValueError(param_name)

    if valid_values and value not in valid_values:
        raise ValueNotValidError(param_name, value, valid_values)
    return value


def create_config_obj(config_path: str) -> ConfigParser:
    """
    Создает объект конфига с нужными настройками.
    :param config_path: путь до файла конфига.
    :return: объект конфига.
    """
    config = ConfigParser(delimiters=(":", ))
    config.optionxform = str
    config.read_file(codecs.open(config_path, "r", "utf8"))
    return config


def load_main_config(config_path: str):
    """
    Парсит и проверяет на правильность основной конфиг.
    :param config_path: путь до основного конфига.
    :return: спарсеный основной конфиг.
    """
    config = create_config_obj(config_path)
    values = {
        "FunPay": {
            "golden_key": "any",
            "user_agent": "any",
            "autoRaise": ["0", "1"],
            "autoResponse": ["0", "1"],
            "autoDelivery": ["0", "1"],
            "autoRestore": ["0", "1"]
        },
        "Telegram": {
            "enabled": ["0", "1"],
            "token": "any",
            "secretKey": "any",
            "lotsRaiseNotification": ["0", "1"],
            "productsDeliveryNotification": ["0", "1"],
            "newMessageNotification": ["0", "1"]
        },
        "Other": {
            "watermark": "any"
        }
    }

    for section_name in values:
        if section_name not in config.sections():
            raise ConfigParseError(config_path, section_name, SectionNotFoundError())

        for param_name in values[section_name]:
            try:
                if values[section_name][param_name] == "any":
                    check_param(param_name, config[section_name])
                else:
                    check_param(param_name, config[section_name], valid_values=values[section_name][param_name])
            except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
                raise ConfigParseError(config_path, section_name, e)
        return config


def load_auto_response_config(config_path: str):
    """
    Парсит и проверяет на правильность конфиг команд.

    :param config_path: путь до конфига команд.
    :return: спарсеный конфиг команд.
    """
    config = create_config_obj(config_path)
    command_sets = []
    for command in config.sections():
        try:
            check_param("response", config[command])
            check_param("telegramNotification", config[command], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("notificationText", config[command], raise_if_not_exists=False)
        except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
            raise ConfigParseError(config_path, command, e)

        if "|" in command:
            command_sets.append(command)

    for command_set in command_sets:
        commands = command_set.split("|")
        parameters = config[command_set]

        for new_command in commands:
            new_command = new_command.strip()
            if not new_command:
                continue
            if new_command in config.sections():
                raise ConfigParseError(config_path, command_set, SubCommandAlreadyExists(new_command))
            config.add_section(new_command)
            for param_name in parameters:
                config.set(new_command, param_name, parameters[param_name])

    return config


def load_raw_auto_response_config(config_path: str):
    """
    Загружает исходный конфиг авто-ответчика.

    :param config_path: путь до конфига команд.
    :return: спарсеный конфиг команд.
    """
    config = create_config_obj(config_path)
    return config


def load_auto_delivery_config(config_path: str):
    """
    Парсит и проверяет на правильность конфиг авто-выдачи.

    :param config_path: путь до конфига авто-выдачи.
    :return: спарсеный конфиг товаров для авто-выдачи.
    """
    config = create_config_obj(config_path)

    for lot_title in config.sections():
        try:
            # Проверяем обязательный параметр response.
            lot_response = check_param("response", config[lot_title])
            check_param("disable", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("disableAutoRestore", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            check_param("disableAutoDisable", config[lot_title], valid_values=["0", "1"], raise_if_not_exists=False)
            # Проверяем указан параметр productsFileName.
            products_file_name = check_param("productsFileName", config[lot_title], raise_if_not_exists=False)
            if products_file_name is None:
                # Если данного параметра нет, то в текущем лоте более нечего проверять -> переход на след. итерацию.
                continue
        except (ParamNotFoundError, EmptyValueError, ValueNotValidError) as e:
            raise ConfigParseError(config_path, lot_title, e)

        # Проверяем, существует ли файл.
        if not os.path.exists(f"storage/products/{products_file_name}"):
            raise ConfigParseError(config_path, lot_title,
                                   ProductsFileNotFoundError(f"storage/products/{products_file_name}"))

        # Проверяем, есть ли хотя бы 1 переменная $product в тексте response.
        if "$product" not in lot_response:
            raise ConfigParseError(config_path, lot_title, NoProductVarError())
    return config
