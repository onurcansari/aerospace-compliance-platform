from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.user_report import UserReport, ReportStatus


class IReportRepository(ABC):

    @abstractmethod
    def get_by_id(self, report_id: int) -> Optional[UserReport]:
        ...

    @abstractmethod
    def get_all(self, status: Optional[ReportStatus] = None) -> List[UserReport]:
        ...

    @abstractmethod
    def save(self, report: UserReport) -> UserReport:
        ...

    @abstractmethod
    def update_status(self, report_id: int, status: ReportStatus, extracted_text: Optional[str] = None) -> None:
        ...

    @abstractmethod
    def delete(self, report_id: int) -> bool:
        ...