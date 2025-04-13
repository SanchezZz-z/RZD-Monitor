from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from monitor_tickets_rzd_bot.db_connection import database_connection
from monitor_tickets_rzd_bot.testing import get_user_id_by_username, add_allowed_user, remove_allowed_user
from monitor_tickets_rzd_bot.tgbot.filters.admin import AdminFilter

from monitor_tickets_rzd_bot.tgbot.misc.states import Train

admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(CommandStart())
async def admin_start(message: Message,  state: FSMContext):
    # Чистим любые сохраненные данные
    await state.update_data({})
    await message.reply("Приветствую, одмен!\n\n"
                        "Вы в главном меню\n\n"
                        "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
                        "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое")
    await state.set_state(Train.main_menu)

# Команда для выдачи доступа
@admin_router.message(Command("add_user"))
async def add_user(message: types.Message):
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    try:
        username = message.text.split(maxsplit=1)[1].lstrip("@")
        user_id = await get_user_id_by_username(connection_pool, username)
        if user_id:
            await add_allowed_user(connection_pool, user_id)
            await message.answer("Пользователь @{} (ID: {}) добавлен в разрешённые.".format(username, user_id))
        else:
            await message.answer("Пользователь @{} не найден. Попросите его написать боту.".format(username))
    except IndexError:
        await message.answer("Укажите username, например: /add_user @username")


# Команда для удаления доступа (только админ)
@admin_router.message(Command("remove_user"))
async def remove_user(message: types.Message):
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    try:
        username = message.text.split(maxsplit=1)[1].lstrip("@")
        user_id = await get_user_id_by_username(connection_pool, username)
        if user_id:
            await remove_allowed_user(connection_pool, user_id)
            await message.answer("Пользователь @{} (ID: {}) удалён из разрешённых.".format(username, user_id))
        else:
            await message.answer("Пользователь @{} не найден.".format(username))
    except IndexError:
        await message.answer("Укажите username, например: /remove_user @username")

# Список допущенных пользователей
@admin_router.message(Command("list_users"))
async def list_users(message: types.Message):
    # Получаем пул соединений инициализированный при запуске бота
    connection_pool = await database_connection.get_connection_pool()
    async with connection_pool.acquire() as conn:
        allowed_users = await conn.fetch("SELECT r.user_id, r.username FROM allowed_users AS l INNER JOIN users AS r ON l.user_id = r.user_id")
    if allowed_users:
        users = ["ID: {}, Username: @{}".format(user["user_id"], user["username"] or "не указан") for user in allowed_users]
        await message.answer("Разрешённые пользователи:\n" + "\n".join(users))
    else:
        await message.answer("Список разрешённых пользователей пуст.")
