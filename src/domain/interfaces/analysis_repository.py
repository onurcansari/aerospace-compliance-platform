from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from src.domain.entities.analysis_log import AnalysisLog


class IAnalysisRepository(ABC):

    @abstractmethod
    def get_by_id(self, log_id: int) -> Optional[AnalysisLog]:
        ...

    @abstractmethod
    def get_by_report(self, report_id: int) -> List[AnalysisLog]:
        ...

    @abstractmethod
    def get_by_requirement(self, requirement_id: int) -> List[AnalysisLog]:
        ...

    @abstractmethod
    def save(self, log: AnalysisLog) -> AnalysisLog:
        ...

    @abstractmethod
    def get_compliance_summary(self, report_id: int) -> Dict:
        ...