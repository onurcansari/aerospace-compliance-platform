"""
StandardsService
Standartlarla ilgili tum is mantigi buradadir.
API katmani dogrudan veritabanina dokunmaz, bu servis uzerinden calisir.
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.domain.entities.standard import Standard, StandardStatus, StandardType
from src.infrastructure.repositories.repositories import StandardRepository
from src.rag.chunker import TextChunker
from src.rag.pdf_extractor import PDFExtractor
from src.rag.vector_store import VectorStore


class StandardsService:
    """
    Standart ekleme, listeleme ve PDF indeksleme islemlerini yonetir.

    Kullanim:
        service = StandardsService(db)
        standard = service.create_standard(...)
    """

    def __init__(self, db: Session):
        self._repo = StandardRepository(db)
        self._extractor = PDFExtractor()
        self._chunker = TextChunker(chunk_size=200, overlap=40)
        self._vector_store = VectorStore()

    def create_standard(
        self,
        code: str,
        title: str,
        standard_type: str,
        version: str,
        issuing_body: str,
        publication_year: int,
        description: Optional[str] = None,
    ) -> Standard:
        """Yeni bir standart kaydeder."""
        # Ayni kod zaten var mi?
        existing = self._repo.get_by_code(code)
        if existing:
            raise ValueError(f"Bu kod zaten kayitli: {code}")

        standard = Standard(
            code=code.upper(),
            title=title,
            standard_type=StandardType(standard_type),
            version=version,
            issuing_body=issuing_body,
            publication_year=publication_year,
            description=description,
        )

        saved = self._repo.save(standard)
        logger.info(f"Standart olusturuldu: {saved.code} (id={saved.id})")
        return saved

    def list_standards(self, status: Optional[str] = None) -> List[Standard]:
        """Tum standartlari listeler."""
        std_status = StandardStatus(status) if status else None
        return self._repo.get_all(status=std_status)

    def get_standard(self, standard_id: int) -> Standard:
        """ID ile tek standart getirir."""
        standard = self._repo.get_by_id(standard_id)
        if not standard:
            raise ValueError(f"Standart bulunamadi: id={standard_id}")
        return standard

    def search_standards(self, query: str) -> List[Standard]:
        """Basliga gore arama yapar."""
        return self._repo.search_by_title(query)

    def index_pdf(self, standard_id: int, pdf_path: str) -> dict:
        """
        PDF'i okur, parcalar ve ChromaDB'ye kaydeder.
        Bu islemi yapinca standart 'indexed' olarak isaretlenir.
        """
        standard = self._repo.get_by_id(standard_id)
        if not standard:
            raise ValueError(f"Standart bulunamadi: id={standard_id}")

        logger.info(f"PDF indeksleme basladi: {standard.code}")

        # 1. PDF'i oku
        doc = self._extractor.extract(pdf_path)

        # 2. Parcala
        chunks = self._chunker.chunk_by_pages(doc.pages, standard_id=standard_id)

        # 3. ChromaDB'ye kaydet
        self._vector_store.add_chunks(chunks, standard_id=standard_id)

        # 4. Standardi indexed olarak isaretле
        standard.pdf_path = pdf_path
        standard.is_indexed = True
        self._repo.save(standard)
        self._repo.mark_as_indexed(standard_id)

        result = {
            "standard_code": standard.code,
            "total_pages": doc.total_pages,
            "total_chunks": len(chunks),
            "status": "indexed",
        }

        logger.info(f"PDF indeksleme tamamlandi: {result}")
        return result

    def delete_standard(self, standard_id: int) -> bool:
        """Standardi siler."""
        return self._repo.delete(standard_id)