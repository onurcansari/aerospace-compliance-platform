from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class StandardType(str, Enum):
    MILITARY = "MIL"
    CIVIL = "CIVIL"
    INTERNATIONAL = "INTL"


class StandardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


@dataclass
class Standard:
    code: str
    title: str
    standard_type: StandardType
    version: str
    issuing_body: str
    publication_year: int

    id: Optional[int] = None
    description: Optional[str] = None
    pdf_path: Optional[str] = None
    is_indexed: bool = False
    status: StandardStatus = StandardStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.code or not self.code.strip():
            raise ValueError("Standart kodu bos olamaz.")
        if not (1900 <= self.publication_year <= 2100):
            raise ValueError(f"Gecersiz yayin yili: {self.publication_year}")

    @property
    def display_name(self) -> str:
        return f"{self.code} --- {self.title} ({self.version})"

    @property
    def is_military(self) -> bool:
        return self.standard_type == StandardType.MILITARY