from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot_template_v3.tgbot.filters.admin import AdminFilter

from tgbot_template_v3.tgbot.misc.states import Train

admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(CommandStart())
async def admin_start(message: Message,  state: FSMContext):
    await message.reply("Приветствую, одмен!\n\n"
                        "Вы в главном меню\n\n"
                        "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
                        "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое\n\n"
                        "/free_seats - проверить, заняты ли места в Вашем купе на протяжении маршрута")
    await state.set_state(Train.main_menu)
