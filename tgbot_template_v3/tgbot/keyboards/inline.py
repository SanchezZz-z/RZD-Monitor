from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# This is a simple keyboard, that contains 2 buttons
def very_simple_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="📝 Створити замовлення",
                                 callback_data="create_order"),
            InlineKeyboardButton(text="📋 Мої замовлення", callback_data="my_orders"),
        ],
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )
    return keyboard


# This is the same keyboard, but created with InlineKeyboardBuilder (preferred way)
def simple_menu_keyboard():
    # First, you should create an InlineKeyboardBuilder object
    keyboard = InlineKeyboardBuilder()

    # You can use keyboard.button() method to add buttons, then enter text and callback_data
    keyboard.button(
        text="📝 Створити замовлення",
        callback_data="create_order"
    )
    keyboard.button(
        text="📋 Мої замовлення",
        # In this simple example, we use a string as callback_data
        callback_data="my_orders"
    )

    # If needed you can use keyboard.adjust() method to change the number of buttons per row
    # keyboard.adjust(2)

    # Then you should always call keyboard.as_markup() method to get a valid InlineKeyboardMarkup object
    return keyboard.as_markup()


# For a more advanced usage of callback_data, you can use the CallbackData factory
class OrderCallbackData(CallbackData, prefix="order"):
    """
    This class represents a CallbackData object for orders.

    - When used in InlineKeyboardMarkup, you have to create an instance of this class, run .pack() method,
    and pass to callback_data parameter.

    - When used in InlineKeyboardBuilder, you have to create an instance of this class and pass to callback_data
    parameter (without .pack() method).

    - In handlers you have to import this class and use it as a filter for callback query handlers, and then unpack
    callback_data parameter to get the data.

    # Example usage in simple_menu.py
    """
    order_id: int


def my_orders_keyboard(orders: list):
    # Here we use a list of orders as a parameter (from simple_menu.py)

    keyboard = InlineKeyboardBuilder()
    for order in orders:
        keyboard.button(
            text=f"📝 {order['title']}",
            # Here we use an instance of OrderCallbackData class as callback_data parameter
            # order id is the field in OrderCallbackData class, that we defined above
            callback_data=OrderCallbackData(order_id=order["id"])
        )

    return keyboard.as_markup()


def right_wrong_inline_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="\U00002705",
        callback_data="correct"
    )
    keyboard.button(
        text="\U0000274C",
        callback_data="wrong"
    )

    return keyboard.as_markup()


class StationOptionCallbackData(CallbackData, prefix="station_option"):
    """
    This class represents a CallbackData object for options.

    - When used in InlineKeyboardMarkup, you have to create an instance of this class, run .pack() method,
    and pass to callback_data parameter.

    - When used in InlineKeyboardBuilder, you have to create an instance of this class and pass to callback_data
    parameter (without .pack() method).

    - In handlers you have to import this class and use it as a filter for callback query handlers, and then unpack
    callback_data parameter to get the data.
    """
    option_num: int


# Функция вызова клавиатуры для выбора станции отправления / назначения
def confirm_station_inline_keyboard(station_options: list):
    station_options_kb = InlineKeyboardBuilder()

    for i in range(1, len(station_options) + 1):
        station_options_kb.button(
            text="{}".format(i),
            callback_data=StationOptionCallbackData(option_num=i)
        )
    station_options_kb.adjust(5)

    retry_kb = InlineKeyboardBuilder()

    retry_kb.button(
        text="Ввести название станции еще раз",
        callback_data=StationOptionCallbackData(option_num=0)
    )

    station_options_kb.attach(retry_kb)

    return station_options_kb.as_markup()


# Клавиатура выбора действия со списком поездов
def start_menu_inline_keyboard(menu_type: str, msg: str):
    keyboard = InlineKeyboardBuilder()

    # Текст в зависимости от типа меню
    menu_text = "поезд" if menu_type == "train" else "монитор"
    # Если у пользователя есть поезда / мониторы, то у него 2 варианта (удалить или добавить)
    if msg:
        keyboard.button(
            text="Удалить {}".format(menu_text),
            callback_data="delete_{}".format(menu_type)
        )
    # В любом случае предлагаем добавить поезд / монитор или вернуться в главное меню
    keyboard.button(
        text="Добавить {}".format(menu_text),
        callback_data="add_{}".format(menu_type)
    )
    keyboard.button(
        text="Назад в главное меню",
        callback_data="main_menu"
    )

    keyboard.adjust(1)

    return keyboard.as_markup()


class UserTrainToDeleteOptionCallbackData(CallbackData, prefix="user_train_to_delete_option"):
    option_num: int


class UserMonitorToDeleteOptionCallbackData(CallbackData, prefix="user_monitor_to_delete_option"):
    option_num: int


# Клавиатура для выбора нескольких вариантов
def few_options_inline_keyboard(menu, options_list_len, selected_options):
    options_kb = InlineKeyboardBuilder()

    # Выбор класса callback_data на основе меню
    callback_data_cls = (UserTrainToDeleteOptionCallbackData if menu == "train" else
                         UserMonitorToDeleteOptionCallbackData)

    for i in range(1, options_list_len + 1):
        # Добавляем галочку рядом с выбранным вариантом
        button_text = "{} {}".format(i, "\U00002611\U0000FE0F" if i in selected_options else "")
        options_kb.button(text=button_text, callback_data=callback_data_cls(option_num=i))

    options_kb.adjust(2)

    done_or_back_kb = InlineKeyboardBuilder()

    done_or_back_kb.button(text="Готово", callback_data=callback_data_cls(option_num=0))
    done_or_back_kb.button(text="Назад", callback_data=callback_data_cls(option_num=-1))

    done_or_back_kb.adjust(1)

    options_kb.attach(done_or_back_kb)

    return options_kb.as_markup()


class UserTrainToMonitorOptionCallbackData(CallbackData, prefix="user_train_to_monitor_option"):
    option_num: int


# Функция вызова клавиатуры для выбора поезда для отслеживания билетов
def select_train_to_monitor_inline_keyboard(train_options: list):
    train_options_kb = InlineKeyboardBuilder()

    for i in range(1, len(train_options) + 1):
        train_options_kb.button(
            text="{}".format(i),
            callback_data=UserTrainToMonitorOptionCallbackData(option_num=i)
        )
    train_options_kb.adjust(5)

    back_kb = InlineKeyboardBuilder()

    back_kb.button(
        text="Назад",
        callback_data=UserTrainToMonitorOptionCallbackData(option_num=0)
    )

    train_options_kb.attach(back_kb)

    return train_options_kb.as_markup()


# Функция вызова клавиатуры для выбора типа вагона (купе, плацкарт, СВ, люкс)
def select_car_type_inline_keyboard(two_storey: bool, has_premium: bool, selected_options):
    car_type_options_kb = InlineKeyboardBuilder()

    # Функция для создания кнопки
    def create_button(kb, text, option):
        check_mark = "\U00002611\U0000FE0F" if option in selected_options else ""
        kb.button(text="{} {}".format(text, check_mark), callback_data=option)

    # Добавление кнопок в зависимости от условий
    # В двухэтажных поездах не бывает плацкартных вагонов
    if two_storey:
        create_button(car_type_options_kb, "Купе", "coupe")
        create_button(car_type_options_kb, "СВ", "lux")
        # Люкс тоже бывает не во всех поездах
        if has_premium:
            create_button(car_type_options_kb, "Люкс", "premium")
    else:
        create_button(car_type_options_kb, "Плацкарт", "plaz")
        create_button(car_type_options_kb, "Купе", "coupe")
        create_button(car_type_options_kb, "СВ", "lux")
        if has_premium:
            create_button(car_type_options_kb, "Люкс", "premium")

    car_type_options_kb.adjust(2)

    disabled_kb = InlineKeyboardBuilder()

    create_button(disabled_kb, "\U0000267F\U0000FE0F", "disabled")

    disabled_kb.adjust(1)

    car_type_options_kb.attach(disabled_kb)

    done_kb = InlineKeyboardBuilder()

    done_kb.button(
        text="Готово",
        callback_data="done"
    )

    done_kb.adjust(1)

    car_type_options_kb.attach(done_kb)

    return car_type_options_kb.as_markup()


# Функция вызова клавиатуры для выбора пола
def select_gender_inline_keyboard():
    gender_kb = InlineKeyboardBuilder()

    gender_kb.button(
        text="Мужской",
        callback_data="male"
    )
    gender_kb.button(
        text="Женский",
        callback_data="female"
    )

    gender_kb.adjust(2)

    return gender_kb.as_markup()


# Функция вызова клавиатуры для вопроса о желании ехать в "однополом" купе
def ask_same_gender_inline_keyboard():
    ask_same_gender_kb = InlineKeyboardBuilder()

    ask_same_gender_kb.button(
        text="Да",
        callback_data="True"
    )
    ask_same_gender_kb.button(
        text="Все равно",
        callback_data="False"
    )

    ask_same_gender_kb.adjust(2)

    return ask_same_gender_kb.as_markup()


# Функция вызова клавиатуры для вопроса о желании ехать в "однополом" купе
def pets_allowed_inline_keyboard():
    pets_allowed_kb = InlineKeyboardBuilder()

    pets_allowed_kb.button(
        text="Да",
        callback_data="no_pets"
    )
    pets_allowed_kb.button(
        text="Нет, я еду с животным",
        callback_data="pets"
    )
    pets_allowed_kb.button(
        text="Нет, мне все равно",
        callback_data="whatever"
    )

    pets_allowed_kb.adjust(2)

    return pets_allowed_kb.as_markup()


# Функция вызова клавиатуры для выбора типа мест (предлагаемый перечень мест зависит от выбранных ранее типов вагонов)
def seat_types_inline_keyboard(selected_car_types: list, two_storey: bool, selected_options: list):
    seat_types_kb = InlineKeyboardBuilder()

    # Функция для создания кнопки
    def create_button(text, option):
        check_mark = "\U00002611\U0000FE0F" if option in selected_options else ""
        seat_types_kb.button(text="{} {}".format(text, check_mark), callback_data=option)

    # При любом раскладе надо предложить нижнее и верхнее места
    create_button("Нижнее", "lower")
    create_button("Верхнее", "upper")

    # Если поезд двухэтажный, тогда добавляем верхнее на втором этаже
    if two_storey:
        create_button("Верхнее на втором этаже", "two_storey_upper")

    # Если в списке выбранных вагонов есть плацкарт, то добавляем боковые места
    if "plaz" in selected_car_types:
        create_button("Нижнее боковое", "side_lower")
        create_button("Верхнее боковое", "side_upper")

    seat_types_kb.adjust(1)

    done_kb = InlineKeyboardBuilder()

    done_kb.button(
        text="Готово",
        callback_data="done"
    )

    done_kb.adjust(1)

    seat_types_kb.attach(done_kb)
    return seat_types_kb.as_markup()


# Обработчик коллбэков для восстановления мониторов
class RestoreMonitor(CallbackData, prefix="mon"):
    task_id: int
    train_id: int


# Клавиатура для восстановления монитора
def restore_monitor_task_inline_keyboard(task_id, train_id):
    restore_monitor_task_kb = InlineKeyboardBuilder()

    restore_monitor_task_kb.button(
        text="Восстановить монитор",
        callback_data=RestoreMonitor(task_id=task_id, train_id=train_id)
    )

    restore_monitor_task_kb.adjust(1)

    return restore_monitor_task_kb.as_markup()


class UserTrainToCheckFreeSeatsOptionCallbackData(CallbackData, prefix="user_train_to_check_option"):
    option_num: int


# Функция вызова клавиатуры для выбора поезда для проверки свободных мест
def select_train_to_check_free_seats_inline_keyboard(train_options: list):
    train_options_kb = InlineKeyboardBuilder()

    for i in range(1, len(train_options) + 1):
        train_options_kb.button(
            text="{}".format(i),
            callback_data=UserTrainToCheckFreeSeatsOptionCallbackData(option_num=i)
        )
    train_options_kb.adjust(5)

    back_kb = InlineKeyboardBuilder()

    back_kb.button(
        text="Назад в главное меню",
        callback_data="main_menu"
    )

    train_options_kb.attach(back_kb)

    return train_options_kb.as_markup()
