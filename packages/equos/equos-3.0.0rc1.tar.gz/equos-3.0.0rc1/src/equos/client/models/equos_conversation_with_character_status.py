from enum import Enum


class EquosConversationWithCharacterStatus(str, Enum):
    BLOCKED = "blocked"
    ENDED = "ended"
    ERROR = "error"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
