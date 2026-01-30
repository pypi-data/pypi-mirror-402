from typing import Protocol, runtime_checkable

from thorlabs_xa.shared.enums import TLMC_MoveModes

@runtime_checkable
class Move(Protocol):

    def move(self, move_mode: TLMC_MoveModes, params: int, max_wait_in_milliseconds: int): ...
