from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from aiogram.types import BotCommandScopeChat, BotCommandScopeDefault
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
from services.game_sevice import GameService
import os
from dotenv import load_dotenv
from pathlib import Path

# Находим корень проекта
project_root = GameService.find_project_root()
env_path = project_root / '.env'

# Загружаем .env
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    #print(f"Загружен .env из: {env_path}")
else:
    print(f"Файл .env не найден в {project_root}")
    # Можно загрузить без пути - будет искать автоматически
    load_dotenv()

# Получаем айдишники меня и Кусоча
admin_ids_str = os.getenv('ADMIN_IDS', '')

if admin_ids_str:
    admin_ids = list(map(int, admin_ids_str.split(',')))
else:
    admin_ids = []

# --- Клавиатуры (UI слой) ---
class GameKeyboards:
    """Фабрика клавиатур."""
    
    @staticmethod
    def get_players_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для выбора количества игроков."""
        builder = InlineKeyboardBuilder()
        
        players_options = [3, 4, 5, 6]
        buttons = [
            InlineKeyboardButton(text=f"{p} 👤", callback_data=f"players:{p}")
            for p in players_options
        ]
        
        builder.row(*buttons, width=4)
        return builder.as_markup()
    
    @staticmethod
    def get_categories_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для выбора категории."""
        builder = InlineKeyboardBuilder()
        
        # Эмодзи для категорий
        category_emoji = {
            "быстрая": "👪",
            "средняя": "🤝",
            "длинная": "🧠",
            "кооперативная": "🃏",
            "все": "♟️"
        }
        
        categories = ["быстрая", "средняя", "длинная", "кооперативная", "все"]
        buttons = []
        for category in categories:
            emoji = category_emoji.get(category, "🎲")
            buttons.append(
                InlineKeyboardButton(
                    text=f"{emoji} {category.title()}", 
                    callback_data=f"category:{category}"
                )
            )
        
        builder.row(*buttons, width=2)
        builder.row(
            InlineKeyboardButton(text="🔙 Назад (выбрать игроков)", callback_data="back_to_players")
        )
        
        return builder.as_markup()

    @staticmethod
    def get_games_keyboard(found_games) -> InlineKeyboardMarkup:
        """Клавиатура для выбора категории."""
        builder = InlineKeyboardBuilder()

        for game in found_games:
            builder.row(InlineKeyboardButton(text=game['name'], callback_data=f"game_for_voting: {game['id']}"))
        return builder.as_markup()

    @staticmethod
    def create_vote_keyboard(user_id: int, games: list, user_votes: dict):
        """Создает клавиатуру с доступными для голосования играми"""
        builder = InlineKeyboardBuilder()
        
        # Получаем данные пользователя
        user_data = user_votes.get(user_id, {"voted": [], "votes": {}})
        voted_games = user_data["voted"]
        
        # Текущий раунд (сколько уже проголосовали)
        current_round = len(voted_games) + 1
        max_points = len(games)
        
        # Добавляем кнопки игр
        for game in games:
            if game in voted_games:
                # Игра уже оценена - показываем с баллами и ✅
                points = user_data["votes"][game]
                button_text = f"✅ {game} ({points} баллов)"
                callback_data = "voted"
            else:
                # Игра доступна для голосования
                available_points = max_points - current_round + 1
                button_text = f"{game} (дай {available_points} баллов)"
                callback_data = game
        
            builder.add(InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            ))
        
        # Добавляем кнопку результатов
        if len(user_data["votes"])==max_points:
            builder.add(InlineKeyboardButton(
                text="📊 Итоговые результаты",
                callback_data="results"
            ))
        
        # Добавляем кнопку сброса (только если уже есть голоса)
        if user_data["voted"] and len(user_data["votes"])<max_points:
            builder.add(InlineKeyboardButton(
                text="🔄 Сбросить мой голос",
                callback_data="reset_vote"
            ))
        
        # Располагаем кнопки: 1 игра в ряд, остальные кнопки тоже в ряд
        builder.adjust(1, 1, 1)
        
        return builder.as_markup()

    @staticmethod
    def add_game_category() -> InlineKeyboardMarkup:
        """Клавиатура для выбора категории при создании игры."""
        builder = InlineKeyboardBuilder()
        
        # Эмодзи для категорий
        category_emoji = {
            "быстрая": "👪",
            "средняя": "🤝",
            "длинная": "🧠",
        }
        
        categories = ["быстрая", "средняя", "длинная"]
        buttons = []
        for category in categories:
            emoji = category_emoji.get(category, "🎲")
            buttons.append(
                InlineKeyboardButton(
                    text=f"{emoji} {category.title()}", 
                    callback_data=f"category:{category}"
                )
            )
        builder.row(*buttons, width=3)
        return builder.as_markup()
    
    @staticmethod
    def add_game_coop() -> InlineKeyboardMarkup:
        """Клавиатура для определения кооперативности при создании игры."""
        builder = InlineKeyboardBuilder()
        
        # Эмодзи для категорий
        category_emoji = {
            "кооперативная": "🃏",
            "нет": "❌"
        }
        
        categories = ["кооперативная", "нет"]
        buttons = []
        for category in categories:
            emoji = category_emoji.get(category, "🎲")
            buttons.append(
                InlineKeyboardButton(
                    text=f"{emoji} {category.title()}", 
                    callback_data=f"category:{category}"
                )
            )
        builder.row(*buttons, width=2)
        return builder.as_markup()

    async def set_main_menu(bot: Bot):
        user_menu_commands = [
        BotCommand(command='/start',
                   description='Посмотреть возможности бота'),
        BotCommand(command='/show_games',
                   description='Посмотреть доступные игры'),
        BotCommand(command='/add_game_voting',
                   description='Добавить игру на голосование'),
        BotCommand(command='/start_voting',
                   description='Проголосовать'),
        BotCommand(command='/cancel',
                   description='Выйти из текущего состояния'),
        BotCommand(command='/dice',
                   description='Кубик d6')
    ]
        admin_menu_commands = [
            BotCommand(command='/start',
                       description='Посмотреть возможности бота'),
            BotCommand(command='/show_games',
                       description='Посмотреть доступные игры'),
            BotCommand(command='/start_game_collection',
                       description='Начать сбор игр на голосование'),
            BotCommand(command='/stop_collection',
                       description='Закончить сбор игр на голосование'),
            BotCommand(command='/add_game_voting',
                       description='Добавить игру на голосование'),
            BotCommand(command='/start_voting',
                       description='Проголосовать'),
            BotCommand(command='/insert_game',
                       description='Добавить или изменить данные игры'),
            BotCommand(command='/cancel',
                       description='Выйти из текущего состояния'),
            BotCommand(command='/dice',
                       description='Кубик d6')
        ]
        # Set default commands for all users
        await bot.set_my_commands(
            user_menu_commands,
            scope=BotCommandScopeDefault()
        )
        
        # Set admin-specific commands for each admin
        for admin_id in admin_ids:
            await bot.set_my_commands(
                admin_menu_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
        )
