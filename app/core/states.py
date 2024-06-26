from aiogram.fsm.state import StatesGroup, State


class QuizStates(StatesGroup):
    quiz_in_progress = State()


class AdminStates(StatesGroup):
    choose_date_interval = State()
