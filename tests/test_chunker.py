"""
RAG Chunker Testleri
Metin parcalamanin dogru calistigini test eder.
"""
import pytest
from src.rag.chunker import TextChunker


class TestTextChunker:

    def test_kisa_metin_tek_chunk(self):
        """Kisa metin tek parca olmali."""
        chunker = TextChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk("Bu kisa bir metindir.", standard_id=1)
        assert len(chunks) == 1

    def test_uzun_metin_birden_fazla_chunk(self):
        """Uzun metin birden fazla parcaya bolunmeli."""
        chunker = TextChunker(chunk_size=10, overlap=2)
        text = " ".join([f"kelime{i}" for i in range(50)])
        chunks = chunker.chunk(text, standard_id=1)
        assert len(chunks) > 1

    def test_chunk_id_formati(self):
        """Chunk ID'si dogru formatlanmali."""
        chunker = TextChunker(chunk_size=10, overlap=0)
        text = " ".join([f"kelime{i}" for i in range(30)])
        chunks = chunker.chunk(text, standard_id=5)
        assert chunks[0].chunk_id == "std_5_chunk_0000"
        assert chunks[1].chunk_id == "std_5_chunk_0001"

    def test_bos_metin_bos_liste(self):
        """Bos metin icin bos liste donmeli."""
        chunker = TextChunker()
        chunks = chunker.chunk("", standard_id=1)
        assert chunks == []

    def test_overlap_cakisma_saglar(self):
        """Overlap ile ardisik chunklar ortak kelime icermeli."""
        chunker = TextChunker(chunk_size=5, overlap=2)
        words = [f"k{i}" for i in range(15)]
        text = " ".join(words)
        chunks = chunker.chunk(text, standard_id=1)

        # Ilk chunkin son kelimeleri ikinci chunkin basinda olmali
        first_words = chunks[0].text.split()
        second_words = chunks[1].text.split()
        overlap_words = first_words[-2:]
        assert overlap_words[0] in second_words