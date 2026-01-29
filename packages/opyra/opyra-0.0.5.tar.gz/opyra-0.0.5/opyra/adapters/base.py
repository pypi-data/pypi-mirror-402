from abc import ABC, abstractmethod
import typing


class AbstractAdapter(ABC):
    type: str  # 'sql' or 'nosql'
    param_style: str = "named" # 'named', 'numeric', etc.

    @abstractmethod
    async def execute(self, query: typing.Any, params: typing.Any = None):
        pass

    @abstractmethod
    async def fetch_all(self, query: typing.Any, params: typing.Any = None) -> list:
        pass

    @abstractmethod
    async def disconnect(self):
        pass

