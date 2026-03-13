from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from services.game_sevice import GameService
from keyboards.keyboards import GameKeyboards
from states.fsm_states import GameSelection

show_games_router = Router()

@show_games_router.message(Command("show_games"))
async def cmd_show_games(message: Message, state: FSMContext):
    """Начало процесса подбора игры."""
    await state.clear()
    await state.set_state(GameSelection.waiting_for_players)
    
    await message.answer(
        "🎮 Подбор игры\n\n"
        "Сколько человек будет играть?",
        reply_markup=GameKeyboards.get_players_keyboard(),
        parse_mode="Markdown"
    )

@show_games_router.message(StateFilter(GameSelection.waiting_for_players, GameSelection.waiting_for_category))
async def unexpected_message(message: Message, state: FSMContext):
    """Обработка сообщений, которые пришли не по делу во время ожидания."""
    current_state = await state.get_state()
    
    if current_state == GameSelection.waiting_for_players.state:
        await message.answer(
            "⏳ Пожалуйста, выбери количество игроков, используя кнопки ниже.",
            reply_markup=GameKeyboards.get_players_keyboard()
        )
    elif current_state == GameSelection.waiting_for_category.state:
        await message.answer(
            "⏳ Пожалуйста, выбери категорию, используя кнопки ниже.",
            reply_markup=GameKeyboards.get_categories_keyboard()
        )