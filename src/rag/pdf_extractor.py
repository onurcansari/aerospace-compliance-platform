
from dataclasses import dataclass
from pathlib import Path
from typing import List

from loguru import logger

import fitz  # PyMuPDF


@dataclass
class PageContent:
    page_number: int
    text: str
    word_count: int


@dataclass
class ExtractedDocument:
    file_path: str
    total_pages: int
    pages: List[PageContent]
    full_text: str


class PDFExtractor:
    """
    PDF dosyalarindan temiz metin cikarir.

    Kullanim:
        extractor = PDFExtractor()
        doc = extractor.extract("MIL-STD-810H.pdf")
        print(doc.total_pages)
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF bulunamadi: {file_path}")

        logger.info(f"PDF okunuyor: {path.name}")

        pdf = fitz.open(str(path))
        pages = []

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            raw_text = page.get_text("text")
            clean_text = self._clean_text(raw_text)

            if clean_text.strip():
                pages.append(PageContent(
                    page_number=page_num + 1,
                    text=clean_text,
                    word_count=len(clean_text.split()),
                ))

        pdf.close()

        full_text = "\n\n".join(p.text for p in pages)
        total_words = sum(p.word_count for p in pages)

        logger.info(
            f"PDF okundu: {len(pages)} sayfa, {total_words} kelime"
        )

        return ExtractedDocument(
            file_path=str(path),
            total_pages=len(pages),
            pages=pages,
            full_text=full_text,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """Gereksiz bosluk ve karakterleri temizler."""
        import re
        # Cok fazla boslugu tek bosluga indir
        text = re.sub(r" {2,}", " ", text)
        # Uc veya daha fazla bos satiri iki satira indir
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Sayfa numarasi gibi tek basina duran sayilari kaldir
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        return text.strip()