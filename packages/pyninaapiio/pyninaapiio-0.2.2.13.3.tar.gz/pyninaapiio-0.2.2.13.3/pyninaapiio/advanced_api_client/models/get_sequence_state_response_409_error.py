from enum import Enum


class GetSequenceStateResponse409Error(str, Enum):
    SEQUENCER_NOT_INITIALIZED = "Sequencer not initialized"

    def __str__(self) -> str:
        return str(self.value)
