from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

# На сервере tgbot_template_v3 надо заменить на monitor_tickets_rzd_bot
from tgbot_template_v3.tgbot.misc.states import Train, Monitor

user_router = Router()

ALLOWED_USERS = [
    5903431760,  # мой второй аккаунт
    5988823498,  # мама
    63951523,  # Никита
    271926089,  # Мила
    281943605,  # Маша
    415360956,  # Кирилл
    350266107,  # Богдана
    1120554844,  # Данек
]


@user_router.message(CommandStart())
async def user_start(message: Message, state: FSMContext):
    # Если пользователь с доступом
    if message.from_user.id in ALLOWED_USERS:
        await message.reply(("Приветствую, {}!\n\n"
                             "Вы в главном меню\n\n"
                             "/trains - посмотреть список поездов, удалить поезд или добавить новый\n\n"
                             "/monitor - посмотреть отслеживаемые поезда, удалить отслеживание или добавить новое"
                             .format(message.from_user.first_name)))
        await state.set_state(Train.main_menu)
    # Если доступа нет
    else:
        await message.reply("Приветствую, {}!\n"
                            "К сожалению, у Вас нет доступа к этому боту".format(message.from_user.first_name))


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
