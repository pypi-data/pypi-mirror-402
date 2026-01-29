from abc import ABC, abstractmethod
from typing import List, Optional, Union
from ..schema import Conversation

class BaseCollector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        pass

    def generate_id(self, source: str, index: Union[int, str]) -> str:
        return f"{source}_{index}"
