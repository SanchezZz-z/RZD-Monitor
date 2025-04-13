from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from monitor_tickets_rzd_bot.db_connection import database_connection
from monitor_tickets_rzd_bot.testing import save_user, check_access
# На сервере monitor_tickets_rzd_bot надо заменить на monitor_tickets_rzd_bot
from monitor_tickets_rzd_bot.tgbot.misc.states import Train, Monitor

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message, state: FSMContext):
    # Чистим любые сохраненные данные
    await state.update_data({})
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    user_id = message.from_user.id
    username = message.from_user.username
    await save_user(connection_pool, user_id, username)
    # Если доступа нет
    if not await check_access(connection_pool, message):
        await message.reply("Приветствую, {}!\n"
                            "К сожалению, у Вас нет доступа к этому боту:(\n"
                            "Но может быть скоро появится...".format(message.from_user.first_name))
    # Если доступ есть
    else:
        await message.reply(("Приветствую, {}!\n\n"
                             "Вы в главном меню\n\n"
                             "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
                             "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое"
                             .format(message.from_user.first_name)))
        await state.set_state(Train.main_menu)


# При рестарте возвращаем пользователя в состояние main_menu
# Нужно добавить, что команда рестарт срабатывает только в том случае, если пользователь уже находится хоть в каком-то
# состоянии
@user_router.message(~StateFilter(None), Command("main_menu"))
async def restart(message: types.Message, state: FSMContext):
    await state.set_state(Train.main_menu)
    # Чистим любые сохраненные данные
    await state.update_data({})
    text = ("Вы в главном меню\n\n"
            "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
            "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое")
    await message.answer(text)


# Если пользователь решил вернуться в главное меню
@user_router.callback_query(StateFilter(Train.train_menu, Monitor.monitor_menu),
                            F.data == "main_menu")
async def back_to_main_menu(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    # Чистим любые сохраненные данные
    await state.update_data({})
    # Возвращаем в состояние main_menu
    await state.set_state(Train.main_menu)
    text = ("Вы в главном меню\n\n"
            "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
            "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое")
    await callback_query.message.edit_text(text)
