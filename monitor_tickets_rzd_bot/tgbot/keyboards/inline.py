from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from monitor_tickets_rzd_bot.const import LASTOCHKA_DIRECTIONS, LASTOCHKA_TABLES, LASTOCHKA_CAR_TYPES, LASTOCHKA_SPECIAL_SEATS


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

class TrainTypesOptionCallbackData(CallbackData, prefix="train_type_option"):
    train_type: int

# Функция вызова клавиатуры для выбора поезда для отслеживания билетов
def select_train_type_inline_keyboard(train_types: list):
    train_types_kb = InlineKeyboardBuilder()

    for train_type in train_types:
        train_types_kb.button(
            text="{}".format(train_type["train_type"]),
            callback_data=TrainTypesOptionCallbackData(train_type=train_type["id"])
        )
    train_types_kb.adjust(1)

    return train_types_kb.as_markup()

# Функция вызова клавиатуры для выбора особых мест в Ласточке (либо инвалидных, либо с перевозкой животных)
def select_seat_preference_lasto4ka_inline_keyboard(selected_options: list):

    seat_preference_kb = InlineKeyboardBuilder()

    # Функция для создания кнопки
    def create_button(text, option):
        check_mark = "\U00002611\U0000FE0F" if option in selected_options else ""
        seat_preference_kb.button(text="{} {}".format(text, check_mark), callback_data=option)


    create_button("Место с провозом животных", "pets")
    create_button("Место для инвалида \U0000267F\U0000FE0F", "disabled")
    create_button("Нет", "whatever")

    seat_preference_kb.adjust(1)

    return seat_preference_kb.as_markup()

# Функция вызова клавиатуры для вопроса о специальных местах
def select_sapsan_special_seats_inline_keyboard():

    special_seats_kb = InlineKeyboardBuilder()

    special_seats_kb.button(
        text="Я путешествую с ребёнком до 10 лет",
        callback_data="kids"
    )
    special_seats_kb.button(
        text="Я путешествую с ребёнком до 1 года",
        callback_data="babies"
    )
    special_seats_kb.button(
        text="Я путешествую с домашним животным",
        callback_data="pets"
    )
    special_seats_kb.button(
        text="Мне нужно место для инвалида",
        callback_data="disabled"
    )
    special_seats_kb.button(
        text="Нет, мне подойдут обычные места",
        callback_data="whatever"
    )

    special_seats_kb.adjust(1)

    return special_seats_kb.as_markup()

# Функция вызова клавиатуры для выбора типа вагона
def select_sapsan_car_type_inline_keyboard(special_seat: str, selected_options: list):

    car_type_options_kb = InlineKeyboardBuilder()

    # Функция для создания кнопки с галочкой
    def create_button(kb, text, option):
        check_mark = "\U00002611\U0000FE0F" if option in selected_options else ""
        kb.button(text="{} {}".format(text, check_mark), callback_data=option)

    # Все возможные вагоны
    all_car_types = [
        ("Первый класс", "first_class"),
        ("Купе-переговорная", "negotiation_coupe"),
        ("Бизнес-купе", "business_coupe"),
        ("Бизнес-класс", "business_class"),
        ("Купе-Сьют", "coupe_suite"),
        ("Вагон-бистро", "bistro_car"),
        ("Семейный", "family"),
        ("Эконом+", "eco_plus"),
        ("Эконом", "eco"),
        ("Базовый", "base")
    ]

    # Фильтрация в зависимости от special_seat
    if special_seat == "pets":
        car_types = [("Эконом", "eco"), ("Купе-Сьют", "coupe_suite")]
    else:  # kids, babies, whatever - все вагоны доступны
        car_types = all_car_types

    # Добавляем кнопки
    for text, option in car_types:
        create_button(car_type_options_kb, text, option)

    car_type_options_kb.adjust(2)

    done_kb = InlineKeyboardBuilder()

    done_kb.button(
        text="Готово",
        callback_data="done"
    )

    done_kb.adjust(1)
    car_type_options_kb.attach(done_kb)

    return car_type_options_kb.as_markup()

# Функция вызова клавиатуры для вопроса о направлении посадки (по ходу или против хода)
def select_sapsan_direction_inline_keyboard(selected_car_types: list):

    direction_kb = InlineKeyboardBuilder()
    direction_cars = {"first_class", "business_class", "bistro_car", "family", "eco_plus", "eco", "base"}

    if any(car in direction_cars for car in selected_car_types):
        direction_kb.button(text="По ходу движения", callback_data="forward")
        direction_kb.button(text="Против хода движения", callback_data="backwards")
        direction_kb.button(text="Мне всё равно", callback_data="whatever")
        direction_kb.adjust(2)
        return direction_kb.as_markup()
    return None

# Функция вызова клавиатуры для вопроса о столе
def select_sapsan_table_inline_keyboard(selected_car_types: list):
    table_kb = InlineKeyboardBuilder()
    table_choice_cars = {"business_class", "family", "eco_plus", "eco", "base"}

    if any(car in table_choice_cars for car in selected_car_types):
        table_kb.button(text="Да, нужен стол", callback_data="table")
        table_kb.button(text="Нет, не нужен стол", callback_data="no_table")
        table_kb.button(text="Мне всё равно", callback_data="whatever")
        table_kb.adjust(2)
        return table_kb.as_markup()
    return None

# Функция вызова клавиатуры для выбора типа места
def select_sapsan_seat_types_inline_keyboard(special_seat: str, selected_car_types: list, direction: str, table: str, selected_options: list):
    seat_types_kb = InlineKeyboardBuilder()

    def create_button(text, option):
        check_mark = "\U00002611\U0000FE0F" if option in selected_options else ""
        seat_types_kb.button(text="{} {}".format(text, check_mark), callback_data=option)

    all_seat_types = {
        "no_table": ("Не у стола", ["first_class", "business_class", "family", "eco_plus", "eco", "base"]),
        "table": ("У стола", ["business_class", "bistro_car", "family", "eco_plus", "eco", "base", "negotiation_coupe", "business_coupe", "coupe_suite"]),
        "separate": ("Отдельные места", ["first_class"]),
        "no_window": ("Без окна", ["eco", "base"]),
        "coupe": ("Купе", ["negotiation_coupe", "business_coupe", "coupe_suite"]),
        "pets": ("Для проезда с животными", ["eco"]),
        "kids": ("Место для пассажира с детьми", ["family", "eco_plus"]),
        "babies": ("Место для матери и ребёнка", ["eco_plus"])
    }

    if special_seat == "kids":
        available_seats = {k: v for k, v in all_seat_types.items() if k != "babies"}  # Исключаем babies
    elif special_seat == "babies":
        available_seats = {k: v for k, v in all_seat_types.items() if k != "kids"}  # Исключаем kids
    elif special_seat == "whatever":
        available_seats = {k: v for k, v in all_seat_types.items() if k not in ["kids", "babies"]}
    else:  # pets и disabled обрабатываются раньше
        return None

    valid_seat_types = []
    for seat_type, (text, cars) in available_seats.items():
        if any(car in selected_car_types for car in cars):
            # Исключаем взаимоисключающие варианты стола
            if (seat_type == "table" and table == "no_table") or (seat_type == "no_table" and table == "table"):
                continue
            # Исключаем "no_window", если выбран "table"
            if seat_type == "no_window" and table == "table":
                continue
            # Условие для family и backwards
            if "family" in selected_car_types and seat_type in ["no_table", "table",
                                                                "kids"] and direction == "backwards":
                continue
            valid_seat_types.append((text, seat_type))

    # Если только один вариант, возвращаем его как строку
    if len(valid_seat_types) == 1:
        return valid_seat_types[0][1]  # Возвращаем seat_type, например "table"

    # Иначе формируем клавиатуру
    for text, seat_type in valid_seat_types:
        create_button(text, seat_type)

    seat_types_kb.adjust(1)

    done_kb = InlineKeyboardBuilder()

    done_kb.button(
        text="Готово",
        callback_data="done"
    )

    done_kb.adjust(1)
    seat_types_kb.attach(done_kb)

    return seat_types_kb.as_markup()


def select_lastochka_special_seats_inline_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, text in LASTOCHKA_SPECIAL_SEATS.items():
        kb.button(text=text, callback_data=key)
    kb.adjust(1)
    return kb.as_markup()


def select_lastochka_car_type_inline_keyboard(special_seat: str, selected: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, text in LASTOCHKA_CAR_TYPES.items():
        if special_seat == "whatever" or not special_seat:  # Ограничения по специальным местам уже учтены ранее
            check_mark = "\U00002611\U0000FE0F" if key in selected else ""
            kb.button(text=f"{text} {check_mark}", callback_data=key)
    kb.button(text="Готово", callback_data="done")
    kb.adjust(1)
    return kb.as_markup()


def select_lastochka_sapsan_any_seat_inline_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data="yes")
    kb.button(text="Нет", callback_data="no")
    kb.adjust(1)
    return kb.as_markup()


def select_lastochka_direction_inline_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, text in LASTOCHKA_DIRECTIONS.items():
        kb.button(text=text, callback_data=key)
    kb.adjust(1)
    return kb.as_markup()


def select_lastochka_table_inline_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, text in LASTOCHKA_TABLES.items():
        kb.button(text=text, callback_data=key)
    kb.adjust(1)
    return kb.as_markup()


def select_lastochka_seat_types_inline_keyboard(car_types: list, selected: list, special_seat: str = None) -> InlineKeyboardMarkup | str:
    kb = InlineKeyboardBuilder()

    available_seat_types = []
    if "eco" in car_types:
        available_seat_types.append(("window", "У окна"))
        available_seat_types.append(("no_window", "Без окна"))
        if special_seat == "whatever":
            available_seat_types.append(("pets", "Для проезда с животными"))
    if "base" in car_types:
        available_seat_types.append(("window", "У окна"))
        available_seat_types.append(("no_window", "Без окна"))

    available_seat_types = list(set(available_seat_types))

    # Если остался только один вариант, возвращаем его как строку
    if len(available_seat_types) == 1:
        return available_seat_types[0][0]

    # Если нет доступных вариантов, показываем только "Готово"
    if not available_seat_types:
        kb.button(text="Готово", callback_data="done")
        kb.adjust(1)
        return kb.as_markup()

    # Добавляем кнопки для всех доступных вариантов с галочкой для выбранных
    for seat_type, text in available_seat_types:
        check_mark = "\U00002611\U0000FE0F" if seat_type in selected else ""
        kb.button(text="{} {}".format(text, check_mark), callback_data=seat_type)

    kb.button(text="Готово", callback_data="done")
    kb.adjust(1)
    return kb.as_markup()
