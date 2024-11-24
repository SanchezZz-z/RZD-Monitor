# import aiogram.exceptions
# from aiogram import types, Router, F
# from aiogram.filters import Command, StateFilter
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.types import CallbackQuery, BufferedInputFile
# from aiogram.utils.keyboard import InlineKeyboardBuilder
#
# from db_connection import database_connection
# from rzd_web_check_free_seat import free_seats_check, make_pdf_async
# from testing import get_user_trains, get_train_info
# from tgbot_template_v3.tgbot.keyboards.inline import select_train_to_check_free_seats_inline_keyboard, \
#     UserTrainToCheckFreeSeatsOptionCallbackData, right_wrong_inline_keyboard
# from tgbot_template_v3.tgbot.misc.states import Train
#
# free_seats_menu_router = Router()
#
# import json
#
#
# class FreeSeats(StatesGroup):
#     select_train = State()
#     confirm_train_to_check = State()
#     select_car_num = State()
#     select_seat = State()
#     perform_check = State()
#
#
# INVALID_STATIONS = [2000000, 2000125, 2000174, 2000351, 2000377, 2000427, 2004000, 2004730, 2004745, 2004755, 2005574,
#                     2005601, 2010000, 2010161, 2014000, 2014421, 2014704, 2020800, 2024739, 2028039, 2028055, 2028145,
#                     2030120, 2060000, 2060320, 2060615, 2064000, 2064287, 2064291]
#
#
# @free_seats_menu_router.message(Train.main_menu, Command("free_seats"))
# async def get_train_list(message: types.Message, state: FSMContext):
#     # Получаем пул соединений инициализированный при запуске бота
#     connection_pool = await database_connection.get_connection_pool()
#     user_trains_msg, user_trains_db_ids = await get_user_trains(connection_pool, message.from_user.id)
#     # Если у пользователя есть добавленные поезда:
#     if user_trains_msg:
#         # Переводим пользователя в состояние select_train
#         await state.set_state(FreeSeats.select_train)
#         # Сохраним список поездов пользователя и айдишники их записей в БД
#         await state.update_data(user_trains=user_trains_msg)
#         await state.update_data(train_db_ids=user_trains_db_ids)
#         await message.answer(text="Ваши поезда:\n\n" + user_trains_msg
#                                   + "\n\nВыберите поезд для проверки свободных мест",
#                              reply_markup=select_train_to_check_free_seats_inline_keyboard(
#                                  user_trains_msg.strip().split("\n\n")))
#     # Если поездов нет:
#     else:
#         # Возвращаем в состояние main_menu
#         await state.set_state(Train.main_menu)
#         # То предлагаем добавить или вернуться в главное меню
#         await message.answer(text="У Вас пока что нет ни одного поезда\n"
#                                   "Прежде чем добавить монитор, перейдите в меню /trains и добавьте "
#                                   "нужный поезд или нажмите кнопку ниже",
#                              reply_markup=InlineKeyboardBuilder().button(
#
#                                  text="Добавить поезд",
#                                  callback_data="add_train"
#
#                              ).as_markup())
#
#
# # Подтверждение поезда, который пользователь хочет отслеживать
# @free_seats_menu_router.callback_query(FreeSeats.select_train, UserTrainToCheckFreeSeatsOptionCallbackData.filter())
# async def confirm_train_to_check_free_seats(callback_query: CallbackQuery,
#                                             callback_data: UserTrainToCheckFreeSeatsOptionCallbackData,
#                                             state: FSMContext):
#     await callback_query.answer()
#
#     # Данные пользователя
#     user_data = await state.get_data()
#
#     # Получаем номер, который выбрал пользователь
#     option_num = callback_data.option_num
#
#     # Если пользователь выбрал "Назад" (то есть, выбрал 0)
#     if not option_num:
#         # Возвращаем в состояние main_menu
#         await state.set_state(Train.main_menu)
#         # Получаем пул соединений инициализированный при запуске бота
#         connection_pool = await database_connection.get_connection_pool()
#         user_trains_msg, user_trains_db_ids = await get_user_trains(connection_pool, callback_query.from_user.id)
#         # Если у пользователя есть добавленные поезда:
#         if user_trains_msg:
#             # Переводим пользователя в состояние select_train
#             await state.set_state(FreeSeats.select_train)
#             # Сохраним список поездов пользователя и айдишники их записей в БД
#             await state.update_data(train_db_ids=user_trains_db_ids)
#             await callback_query.answer(text="Ваши поезда:\n\n" + user_trains_msg
#                                              + "\n\nВыберите поезд для проверки свободных мест",
#                                         reply_markup=select_train_to_check_free_seats_inline_keyboard(
#                                             user_trains_msg.strip().split("\n\n")))
#
#     # Если пользователь выбрал один из поездов
#     else:
#         # Сохраняем выбор пользователя
#         await state.update_data(user_choice=int(option_num))
#         # Переводим в состояние confirm_delete_train
#         await state.set_state(FreeSeats.confirm_train_to_check)
#         # Получаем информацию о поезде
#         option_info = user_data["user_trains"].strip().split("\n\n")[option_num - 1].split("\n", maxsplit=1)[1]
#         text = "Вы выбрали:\n\n{}\n\nВерно?".format(option_info)
#         await callback_query.message.edit_text(text, reply_markup=right_wrong_inline_keyboard())
#
#
# # Пользователь нажал не на ту цифру
# @free_seats_menu_router.callback_query(FreeSeats.confirm_train_to_check, F.data == "wrong")
# async def confirm_train_to_check_fail(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#
#     user_data = await state.get_data()
#
#     # Удалим сохраненный ранее выбор пользователя
#     await state.update_data(user_choice=None)
#
#     # Возвращаем пользователя в состояние выбора поезда
#     await state.set_state(FreeSeats.select_train)
#
#     await callback_query.message.edit_text(text="Ваши поезда:\n\n" + user_data["user_trains"]
#                                                 + "\n\nВыберите поезд для проверки свободных мест",
#                                            reply_markup=select_train_to_check_free_seats_inline_keyboard(
#                                                user_data["user_trains"].strip().split("\n\n")))
#
#
# # Пользователь подтвердил выбор поезда
# @free_seats_menu_router.callback_query(FreeSeats.confirm_train_to_check, F.data == "correct")
# async def add_train_to_check_success(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#
#     user_data = await state.get_data()
#
#     # Удаляем все ненужные данные, состояние сохраняем
#     await state.update_data(user_choice=None)
#     await state.update_data(user_trains=None)
#     await state.update_data(train_db_ids=None)
#
#     # Получаем пул соединений инициализированный при запуске бота
#     connection_pool = await database_connection.get_connection_pool()
#
#     # Сохраним данные о выбранном поезде (нужно будет для уточнения некоторых вопросов)
#     (chosen_train_num,
#      chosen_trip_date,
#      chosen_origin_station,
#      chosen_destination_station) = await get_train_info(connection_pool,
#                                                         user_data["train_db_ids"][user_data["user_choice"] - 1],
#                                                         monitor=False)
#
#     await state.update_data(train_num=chosen_train_num)
#     await state.update_data(trip_date=chosen_trip_date)
#     await state.update_data(origin_station=chosen_origin_station)
#     await state.update_data(destination_station=chosen_destination_station)
#
#     # Вот тут проверяем станции отправления и прибытия
#
#     # Перейдем в состояние выбора номера вагона
#     await state.set_state(FreeSeats.select_car_num)
#
#     await callback_query.message.edit_text(text="Пожалуйста, введите номер вагона")
#
#
# # Пользователь ввел что-то кроме числа
# @free_seats_menu_router.message(FreeSeats.select_car_num, ~F.text.strip().isdigit())
# async def confirm_car_num_wrong_input(message: types.Message):
#
#     text = "Пожалуйста, введите число"
#     await message.answer(text)
#
#
# # Пользователь ввел число
# @free_seats_menu_router.message(FreeSeats.select_car_num, F.text.strip().isdigit())
# async def confirm_car_num(message: types.Message, state: FSMContext):
#
#     # Пользователь ввел 0 или отрицательное число
#     if int(message.text) < 1:
#
#         text = "Пожалуйста, введите целое положительное число"
#         await message.answer(text)
#
#     else:
#
#         car_num = "0" + message.text if int(message.text) < 10 else message.text
#
#         # Сохраняем номер вагона
#         await state.update_data(car_num=car_num)
#
#         text = "Номер вагона:\n\n\u25B6 {}\n\nВерно?".format(message.text)
#
#         await message.answer(text, reply_markup=right_wrong_inline_keyboard())
#
#
# # На случай, если пользователь неправильно ввел цифру (опечатался или увидел, что ошибся, например)
# @free_seats_menu_router.callback_query(FreeSeats.select_car_num, F.data == "wrong")
# async def confirm_car_num_fail(callback_query: CallbackQuery, state: FSMContext):
#
#     await callback_query.answer()
#     # Удалим сохраненный ранее номер вагона
#     await state.update_data(car_num=None)
#     await callback_query.message.edit_text(text="Пожалуйста, введите номер вагона")
#
#
# # Пользователь подтвердил выбор вагона
# @free_seats_menu_router.callback_query(FreeSeats.select_car_num, F.data == "correct")
# async def confirm_seat(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#
#     # Перейдем в состояние ввода места
#     await state.set_state(FreeSeats.select_seat)
#
#     await callback_query.message.edit_text(text="Пожалуйста, введите номер места")
#
#
# # Пользователь ввел что-то кроме числа
# @free_seats_menu_router.message(FreeSeats.select_seat, ~F.text.strip().isdigit())
# async def confirm_seat_wrong_input(message: types.Message):
#
#     text = "Пожалуйста, введите число"
#     await message.answer(text)
#
#
# # Пользователь ввел число
# @free_seats_menu_router.message(FreeSeats.select_seat, F.text.strip().isdigit())
# async def confirm_seat(message: types.Message, state: FSMContext):
#
#     # Пользователь ввел 0 или отрицательное число
#     if int(message.text) < 1:
#
#         text = "Пожалуйста, введите целое положительное число"
#         await message.answer(text)
#
#     else:
#
#         # Сохраняем номер вагона
#         await state.update_data(seat=int(message.text))
#
#         text = "Номер места:\n\n\u25B6 {}\n\nВерно?".format(message.text)
#
#         await message.answer(text, reply_markup=right_wrong_inline_keyboard())
#
#
# # На случай, если пользователь неправильно ввел цифру (опечатался или увидел, что ошибся, например)
# @free_seats_menu_router.callback_query(FreeSeats.select_seat, F.data == "wrong")
# async def confirm_seat_fail(callback_query: CallbackQuery, state: FSMContext):
#
#     await callback_query.answer()
#     # Удалим сохраненный ранее номер вагона
#     await state.update_data(seat=None)
#     await callback_query.message.edit_text(text="Пожалуйста, введите номер места")
#
#
# # Пользователь подтвердил выбор вагона
# @free_seats_menu_router.callback_query(FreeSeats.select_seat, F.data == "correct")
# async def confirm_seat(callback_query: CallbackQuery, state: FSMContext):
#     await callback_query.answer()
#
#     # Подтянем данные пользователя, чтобы получить всю необходимую информацию
#     user_data = await state.get_data()
#
#     await callback_query.message.edit_text("Подождите, выполняется проверка")
#
#     free_seats_info = await free_seats_check(user_data["train_num"],
#                                              user_data["origin_station"],
#                                              user_data["destination_station"],
#                                              user_data["trip_date"].strftime("%Y-%m-%d"),
#                                              user_data["car_num"],
#                                              user_data["seat"])
#
#     if type(free_seats_info) is str:
#
#         # Возвращаем в состояние main_menu
#         await state.set_state(Train.main_menu)
#
#         text = ("Вы в главном меню\n\n"
#                 "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
#                 "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое\n\n"
#                 "/free_seats - проверить, заняты ли места в Вашем купе на протяжении маршрута")
#
#         await callback_query.message.edit_text(free_seats_info + "\n\n" + text)
#
#     else:
#
#         pdf_buffer = await make_pdf_async(free_seats_info)
#
#         await callback_query.answer_document(
#             BufferedInputFile(
#                 pdf_buffer.read(),
#                 filename="Свободные места"
#             ),
#             caption="Информация о свободных местах находится в файле"
#         )
#
#
#
#
#
# with open("/Users/sanchezzzz/PycharmProjects/RZD/stations v2.0.json", "r", encoding="utf-8") as f:
#     data = json.load(f)
#     names = []
#     for station in data:
#         names.append(station["name"])
#         # if station["expressCode"] in INVALID_STATIONS:
#         #     names.append("".join(station["name"].split("(")[0]))
#
# max_len_name = ""
# for name in names:
#     if len(name) > len(max_len_name):
#         max_len_name = name
#     else:
#         continue
#
# print(max_len_name)
