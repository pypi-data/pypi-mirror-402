from enum import Enum


class CreateEquosFaceRequestIdentity(str, Enum):
    DEBORAH = "deborah"
    TOMMY = "tommy"

    def __str__(self) -> str:
        return str(self.value)
