from dataclasses import dataclass
import logging

from aiogram.fsm.state import State, StatesGroup


@dataclass
class Mode(StatesGroup):
    main: State = State()
