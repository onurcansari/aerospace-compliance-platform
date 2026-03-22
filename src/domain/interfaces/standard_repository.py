from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.standard import Standard, StandardStatus


class IStandardRepository(ABC):

    @abstractmethod
    def get_by_id(self, standard_id: int) -> Optional[Standard]:
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Standard]:
        ...

    @abstractmethod
    def get_all(self, status: Optional[StandardStatus] = None) -> List[Standard]:
        ...

    @abstractmethod
    def save(self, standard: Standard) -> Standard:
        ...

    @abstractmethod
    def delete(self, standard_id: int) -> bool:
        ...

    @abstractmethod
    def mark_as_indexed(self, standard_id: int) -> None:
        ...

    @abstractmethod
    def search_by_title(self, query: str) -> List[Standard]:
        ...