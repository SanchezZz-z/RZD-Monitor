from datetime import datetime, timedelta

import aiogram.exceptions
import httpx
from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from monitor_tickets_rzd_bot.db_connection import database_connection
from monitor_tickets_rzd_bot.rzd_app import get_train
from monitor_tickets_rzd_bot.testing import find_matches, add_user_train, get_user_trains, delete_selected_trains, \
    get_user_choice
from ..calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback
from monitor_tickets_rzd_bot.tgbot.keyboards.inline import confirm_station_inline_keyboard, StationOptionCallbackData, \
    right_wrong_inline_keyboard, start_menu_inline_keyboard, UserTrainToDeleteOptionCallbackData, \
    few_options_inline_keyboard, select_train_type_inline_keyboard, TrainTypesOptionCallbackData
# from monitor_tickets_rzd_bot.tgbot.keyboards.reply import confirm_train_reply_keyboard
from ..keyboards.reply import confirm_train_reply_keyboard
from monitor_tickets_rzd_bot.tgbot.misc.states import Train

train_menu_router = Router()

# 
@train_menu_router.message(Train.main_menu, Command("trains"))
async def get_train_list(message: types.Message, state: FSMContext):
    # Переведем пользователя в состояние train_menu
    await state.set_state(Train.train_menu)
    # Здесь вызовем функцию, которая обращается к БД и выводит список поездов пользователя
    # Список поездов отсортирован по дате и времени отправления

    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()

    user_trains_msg, user_trains_db_ids = await get_user_trains(connection_pool, message.from_user.id)

    # Если у пользователя есть добавленные поезда:
    if user_trains_msg:
        # Сохраним список поездов пользователя и айдишники их записей в БД
        await state.update_data(user_trains=user_trains_msg)
        await state.update_data(train_db_ids=user_trains_db_ids)
        await message.answer(text="Ваши поезда:\n\n" + user_trains_msg
                                  + "\n\nВы бы хотели удалить поезд или добавить новый?",
                             reply_markup=start_menu_inline_keyboard("train", user_trains_msg))
    # Если поездов нет:
    else:
        # То предлагаем добавить или вернуться в главное меню
        await message.answer(text="У Вас пока что нет ни одного поезда",
                             reply_markup=start_menu_inline_keyboard("train", user_trains_msg))


# Если пользователь решил удалить поезд
@train_menu_router.callback_query(Train.train_menu, F.data == "delete_train")
async def get_trains_to_delete(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Переводим пользователя в состояние удаления поезда
    await state.set_state(Train.delete_train)
    # Подтягиваем сообщение с поездами пользователя
    user_data = await state.get_data()
    # Создадим список для хранения выбранных поездов пользователя
    await state.update_data(delete_selected_trains=[])
    await callback_query.message.edit_text(text=user_data["user_trains"]
                                           + "\n\nПожалуйста, выберите номер поезда (можно выбрать сразу "
                                           "несколько), который Вы хотели бы удалить и нажмите 'Готово'",
                                           reply_markup=few_options_inline_keyboard("train",
                                                                                    user_data["user_trains"]
                                                                                    .count("\U0001F4CD"), []))


# Подтверждение поездов, который пользователь хочет удалить
@train_menu_router.callback_query(Train.delete_train, UserTrainToDeleteOptionCallbackData.filter())
async def confirm_train_delete(callback_query: CallbackQuery, callback_data: UserTrainToDeleteOptionCallbackData,
                               state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Получаем номер, который выбрал пользователь
    option_num = callback_data.option_num

    # Если пользователь выбрал "Назад" (то есть, выбрал -1)
    if option_num == -1:
        # Возвращаем в состояние train_menu
        await state.set_state(Train.train_menu)
        # Предлагаем снова выбрать действие
        await callback_query.message.edit_text(text="Ваши поезда:\n\n" + user_data["user_trains"]
                                                    + "\n\nВы бы хотели удалить поезд или добавить новый?",
                                               reply_markup=start_menu_inline_keyboard("train",
                                                                                       user_data["user_trains"]))
    # Если пользователь выбрал "Готово" (то есть, выбрал 0)
    elif not option_num:
        # Если пользователь сразу нажал "Готово", не выбрав ни одного поезда
        if not len(user_data["delete_selected_trains"]):

            try:
                await callback_query.message.edit_text(
                    text=user_data["user_trains"] + "\n\nПожалуйста, выберите <i><u>хотя бы один</u></i> поезд",
                    reply_markup=few_options_inline_keyboard("train", user_data["user_trains"].count("\U0001F4CD"),
                                                             user_data["delete_selected_trains"]))
            except aiogram.exceptions.TelegramBadRequest:
                pass
        else:

            # Переводим в состояние confirm_delete_train
            await state.set_state(Train.confirm_delete_train)

            option_info = get_user_choice(user_data["user_trains"], sorted(user_data["delete_selected_trains"]))

            if len(user_data["delete_selected_trains"]) > 1:

                text = "{}\n\nВы действительно хотите удалить выбранные поезда?".format(option_info[:-3])
                await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

            else:

                text = "{}\n\nВы действительно хотите удалить выбранный поезд?".format(option_info[:-3])
                await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())
    # Если пользователь выбрал один из поездов
    else:
        # Если пользователь выбрал поезд, который уже есть в списке (дважды нажал на одну кнопку), то выбор отменяется
        if option_num in user_data["delete_selected_trains"]:
            user_data["delete_selected_trains"].remove(option_num)
        # Если пользователь нажал на кнопку, то сохраняем его выбор
        else:
            user_data["delete_selected_trains"].append(option_num)

        # И показываем клавиатуру с учетом выбора пользователя
        await callback_query.message.edit_text(
            text=user_data["user_trains"] + "\n\nПожалуйста, выберите номер поезда (можно выбрать сразу несколько), "
                                            "который Вы хотели бы удалить и нажмите 'Готово'",
            reply_markup=few_options_inline_keyboard("train", user_data["user_trains"].count("\U0001F4CD"),
                                                     user_data["delete_selected_trains"]))


# Пользователь нажал не на ту цифру
@train_menu_router.callback_query(Train.confirm_delete_train, F.data == "wrong")
async def confirm_train_delete_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные с поездами
    user_data = await state.get_data()
    # Возвращаем в предыдущее состояние
    await state.set_state(Train.delete_train)
    # Удалим сохраненные ранее выбранные поезда
    await state.update_data(delete_selected_trains=[])
    # Снова покажем список поездов пользователя и почистим его старый выбор
    await (callback_query.message.edit_text(
        text=user_data["user_trains"] + "\n\nПожалуйста, выберите номер поезда (можно выбрать сразу несколько), "
                                        "который Вы хотели бы удалить и нажмите 'Готово'",
        reply_markup=few_options_inline_keyboard("train", user_data["user_trains"].count("\U0001F4CD"), [])))


# Пользователь подтвердил поезда к удалению
@train_menu_router.callback_query(Train.confirm_delete_train, F.data == "correct")
async def confirm_train_delete_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные пользователя, чтобы можно было выбрать id записи, которую необходимо удалить
    user_data = await state.get_data()
    # Получим айди записи, которую необходимо удалить
    ids_to_delete = [user_data["train_db_ids"][option - 1] for option in user_data["delete_selected_trains"]]
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    # Удаляем поезд с выбранным айди
    await delete_selected_trains(connection_pool, ids_to_delete)
    # Отправляем сообщение, что поезда успешно удалены
    if len(ids_to_delete) > 1:
        delete_success_msg = "Выбранные поезда успешно удалены"
    else:
        delete_success_msg = "Выбранный поезд успешно удален"
    # Чистим все сохраненные данные
    await state.update_data({})
    # Возвращаем в состояние train_menu
    await state.set_state(Train.train_menu)
    # Показываем список поездов (как будто снова ввели команду /trains)
    user_trains_msg, user_trains_db_ids = await get_user_trains(connection_pool, callback_query.from_user.id)

    # Если у пользователя есть добавленные поезда:
    if user_trains_msg:
        # Сохраним список поездов пользователя и айдишники их записей в БД
        await state.update_data(user_trains=user_trains_msg)
        await state.update_data(train_db_ids=user_trains_db_ids)
        await callback_query.message.edit_text(text="\U00002705" + delete_success_msg + "\n\n" + "Ваши поезда:\n\n"
                                                    + user_trains_msg
                                                    + "\n\nВы бы хотели удалить поезд или добавить новый?",
                                               reply_markup=start_menu_inline_keyboard("train", user_trains_msg))
    # Если поездов нет:
    else:
        # То предлагаем добавить или вернуться в главное меню
        await callback_query.message.edit_text(text="У Вас пока что нет ни одного поезда",
                                               reply_markup=start_menu_inline_keyboard("train", user_trains_msg))


# Процесс добавления поезда в отслеживаемые
# Первым делом выбрать станцию отправления
@train_menu_router.callback_query(StateFilter(Train.train_menu, Train.main_menu), F.data == "add_train")
async def get_start_station(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Чистим любые сохраненные данные
    await state.update_data({})
    await callback_query.message.edit_text("Пожалуйста, введите станцию отправления")
    await state.set_state(Train.train_menu_start)


# Предложить пользователю выбор из станций в соответствии с вводом
@train_menu_router.message(StateFilter(Train.train_menu_start, Train.select_destination))
async def select_station(message: types.Message, state: FSMContext):
    user_input = message.text

    connection_pool = await database_connection.get_connection_pool()

    # Сохраним сообщение, чтобы потом избежать ошибки при вызове календаря
    await state.update_data(message_for_calendar=message)

    matches = await find_matches(user_input, connection_pool, threshold=0.2, limit=10)
    if not matches:
        await message.answer("Не найдено станций по вашему запросу. Попробуйте ещё раз.")
        return

    station_options = ["{} - {}".format(n + 1, match[0]) for n, match in enumerate(matches)]
    response = "\n".join(station_options)

    # matches = find_matches(user_input, stations_data, threshold=30, limit=10)
    # station_options = ["{} - ".format(n + 1) + matches[n][0] + "\n" for n in range(len(matches))]
    # placeholders = ("{}" * len(station_options)).format(*station_options)
    # Если выбираем станцию отправления
    if await state.get_state() == Train.train_menu_start:
        await message.answer("Пожалуйста, выберите станцию отправления из списка:\n\n" + response +
                             "\nЕсли станции нет в списке, убедитесь, что правильно ввели название",
                             reply_markup=confirm_station_inline_keyboard(station_options))
        await state.set_state(Train.confirm_start)
        # Сохраним список с туплами, чтобы потом можно было выбрать из него expressCode
        await state.update_data(start_station_options=matches)
    # Если выбираем станцию назначения
    elif await state.get_state() == Train.select_destination:
        await message.answer("Пожалуйста, выберите станцию назначения из списка:\n\n" + response +
                             "\nЕсли станции нет в списке, убедитесь, что правильно ввели название",
                             reply_markup=confirm_station_inline_keyboard(station_options))
        await state.set_state(Train.confirm_destination)
        # Сохраним список с туплами, чтобы потом можно было выбрать из него expressCode
        await state.update_data(destination_station_options=matches)


# Подтверждение станции отправления или назначения. На этом этапе пользователь выбирает один из вариантов, предложенных
# в соответствии с его запросом или выбирает вариант повторного ввода станции
@train_menu_router.callback_query(StateFilter(Train.confirm_start, Train.confirm_destination),
                                  StationOptionCallbackData.filter())
async def confirm_station(callback_query: CallbackQuery, callback_data: StationOptionCallbackData, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Получаем номер, который выбрал пользователь
    option_num = callback_data.option_num

    # Если этот номер равен 0 (пользователь выбрал "Ввести название станции еще раз")
    # В случае, если пользователь неверно ввел станцию или не видит станцию в списке, предложить ему еще раз ввести
    # название станции и сбросить состояние до Train.train_menu_start
    if not option_num:

        # Если это произошло на этапе подтверждения станции отправления
        if await state.get_state() == Train.confirm_start:

            # Возвращаемся в состояние ввода станции отправления
            await state.set_state(Train.train_menu_start)
            # Удалим сохраненный список с данными по возможным станциям отправления
            await state.update_data(start_station_options=None)

            await callback_query.message.edit_text("Пожалуйста, внимательно введите станцию отправления")

        # Если это произошло на этапе подтверждения станции назначения
        elif await state.get_state() == Train.confirm_destination:

            # Возвращаемся в состояние ввода станции назначения
            await state.set_state(Train.select_destination)
            # Удалим сохраненный список с данными по возможным станциям назначения
            await state.update_data(destination_station_options=None)

            await callback_query.message.edit_text("Пожалуйста, внимательно введите станцию назначения")

    # Если пользователь выбрал один из предложенных вариантов
    else:
        if await state.get_state() == Train.confirm_start:

            # Сохраняем название и expressCode выбранной станции
            await state.update_data(start_station_name=user_data["start_station_options"][option_num - 1][0])
            await state.update_data(start_station_expressCode=user_data["start_station_options"][option_num - 1][1])

            option_info = user_data["start_station_options"][option_num - 1]
            text = "Станция отправления:\n\n<i><u>{}</u></i>\n\nВерно?".format(option_info[0])

            await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

        elif await state.get_state() == Train.confirm_destination:

            # Сохраняем название и expressCode выбранной станции
            await state.update_data(
                destination_station_name=user_data["destination_station_options"][option_num - 1][0])
            await state.update_data(
                destination_station_expressCode=user_data["destination_station_options"][option_num - 1][1])

            option_info = user_data["destination_station_options"][option_num - 1]
            text = "Станция назначения:\n\n<i><u>{}</u></i>\n\nВерно?".format(option_info[0])

            await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())


# Если пользователь случайно тыкнул не на ту цифру
@train_menu_router.callback_query(StateFilter(Train.confirm_start, Train.confirm_destination), F.data == "wrong")
async def confirm_station_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    # Если идет выбор станции отправления
    if await state.get_state() == Train.confirm_start:

        station_options = ["{} - ".format(n + 1) + user_data["start_station_options"][n][0] + "\n" for n in
                           range(len(user_data["start_station_options"]))]
        placeholders = ("{}" * len(station_options)).format(*station_options)

        # Если пользователь ошибся при выборе станции, то мы удаляем сохраненную ранее
        await state.update_data(start_station_name=None)
        await state.update_data(start_station_expressCode=None)

        await callback_query.message.edit_text(
            "Пожалуйста, выберите станцию отправления из списка:\n\n" + placeholders +
            "\nЕсли станции нет в списке, убедитесь, что правильно ввели название",
            reply_markup=confirm_station_inline_keyboard(station_options))

    # Если идет выбор станции назначения
    elif await state.get_state() == Train.confirm_destination:

        station_options = ["{} - ".format(n + 1) + user_data["destination_station_options"][n][0] + "\n" for n in
                           range(len(user_data["destination_station_options"]))]
        placeholders = ("{}" * len(station_options)).format(*station_options)

        await callback_query.message.edit_text(
            "Пожалуйста, выберите станцию назначения из списка:\n\n" + placeholders +
            "\nЕсли станции нет в списке, убедитесь, что правильно ввели название",
            reply_markup=confirm_station_inline_keyboard(station_options))


# Обработка вариантов, если пользователь подтверждает свой выбор
@train_menu_router.callback_query(StateFilter(Train.confirm_start, Train.confirm_destination),
                                  F.data == "correct")
async def confirm_station_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()

    # Если станция отправления была указана верна, то мы переходим к выбору станции назначения
    if await state.get_state() == Train.confirm_start:

        # Удалим сохраненный список с туплами
        await state.update_data(start_station_options=None)

        # Перейдем в состояние выбора станции назначения
        await state.set_state(Train.select_destination)
        await callback_query.message.edit_text("Пожалуйста, введите станцию назначения")

    # Если станция отправления была указана верна, то мы переходим к выбору даты
    elif await state.get_state() == Train.confirm_destination:

        # Удалим сохраненный список с туплами
        await state.update_data(destination_station_options=None)
        # Перейдем в состояние выбора даты
        await state.set_state(Train.select_date)

        # Запускаем календарь
        await callback_query.message.edit_text(
            "Пожалуйста, выберете дату поездки:",
            reply_markup=await SimpleCalendar(
                locale=await get_user_locale(user_data["message_for_calendar"].from_user))
            .start_calendar(year=datetime.now().year, month=datetime.now().month)
        )


# Обработка вариантов выбранной даты
@train_menu_router.callback_query(SimpleCalendarCallback.filter())
async def select_date(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.today(), datetime.today() + timedelta(days=100))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(trip_date=date.date())
        await callback_query.answer()
        await callback_query.message.edit_text(
            "Дата поездки: {}\nВерно?".format(date.strftime("%d.%m.%Y")),
            reply_markup=right_wrong_inline_keyboard()
        )


# Если дата выбрана неверно, то удалим сохраненную дату и снова покажем календарь
@train_menu_router.callback_query(Train.select_date, F.data == "wrong")
async def select_date_failed(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Загружаем сохраненные данные, чтобы обойти ошибку при вызове календаря:)
    user_data = await state.get_data()
    await state.update_data(trip_date=None)
    await callback_query.message.edit_text(
        "Пожалуйста, выберете дату поездки:",
        reply_markup=await SimpleCalendar(
            locale=await get_user_locale(user_data["message_for_calendar"].from_user))
        .start_calendar(year=datetime.now().year, month=datetime.now().month)
    )


# Если дата выбрана правильно, то покажем пользователю информацию о поездке и спросим, все ли верно
@train_menu_router.callback_query(Train.select_date, F.data == "correct")
async def select_date_success(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    # Сообщение для обхода ошибок нам больше не понадобится
    await state.update_data(message_for_calendar=None)

    await callback_query.message.edit_text("\U00002139 Детали поездки:\n\n\U0001F4CD Маршрут:\n\n{}"
                                           "\n\U0001F53D\n{}\n\n\U0001F5D3 Дата поездки:\n\n{}\n\nВсё правильно?"
                                           .format(user_data["start_station_name"],
                                                   user_data["destination_station_name"],
                                                   user_data["trip_date"].strftime("%d.%m.%Y")),
                                           reply_markup=right_wrong_inline_keyboard())

    await state.set_state(Train.select_train)


# Если информация о поездке неверная, то начнем процесс с самого начала
@train_menu_router.callback_query(Train.select_train, F.data == "wrong")
async def trip_info_wrong(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Полностью чистим сохраненные данные, состояние сохраняем
    await state.set_data({})
    # Переводим в самое первое состояние
    await state.set_state(Train.train_menu_start)
    await callback_query.message.edit_text(text="Попробуем еще раз")
    await callback_query.message.answer("Пожалуйста, введите станцию отправления")


# Если информация о поездке верна, то выведем список всех подходящих поездов
@train_menu_router.callback_query(Train.select_train, F.data == "correct")
async def trip_info_right(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подгрузим данные пользователя
    user_data = await state.get_data()
    await callback_query.message.edit_text("Пожалуйста, подождите, идет поиск поездов")
    # И с их помощью сделаем запрос к API РЖД на получение данных о подходящих поездах
    # Это необходимо, чтобы получить номера поездов в том виде, в котором их возвращает API (они немного отличаются от
    # того, что мы видим на страничке с результатами поиска)
    try:
        trains_options = await get_train(user_data["start_station_expressCode"],
                                         user_data["destination_station_expressCode"],
                                         user_data["trip_date"].strftime("%d.%m.%Y"))
        await state.update_data(trains_options=trains_options)

        # Убедимся, что между выбранными станциями вообще есть поезда
        if not len(trains_options[1]):

            text = ("Поезда не найдены\nУбедитесь, что в выбранную дату между выбранными станциями ходят поезда или "
                    "что между выбранными станциями вообще есть прямое сообщение\nЭто можно сделать на официальном "
                    "сайте РЖД или в приложении \nПроверьте правильность введенных ранее данных и попробуйте еще раз")

            # Полностью чистим сохраненные данные, состояние сохраняем
            await state.set_data({})
            # Переводим в самое первое состояние
            await state.set_state(Train.train_menu_start)
            await callback_query.message.edit_text(text)
            await callback_query.message.answer("Попробуем еще раз")
            await callback_query.message.answer("Пожалуйста, введите станцию отправления")

        # Если поезда все-таки есть

        else:

            # Сохраним типы поездов, которые нашлись для выбранного маршрута

            train_type_options = [key for key in trains_options[0].keys() if len(trains_options[0][key]) > 0]
            train_types = []

            for i in range(1, len(train_type_options) + 1):
                train_types.append({"id": i, "train_type": train_type_options[i - 1]})

            await state.update_data(train_types=train_types)

            # Если у нас только один тип поездов (скорее всего, это "Скорые и пассажирские", то есть обычные поезда), то
            # сразу выводим сообщение с этим типом поездов. Но если у нас есть несколько типов поездов, как, например,
            # между Москвой и Санкт-Петербургом, тогда необходимо еще уточнить у пользователя тип поезда

            if len(train_types) == 1:

                # Если тип поезда всего один, то считаем, что у пользователя нет выбора

                await state.update_data(selected_train_type=train_types[0]["train_type"])

                trains_message = "{}\n\n" * len(trains_options[0][train_types[0]["train_type"]])
                trains_message = trains_message.format(*trains_options[0][train_types[0]["train_type"]])

                # В случае, если размер сообщения с поездами превышает максимальный допустимый (то есть, поездов слишком
                # много, как, например, по маршруту Москва - Тверь), то делим его пополам и отправляем двумя сообщениями
                # (хотя, с другой стороны если поездов настолько много, то на них не должно быть дефицита билетов)

                if len(trains_message) > 4096:
                    trains_list = trains_message.strip().split("\n\n")
                    first_message = "\n\n".join(trains_list[:(len(trains_list)) // 2])
                    second_message = "\n\n".join(trains_list[(len(trains_list)) // 2:])
                    await callback_query.message.edit_text(first_message)
                    await callback_query.message.answer(second_message + "\n\nПожалуйста, выберите нужный поезд"
                                                                         "\nЕсли нужного "
                                                                         "поезда нет в списке выберите 0",
                                                        reply_markup=confirm_train_reply_keyboard(trains_options[1]),
                                                        one_time_keyboard=True)
                else:
                    await callback_query.message.edit_text(trains_message[:-2])
                    await callback_query.message.answer("Пожалуйста, выберите нужный поезд\nЕсли нужного"
                                                        " поезда нет в списке выберите 0",
                                                        reply_markup=confirm_train_reply_keyboard(trains_options[1][train_types[0]["train_type"]]),
                                                        one_time_keyboard=True)

                # Переходим в состояние подтверждения поезда
                await state.set_state(Train.confirm_train)

            # А если у нас есть несколько типов поездов, тогда необходимо, чтобы пользователь выбрал какой-то один

            else:


                await callback_query.message.edit_text(
                    "Пожалуйста, выберите тип поезда",
                    reply_markup=select_train_type_inline_keyboard(train_types)
                )

                # Переходим в состояние выбора типа поезда

                await state.set_state(Train.select_train_type)

    except httpx.ReadTimeout:
        await callback_query.message.edit_text(text="Упс, ожидание ответа от сервера заняло слишком много времени\n"
                                                    "Нажмите на кнопку под этим сообщением, чтобы попробовать еще раз",
                                               reply_markup=InlineKeyboardBuilder().button(

                                                   text="Попробовать еще раз",
                                                   callback_data="correct"

                                               ).as_markup())


# Выбор типа поезда (при необходимости)
@train_menu_router.callback_query(Train.select_train_type, TrainTypesOptionCallbackData.filter())
async def confirm_train_type(callback_query: CallbackQuery, callback_data: TrainTypesOptionCallbackData,
                               state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    # Получаем id типа поезда, который выбрал пользователь

    train_type_id = callback_data.train_type
    selected_train_type = user_data["train_types"][train_type_id - 1]["train_type"]

    # Сохраняем выбор пользователя
    await state.update_data(selected_train_type=selected_train_type)

    text = ("Выбранный тип поезда:\n\n<i><u>{}</u></i>\n\nВерно?"
            .format(selected_train_type))

    # Переходим в состояние подтверждения типа поезда
    await state.set_state(Train.confirm_train_type)

    await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())

# Если пользователь мискликнул тип поезда
@train_menu_router.callback_query(Train.confirm_train_type, F.data == "wrong")
async def train_type_wrong(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    # Возвращаем в предыдущее состояние
    await state.set_state(Train.select_train_type)
    # Удалим сохраненные ранее выбранные типы вагонов
    await state.update_data(selected_train_type=None)
    # Снова покажем список поездов пользователя и почистим его старый выбор
    await callback_query.message.edit_text(
        "Пожалуйста, выберите тип поезда",
        reply_markup=select_train_type_inline_keyboard(user_data["train_types"])
    )

# Если пользователь подтвердил тип поезда, тогда выводим информацию и просим выбрать поезд
@train_menu_router.callback_query(Train.confirm_train_type, F.data == "correct")
async def train_type_right(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()

    trains_message = "{}\n\n" * len(user_data["trains_options"][0][user_data["selected_train_type"]])
    trains_message = trains_message.format(*user_data["trains_options"][0][user_data["selected_train_type"]])

    # В случае, если размер сообщения с поездами превышает максимальный допустимый (то есть, поездов слишком
    # много, как, например, по маршруту Москва - Тверь), то делим его пополам и отправляем двумя сообщениями
    # (хотя, с другой стороны если поездов настолько много, то на них не должно быть дефицита билетов)

    if len(trains_message) > 4096:
        trains_list = trains_message.strip().split("\n\n")
        first_message = "\n\n".join(trains_list[:(len(trains_list)) // 2])
        second_message = "\n\n".join(trains_list[(len(trains_list)) // 2:])
        await callback_query.message.edit_text(first_message)
        await callback_query.message.answer(second_message + "\n\nПожалуйста, выберите нужный поезд"
                                                             "\nЕсли нужного "
                                                             "поезда нет в списке выберите 0",
                                            reply_markup=confirm_train_reply_keyboard(user_data["trains_options"][1]),
                                            one_time_keyboard=True)
    else:
        await callback_query.message.edit_text(trains_message[:-2])
        await callback_query.message.answer("Пожалуйста, выберите нужный поезд\nЕсли нужного"
                                            " поезда нет в списке выберите 0",
                                            reply_markup=confirm_train_reply_keyboard(
                                                user_data["trains_options"][1][user_data["selected_train_type"]]),
                                            one_time_keyboard=True)

    # Переходим в состояние подтверждения поезда
    await state.set_state(Train.confirm_train)

# Если пользователь ввел что-то кроме цифр
@train_menu_router.message(Train.confirm_train, ~F.text.strip().isdigit())
async def confirm_train_wrong_input(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    num_of_trains = sum(len(lst) for lst in user_data["trains_options"][1].values())

    if num_of_trains == 1:

        # Явно укажем пользователю, как именно надо ответить на сообщение
        text = "Пожалуйста, выберите 1\n"

        await message.answer(text)

    elif num_of_trains > 1:

        text = "Пожалуйста, выберите число от 0 до {}\n".format(num_of_trains)

        await message.answer(text, reply_markup=confirm_train_reply_keyboard(user_data["trains_options"][1]),
                             one_time_keyboard=True)


# Если пользователь выбрал поезд, то попросим подтвердить выбор
@train_menu_router.message(Train.confirm_train, F.text.strip().isdigit())
async def confirm_train(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    num_of_trains = sum(len(lst) for lst in user_data["trains_options"][1].values())

    # Если пользователь ввел 0 (нужного поезда нет в списке)

    if int(message.text.strip()) == 0:
        text = ("Убедитесь, что в выбранную дату между выбранными станциями ходят поезда или что между выбранными "
                "станциями вообще есть прямое сообщение\nЭто можно сделать на официальном сайте РЖД или в приложении"
                "\nПроверьте правильность введенных ранее данных и попробуйте еще раз\nПовторно взгляните на список "
                "поездов выше, возможно, Вы просто не заметили нужный поезд")

        # Полностью чистим сохраненные данные, состояние сохраняем
        await state.set_data({})
        # Переводим в самое первое состояние
        await state.set_state(Train.train_menu_start)
        await message.answer(text)
        await message.answer("Попробуем еще раз")
        await message.answer("Пожалуйста, введите станцию отправления")

    # Обработка случаев, когда число, введенное пользователем, больше длины списка поездов
    elif int(message.text.strip()) > num_of_trains:

        text = "Пожалуйста, введите число от 1 до {}\n".format(num_of_trains)

        await message.answer(text, reply_markup=confirm_train_reply_keyboard(user_data["trains_options"][1]),
                             one_time_keyboard=True)

    else:

        # Сохраним выбор пользователя
        await state.update_data(train_choice=int(message.text))

        trains_message = "{}\n\n" * len(user_data["trains_options"][0][user_data["selected_train_type"]])
        trains_message = trains_message.format(*user_data["trains_options"][0][user_data["selected_train_type"]])

        # Представим сообщение в виде списка, чтобы после ответа пользователя уточнить, уверен ли он в своем выборе
        trains_list = trains_message.strip().split("\n\n")

        # Информация по выбранному поезду
        selected_train_info = "".join(trains_list[int(message.text.strip()) - 1].split("\n", maxsplit=1)[1])

        # Отдельно сохраним информацию в том виде, в котором она отображается на сайте / в приложении, чтобы потом
        # добавить ее в БД (чтобы можно было отображать ее в списке поездов пользователя)
        await state.update_data(selected_train_info=selected_train_info)

        text = "Выбранный поезд:\n\n{}\n\nВерно?".format(selected_train_info)

        await message.answer(text, reply_markup=right_wrong_inline_keyboard())


# На случай, если пользователь неправильно ввел цифру (опечатался или увидел, что ошибся, например)
@train_menu_router.callback_query(Train.confirm_train, F.data == "wrong")
async def confirm_train_fail(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные пользователя, чтобы получить информацию обо всех поездах
    user_data = await state.get_data()
    # Удалим сохраненный ранее выбор поезда и информацию о выбранном поезде
    await state.update_data(train_choice=None)
    await state.update_data(selected_train_info=None)

    trains_message = "{}\n\n" * len(user_data["trains_options"][0][user_data["selected_train_type"]])
    trains_message = trains_message.format(*user_data["trains_options"][0][user_data["selected_train_type"]])

    # Если пользователь опечатался, то фактически надо просто повторить шаг с выводом доступных поездов и вводом номера
    # как в корутине trip_info_right
    if len(trains_message) > 4096:
        trains_list = trains_message.strip().split("\n\n")
        first_message = "\n\n".join(trains_list[:(len(trains_list)) // 2])
        second_message = "\n\n".join(trains_list[(len(trains_list)) // 2:])
        await callback_query.message.edit_text(first_message)
        await callback_query.message.answer(second_message + "\n\nПожалуйста, выберите нужный поезд"
                                                             "\nЕсли нужного "
                                                             "поезда нет в списке выберите 0")
    else:
        await callback_query.message.edit_text(trains_message[:-2] +
                                               "\n\nПожалуйста, выберите нужный поезд\nЕсли нужного "
                                               "поезда нет в списке выберите 0")


# Ну все, поезд выбран, можно добавлять в БД
@train_menu_router.callback_query(Train.confirm_train, F.data == "correct")
async def add_train(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Подтянем данные пользователя, чтобы получить всю необходимую информацию
    user_data = await state.get_data()

    # Тип поезда
    train_type = user_data["selected_train_type"]

    # Номер поезда (в том виде, в котором он получен от API)
    train_num = user_data["trains_options"][1][train_type][user_data["train_choice"] - 1]

    # Код станции отправления
    origin_station = user_data["start_station_expressCode"]

    # Код станции назначения
    destination_station = user_data["destination_station_expressCode"]

    # Дата поездки
    trip_date = user_data["trip_date"]

    # Информация о выбранном поезде (ее необходимо слегка дополнить, а именно добавить станцию отправления и назначения
    # пользователя)
    train_info = user_data["selected_train_info"]

    # В том случае, когда пользователь в качестве отправления выбрал вариант типа Название_Города (Все Вокзалы)
    route_start = user_data["start_station_name"].split("(Все ")[0].strip()
    route_finish = user_data["destination_station_name"].split("(Все ")[0].strip()
    user_route = "\U0001F4CD " + route_start + " — " + route_finish + "\n"

    # Добавим строчку именно с маршрутом пользователя
    train_info = user_route + train_info

    # Время отправления
    departure_time = user_data["trains_options"][2][train_type][user_data["train_choice"] - 1]

    # Запись о двухэтажности (True / False)
    is_two_storey = user_data["trains_options"][3][train_type][user_data["train_choice"] - 1]

    # Полностью чистим сохраненные данные, состояние сохраняем
    await state.set_data({})

    # Возвращаемся в начальное состояние main_menu
    await state.set_state(Train.main_menu)

    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()

    add_train_message = await add_user_train(connection_pool, (callback_query.from_user.id, origin_station,
                                                               destination_station, trip_date, train_num, train_info,
                                                               departure_time, is_two_storey, train_type))

    await callback_query.message.edit_text(add_train_message +
                                           "\n\n/trains - к списку поездов\n"
                                           "/monitor - к списку отслеживаний\n"
                                           "/main_menu - в главное меню")
