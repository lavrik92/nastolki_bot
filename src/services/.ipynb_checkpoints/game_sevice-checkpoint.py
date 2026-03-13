from typing import List, Dict, Any, Optional
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Определяем где хранить данные
def get_data_file():
    """Возвращает правильный путь для data.json"""
    
    # Для Amvera (папка /data существует и доступна для записи)
    if os.path.exists("/data"):
        return "/data/data/data.json"
    
    # Для локальной разработки
    local_path = Path(__file__).parent.parent.parent / "data" / "data" / "data.json"
    # Создаём папку data, если её нет
    local_path.parent.mkdir(exist_ok=True)
    return str(local_path)

# Используй эту переменную везде в коде
DATA_FILE = get_data_file()

with open(DATA_FILE, 'r') as file:
    games_catalog = json.load(file)

# --- База данных в памяти ---
global game_collection
game_collection = {
    "is_active": False,           # Идет ли сейчас сбор
    "creator_id": None,           # ID создателя
    "games": set(),                  # Список игр
    "users": {}               # Участники (чтобы знать, кто добавлял и что)
}

class GameService:
    """Сервис для работы с играми."""

    @staticmethod
    def find_project_root():
        """Ищет корневую папку проекта (где лежит .env)"""
        current_dir = Path.cwd()
        
        # Ищем .env в текущей папке и выше (максимум 3 уровня)
        for _ in range(4):  # проверяем текущую + 3 уровня вверх
            if (current_dir / '.env').exists():
                return current_dir
            current_dir = current_dir.parent
        
        # Если не нашли, возвращаем текущую папку
        return Path.cwd()

    @staticmethod
    def names_of_games() -> List:
        """Возвращает названия существующих игр"""
        list_of_games = []
        for game in games_catalog:
            list_of_games.append(game['name'])
        return list_of_games
    
    @staticmethod
    def filter_games(players: int, category: str) -> List[Dict[str, Any]]:
        """
        Фильтрует игры по количеству игроков и категории.
        Игра подходит, если players входит в диапазон [players_min, players_max]
"""
        filtered = []
        for game in games_catalog:
            if game['players_min'] <= players <= game['players_max']:
                if category.lower() == 'все':
                    filtered.append(game)
                elif category.lower() == 'кооперативная':
                    if game['coop_flg'] == 'Coop':
                        filtered.append(game)
                elif game['category'].lower() == category.lower():
                    filtered.append(game)
        return filtered
    
    @staticmethod
    def format_games_result(games: List[Dict[str, Any]], players: int, category: str) -> str:
        """Форматирует результат поиска для отправки пользователю."""
        if not games:
            return (
                f"😢 Ничего не найдено\n\n"
                f"Для {players} игроков в категории {category.title()} игр нет.\n\n"
                f"Попробуй выбрать другое количество игроков или категорию.\n"
                f"Используй /show_games для нового поиска."
            )
        
        text = (
            f"✅ Найденные игры\n"
            f"👥 {players} игроков | 📌 {category.title()}\n\n"
        )
        
        for i, game in enumerate(games, 1):
            text += (
                f"{i}. {game['name']}\n"
                f"   👥 {game['players_min']}-{game['players_max']} чел.\n"
                f"   📝 {game['description']}\n\n"
            )
        
        text += "🎲 Используй /show_games для нового поиска."
        return text
