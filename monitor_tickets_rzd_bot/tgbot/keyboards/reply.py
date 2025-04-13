from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# Клавиатура для выбора станции из списка
def confirm_station_reply_keyboard(station_options: list):
    # Сделаем кастомную клавиатуру
    builder = ReplyKeyboardBuilder()
    # Первые ряды будут из кнопок с номерами станций
    for i in range(1, len(station_options) + 1):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5)
    # Последний ряд будет с предложением ввести название станции повторно
    builder.row(types.KeyboardButton(
        text="Ввести название станции еще раз"
    ))
    return builder


# Клавиатура для подтверждения верно / неверно
def right_wrong_reply_keyboard():
    # Сделаем кастомную клавиатуру
    builder = ReplyKeyboardBuilder()
    # Первые ряды будут из кнопок с номерами станций
    builder.row(
        types.KeyboardButton(text="\U00002705"),
        types.KeyboardButton(text="\U0000274C")
    )
    return builder


# Клавиатура для выбора поезда
def confirm_train_reply_keyboard(trains_options: list):
    retry_kb = ReplyKeyboardBuilder()
    # Первый ряд будет с предложением ввести название станции повторно
    retry_kb.row(types.KeyboardButton(
        text="0"
    ))

    options_kb = ReplyKeyboardBuilder()
    for i in range(1, len(trains_options) + 1):
        options_kb.add(types.KeyboardButton(text=str(i)))
    options_kb.adjust(3)

    retry_kb.attach(options_kb)

    return retry_kb.as_markup()
