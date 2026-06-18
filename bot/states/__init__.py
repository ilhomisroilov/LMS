"""FSM states for the bot."""
from aiogram.fsm.state import State, StatesGroup


class Auth(StatesGroup):
    waiting_phone = State()


class TakeAttendance(StatesGroup):
    selecting_group = State()
    marking = State()
