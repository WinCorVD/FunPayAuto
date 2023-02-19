"""
CBT - CallBack Texts. В данном модуле расписаны все CallBack'и для Telegram клавиатуры (+ User-state'ы)
"""

# Основное меню
MAIN = "1"
"""
Callback для открытия основного меню настроек.
"""

CATEGORY = "2"
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

SWITCH = "3"
"""
Callback для переключения определенного параметра из основного конфига.
Использование: CBT.SWITCH:section_name:option_name

section_name: название секции.
option_name: название опции.
"""


# Настройки авто-ответчика
ADD_CMD = "4"
"""
Callback для активации режима ввода текста новой команды / сета команд.


User-state: ожидается сообщение с текстом новой команды / сета команд.
"""


CMD_LIST = "5"
"""
Callback для открытия списка команд.
Использование: CBT.CMD_LIST:offset

offset: int - смещение списка команд.
"""


EDIT_CMD = "6"
"""
Callback для открытия меню редактирования команды.
Использование: CBT.EDIT_CMD:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


EDIT_CMD_RESPONSE_TEXT = "7"
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


EDIT_CMD_NOTIFICATION_TEXT = "8"
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


SWITCH_CMD_NOTIFICATION = "9"
"""
Callback для вкл/выкл Telegram уведомления об использовании команды.
Использование: CBT.SWITCH_CMD_NOTIFICATION:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


DEL_CMD = "10"
"""
Callback для удаления команды из конфига авто-ответчика.
Использование: CBT.DEL_CMD:command_index:offset

command_index: int - числовой индекс команды.
offset: int - смещение списка команд.
"""


# FUNPAY LOTS LIST
FP_LOTS_LIST = "11"
"""
Callback для открытия списка лотов, спарсенных напрямую с Funpay.
Использование: CBT.FP_LOTS_LIST:offset

offset: int - смещение списка FunPay лотов.
"""

ADD_AD_TO_LOT = "12"
"""
Callback для подключения к лоту авто-выдачи.
Использование: CBT.ADD_AD_TO_LOT:lot_index:offset

lot_index: int - числовой индекс FunPay лота.
offset: int - смещение списка FunPay лотов.
"""

ADD_AD_TO_LOT_MANUALLY = "13"
"""
Callback для активации режима ввода названия лота для подключения к нему авто-выдачи.
Использование: CBT.ADD_AD_TO_LOT_MANUALLY:offset

offset: int - смещение списка FunPay лотов.


User-state: ожидается сообщение с названием лота для подключения к нему авто-выдачи.
data:
offset: int - смещение списка FunPay лотов.
"""


# Настройки лотов с авто-выдачей
AD_LOTS_LIST = "14"
"""
Callback для открытия списка лотов с авто-выдачей.
Использование: CBT.AD_LOTS_LIST:offset

offset: int - смещение списка лотов с авто-выдачей.
"""


EDIT_AD_LOT = "15"
"""
Callback для открытия меню редактирования авто-выдачи лота.
Использование: CBT.EDIT_AD_LOT:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.
"""


EDIT_LOT_DELIVERY_TEXT = "16"
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


BIND_PRODUCTS_FILE = "17"
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


DEL_AD_LOT = "18"
"""
Callback для удаления лота из конфига авто-выдачи.
Использование: CBT.DEL_AD_LOT:lot_index:offset

lot_index: int - числовой индекс лота с авто-выдачей.
offset: int - смещение списка лотов с авто-выдачей.
"""


# Настройки файлов с товарами
PRODUCTS_FILES_LIST = "19"
"""
Callback для открытия списка файлов с товарами.
Использование: CBT.PRODUCTS_FILES_LIST:offset

offset:int - смещение списка файлов с товарами.
"""


EDIT_PRODUCTS_FILE = "20"
"""
Callback для открытия меню редактирования файла с товарами.
Использование: CBT.EDIT_PRODUCTS_FILE:file_index:offset

file_index: int - числовой индекс файла с товарами.
offset: int - смещение списка файлов с товарами.
"""


UPLOAD_PRODUCTS_FILE = "21"
"""
Callback для активации режима выгрузки файла с товарами.


User-state: ожидается сообщение с файлом с товарами.
"""


CREATE_PRODUCTS_FILE = "22"
"""
Callback для активации режима ввода названия нового товарного файла.


User-state: ожидается сообщение с названием нового товарного файла.
"""

ADD_PRODUCTS_TO_FILE = "23"
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
DOWNLOAD_CFG = "24"
"""
Callback для отправки файла конфига
Использование: CBT.DOWNLOAD_CFG:config

config: str - тип конфига.
    main - основной конфиг configs/_main.cfg
    autoResponse - конфиг авто-ответчика configs/auto_response.cfg
    autoDelivery - конфиг авто-выдачи configs/auto_delivery.cfg
"""


# Шаблоны ответов
TMPLT_LIST = "25"
"""
Callback для открытия списка шаблонов ответа.
Использование: CBT.TMPLT_LIST:offset

offset: int - смещение списка шаблонов ответа.
"""


TMPLT_LIST_ANS_MODE = "26"
"""
Callback для открытия списка шаблонов ответа в режиме ответа.
Использование: CBT.TMPLT_LIST_ANS_MODE:offset:node_id:username:prev:order_id

offset: int - смещение списка шаблонов ответа.
node_id: int - ID переписки, в которую нужно отправить шаблон.
username: str - имя пользователя, с которым ведется переписка.
"""


EDIT_TMPLT = "27"
"""
Callback для открытия меню изменения шаблона ответа.
Использование: CBT.EDIT_TMPLT:template_index:offset

template_index: int - числовой индекс шаблона ответа.
offset: int - смещение списка шаблонов ответа.
"""


DEL_TMPLT = "28"
"""
Callback для удаления шаблона ответа.
Использование: CBT.DEL_TMPLT:template_index:offset

template_index: int - числовой индекс шаблона ответа.
offset: int - смещение списка шаблонов ответа.
"""


ADD_TMPLT = "29"
"""
Callback для активации режима ввода текста нового шаблона ответа.
Использование: CBT.ADD_TMPLT:offset

offset: int - смещение списка шаблонов ответа.


User-state: ожидается сообщение с текстом нового шаблона ответа.
data:
offset: int - смещение списка шаблонов ответа.
"""

SEND_TMPLT = "30"
"""
Callback для отправки шаблона в ЛС FunPay.
Использование: CBT.SEND_TMPLT:index:node_id:username

index: int - числовой индекс шаблона.
node_id: int - ID переписки, в которую нужно отправить шаблон.
username: str - имя пользователя, с которым ведется переписка.
"""


# Прочее
SWITCH_TG_NOTIFICATIONS = "31"
"""
Callback для вкл. / выкл. определенного типа уведомлений в определенном Telegram чате.
Использование: switch_tg_notification:chat_id:notification_type

chat_id: int - ID Telegram чата.
notification_type: str - тип уведомлений (tg_bot.utils.NotificationTypes)
"""


REQUEST_REFUND = "32"
"""
Callback для обновления меню с действиями по заказу (уточнение по возврату средств)
Использование: CBT.REQUEST_REFUND:order_id

order_id: str - ID заказа (без #)
"""

REFUND_CONFIRMED = "33"
"""
Callback для подтверждения возврата средств.
Использование: CBT.REFUND_CONFIRMED:order_id

order_id: str - ID заказа (без #)
"""

REFUND_CANCELLED = "34"
"""
Callback для отмены возврата средств.
Использование: CBT.REFUND_CANCELLED:order_id

order_id: str - ID заказа (без #)
"""


BAN = "35"
"""
Callback для активации режима ввода никнейма FunPay пользователя для добавления его в ЧС.


User-state: ожидается сообщение с никнеймом FunPay пользователя для добавления его в ЧС.
"""

UNBAN = "36"
"""
Callback для активации режима ввода никнейма FunPay пользователя для удаления его из ЧС.


User-state: ожидается сообщение с никнеймом FunPay пользователя для удаления его из ЧС.
"""


SHUT_DOWN = "37"
"""
Callback для отключения бота.
Использование: CBT.SHUT_DOWN:stage:instance_id

stage: int - текущая стадия подтверждения (0-6)
instance_id: int - ID запуска FPC.
"""

CANCEL_SHUTTING_DOWN = "38"
"""
Callback для отмены отключения бота.
"""


SEND_FP_MESSAGE = "to_node"
"""
Callback для отправки сообщения в чат FunPay.
Использование: CBT.SEND_FP_MESSAGE:node_id:username

node_id: int - ID переписки, в которую нужно отправить сообщение.
username: str - никнейм пользователя, переписка с которым ведется.
"""


UPDATE_PROFILE = "39"
"""
Callback для обновления статистики аккаунта.
"""


MANUAL_AD_TEST = "40"
"""
Callback для активации режима ввода названия лота для теста авто-выдачи.


User-state: ожидается сообщение с названием лота для теста авто-выдачи.
"""


CLEAR_USER_STATE = "41"
"""
Callback для установки состояния пользователя на None.
"""