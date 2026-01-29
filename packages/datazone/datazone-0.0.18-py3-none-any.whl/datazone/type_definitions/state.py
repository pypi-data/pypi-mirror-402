from enum import Enum
from typing import Optional


class StateWriteOn(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NOW = "now"


class State:
    def write(self, key: str, value: str, on: StateWriteOn = StateWriteOn.NOW):
        ...
    """
    Write a key-value pair to the state.
    """

    def read(self, key: str, default: Optional[str] = None):
        ...
    """
    Read a value from the state.
    """
