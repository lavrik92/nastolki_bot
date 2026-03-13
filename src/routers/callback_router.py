from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from services.game_sevice import GameService
from keyboards.keyboards import GameKeyboards
from states.fsm_states import GameSelection, GameSelection2
from routers.game_selection_router import game_collection

callback_router = Router()

@callback_router.callback_query(F.data.startswith("players:"), StateFilter(GameSelection.waiting_for_players))
async def process_players_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества игроков."""
    await callback.answer()
    
    _, players_str = callback.data.split(":")
    players = int(players_str)

    current_state = await state.get_state()
    await state.update_data(selected_players=players)

    await state.set_state(GameSelection.waiting_for_category)

    
    try:
        await callback.message.edit_text(
            f"✅ Выбрано: {players} игроков\n\n"
            f"Теперь выбери категорию:",
            reply_markup=GameKeyboards.get_categories_keyboard()
        )
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(
                f"✅ Выбрано: {players} игроков\n\n"
                f"Теперь выбери категорию:",
                reply_markup=GameKeyboards.get_categories_keyboard()
            )

@callback_router.callback_query(F.data.startswith("category:"), StateFilter(GameSelection.waiting_for_category))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории и показ результатов."""
    await callback.answer()
    
    _, category = callback.data.split(":")
    user_data = await state.get_data()
    players = user_data.get('selected_players')
    
    if not players:
        await state.clear()
        await callback.message.edit_text(
            "❌ Ошибка данных. Начни подбор заново.",
            reply_markup=None
        )
        await cmd_show_games(callback.message, state)
        return
    
    found_games = GameService.filter_games(players, category)
    result_text = GameService.format_games_result(found_games, players, category)
    
    try:
        await callback.message.edit_text(
            result_text,
            reply_markup=None,
            #parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(
                result_text,
                #parse_mode="Markdown"
            )
    
    await state.clear()
    
    await callback.message.answer(
        "🔄 Что дальше?\n"
        "• /show_games - новый подбор\n"
        "• /start - главное меню",
        #parse_mode="Markdown"
    )

@callback_router.callback_query(F.data == "back_to_players", StateFilter(GameSelection.waiting_for_category, GameSelection2.waiting_for_category_1))
async def process_back_to_players(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору количества игроков."""
    await callback.answer()
    current_state = await state.get_state()
    if current_state == GameSelection.waiting_for_category.state:
        await state.set_state(GameSelection.waiting_for_players)
    elif current_state == GameSelection2.waiting_for_category_1.state:
        await state.set_state(GameSelection2.waiting_for_players_1)
    
    try:
        await callback.message.edit_text(
            "🎮 Подбор игры\n\n"
            "Сколько человек будет играть?",
            reply_markup=GameKeyboards.get_players_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "🎮 Подбор игры\n\n"
            "Сколько человек будет играть?",
            reply_markup=GameKeyboards.get_players_keyboard(),
            parse_mode="Markdown"
        )

@callback_router.callback_query(F.data.startswith("players:"), StateFilter(GameSelection2.waiting_for_players_1))
async def process_players_selection2(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества игроков."""
    await callback.answer()
    
    _, players_str = callback.data.split(":")
    players = int(players_str)

    current_state = await state.get_state()
    await state.update_data(selected_players=players)

    await state.set_state(GameSelection2.waiting_for_category_1)

    try:
        await callback.message.edit_text(
            f"✅ Выбрано: {players} игроков\n\n"
            f"Теперь выбери категорию:",
            reply_markup=GameKeyboards.get_categories_keyboard()
        )
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(
                f"✅ Выбрано: {players} игроков\n\n"
                f"Теперь выбери категорию:",
                reply_markup=GameKeyboards.get_categories_keyboard()
            )

@callback_router.callback_query(F.data.startswith("category:"), StateFilter(GameSelection2.waiting_for_category_1))
async def process_category_selection2(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории и показ результатов."""
    await callback.answer()
    
    _, category = callback.data.split(":")
    user_data = await state.get_data()
    players = user_data.get('selected_players')
    
    #if not players:
    #    await state.clear()
    #    await callback.message.edit_text(
    #        "❌ Ошибка данных. Начни подбор заново.",
    #        reply_markup=None
    #    )
    #    await cmd_add_game_voting(callback.message, state)
    #    return

    global found_games
    found_games = GameService.filter_games(players, category)

    keyboard = GameKeyboards.get_games_keyboard(found_games)

    await state.set_state(GameSelection2.waiting_for_game_1)
    
    try:
        await callback.message.edit_text(
            text="Выбери игру для голосования",
            reply_markup=keyboard
        )
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(
                text="Ошибочка",
                reply_markup=keyboard
                #parse_mode="Markdown"
            )

@callback_router.callback_query(F.data.startswith("game_for_voting:"), StateFilter(GameSelection2.waiting_for_game_1))
async def process_category_selection3(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора игры и показ результатов."""
    await callback.answer()
    global game_collection
    
    _, game_id = callback.data.split(":")

    user_id = callback.from_user.id
    for game in found_games:
        if game['id']==int(game_id):
            game_name = game['name']
            game_collection['games'].add(game_name)
            

    if user_id in game_collection['users'].keys():
        game_collection['users'][user_id] += [game_name]
    else:
        game_collection['users'][user_id] = [game_name]
    
    await callback.message.delete()
    await callback.message.answer(f"Игра {game_name} добавлена")
    
# --- Обработчик для всех остальных callback-запросов (не подходящих под условия) ---
@callback_router.callback_query()
async def process_unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback-запросов."""
    await callback.answer("Это действие больше не доступно", show_alert=True)
    await callback.message.delete()
