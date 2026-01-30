from enum import Enum


class QueueJobStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DELAYED = "delayed"
    FAILED = "failed"
    PAUSED = "paused"
    WAITING = "waiting"

    def __str__(self) -> str:
        return str(self.value)
