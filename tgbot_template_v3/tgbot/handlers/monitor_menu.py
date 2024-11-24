import aiogram.exceptions
import httpx
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db_connection import database_connection
from monitor_setup import generate_user_messages
from rzd_app import get_seats
from testing import get_user_trains, get_train_info, add_train_to_monitor, add_monitor_task, get_active_monitors, \
    get_user_choice, delete_selected_monitors, quick_restore_task_check, quick_restore_task_setup, quick_restore_task
from tgbot_template_v3.tgbot.keyboards.inline import select_train_to_monitor_inline_keyboard, \
    UserTrainToMonitorOptionCallbackData, right_wrong_inline_keyboard, select_car_type_inline_keyboard, \
    select_gender_inline_keyboard, ask_same_gender_inline_keyboard, pets_allowed_inline_keyboard, \
    seat_types_inline_keyboard, start_menu_inline_keyboard, few_options_inline_keyboard, \
    UserMonitorToDeleteOptionCallbackData, RestoreMonitor
from tgbot_template_v3.tgbot.misc.states import Monitor, Train

monitor_menu_router = Router()

TRAINS_WITH_LUX = ["054Ч", "053Ч", "002А", "001А", "002Й", "001Г", "009Г", "009Ж", "010А", "010Ч", "010Й", "009Й",
                   "012М", "011Э", "018А", "017А", "020С", "019С", "030С", "030Й", "042Й", "041Й", "102М", "102С", ]

CAR_TYPES = {
    "coupe": "Купе",
    "plaz": "Плацкарт",
    "lux": "СВ",
    "premium": "Люкс",
}

GENDERS = {
    "female": "Женский",
    "male": "Мужской",
}

YES_OR_WHATEVER = {
    "True": "Да",
    "False": "Все равно",
}

PETS = {
    "no_pets": "Да",
    "pets": "Нет, я еду с животным",
    "whatever": "Нет, мне все равно",
}

SEAT_TYPES = {
    "lower": "Нижнее",
    "upper": "Верхнее",
    "two_storey_upper": "Верхнее на втором этаже",
    "disabled": "Для инвалидов и их сопровождающих",
    "side_lower": "Нижнее боковое",
    "side_upper": "Верхнее боковое",
    "whole_coupe": "Все купе",
}


# Переход в модуль с мониторами
@monitor_menu_router.message(Train.main_menu, Command("monitor"))
async def get_monitor_list(message: types.Message, state: FSMContext):
    # Переведем пользователя в состояние monitor_menu
    await state.set_state(Monitor.monitor_menu)
    # Здесь вызовем функцию, которая обращается к БД и выводит список активных мониторов пользователя
    # Список поездов отсортирован по дате и времени отправления

    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    user_monitors_msg, user_monitors_db_ids = await get_active_monitors(connection_pool, message.from_user.id)

    # Сохраним список мониторов пользователя и айдишники их записей в БД
    await state.update_data(user_monitors=user_monitors_msg)
    await state.update_data(monitor_db_ids=user_monitors_db_ids)

    # Если у пользователя есть активные мониторы:
    if user_monitors_msg:
        await message.answer(text="Ваши активные мониторы:\n\n" + user_monitors_msg
                                  + "\n\nВы бы хотели удалить монитор или добавить новый?",
                             reply_markup=start_menu_inline_keyboard("monitor", user_monitors_msg))
    # Если активных мониторов нет:
    else:
        # То предлагаем добавить или вернуться в главное меню
        await message.answer(text="У Вас пока что нет активных мониторов",
                             reply_markup=start_menu_inline_keyboard("monitor", user_monitors_msg))


# Если пользователь решил удалить монитор
@monitor_menu_router.callback_query(Monitor.monitor_menu, F.data == "delete_monitor")
async def get_monitors_to_delete(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Переводим пользователя в состояние удаления монитора
    await state.set_state(Monitor.delete_monitor)
    # Подтягиваем сообщение с поездами пользователя
    user_data = await state.get_data()
    # Создадим список для хранения выбранных поездов пользователя
    await state.update_data(delete_selected_monitors=[])
    await callback_query.message.edit_text(text=user_data["user_monitors"]
                                           + "\n\nПожалуйста, выберите номер монитора (можно выбрать сразу "
                                             "несколько), который Вы хотели бы удалить и нажмите 'Готово'",
                                           reply_markup=few_options_inline_keyboard("monitor",
                                                                                    user_data["user_monitors"]
                                                                                    .count("\U0001F4CD"),
                                                                                    []))


# Подтверждение поезда, который пользователь хочет удалить
@monitor_menu_router.callback_query(Monitor.delete_monitor, UserMonitorToDeleteOptionCallbackData.filter())
async def confirm_monitor_delete(callback_query: CallbackQuery, callback_data: UserMonitorToDeleteOptionCallbackData,
                                 state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Получаем номер, который выбрал пользователь
    option_num = callback_data.option_num

    # Если пользователь выбрал "Назад" (то есть, выбрал -1)
    if option_num == -1:
        # Возвращаем в состояние monitor_menu
        await state.set_state(Monitor.monitor_menu)
        # Предлагаем снова выбрать действие
        await callback_query.message.edit_text(text="Ваши активные мониторы:\n\n" + user_data["user_monitors"]
                                                    + "\n\nВы бы хотели удалить монитор или добавить новый?",
                                               reply_markup=start_menu_inline_keyboard("monitor",
                                                                                       user_data["user_monitors"]))
    # Если пользователь выбрал "Готово" (то есть, выбрал 0)
    elif not option_num:
        # Если пользователь сразу нажал "Готово", не выбрав ни одного поезда
        if not len(user_data["delete_selected_monitors"]):

            try:
                await callback_query.message.edit_text(
                    text=user_data["user_monitors"] + "\n\nПожалуйста, выберите <i><u>хотя бы один</u></i> монитор",
                    reply_markup=few_options_inline_keyboard("monitor",
                                                             user_data["user_monitors"].count("\U0001F4CD"),
                                                             user_data["delete_selected_monitors"]))
            except aiogram.exceptions.TelegramBadRequest:
                pass
        else:

            # Переводим в состояние confirm_delete_monitor
            await state.set_state(Monitor.confirm_delete_monitor)

            option_info = get_user_choice(user_data["user_monitors"], sorted(user_data["delete_selected_monitors"]))

            if len(user_data["delete_selected_monitors"]) > 1:

                text = "{}Вы действительно хотите удалить выбранные мониторы?".format(option_info)
                await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

            else:

                text = "{}Вы действительно хотите удалить выбранный монитор?".format(option_info)
                await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())
    # Если пользователь выбрал один из поездов
    else:
        # Если пользователь выбрал поезд, который уже есть в списке (дважды нажал на одну кнопку), то выбор отменяется
        if option_num in user_data["delete_selected_monitors"]:
            user_data["delete_selected_monitors"].remove(option_num)
        # Если пользователь нажал на кнопку, то сохраняем его выбор
        else:
            user_data["delete_selected_monitors"].append(option_num)

        # И показываем клавиатуру с учетом выбора пользователя
        await callback_query.message.edit_text(
            text=user_data["user_monitors"] + "\n\nПожалуйста, выберите номер монитора (можно выбрать сразу несколько),"
                                              " который Вы хотели бы удалить и нажмите 'Готово'",
            reply_markup=few_options_inline_keyboard("monitor",
                                                     user_data["user_monitors"].count("\U0001F4CD"),
                                                     user_data["delete_selected_monitors"]))


# Пользователь нажал не на ту цифру
@monitor_menu_router.callback_query(Monitor.confirm_delete_monitor, F.data == "wrong")
async def confirm_monitor_delete_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные с поездами
    user_data = await state.get_data()
    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.delete_monitor)
    # Удалим сохраненные ранее выбранные поезда
    await state.update_data(delete_selected_monitors=[])
    # Снова покажем список поездов пользователя и почистим его старый выбор
    await (callback_query.message.edit_text(
        text=user_data["user_monitors"] + "\n\nПожалуйста, выберите номер монитора(можно выбрать сразу несколько), "
                                          "который Вы хотели бы удалить и нажмите 'Готово'",
        reply_markup=few_options_inline_keyboard("monitor", user_data["user_monitors"].count("\U0001F4CD"), [])))


# Пользователь подтвердил поезда к удалению
@monitor_menu_router.callback_query(Monitor.confirm_delete_monitor, F.data == "correct")
async def confirm_monitor_delete_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные пользователя, чтобы можно было выбрать id записи, которую необходимо удалить
    user_data = await state.get_data()
    # Получим айди записи, которую необходимо удалить
    ids_to_delete = [user_data["monitor_db_ids"][option - 1] for option in user_data["delete_selected_monitors"]]
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    # Удаляем поезд с выбранным айди
    await delete_selected_monitors(connection_pool, ids_to_delete)
    # Отправляем сообщение, что поезда успешно удалены
    if len(ids_to_delete) > 1:
        delete_success_msg = "Выбранные мониторы успешно удалены"
    else:
        delete_success_msg = "Выбранный монитор успешно удален"
    # Чистим все сохраненные данные
    await state.update_data({})
    # Возвращаем в состояние monitor_menu
    await state.set_state(Monitor.monitor_menu)
    # Показываем список поездов (как будто снова ввели команду /monitor)
    user_monitors_msg, user_monitors_db_ids = await get_active_monitors(connection_pool, callback_query.from_user.id)

    # Если у пользователя есть добавленные поезда:
    if user_monitors_msg:
        # Сохраним список поездов пользователя и айдишники их записей в БД
        await state.update_data(user_monitors=user_monitors_msg)
        await state.update_data(monitor_db_ids=user_monitors_db_ids)
        await callback_query.message.edit_text(text="\U00002705" + delete_success_msg + "\n\n"
                                                    + "Ваши активные мониторы:\n\n"
                                                    + user_monitors_msg
                                                    + "\n\nВы бы хотели удалить монитор или добавить новый?",
                                               reply_markup=start_menu_inline_keyboard("monitor", user_monitors_msg))
    # Если поездов нет:
    else:
        # То предлагаем добавить или вернуться в главное меню
        await callback_query.message.edit_text(text="У Вас пока что нет активных мониторов",
                                               reply_markup=start_menu_inline_keyboard("monitor", user_monitors_msg))


# Процесс добавления монитора (таска)
# Первым делом выбрать поезд из списка поездов, места на который будут мониториться
@monitor_menu_router.callback_query(Monitor.monitor_menu, F.data == "add_monitor")
async def select_train_to_monitor(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Если мы начинаем сначала (функция confirm_monitor_setup_fail), тогда надо добавить небольшую подпись к сообщению
    retry_msg = "Попробуем еще раз\n\n" if await state.get_state() == Monitor.confirm_monitor_setup else ""
    # Чистим любые сохраненные данные
    await state.update_data({})
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    user_trains_msg, user_trains_db_ids = await get_user_trains(connection_pool, callback_query.from_user.id)
    # Если у пользователя есть добавленные поезда:
    if user_trains_msg:
        # Переводим пользователя в состояние add_train_to_monitor
        await state.set_state(Monitor.add_train_to_monitor)
        # Сохраним список поездов пользователя и айдишники их записей в БД
        await state.update_data(user_trains=user_trains_msg)
        await state.update_data(train_db_ids=user_trains_db_ids)
        await callback_query.message.edit_text(text=retry_msg + "Ваши поезда:\n\n" + user_trains_msg
                                               + "\n\nВыберите поезд для отслеживания билетов",
                                               reply_markup=select_train_to_monitor_inline_keyboard(
                                                   user_trains_msg.strip().split("\n\n")))
    # Если поездов нет:
    else:
        # Возвращаем в состояние main_menu
        await state.set_state(Train.main_menu)
        # То предлагаем добавить или вернуться в главное меню
        await callback_query.message.edit_text(text="У Вас пока что нет ни одного поезда\n"
                                                    "Прежде чем добавить монитор, перейдите в меню /trains и добавьте "
                                                    "нужный поезд или нажмите кнопку ниже",
                                               reply_markup=InlineKeyboardBuilder().button(

                                                   text="Добавить поезд",
                                                   callback_data="add_train"

                                               ).as_markup())


# Подтверждение поезда, который пользователь хочет отслеживать
@monitor_menu_router.callback_query(Monitor.add_train_to_monitor, UserTrainToMonitorOptionCallbackData.filter())
async def confirm_train_to_monitor(callback_query: CallbackQuery, callback_data: UserTrainToMonitorOptionCallbackData,
                                   state: FSMContext):
    await callback_query.answer()

    # Данные пользователя
    user_data = await state.get_data()

    # Получаем номер, который выбрал пользователь
    option_num = callback_data.option_num

    # Если пользователь выбрал "Назад" (то есть, выбрал 0)
    if not option_num:
        # Возвращаем в состояние monitor_menu
        await state.set_state(Monitor.monitor_menu)
        # Получаем пул соединений инициализированный при запуске бота
        connection_pool = await database_connection.get_connection_pool()
        user_monitors_msg, user_monitors_db_ids = await get_active_monitors(connection_pool,
                                                                            callback_query.from_user.id)
        # Предлагаем снова выбрать действие
        if user_monitors_msg:
            text = ("Ваши активные мониторы:\n\n" + user_monitors_msg +
                    "\n\nВы бы хотели удалить монитор или добавить новый?")
        else:
            text = "У Вас пока что нет активных мониторов"
        await callback_query.message.edit_text(text=text,
                                               reply_markup=start_menu_inline_keyboard("monitor", user_monitors_msg))

    # Если пользователь выбрал один из поездов
    else:
        # Сохраняем выбор пользователя
        await state.update_data(user_choice=int(option_num))
        # Переводим в состояние confirm_delete_train
        await state.set_state(Monitor.confirm_train_to_monitor)
        # Получаем информацию о поезде
        option_info = user_data["user_trains"].strip().split("\n\n")[option_num - 1].split("\n", maxsplit=1)[1]
        text = "Вы хотите отслеживать билеты на выбранный поезд:\n\n{}\n\nВерно?".format(option_info)
        await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())


# Пользователь нажал не на ту цифру
@monitor_menu_router.callback_query(Monitor.confirm_train_to_monitor, F.data == "wrong")
async def add_train_to_monitor_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Удалим сохраненный ранее выбор пользователя
    await state.update_data(user_choice=None)

    # Возвращаем пользователя в состояние выбора поезда
    await state.set_state(Monitor.add_train_to_monitor)

    await callback_query.message.edit_text(text="Ваши поезда:\n\n" + user_data["user_trains"]
                                                + "\n\nВыберите поезд для отслеживания билетов",
                                           reply_markup=select_train_to_monitor_inline_keyboard(
                                               user_data["user_trains"].strip().split("\n\n")))


# Пользователь подтвердил выбор поезда
# Начинается настройка монитора
@monitor_menu_router.callback_query(Monitor.confirm_train_to_monitor, F.data == "correct")
async def add_train_to_monitor_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Удаляем все ненужные данные, состояние сохраняем
    await state.update_data(user_choice=None)
    await state.update_data(user_trains=None)
    await state.update_data(train_db_ids=None)

    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()

    # Сохраним данные о выбранном поезде (нужно будет для уточнения некоторых вопросов)
    (chosen_train_num,
     chosen_trip_date,
     chosen_origin_station,
     chosen_destination_station,
     chosen_is_two_storey,
     chosen_train_info) = await get_train_info(connection_pool,
                                               user_data["train_db_ids"][user_data["user_choice"] - 1])

    await state.update_data(train_num=chosen_train_num)
    await state.update_data(trip_date=chosen_trip_date)
    await state.update_data(origin_station=chosen_origin_station)
    await state.update_data(destination_station=chosen_destination_station)
    await state.update_data(is_two_storey=chosen_is_two_storey)
    # Нам не нужна вся информация
    await state.update_data(train_info="\n".join(chosen_train_info.split("\n")[:4]))

    # Подготовим на будущее (чтобы в функции confirm_seat_type_success не было KeyError исключения при первом if)
    await state.update_data(selected_car_types=None)
    await state.update_data(gender=None)
    await state.update_data(same_gender_only=None)
    await state.update_data(pets_allowed=None)
    await state.update_data(selected_seat_types=None)

    # Перейдем в состояние выбора типа вагона
    await state.set_state(Monitor.select_car_type)

    # Создадим список для хранения выбранных поездов пользователя
    await state.update_data(selected_car_types=[])

    # Первый вопрос - тип вагона: плацкарт, купе, СВ или люкс
    await callback_query.message.edit_text(text="Пожалуйста, выберите подходящий тип вагона (можно выбрать сразу "
                                                "несколько) и нажмите 'Готово'\n\n"
                                                "Если Вам необходимы места для инвалида и сопровождающего, выберите "
                                                "<i><u>только</u></i> \U0000267F\U0000FE0F",
                                           reply_markup=select_car_type_inline_keyboard(chosen_is_two_storey,
                                                                                        chosen_train_num in
                                                                                        TRAINS_WITH_LUX, []))


# Подтверждение типа вагона
@monitor_menu_router.callback_query(Monitor.select_car_type, F.data.in_(["coupe", "plaz", "lux", "premium", "disabled",
                                                                         "done"]))
async def confirm_car_type(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Если пользователь сделал выбор
    if callback_query.data == "done":
        # Если пользователь сразу нажал "Готово", не выбрав ни одного типа вагонов
        if not len(user_data["selected_car_types"]):

            try:
                await callback_query.message.edit_text(
                    text="Пожалуйста, выберите <i><u>хотя бы один</u></i> тип вагона и нажмите 'Готово'\n\n"
                         "Если Вам необходимы места для инвалида и сопровождающего, выберите "
                         "<i><u>только</u></i> \U0000267F\U0000FE0F",
                    reply_markup=select_car_type_inline_keyboard(user_data["is_two_storey"],
                                                                 user_data["train_num"] in TRAINS_WITH_LUX,
                                                                 user_data["selected_car_types"]))
            except aiogram.exceptions.TelegramBadRequest:
                pass

        # Если пользователь сделал выбор
        else:

            # Если пользователь выбрал что-то кроме мест для инвалидов
            if "disabled" in user_data["selected_car_types"] and len(user_data["selected_car_types"]) != 1:

                # Удалим сохраненные ранее выбранные типы вагонов
                await state.update_data(selected_car_types=[])

                await callback_query.message.edit_text(text="Если Вам необходимы места для инвалида и сопровождающего, "
                                                            "выберите <i><u>только</u></i> \U0000267F\U0000FE0F\n\n"
                                                            "Пожалуйста, не выбирайте другие варианты",
                                                       reply_markup=select_car_type_inline_keyboard(
                                                           user_data["is_two_storey"],
                                                           user_data["train_num"] in
                                                           TRAINS_WITH_LUX, []))

            # Если пользователь выбрал только инвалидное место
            elif "disabled" in user_data["selected_car_types"] and len(user_data["selected_car_types"]) == 1:

                # Из-за того, что сам вопрос про тип вагона, а не про тип места, то выборы пользователя сохраняются как
                # выбор типа вагона, поэтому его надо очистить
                await state.update_data(selected_car_types=None)
                # А тип места добавить
                await state.update_data(selected_seat_types=["disabled"])

                # Переводим в состояние confirm_seat_type
                await state.set_state(Monitor.confirm_seat_type)

                # Переход к обзору настроек таска
                await confirm_seat_type_success(callback_query, state)

            else:

                # Переводим в состояние confirm_car_type
                await state.set_state(Monitor.confirm_car_type)

                option_info = ""

                for selected_option in user_data["selected_car_types"]:
                    option_info += "\u25B6 {}\n".format(CAR_TYPES[selected_option])

                text = "Вы выбрали:\n\n{}\n\nВсе верно?".format(option_info[:-1])
                await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

    # Если пользователь выбрал один из поездов
    else:
        # Если пользователь выбрал тип вагона, который уже есть в списке (дважды нажал на одну кнопку), то выбор
        # отменяется
        if callback_query.data in user_data["selected_car_types"]:
            user_data["selected_car_types"].remove(callback_query.data)
        # Если пользователь нажал на кнопку, то сохраняем его выбор
        else:
            user_data["selected_car_types"].append(callback_query.data)

        # И показываем клавиатуру с учетом выбора пользователя
        await callback_query.message.edit_text(
            text="Пожалуйста, выберите подходящий тип вагона (можно выбрать сразу несколько) и нажмите 'Готово'\n\n"
                 "Если Вам необходимы места для инвалида и сопровождающего, выберите <i><u>только</u></i> "
                 "\U0000267F\U0000FE0F",
            reply_markup=select_car_type_inline_keyboard(user_data["is_two_storey"],
                                                         user_data["train_num"] in TRAINS_WITH_LUX,
                                                         user_data["selected_car_types"]))


# Пользователь выбрал не тот тип вагона
@monitor_menu_router.callback_query(Monitor.confirm_car_type, F.data == "wrong")
async def confirm_car_type_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.select_car_type)
    # Удалим сохраненные ранее выбранные типы вагонов
    await state.update_data(selected_car_types=[])
    # Снова покажем список поездов пользователя и почистим его старый выбор
    await callback_query.message.edit_text(text="Пожалуйста, выберите подходящий тип вагона (можно выбрать сразу "
                                                "несколько) и нажмите 'Готово'",
                                           reply_markup=select_car_type_inline_keyboard(user_data["is_two_storey"],
                                                                                        user_data["train_num"] in
                                                                                        TRAINS_WITH_LUX, []))


# Пользователь подтвердил свой выбор
@monitor_menu_router.callback_query(Monitor.confirm_car_type, F.data == "correct")
async def confirm_car_type_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    # Если пользователь выбрал только плацкарт, только люкс или плацкарт и люкс (что очень странно), то нет смысла
    # спрашивать пол пользователя (переходим сразу к вопросу о животных)
    # Если пользователь выбрал только люкс, то нет смысла спрашивать что-либо еще (переходим к обзору таска)
    if set(user_data["selected_car_types"]).issubset({"plaz", "premium"}):
        if user_data["selected_car_types"] == ["premium"]:

            # Переводим в состояние confirm_seat_type
            await state.set_state(Monitor.confirm_seat_type)

            # Переход к обзору настроек таска
            await confirm_seat_type_success(callback_query, state)

        else:

            # Переводим в состояние confirm_seat_type
            await state.set_state(Monitor.pets_allowed)

            # Переход к вопросу о животных
            await confirm_same_gender_success(callback_query, state)

    else:
        # Переходим в состояние выбора пола
        await state.set_state(Monitor.select_gender)

        await callback_query.message.edit_text(text="Пожалуйста, выберите пол пассажира",
                                               reply_markup=select_gender_inline_keyboard())


# Подтверждение пола пассажира
@monitor_menu_router.callback_query(Monitor.select_gender, F.data.in_(GENDERS))
async def confirm_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Сохраняем пол пассажира
    await state.update_data(gender=callback_query.data)

    # Переводим в состояние подтверждения пола пассажира
    await state.set_state(Monitor.confirm_gender)

    # Уточняем
    text = "Пол пассажира:\n\n\u25B6 {}\n\nВсе верно?".format(GENDERS[callback_query.data])
    await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())


# Пользователь выбрал не тот пол пассажира
@monitor_menu_router.callback_query(Monitor.confirm_gender, F.data == "wrong")
async def confirm_gender_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.select_gender)
    # Удалим сохраненный ранее выбранный пол
    await state.update_data(gender=None)
    # Спросим еще раз
    await callback_query.message.edit_text(text="Пожалуйста, выберите пол пассажира",
                                           reply_markup=select_gender_inline_keyboard())


# Пользователь подтвердил пол пассажира
@monitor_menu_router.callback_query(Monitor.confirm_gender, F.data == "correct")
async def confirm_gender_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Переходим к вопросу о желании ехать в чисто мужском / женском купе
    await state.set_state(Monitor.ask_same_gender)

    text = "Вы бы хотели ехать в чисто {}ом купе?".format(GENDERS[user_data["gender"]].lower()[:-2])

    await callback_query.message.edit_text(text=text,
                                           reply_markup=ask_same_gender_inline_keyboard())


# Подтверждение желания ехать в "однополом" купе
@monitor_menu_router.callback_query(Monitor.ask_same_gender, F.data.in_(YES_OR_WHATEVER))
async def confirm_same_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Сохраняем ответ пользователя
    await state.update_data(same_gender_only=True if callback_query.data == "True" else False)

    # Переводим в состояние подтверждения пола пассажира
    await state.set_state(Monitor.confirm_same_gender)

    # Уточняем
    text = "Вы бы хотели ехать в чисто {}ом купе?\n\n\u25B6 {}\n\nВсе верно?".format(
        GENDERS[user_data["gender"]].lower()[:-2], YES_OR_WHATEVER[callback_query.data])
    await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())


# Пользователь выбрал не тот вариант ответа
@monitor_menu_router.callback_query(Monitor.confirm_same_gender, F.data == "wrong")
async def confirm_same_gender_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.ask_same_gender)
    # Удалим сохраненный ранее ответ
    await state.update_data(same_gender_only=None)
    # Спросим еще раз
    text = "Вы бы хотели ехать в чисто {}ом купе?".format(GENDERS[user_data["gender"]].lower()[:-2])

    await callback_query.message.edit_text(text=text,
                                           reply_markup=ask_same_gender_inline_keyboard())


# Пользователь подтвердил свой выбор
@monitor_menu_router.callback_query(Monitor.confirm_same_gender, F.data == "correct")
async def confirm_same_gender_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Переходим к вопросу о животных
    await state.set_state(Monitor.pets_allowed)

    await callback_query.message.edit_text(text="Вам необходимо ехать в вагоне, где провоз животных запрещён?",
                                           reply_markup=pets_allowed_inline_keyboard())


# Подтверждение насчет провоза животных
@monitor_menu_router.callback_query(Monitor.pets_allowed, F.data.in_(PETS))
async def confirm_pets(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Сохраняем ответ пользователя
    await state.update_data(pets_allowed=callback_query.data if callback_query.data in ["no_pets", "pets"]
                            else "whatever")

    # Переводим в состояние подтверждения пола пассажира
    await state.set_state(Monitor.confirm_pets_allowed)

    # Уточняем
    text = ("Вам необходимо ехать в вагоне, где провоз животных запрещён?\n\n\u25B6 {}\n\nВсе верно?"
            .format(PETS[callback_query.data]))
    await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())


# Пользователь выбрал не тот вариант ответа
@monitor_menu_router.callback_query(Monitor.confirm_pets_allowed, F.data == "wrong")
async def confirm_pets_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.pets_allowed)
    # Удалим сохраненный ранее ответ
    await state.update_data(pets_allowed=None)
    # Спросим еще раз
    await callback_query.message.edit_text(text="Вам необходимо ехать в вагоне, где провоз животных запрещён?",
                                           reply_markup=pets_allowed_inline_keyboard())


# Пользователь подтвердил свой выбор
@monitor_menu_router.callback_query(Monitor.confirm_pets_allowed, F.data == "correct")
async def confirm_pets_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Переходим к выбору типа мест
    await state.set_state(Monitor.select_seat_type)

    # Создадим список для хранения выбранных поездов пользователя
    await state.update_data(selected_seat_types=[])

    await callback_query.message.edit_text(text="Пожалуйста, выберите подходящий тип места (можно выбрать сразу "
                                                "несколько) и нажмите 'Готово'",
                                           reply_markup=seat_types_inline_keyboard(user_data["selected_car_types"],
                                                                                   user_data["is_two_storey"], []))


# Подтверждение типа места
@monitor_menu_router.callback_query(Monitor.select_seat_type, F.data.in_(["lower", "upper", "two_storey_upper",
                                                                          "side_lower", "side_upper", "done", ]))
async def confirm_seat_type(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Если пользователь сделал выбор
    if callback_query.data == "done":
        # Если пользователь сразу нажал "Готово", не выбрав ни одного типа вагонов
        if not len(user_data["selected_seat_types"]):

            try:
                await callback_query.message.edit_text(
                    text="Пожалуйста, выберите хотя бы один тип места и нажмите 'Готово'",
                    reply_markup=seat_types_inline_keyboard(user_data["selected_car_types"],
                                                            user_data["is_two_storey"],
                                                            user_data["selected_seat_types"]))
            except aiogram.exceptions.TelegramBadRequest:
                pass

        # Если пользователь сделал выбор
        else:

            # Переводим в состояние confirm_seat_type
            await state.set_state(Monitor.confirm_seat_type)

            option_info = ""

            for selected_option in user_data["selected_seat_types"]:
                option_info += "\u25B6 {}\n".format(SEAT_TYPES[selected_option])

            text = "Вы выбрали:\n\n{}\n\nВсе верно?".format(option_info[:-1])
            await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

    # Если пользователь выбрал один из поездов
    else:
        # Если пользователь выбрал тип места, который уже есть в списке (дважды нажал на одну кнопку), то выбор
        # отменяется
        if callback_query.data in user_data["selected_seat_types"]:
            user_data["selected_seat_types"].remove(callback_query.data)
        # Если пользователь нажал на кнопку, то сохраняем его выбор
        else:
            user_data["selected_seat_types"].append(callback_query.data)

        # И показываем клавиатуру с учетом выбора пользователя
        await callback_query.message.edit_text(
            text="Пожалуйста, выберите подходящий тип вагона (можно выбрать сразу несколько) и нажмите 'Готово'",
            reply_markup=seat_types_inline_keyboard(user_data["selected_car_types"],
                                                    user_data["is_two_storey"], user_data["selected_seat_types"]))


# Пользователь выбрал не тот тип места
@monitor_menu_router.callback_query(Monitor.confirm_seat_type, F.data == "wrong")
async def confirm_seat_type_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    # Возвращаем в предыдущее состояние
    await state.set_state(Monitor.select_seat_type)
    # Удалим сохраненные ранее выбранные поезда
    await state.update_data(selected_seat_types=[])
    # Снова покажем список поездов пользователя и почистим его старый выбор
    await callback_query.message.edit_text(text="Пожалуйста, выберите подходящий тип вагона (можно выбрать сразу "
                                                "несколько) и нажмите 'Готово'",
                                           reply_markup=seat_types_inline_keyboard(user_data["selected_car_types"],
                                                                                   user_data["is_two_storey"], []))


# Пользователь подтвердил тип места. Надо показать ему настройку его монитора и если все правильно, то добавить монитор,
# а если нет, то начать сначала
@monitor_menu_router.callback_query(Monitor.confirm_seat_type, F.data == "correct")
async def confirm_seat_type_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    task_setup_msg = "\U0001F6E0 Настройки монитора:\n\n"
    train_info = "{}\n\n".format(user_data["train_info"])
    same_gender_only_msg = ""
    pets_msg = ""

    # Если мониторятся только места для инвалида и сопровождающего
    if user_data["selected_seat_types"] == ["disabled"]:

        car_type_msg = "\U0001F683 Тип вагона:\n\u25B6 Купе\n\n"
        seat_type_msg = ("\U0001F6CF Тип места:\n\u25B6 {}".format(SEAT_TYPES[user_data["selected_seat_types"][0]]) +
                         "\n\n")

    else:

        # Если любое сочетание из вариантов плацкарт + люкс
        if set(user_data["selected_car_types"]).issubset({"plaz", "premium"}):
            # Если чисто люкс, то нет инфы по полу пассажира и животным
            if user_data["selected_car_types"] == ["premium"]:

                car_type_msg = ("\U0001F683 Тип вагона:\n\u25B6 {}\n\n"
                                .format(CAR_TYPES[user_data["selected_car_types"][0]]))
                seat_type_msg = "\U0001F6CF Тип места:\n\u25B6 {}".format(SEAT_TYPES["whole_coupe"])

            # Если плацкарт + люкс, то надо добавить инфу по животным
            else:

                car_type_placeholders = "\n".join("\u25B6 {}".format(CAR_TYPES[car_type]) for car_type
                                                  in user_data["selected_car_types"])
                car_type_msg = "\U0001F683 Тип вагона:\n" + car_type_placeholders + "\n\n"
                pets_msg = ("\U0001F43E Запрет на провоз животных вагоне:\n\u25B6 {}\n\n"
                            .format(PETS[user_data["pets_allowed"]]))
                seat_type_placeholders = "\n".join("\u25B6 {}".format(SEAT_TYPES[seat_type]) for seat_type
                                                   in user_data["selected_seat_types"])
                seat_type_msg = "\U0001F6CF Тип места:\n" + seat_type_placeholders

        # Если вообще любая возможная комбинация из типов мест, то добавляем инфу с полом пассажира
        else:

            car_type_placeholders = "\n".join("\u25B6 {}".format(CAR_TYPES[car_type]) for car_type
                                              in user_data["selected_car_types"])
            car_type_msg = "\U0001F683 Тип вагона:\n" + car_type_placeholders + "\n\n"
            same_gender_only_emoji = "\U0001F46D" if user_data["gender"] == "female" else "\U0001F46C"
            passenger_gender = "женском" if user_data["gender"] == "female" else "мужском"
            same_gender_only_msg = ("{} Место в чисто {} купе:\n\u25B6 {}\n\n"
                                    .format(same_gender_only_emoji, passenger_gender,
                                            YES_OR_WHATEVER[str(user_data["same_gender_only"])]))
            pets_msg = ("\U0001F43E Запрет на провоз животных вагоне:\n\u25B6 {}\n\n"
                        .format(PETS[user_data["pets_allowed"]]))
            seat_type_placeholders = "\n".join("\u25B6 {}".format(SEAT_TYPES[seat_type]) for seat_type
                                               in user_data["selected_seat_types"])
            seat_type_msg = "\U0001F6CF Тип места:\n" + seat_type_placeholders + "\n\n"

    # Переходим в состояние подтверждения настроек
    await state.set_state(Monitor.confirm_monitor_setup)

    # Сохраняем текст с настройками монитора
    await state.update_data(monitor_setup_msg=train_info + car_type_msg + same_gender_only_msg + pets_msg +
                            seat_type_msg)

    # Просьба проверить получившиеся настройки
    check_setup_msg = ("Внимательно проверьте настройки монитора\nЕсли выбранные настройки Вас не устраивают, "
                       "то процесс начнется сначала\n\nВсе верно?")

    await callback_query.message.edit_text(
        text=task_setup_msg + train_info + car_type_msg + same_gender_only_msg + pets_msg + seat_type_msg +
        check_setup_msg,
        reply_markup=right_wrong_inline_keyboard())


# Настройки монитора неправильные
@monitor_menu_router.callback_query(Monitor.confirm_monitor_setup, F.data == "wrong")
async def confirm_monitor_setup_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    # Начинаем процесс сначала
    await select_train_to_monitor(callback_query, state)


# Настройки монитора правильные
# Сначала проверка, есть ли места по требованию пользователя в продаже
# Если есть, то показываем сообщение со списком мест в наличии и возвращаем в главное меню
# Если нет, то добавляем монитор в таблицу с мониторами пользователей
@monitor_menu_router.callback_query(Monitor.confirm_monitor_setup, F.data == "correct")
async def confirm_monitor_setup_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    monitor_setup = {
        "car_type": (sorted(user_data["selected_car_types"]) if user_data["selected_car_types"] is not None else
                     user_data["selected_car_types"]),
        "gender": user_data["gender"],
        "same_gender_only": user_data["same_gender_only"],
        "pets_allowed": user_data["pets_allowed"],
        "seat_type": sorted(user_data["selected_seat_types"])
    }

    await callback_query.message.edit_text("Проверка наличия мест, пожалуйста, подождите")

    try:

        # Запрос на получение мест в выбранном поезде
        seats_data = await get_seats(user_data["origin_station"], user_data["destination_station"],
                                     user_data["trip_date"].strftime("%d.%m.%Y"), user_data["train_num"])

        # Оставляем только места, которые подходят под настройку монитора пользователя
        text = generate_user_messages(monitor_setup, seats_data)

        # Полностью чистим сохраненные данные, состояние сохраняем
        await state.set_data({})

        # Возвращаемся в начальное состояние main_menu
        await state.set_state(Train.main_menu)

        # Если мест нет, то добавляем монитор в БД
        if not text:

            # Получаем пул соединений инициализированный при запуске бота
            connection_pool = await database_connection.get_connection_pool()
            # Сначала добавляем поезд в поезда, которые мониторятся
            train_to_monitor_info = [user_data["origin_station"], user_data["destination_station"],
                                     user_data["trip_date"], user_data["train_num"]]
            train_to_monitor_id = await add_train_to_monitor(connection_pool, train_to_monitor_info)
            # Потом добавляем сам таск
            add_monitor_msg = await add_monitor_task(connection_pool, train_to_monitor_id, callback_query.from_user.id,
                                                     monitor_setup, user_data["monitor_setup_msg"].rstrip())
            await callback_query.message.edit_text(text=add_monitor_msg +
                                                   "\n\n/monitor - к списку отслеживаний\n"
                                                   "/trains - к списку поездов\n"
                                                   "/main_menu - в главное меню")
        # Если места есть, тогда сообщаем об этом пользователю и монитор не добавляем
        else:
            intro_msg = ("" if text.startswith("В соответствии")
                         else "В соответствии с Вашими настройками были найдены места:\n\n")
            outro_msg = "\n\nВы можете приобрести билет на сайте РЖД или в приложении"
            await callback_query.message.edit_text(text=intro_msg + text + outro_msg +
                                                   "\n\n/monitor - к списку отслеживаний\n"
                                                   "/trains - к списку поездов\n"
                                                   "/main_menu - в главное меню")

    except httpx.ReadTimeout:
        await callback_query.message.edit_text(text="Упс, ожидание ответа от сервера заняло слишком много времени\n"
                                                    "Нажмите на кнопку под этим сообщением, чтобы попробовать еще раз",
                                               reply_markup=InlineKeyboardBuilder().button(

                                                   text="Попробовать еще раз",
                                                   callback_data="correct"

                                               ).as_markup())


# Хэндлер для быстрого восстановления сработавшего монитора
@monitor_menu_router.callback_query(RestoreMonitor.filter())
async def restore_monitor(callback_query: CallbackQuery, callback_data: RestoreMonitor):
    await callback_query.answer()

    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    # Для начала проверим, возможно ли в принципе восстановить монитор
    train_data = await quick_restore_task_check(connection_pool, callback_data.train_id)
    # Если можно, то проверяем, есть ли места
    if train_data:
        await callback_query.message.edit_text("Проверка наличия мест, пожалуйста, подождите")
        seats_data = await get_seats(train_data[0]["origin_station"], train_data[0]["destination_station"],
                                     train_data[0]["trip_date"].strftime("%d.%m.%Y"), train_data[0]["train_num"])
        task_setup = await quick_restore_task_setup(connection_pool, callback_data.task_id)
        text = generate_user_messages(task_setup, seats_data)
        # Если мест нет, тогда восстанавливаем монитор
        if not text:
            success_msg = await quick_restore_task(connection_pool, callback_data.task_id, callback_data.train_id)
            await callback_query.message.edit_text(text=success_msg)
        # Если места есть
        else:
            intro_msg = ("" if text.startswith("В соответствии")
                         else "В соответствии с Вашими настройками были найдены места:\n\n")
            outro_msg = "\n\nВы можете приобрести билет на сайте РЖД или в приложении"
            await callback_query.message.edit_text(text=intro_msg + text + outro_msg)
    # Если монитор в принципе нельзя восстановить, значит поезд уже ушел
    else:
        impossible_msg = "Монитор невозможно восстановить, так как отслеживаемый поезд уже ушел"
        await callback_query.message.edit_text(text=impossible_msg)
