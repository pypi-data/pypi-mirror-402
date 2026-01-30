from typing import runtime_checkable
from thorlabs_xa.shared.enums import TLMC_CalibrationState
from thorlabs_xa.shared.params import *

from abc import ABC, abstractmethod

@runtime_checkable
class Calibration(ABC):

    @abstractmethod
    def activate(self) -> None:
        pass

    @abstractmethod
    def deactivate(self) -> None:
        pass

    @abstractmethod
    def get_calibration_state(self, max_wait_in_milliseconds: int) -> TLMC_CalibrationState:
        pass
