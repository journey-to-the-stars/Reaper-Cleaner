from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    PLAY = auto()
    PAUSE = auto()
    DEATH = auto()
    BOSS_VICTORY = auto()
