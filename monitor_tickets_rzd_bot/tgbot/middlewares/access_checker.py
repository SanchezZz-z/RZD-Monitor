from aiogram import BaseMiddleware, types

from db_connection import database_connection
from testing import save_user, is_user_allowed
from monitor_tickets_rzd_bot.tgbot.filters.admin import AdminFilter


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        connection_pool = await database_connection.get_connection_pool()
        config = data["config"]

        # Определяем user_id и message
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            message = event
        elif isinstance(event, types.CallbackQuery):
            user_id = event.from_user.id  # ID пользователя, нажавшего кнопку
            message = getattr(event, "message", None)
        else:
            # Для других типов событий пропускаем без проверки
            return await handler(event, data)

        # Сохраняем пользователя (если есть message и это не бот)
        if message and not event.from_user.is_bot:
            await save_user(connection_pool, event.from_user.id, event.from_user.username)

        # Пропускаем админа
        if isinstance(message, types.Message):  # AdminFilter работает только с Message
            admin_filter = AdminFilter()
            is_admin = await admin_filter(message, config)
            if is_admin:
                return await handler(event, data)
        else: # Для CallbackQuery проверяем напрямую через config
            if user_id in config.tg_bot.admin_ids:
                return await handler(event, data)

        # Пропускаем команду /start
        if isinstance(event, types.Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Проверяем доступ через allowed_users
        if not await is_user_allowed(connection_pool, user_id):
            if isinstance(event, types.Message):
                await message.answer("У вас нет доступа к боту.")
            elif isinstance(event, types.CallbackQuery):
                await event.answer("У вас нет доступа к боту.", show_alert=True)
            return

        return await handler(event, data)
