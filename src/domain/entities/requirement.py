"""
Requirement Entity
Bir standardın tek tek maddelerini temsil eder.
Örnek: MIL-STD-810H Method 514.8 — Vibration
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RequirementCategory(str, Enum):
    ENVIRONMENTAL = "ENVIRONMENTAL"   # Çevresel testler
    ELECTROMAGNETIC = "EMC"           # Elektromanyetik uyumluluk
    SOFTWARE = "SOFTWARE"             # Yazılım sertifikasyonu
    STRUCTURAL = "STRUCTURAL"         # Yapısal dayanım
    SAFETY = "SAFETY"                 # Güvenlik


@dataclass
class Requirement:
    standard_id: int          # Hangi standarda ait
    section_id: str           # Örn: "Method 514.8"
    title: str                # Kısa başlık
    requirement_text: str     # Tam gereksinim metni

    id: Optional[int] = None
    category: RequirementCategory = RequirementCategory.ENVIRONMENTAL
    page_number: Optional[int] = None   # PDF'teki sayfa numarası
    chunk_id: Optional[str] = None      # ChromaDB'deki ID
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.section_id or not self.section_id.strip():
            raise ValueError("Section ID boş olamaz.")
        if len(self.requirement_text) < 10:
            raise ValueError("Gereksinim metni çok kısa.")

    @property
    def full_reference(self) -> str:
        """İzlenebilirlik için tam referans kodu."""
        return f"REQ-{self.standard_id}-{self.section_id}"