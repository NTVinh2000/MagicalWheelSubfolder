import enum

class STATE(enum.Enum):
    WAITING = 0
    GUESS = 1
    KEYWORD = 2
    WRONG = 3
    TIMEOUT = 4