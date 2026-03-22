"""
Metni anlamsal parcalara (chunk) ayirir.
Her chunk ChromaDB'ye ayri bir vektor olarak kaydedilir.
"""
from dataclasses import dataclass
from typing import List

from loguru import logger


@dataclass
class TextChunk:
    chunk_id: str        # Benzersiz ID: "std_1_chunk_0042"
    text: str            # Parca metni
    page_number: int     # Hangi sayfadan geldi
    chunk_index: int     # Kacinci parca
    word_count: int


class TextChunker:
    """
    Uzun metni kucuk, anlamli parcalara boler.

    chunk_size: Her parcada kac kelime olsun (varsayilan 200)
    overlap:    Parcalar arasi kac kelime cakissin (baglam icin)

    Kullanim:
        chunker = TextChunker(chunk_size=200, overlap=40)
        chunks = chunker.chunk(full_text, standard_id=1)
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 40):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, standard_id: int, page_number: int = 0) -> List[TextChunk]:
        words = text.split()
        if not words:
            return []

        chunks = []
        index = 0
        chunk_num = 0
        total_words = len(words)

        while index < total_words:
            end = min(index + self.chunk_size, total_words)
            chunk_words = words[index:end]
            chunk_text = " ".join(chunk_words)

            chunk_id = f"std_{standard_id}_chunk_{chunk_num:04d}"

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                page_number=page_number,
                chunk_index=chunk_num,
                word_count=len(chunk_words),
            ))

            chunk_num += 1
            # Bir sonraki parca overlap kadar geri baslar
            index += self.chunk_size - self.overlap

        logger.info(f"standard_id={standard_id}: {len(chunks)} chunk olusturuldu.")
        return chunks

    def chunk_by_pages(self, pages: list, standard_id: int) -> List[TextChunk]:
        """Her sayfayi ayri ayri parcalar."""
        all_chunks = []
        for page in pages:
            page_chunks = self.chunk(
                text=page.text,
                standard_id=standard_id,
                page_number=page.page_number,
            )
            all_chunks.extend(page_chunks)
        return all_chunks