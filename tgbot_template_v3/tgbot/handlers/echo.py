from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hcode

echo_router = Router()

LOGIN_ERROR_MSG = ("Вероятно, бот был перезапущен, поэтому Вас разлогинило\nЧтобы залогиниться, "
                   "воспользуйтесь командой /start")


@echo_router.message(F.text, StateFilter(None))
async def bot_echo(message: types.Message):
    await message.answer(LOGIN_ERROR_MSG)


@echo_router.message(F.text)
async def bot_echo_all(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    text = [
        f"Эхо с состоянием {hcode(state_name)}",
        "Сообщение:",
        hcode(message.text),
    ]
    await message.answer("\n".join(text))
