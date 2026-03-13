from aiogram.fsm.state import State, StatesGroup

class GameSelection(StatesGroup):
    """Состояния для процесса выбора игры."""
    waiting_for_players = State()      # Ждем выбор количества игроков
    waiting_for_category = State()     # Ждем выбор категории

class GameSelection2(StatesGroup):
    """Состояния для процесса выбора игры."""
    waiting_for_players_1 = State()      # Ждем выбор количества игроков в первый раз
    waiting_for_category_1 = State()     # Ждем выбор категории в первый раз
    waiting_for_game_1 = State()

# --- Состояния (только для сбора игр) ---
class GamesCollection(StatesGroup):
    collecting = State()  # Режим сбора игр

# --- Состояния (только для голосования) ---
class Voting(StatesGroup):
    """Состояния для процесса голосования."""
    waiting_for_voting = State()  # Режим сбора оценок

class InsertGame(StatesGroup):
    """Состояния для процесса добавления игры."""
    waiting_name = State()             # Ждем название игры
    waiting_min_players = State()      # Ждем минимального кол-ва игроков
    waiting_max_players = State()      # Ждем максимального кол-ва игроков
    waiting_get_category = State()     # Ждём категорию игры
    waiting_coop_answer = State()      # Ждём подтверждения кооперативности
    waiting_description = State()      # Ждём описание игры