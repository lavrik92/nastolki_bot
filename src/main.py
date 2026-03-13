import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from routers.main_router import main_router
from routers.show_games_router import show_games_router
from routers.callback_router import callback_router
from routers.insert_game_router import insert_game_router
from routers.voting_router import voting_router, user_votes
from routers.game_selection_router import games_selection_router, game_collection
from keyboards.keyboards import GameKeyboards
from states.fsm_states import GameSelection2
from services.game_sevice import GameService

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

# Получаем токен
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Получаем айдишники меня и Кусоча
admin_ids_str = os.getenv('ADMIN_IDS', '')

if admin_ids_str:
    admin_ids = list(map(int, admin_ids_str.split(',')))
else:
    admin_ids = []

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("name.log")

# --- Запуск бота ---
async def main():
    """Точка входа."""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем роутеры
    dp.include_router(main_router)
    dp.include_router(show_games_router)
    dp.include_router(games_selection_router)
    dp.include_router(voting_router)
    dp.include_router(insert_game_router)
    dp.include_router(callback_router)
    
    dp.startup.register(GameKeyboards.set_main_menu)
    
    logger.info("Бот запущен...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())