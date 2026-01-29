from enum import Enum


class EquosFaceIdentity(str, Enum):
    DEBORAH = "deborah"
    TOMMY = "tommy"

    def __str__(self) -> str:
        return str(self.value)
