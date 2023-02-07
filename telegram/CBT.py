"""
CBT - CallBack Texts. В данном модуле расписаны все CallBack'и для Telegram клавиатуры (+ User-state'ы)
"""

# Основное меню
MAIN = "settings_main_page"
"""
Callback для открытия основного меню настроек.
"""


CATEGORY = "category"
"""
Callback для открытия определенной категории настроек.
Использование: CBT.CATEGORY:category_name

category_name: str - название категории настроек.
    main - основные переключатели.
    telegram - переключатели Telegram-уведомлений.
    autoResponse - настройки авто-ответчика.
    autoDelivery - настройки авто-выдачи.
    blockList - переключатели ЧС.
"""

SWITCH = "switch"
"""
Callback для переключения определенного параметра из основного конфига.
Использование: CBT.SWITCH:section_name:option_name

section_name: название секции.
option_name: название опции.
"""


# Настройки авто-ответчика
ADD_CMD = "add_command"
"""
Callback для активации режима ввода текста новой команды / сета команд.


User-state: ожидается сообщение с текстом новой команды / сета команд.
"""


CMD_LIST = "commands_list"
"""
Callback для открытия списка команд.
Использование: CBT.CMD_LIST:offset

offset: int - смещение списка команд.
"""


EDIT_CMD = "edit_command"
"""
Callback для открытия меню редактирования команды.
Использование: CBT.EDIT_CMD:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


EDIT_CMD_RESPONSE_TEXT = "edit_command_response_text"
"""
Callback для активации режима ввода нового текста ответа на команду.
Использование: CBT.EDIT_CMD_RESPONSE_TEXT:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.


User-state: ожидается сообщение с новым текстом ответа на команду.
data:
command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


EDIT_CMD_NOTIFICATION_TEXT = "edit_command_notification_text"
"""
Callback для активации режима ввода нового текста уведомления об использовании команде.
Использование: CBT.EDIT_CMD_NOTIFICATION_TEXT:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.


User-state: ожидается сообщение с новым текстом уведомления об использовании команде.
data:
command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


SWITCH_CMD_NOTIFICATION = "switch_command_notification"
"""
Callback для вкл/выкл Telegram уведомления об использовании команды.
Использование: CBT.SWITCH_CMD_NOTIFICATION:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


DEL_CMD = "delete_command"
"""
Callback для удаления команды из конфига авто-ответчика.
Использование: CBT.DEL_CMD:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


# FUNPAY LOTS LIST
FP_LOTS_LIST = "funpay_lots_list"
"""
Callback для открытия списка лотов, спарсенных напрямую с Funpay.
Использование: CBT.FP_LOTS_LIST:offset

offset: int - смещение списка FunPay лотов.
"""

ADD_AD_TO_LOT = "add_auto_delivery_to_lot"
"""
Callback для подключения к лоту авто-выдачи.
Использование: CBT.ADD_AD_TO_LOT:lot_index:offset

lot_index: int - числовой индекс FunPay лота.
offset: int - смещение списка FunPay лотов.
"""

ADD_AD_TO_LOT_MANUALLY = "add_auto_delivery_to_lot_manually"
"""
Callback для активации режима ввода названия лота для подключения к нему авто-выдачи.
Использование: CBT.ADD_AD_TO_LOT_MANUALLY:offset

offset: int - смещение списка FunPay лотов.


User-state: ожидается сообщение с названием лота для подключения к нему авто-выдачи.
data:
offset: int - смещение списка FunPay лотов.
"""


# Настройки лотов с авто-выдачей
AD_LOTS_LIST = "auto_delivery_lots_list"
"""
Callback для открытия списка лотов с авто-выдачей.
Использование: CBT.AD_LOTS_LIST:offset

offset: int - смещение списка лотов с авто-выдачей.
"""


EDIT_AD_LOT = "edit_auto_delivery_lot"
"""
Callback для открытия меню редактирования авто-выдачи лота.
Использование: CBT.EDIT_AD_LOT:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.
"""


EDIT_LOT_DELIVERY_TEXT = "edit_lot_delivery_text"
"""
Callback для активации режима ввода нового текста выдачи товара.
Использование: CBT.EDIT_LOT_DELIVERY_TEXT:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.

User-state: ожидается сообщение с новым текстом выдачи товара.
data:
lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с автовыдачей.
"""


BIND_PRODUCTS_FILE = "bind_product_file"
"""
Callback для активации режима ввода названия файла с товарами для привязки к лоту с авто-выдачей.
Использование: CBT.BIND_PRODUCTS_FILE:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.

User-state: ожидается сообщение с названием файла с товарами для привязки к лоту с авто-выдачей.
data:
lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с автовыдачей.
"""


DEL_AD_LOT = "delete_auto_delivery_lot"
"""
Callback для удаления лота из конфига авто-выдачи.
Использование: CBT.DEL_AD_LOT:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.
"""


# Настройки файлов с товарами
PRODUCTS_FILES_LIST = "products_files_list"
"""
Callback для открытия списка файлов с товарами.
Использование: CBT.PRODUCTS_FILES_LIST:offset

offset:int - смещение списка файлов с товарами.
"""


EDIT_PRODUCTS_FILE = "edit_products_file"
"""
Callback для открытия меню редактирования файла с товарами.
Использование: CBT.EDIT_PRODUCTS_FILE:file_index:offset

file_index: int - числовой индекс файла с товарами.
offset: int - смещение списка файлов с товарами.
"""


UPLOAD_PRODUCTS_FILE = "upload_products_file"
"""
Callback для активации режима выгрузки файла с товарами.


User-state: ожидается сообщение с файлом с товарами.
"""


CREATE_PRODUCTS_FILE = "create_products_file"
"""
Callback для активации режима ввода названия нового товарного файла.


User-state: ожидается сообщение с названием нового товарного файла.
"""

ADD_PRODUCTS_TO_FILE = "add_products_to_file"
"""
Callback для активации режима ввода товаров для последующего добавления их в товарный файл.
Использование: CBT.ADD_PRODUCTS_TO_FILE:file_index:index:offset:previous_page

file_index: int - числовой индекс файла с товарами.
element_index: int - числовой индекс файла с товарами / лота с авто-выдачей.
offset: int - смещение списка файлов с товарами / списка лотов с авто-выдачей.
previous_page: int - предыдущая страница.
    0 - страница редактирования файла с товарами.
    1 - страница редактирования авто-выдачи лота.


User-state: ожидается сообщение товарами для последующего добавления их в товарный файл.
data:
file_index: int - числовой индекс файла с товарами.
element_index: int - числовой индекс файла с товарами / лота с авто-выдачей.
offset: int - смещение списка файлов с товарами.
previous_page: int - предыдущая страница.
    0 - страница редактирования файла с товарами.
    1 - страница редактирования авто-выдачи лота.
"""


# Конфиги
DOWNLOAD_CFG = "download_config"
"""
Callback для отправки файла конфига
Использование: CBT.DOWNLOAD_CFG:config

config: str - тип конфига.
    main - основной конфиг configs/_main.cfg
    autoResponse - конфиг авто-ответчика configs/auto_response.cfg
    autoDelivery - конфиг авто-выдачи configs/auto_delivery.cfg
"""


# Прочее
SHUT_DOWN = "shut_down"
"""
Callback для отключения бота.
Использование: CBT.SHUT_DOWN:stage:instance_id

stage: int - текущая стадия подтверждения (0-6)
instance_id: int - ID запуска FPC.
"""


CANCEL_SHUTTING_DOWN = "cancel_shutting_down"
"""
Callback для отмены отключения бота.
"""
