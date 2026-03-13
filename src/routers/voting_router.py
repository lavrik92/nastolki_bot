import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.game_sevice import game_collection
from keyboards.keyboards import GameKeyboards
from states.fsm_states import Voting
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

voting_router = Router()

# Хранилище данных пользователей {user_id: {"voted": [игры], "votes": {игра: баллы}}}
user_votes = {}

global game_collection

@voting_router.message(Command("start_voting"))
async def cmd_start_voting(message: types.Message, state: FSMContext):
    """Обработчик команды /start_voting"""
    
    if game_collection["is_active"]:
        await message.answer(
            "❌ Сбор игр пока идет!\n"
        )
        return
    
    games = list(game_collection['games'])
    if not games:
        await message.answer(
            "❌ Сначала надо выбрать игры для голосования"
        )
        return
    
    user_id = message.from_user.id
    
    # Инициализируем пользователя
    if user_id not in user_votes:
        user_votes[user_id] = {"voted": [], "votes": {}}
    
    keyboard = GameKeyboards.create_vote_keyboard(user_id, games, user_votes)

    await state.set_state(Voting.waiting_for_voting)
    
    max_points = len(games)
    await message.answer(
        f"🎮 Рейтинговое голосование за лучшую игру!\n\n"
        f"Правила:\n"
        f"1. Сначала выбери ЛУЧШУЮ игру (получит {max_points} баллов)\n"
        f"2. Потом вторую по убыванию (получит {max_points-1} баллов)\n"
        f"3. И так далее до худшей (получит 1 балл)\n\n"
        f"Твой выбор:",
        reply_markup=keyboard
    )

@voting_router.callback_query(StateFilter(Voting.waiting_for_voting))
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик всех нажатий на кнопки"""
    global game_collection
    games = list(game_collection['games'])

    user_id = callback.from_user.id
    
    # Обработка кнопки сброса
    if callback.data == "reset_vote":
        # Сбрасываем голоса пользователя
        if user_id in user_votes:
            user_votes[user_id] = {"voted": [], "votes": {}}
        
        # Обновляем клавиатуру
        keyboard = GameKeyboards.create_vote_keyboard(user_id, games, user_votes)
        
        max_points = len(games)
        await callback.message.edit_text(
            text=f"🎮 Рейтинговое голосование за лучшую игру!\n\n"
                 f"Правила:\n"

    f"1. Сначала выбери ЛУЧШУЮ игру (получит {max_points} баллов)\n"
                 f"2. Потом вторую по убыванию (получит {max_points-1} баллов)\n"
                 f"3. И так далее до худшей (получит 1 балл)\n"
                 f"🔄 Твои голоса сброшены! Можешь голосовать заново."
                 f"🔄 Переголосовать нельзя, если оценил все игры\n\n"
                 f"Твой выбор:",
            reply_markup=keyboard
        )
        
        await callback.answer("Голоса успешно сброшены!")
        return
    
    # Обработка результатов
    if callback.data == "results":
        if not user_votes:
            await callback.message.answer("😢 Пока никто не голосовал!")
        else:
            # Собираем все баллы по играм
            total_scores = {}
            participants = 0
            
            for uid, user_data in user_votes.items():
                if user_data["votes"]:  # Если пользователь хоть за что-то голосовал
                    participants += 1
                    for game, points in user_data["votes"].items():
                        total_scores[game] = total_scores.get(game, 0) + points
            
            if not total_scores:
                await callback.message.answer("😢 Пока никто не голосовал!")
            else:
                # Сортируем по убыванию
                sorted_games = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
                
                results_text = f"📊 Общие результаты (участников: {participants}):\n\n"
                medals = ["🏆", "🥈", "🥉"] + ["📌"]*20
                i = 0
                for game, score in sorted_games:
                    # Показываем различные эмодзи для наглядности
                    emoji = medals[i]
                    results_text += f"{emoji} {game}: {score} баллов\n"
                    i += 1
                
                await callback.message.answer(results_text)
        
        await callback.answer()
        return
    
    # Обработка заблокированных кнопок
    if callback.data == "voted":
        await callback.answer("Эта игра уже оценена!", show_alert=True)
        return
    
    # Голосование за игру
    game_name = callback.data
    max_points = len(games)
    
    # Проверяем, не голосовал ли уже за эту игру
    if user_id not in user_votes:
        user_votes[user_id] = {"voted": [], "votes": {}}
    
    if game_name in user_votes[user_id]["voted"]:
        await callback.answer("Ты уже оценил эту игру!", show_alert=True)
        return
    
    # Сколько уже проголосовали
    voted_count = len(user_votes[user_id]["voted"])
    
    # Сколько баллов даем за эту игру
    points_to_give = max_points - voted_count
    
    # Проверяем, не пытается ли пользователь проголосовать больше раз, чем игр
    if voted_count >= max_points:
        await callback.answer("Ты уже оценил все игры!", show_alert=True)
        await state.clear()
        return
    
    # Сохраняем голос
    user_votes[user_id]["voted"].append(game_name)
    user_votes[user_id]["votes"][game_name] = points_to_give
    
    # Обновляем клавиатуру
    keyboard = GameKeyboards.create_vote_keyboard(user_id, games, user_votes)
    
    # Проверяем, закончил ли пользователь голосование
    remaining = max_points - (voted_count + 1)
    
    if remaining > 0:
        status_text = (f"✅ Оценена: {game_name} ({points_to_give} баллов)\n"
                      f"📌 Осталось оценить игр: {remaining}\n"
                      f"👇 Выбери следующую по значимости игру:")
    else:
        status_text = "🎉 Ты оценил все игры! Спасибо за участие!"
    
    await callback.message.edit_text(
        text=f"🎮 Рейтинговое голосование\n\n"
             f"{status_text}",
        reply_markup=keyboard
    )

    await callback.answer(f"Игра '{game_name}' получила {points_to_give} баллов!")