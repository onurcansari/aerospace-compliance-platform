"""
AnalysisLog Entity
Her uyumluluk analizi işleminin kaydı.
Savunma sanayiinde her analiz izlenebilir olmalıdır.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ComplianceVerdict(str, Enum):
    COMPLIANT = "COMPLIANT"            # Tam uyumlu
    PARTIALLY_COMPLIANT = "PARTIAL"    # Kısmen uyumlu
    NON_COMPLIANT = "NON_COMPLIANT"    # Uyumsuz
    INSUFFICIENT_DATA = "INSUFFICIENT" # Yetersiz veri


@dataclass
class AnalysisLog:
    report_id: int
    requirement_id: int
    verdict: ComplianceVerdict
    ai_reasoning: str          # AI'ın detaylı gerekçesi
    confidence_score: float    # 0.0 ile 1.0 arası güven skoru

    id: Optional[int] = None
    retrieved_chunks: Optional[str] = None  # RAG'ın bulduğu metinler
    llm_model_used: str = "gpt-4o"
    analysis_duration_ms: int = 0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"Güven skoru 0.0-1.0 arasında olmalı: {self.confidence_score}")
        if len(self.ai_reasoning) < 20:
            raise ValueError("AI gerekçesi çok kısa.")

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_score >= 0.85

    @property
    def verdict_label(self) -> str:
        labels = {
            ComplianceVerdict.COMPLIANT: "Uyumlu",
            ComplianceVerdict.PARTIALLY_COMPLIANT: "Kısmen Uyumlu",
            ComplianceVerdict.NON_COMPLIANT: "Uyumsuz",
            ComplianceVerdict.INSUFFICIENT_DATA: "Yetersiz Veri",
        }
        return labels.get(self.verdict, "Bilinmiyor")