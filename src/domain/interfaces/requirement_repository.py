from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.requirement import Requirement, RequirementCategory


class IRequirementRepository(ABC):

    @abstractmethod
    def get_by_id(self, requirement_id: int) -> Optional[Requirement]:
        ...

    @abstractmethod
    def get_by_standard(self, standard_id: int, category: Optional[RequirementCategory] = None) -> List[Requirement]:
        ...

    @abstractmethod
    def get_by_chunk_id(self, chunk_id: str) -> Optional[Requirement]:
        ...

    @abstractmethod
    def save(self, requirement: Requirement) -> Requirement:
        ...

    @abstractmethod
    def save_batch(self, requirements: List[Requirement]) -> List[Requirement]:
        ...

    @abstractmethod
    def delete_by_standard(self, standard_id: int) -> int:
        ...