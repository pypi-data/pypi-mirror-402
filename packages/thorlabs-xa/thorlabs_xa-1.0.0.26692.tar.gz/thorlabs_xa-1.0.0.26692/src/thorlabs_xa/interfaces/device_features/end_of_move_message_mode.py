from typing import Protocol, runtime_checkable

from thorlabs_xa.shared.enums import TLMC_EndOfMoveMessageMode

@runtime_checkable
class EndOfMoveMessageMode(Protocol):

    def set_end_of_move_messages_mode(self, message_mode: TLMC_EndOfMoveMessageMode) -> None: ...