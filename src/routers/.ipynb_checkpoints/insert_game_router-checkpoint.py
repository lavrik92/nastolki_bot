from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram import Bot, Dispatcher
import aiogram.utils.markdown as fmt
import json

from keyboards.keyboards import GameKeyboards
from states.fsm_states import InsertGame
from services.game_sevice import GameService, games_catalog
import os
from pathlib import Path

# Определяем где хранить данные
def get_data_file():
    """Возвращает правильный путь для data.json"""
    
    # Для Amvera (папка /data существует и доступна для записи)
    if os.path.exists("/data"):
        return "/data/data/data.json"
    
    # Для локальной разработки
    local_path = Path(__file__).parent.parent / "data" / "data" / "data.json"
    # Создаём папку data, если её нет
    local_path.parent.mkdir(exist_ok=True)
    return str(local_path)

# Используй эту переменную везде в коде
DATA_FILE = get_data_file()

insert_game_router = Router()
new_game = dict()

global games_catalog

@insert_game_router.message(Command("insert_game"))
async def cmd_insert_game(message: Message, state: FSMContext):
    """Начало процесса добавления игры."""
    await state.clear()
    await state.set_state(InsertGame.waiting_name)
    
    await message.answer("Как называется игра?")
    
@insert_game_router.message(StateFilter(InsertGame.waiting_name))
async def get_name(message: Message, state: FSMContext):
    """Обработка получения названия игры."""
    await state.clear()
    await state.set_state(InsertGame.waiting_min_players)
    
    new_game['name'] = message.text
    
    await message.answer("Какое минимальное число игроков?")
    
@insert_game_router.message(StateFilter(InsertGame.waiting_min_players))
async def get_min_players(message: Message, state: FSMContext):
    """Обработка получения минимального числа игроков."""
    if message.text.isdigit():
        await state.clear()
        await state.set_state(InsertGame.waiting_max_players)
        
        new_game['players_min'] = int(message.text)
        
        await message.answer("Какое максимальное число игроков?")
    else:
        current_state = await state.get_state()
        await message.answer("Пожалуйста, введите минимальное количество игроков числом")
        
@insert_game_router.message(StateFilter(InsertGame.waiting_max_players))
async def get_max_players(message: Message, state: FSMContext):
    """Обработка получения максимального числа игроков."""
    if message.text.isdigit():
        if int(message.text) >= new_game['players_min']:
            await state.clear()
            await state.set_state(InsertGame.waiting_get_category)
            
            new_game['players_max'] = int(message.text)
                        
            await message.answer(
                "Выберите категорию игру", 
                reply_markup=GameKeyboards.add_game_category()
            )
        else:
            current_state = await state.get_state()
            await message.answer(f"Максимальное число игроков должно превышать минимальное.\n"
                           f"Пожалуйста, введите максимальное количество игроков")
    else:
        current_state = await state.get_state()
        await message.answer("Пожалуйста, введите максимальное количество игроков числом")
        
        
@insert_game_router.callback_query(F.data.startswith("category:"), StateFilter(InsertGame.waiting_get_category))
async def get_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    await callback.answer()
    
    _, category = callback.data.split(":")
    new_game['category'] = category
    await state.set_state(InsertGame.waiting_coop_answer)
    
    try:
        await callback.message.edit_text(
            f"✅ Выбрана категория: {category}\n\n"
            f"Теперь ответь: игра кооперативная?",
            reply_markup=GameKeyboards.add_game_coop()
        )
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(
            f"✅ Выбрана категория: {category}\n\n"
            f"Теперь ответь: игра кооперативная?",
            reply_markup=GameKeyboards.add_game_coop()
        )
            
@insert_game_router.callback_query(F.data.startswith("category:"), StateFilter(InsertGame.waiting_coop_answer))
async def get_coop(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения кооперативности"""
    await callback.answer()
    
    _, category = callback.data.split(":")
    if category.lower() == 'кооперативная':
        new_game['coop_flg'] = 'Coop'
    else:
        new_game['coop_flg'] = 'Not'
    
    await state.set_state(InsertGame.waiting_description)
    
    try:
        await callback.message.edit_text(f"Теперь добавь описание игры")
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower():
            await callback.message.answer(f"Теперь добавь описание игры")

@insert_game_router.message(StateFilter(InsertGame.waiting_description))
async def get_description(message: Message, state: FSMContext):    
    game_list = GameService.names_of_games()
    
    new_game['description'] = message.text
    new_game['id'] = len(game_list)
    
    if new_game['name'] in game_list:
        for game in games_catalog:
            if new_game['name'] == game['name']:
                game['players_min'] = new_game['players_min']
                game['players_max'] = new_game['players_max']
                game['category'] = new_game['category']
                game['coop_flg'] = new_game['coop_flg']
                game['description'] = new_game['description']
                
                await message.answer(f"Обновлена игра {game['name']}\n")
    else:
        games_catalog.append(new_game.copy())
        await message.answer(f"Добавлена игра {new_game['name']}\n")

    with open("/data/data/data.json", 'w') as file:
        json.dump(games_catalog, file)
    
    await state.clear()
    
    await message.answer(
        "🔄 Что дальше?\n"
        "• /show_games - новый подбор\n"
        "• /start - главное меню",
        #parse_mode="Markdown"
    )