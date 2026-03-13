from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from services.game_sevice import GameService, game_collection
from keyboards.keyboards import GameKeyboards
from states.fsm_states import GameSelection, GameSelection2, GamesCollection
from aiogram.fsm.state import State, StatesGroup

games_selection_router = Router()

# --- Команда для начала сбора игр ---
@games_selection_router.message(Command("start_game_collection"))
async def cmd_start_collection(message: Message, state: FSMContext):
    """Начинает сбор игр от всех участников."""
    global game_collection
    global user_votes

    user_votes = {}
    
    # Если сбор уже идет
    if game_collection["is_active"]:
        await message.answer(
            "❌ Сбор игр уже идет!\n"
            "Создатель может завершить сбор командой /stop_collection"
        )
        return
     # Запускаем сбор
    game_collection['is_active'] = True
    game_collection["creator_id"] = message.from_user.id
    game_collection["games"] = set()
    game_collection["users"] = {}
    
    # Устанавливаем состояние
    await state.set_state(GamesCollection.collecting)
    
    await message.answer(
        "🎮 Сбор игр начат!"
        #parse_mode="Markdown"
    )

@games_selection_router.message(Command("stop_collection"))
async def cmd_stop_collection(message: Message, state: FSMContext):
    """Начинает сбор игр от всех участников."""
    global game_collection
    
    # Если сбор уже идет
    if not game_collection["is_active"]:
        await message.answer(
            "❌ Сбор игр ещё не идет!"
        )
        return

    #Закрываем голосование
    game_collection['is_active'] = False

    await state.clear()
    await message.answer(
        "🎮 Сбор игр закончен!"
        #parse_mode="Markdown"
    )

@games_selection_router.message(Command("add_game_voting"))
async def cmd_add_game_voting(message: Message, state: FSMContext):
    """Начало процесса подбора игры."""
    global game_collection
    
    # Проверяем, активен ли сбор
    if not game_collection["is_active"]:
        await state.clear()
        await message.answer("Добавление игр для голосования сейчас недоступно")
        return
    await state.set_state(GameSelection2.waiting_for_players_1)
    
    await message.answer(
        "🎮 На сколько человек рассчитана игра?",
        reply_markup=GameKeyboards.get_players_keyboard(),
        parse_mode="Markdown"
    )