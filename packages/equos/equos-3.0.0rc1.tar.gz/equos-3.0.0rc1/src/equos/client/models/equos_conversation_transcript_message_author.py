from enum import Enum


class EquosConversationTranscriptMessageAuthor(str, Enum):
    CHARACTER = "character"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
