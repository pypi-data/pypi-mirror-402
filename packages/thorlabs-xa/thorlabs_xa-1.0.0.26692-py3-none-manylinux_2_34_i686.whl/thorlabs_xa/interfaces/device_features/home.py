from typing import Protocol, runtime_checkable

@runtime_checkable
class Home(Protocol):

    def home(self, timeout: int) -> None: ...
