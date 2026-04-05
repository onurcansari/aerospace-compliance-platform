
from dataclasses import dataclass
from typing import List, Optional

import chromadb
from loguru import logger


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    standard_id: int
    page_number: int
    similarity_score: float


class VectorStore:
    """
    ChromaDB uzerinde embed + arama islemlerini yonetir.

    Kullanim:
        store = VectorStore()
        store.add_chunks(chunks, standard_id=1)
        results = store.search("vibrasyon testi gereksinimleri", top_k=5)
    """

    COLLECTION_NAME = "aerospace_standards"

    def __init__(self, persist_dir: str = "./chroma_db"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"VectorStore hazir. Koleksiyon: {self.COLLECTION_NAME}")

    def add_chunks(self, chunks: list, standard_id: int) -> None:
        """Chunklari ChromaDB'ye ekler."""
        if not chunks:
            logger.warning("Eklenecek chunk yok.")
            return

        # Once eskileri sil
        self._delete_by_standard(standard_id)

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "standard_id": standard_id,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        # Kucuk gruplara bolarak ekle
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self._collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )

        logger.info(
            f"standard_id={standard_id}: {len(chunks)} chunk ChromaDB'ye eklendi."
        )
    def search(self, query: str, top_k: int = 5, standard_id: Optional[int] = None) -> List[SearchResult]:
        """Sorguya en yakin chunklari bulur."""
        where = {"standard_id": standard_id} if standard_id else None

        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )

        search_results = []
        if not results["ids"] or not results["ids"][0]:
            return []

        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            text = results["documents"][0][i]
            # ChromaDB cosine distance'i 0-2 arasi verir, 1'den cikar similarity'e ceviriz
            distance = results["distances"][0][i]
            similarity = round(1 - (distance / 2), 4)

            search_results.append(SearchResult(
                chunk_id=chunk_id,
                text=text,
                standard_id=metadata["standard_id"],
                page_number=metadata["page_number"],
                similarity_score=similarity,
            ))

        logger.info(f"'{query[:50]}' icin {len(search_results)} sonuc bulundu.")
        return search_results

    def _delete_by_standard(self, standard_id: int) -> None:
        """Bir standarda ait tum chunklari siler."""
        try:
            # Once mevcut chunk'lari getir
            existing = self._collection.get(
                where={"standard_id": standard_id}
            )
            if existing and existing["ids"]:
                logger.info(
                    f"standard_id={standard_id}: "
                    f"{len(existing['ids'])} eski chunk siliniyor..."
                )
                # Kucuk gruplara bolarak sil (ChromaDB bazen buyuk silmelerde takilir)
                ids = existing["ids"]
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    batch = ids[i:i + batch_size]
                    self._collection.delete(ids=batch)
                logger.info(f"standard_id={standard_id}: eski chunk'lar silindi.")
        except Exception as e:
            logger.warning(f"Eski chunk silerken hata (devam ediliyor): {e}")
    def get_chunk_count(self) -> int:
        return self._collection.count()