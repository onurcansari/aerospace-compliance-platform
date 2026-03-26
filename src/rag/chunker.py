"""
Metni anlamsal parcalara (chunk) ayirir.
Her chunk ChromaDB'ye ayri bir vektor olarak kaydedilir.
"""
from dataclasses import dataclass
from typing import List

from loguru import logger


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    page_number: int
    chunk_index: int
    word_count: int


class TextChunker:
    """
    Uzun metni kucuk, anlamli parcalara boler.

    chunk_size: Her parcada kac kelime olsun (varsayilan 200)
    overlap:    Parcalar arasi kac kelime cakissin (baglam icin)
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 40):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(
        self,
        text: str,
        standard_id: int,
        page_number: int = 0,
        start_index: int = 0,  # Global sayac buradan baslar
    ) -> List[TextChunk]:
        words = text.split()
        if not words:
            return []

        chunks = []
        index = 0
        chunk_num = start_index
        total_words = len(words)

        while index < total_words:
            end = min(index + self.chunk_size, total_words)
            chunk_words = words[index:end]
            chunk_text = " ".join(chunk_words)

            # ID artik global sayaci kullanıyor
            chunk_id = f"std_{standard_id}_chunk_{chunk_num:04d}"

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                page_number=page_number,
                chunk_index=chunk_num,
                word_count=len(chunk_words),
            ))

            chunk_num += 1
            index += self.chunk_size - self.overlap

        return chunks

    def chunk_by_pages(self, pages: list, standard_id: int) -> List[TextChunk]:
        """
        Her sayfayi ayri ayri parcalar.
        DUZELTME: Global sayac kullanir, her sayfada sifirlanmaz.
        """
        all_chunks = []
        global_index = 0  # Tum sayfalar boyunca artan sayac

        for page in pages:
            page_chunks = self.chunk(
                text=page.text,
                standard_id=standard_id,
                page_number=page.page_number,
                start_index=global_index,  # Kaldigi yerden devam et
            )
            all_chunks.extend(page_chunks)
            global_index += len(page_chunks)  # Sayaci ilerlet

        logger.info(
            f"standard_id={standard_id}: "
            f"toplam {len(all_chunks)} chunk olusturuldu "
            f"({len(pages)} sayfa)."
        )
        return all_chunks