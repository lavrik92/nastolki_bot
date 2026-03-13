from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher
import aiogram.utils.markdown as fmt
import emoji

main_router = Router()

@main_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    name = f"{message.from_user.first_name}"
    answer = fmt.text(
            fmt.text(f"👋 Привет, {name}! Я бот для подбора настольной игры. "),
            fmt.text(emoji.emojize("Я предназначен исключительно для внутреннего пользования! Никому чужому меня не показывать :zipper-mouth_face:")),
            fmt.text("🎮 Доступные команды: "),
            fmt.text("/start - команда для начала работы с ботом и для справки по доступным командам"),
            fmt.text("/show_games - посмотреть игры в наличии по категориям"),
            fmt.text("/cancel - сбросить текущее состояние"),
            fmt.text(emoji.emojize('/dice - игральный кубик, чисто по фану :woozy_face:')),
            fmt.text("❗ Команды также доступны в меню внизу слева. "),
            sep="\n"
        )
    await message.answer(answer, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

@main_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("🤷 Нет активного подбора игр.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Подбор игры отменен.\n"
        "Используй /show_games чтобы начать заново.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

@main_router.message(Command("dice"))
async def cmd_dice(message: Message):
    "Игральный кубик d6"
    await message.answer_dice(emoji="🎲")