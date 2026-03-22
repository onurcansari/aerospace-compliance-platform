"""
UserReport Entity
Kullanıcının analiz için yüklediği teknik raporlar.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ReportStatus(str, Enum):
    PENDING = "PENDING"         # Yüklendi, analiz bekleniyor
    PROCESSING = "PROCESSING"   # Analiz ediliyor
    COMPLETED = "COMPLETED"     # Tamamlandı
    FAILED = "FAILED"           # Hata oluştu


class ReportType(str, Enum):
    DESIGN = "DESIGN"           # Tasarım raporu
    TEST = "TEST"               # Test raporu
    QUALIFICATION = "QUAL"      # Kalifikasyon raporu
    COMPLIANCE = "COMPLIANCE"   # Uyumluluk beyanı


@dataclass
class UserReport:
    title: str
    file_path: str
    report_type: ReportType

    id: Optional[int] = None
    original_filename: str = ""
    file_size_bytes: int = 0
    status: ReportStatus = ReportStatus.PENDING
    extracted_text: Optional[str] = None
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("Rapor başlığı boş olamaz.")
        if not self.file_path:
            raise ValueError("Dosya yolu boş olamaz.")

    @property
    def is_ready_for_analysis(self) -> bool:
        return (
            self.status == ReportStatus.PENDING
            and self.extracted_text is not None
        )

    @property
    def file_size_kb(self) -> float:
        return round(self.file_size_bytes / 1024, 2)