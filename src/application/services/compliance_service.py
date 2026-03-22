"""
ComplianceService
Kullanicinin yukledigи teknik raporu standartlarla karsilastirir.
RAG kullanarak ilgili maddeleri bulur, OpenAI ile analiz eder.
"""
import json
import time
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.domain.entities.analysis_log import AnalysisLog, ComplianceVerdict
from src.domain.entities.user_report import ReportStatus, ReportType, UserReport
from src.infrastructure.repositories.repositories import (
    AnalysisRepository,
    ReportRepository,
)
from src.rag.pdf_extractor import PDFExtractor
from src.rag.vector_store import VectorStore


class ComplianceService:
    """
    Teknik rapor yukleme ve uyumluluk analizi islemlerini yonetir.

    Kullanim:
        service = ComplianceService(db)
        report = service.upload_report(...)
        result = service.analyze(report_id=1, query="vibrasyon testi")
    """

    def __init__(self, db: Session, openai_api_key: Optional[str] = None):
        self._report_repo = ReportRepository(db)
        self._analysis_repo = AnalysisRepository(db)
        self._extractor = PDFExtractor()
        self._vector_store = VectorStore()
        self._openai_key = openai_api_key

    def upload_report(
        self,
        title: str,
        file_path: str,
        original_filename: str,
        report_type: str,
        file_size_bytes: int,
    ) -> UserReport:
        """Kullanicinin raporunu kaydeder ve metnini cikarir."""

        report = UserReport(
            title=title,
            file_path=file_path,
            original_filename=original_filename,
            report_type=ReportType(report_type),
            file_size_bytes=file_size_bytes,
        )
        saved = self._report_repo.save(report)

        # PDF'ten metni cikar
        try:
            self._report_repo.update_status(saved.id, ReportStatus.PROCESSING)
            doc = self._extractor.extract(file_path)
            self._report_repo.update_status(
                saved.id,
                ReportStatus.COMPLETED,
                extracted_text=doc.full_text,
            )
            logger.info(f"Rapor yuklendi ve islendi: '{title}' (id={saved.id})")
        except Exception as e:
            self._report_repo.update_status(saved.id, ReportStatus.FAILED)
            logger.error(f"Rapor islenirken hata: {e}")
            raise

        return self._report_repo.get_by_id(saved.id)

    def analyze(
        self,
        report_id: int,
        query: str,
        standard_id: Optional[int] = None,
        top_k: int = 5,
    ) -> dict:
        """
        Kullanicinin sorusunu RAG ile analiz eder.

        1. Raporu veritabanindan al
        2. ChromaDB'den ilgili standart maddelerini bul
        3. OpenAI ile uyumluluk analizi yap
        4. Sonucu AnalysisLog olarak kaydet
        """
        start_time = time.time()

        # Raporu getir
        report = self._report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapor bulunamadi: id={report_id}")
        if not report.extracted_text:
            raise ValueError("Rapor metni henuz cikarilmamis.")

        # RAG: Ilgili standart maddelerini bul
        search_results = self._vector_store.search(
            query=query,
            top_k=top_k,
            standard_id=standard_id,
        )

        if not search_results:
            return {
                "status": "no_results",
                "message": "Ilgili standart maddesi bulunamadi. Once standart PDF'ini yukleyin.",
                "query": query,
            }

        # Context olustur
        context = "\n\n---\n\n".join([
            f"[Parca {i+1} | Sayfa {r.page_number} | Benzerlik: {r.similarity_score:.2f}]\n{r.text}"
            for i, r in enumerate(search_results)
        ])

        # AI analizi yap
        verdict, reasoning, confidence = self._run_ai_analysis(
            report_text=report.extracted_text[:3000],
            context=context,
            query=query,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Sonucu kaydet
        log = AnalysisLog(
            report_id=report_id,
            requirement_id=1,  # Genel analiz icin
            verdict=verdict,
            ai_reasoning=reasoning,
            confidence_score=confidence,
            retrieved_chunks=json.dumps([r.chunk_id for r in search_results]),
            analysis_duration_ms=duration_ms,
        )
        saved_log = self._analysis_repo.save(log)

        return {
            "analysis_id": saved_log.id,
            "report_id": report_id,
            "query": query,
            "verdict": verdict.value,
            "verdict_label": saved_log.verdict_label,
            "confidence": confidence,
            "reasoning": reasoning,
            "retrieved_chunks": len(search_results),
            "duration_ms": duration_ms,
            "relevant_sections": [
                {
                    "chunk_id": r.chunk_id,
                    "page": r.page_number,
                    "similarity": r.similarity_score,
                    "text_preview": r.text[:200] + "...",
                }
                for r in search_results
            ],
        }

    def get_compliance_summary(self, report_id: int) -> dict:
        """Bir raporun genel uyumluluk ozetini doner."""
        report = self._report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapor bulunamadi: id={report_id}")
        summary = self._analysis_repo.get_compliance_summary(report_id)
        summary["report_title"] = report.title
        summary["report_status"] = report.status.value
        return summary

    def list_reports(self, status: Optional[str] = None) -> List[UserReport]:
        """Tum raporlari listeler."""
        rep_status = ReportStatus(status) if status else None
        return self._report_repo.get_all(status=rep_status)

    def _run_ai_analysis(
        self,
        report_text: str,
        context: str,
        query: str,
    ):
        """
        OpenAI API ile uyumluluk analizi yapar.
        API key yoksa demo mod calisir.
        """
        if not self._openai_key:
            logger.warning("OpenAI API key yok, demo mod calisiyor.")
            return self._demo_analysis(query)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self._openai_key)

            prompt = f"""Sen bir havacilik ve savunma standartlari uzmanisın.
Asagida bir teknik rapordan alinti ve ilgili standart maddeleri verilmistir.

KULLANICI SORUSU: {query}

TEKNIK RAPOR (ilk 3000 karakter):
{report_text}

ILGILI STANDART MADDELERI (RAG ile bulundu):
{context}

Gorеvin:
1. Teknik raporun bu standart maddelerine uyumlu olup olmadigini analiz et.
2. Verdict olarak sadece su degerlerden birini sec: COMPLIANT, PARTIAL, NON_COMPLIANT, INSUFFICIENT
3. Turkce aciklama yaz.
4. 0.0-1.0 arasi guven skoru ver.

Yanıtını SADECE su JSON formatinda ver:
{{
  "verdict": "COMPLIANT",
  "reasoning": "Aciklama buraya...",
  "confidence": 0.85
}}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)

            verdict_map = {
                "COMPLIANT": ComplianceVerdict.COMPLIANT,
                "PARTIAL": ComplianceVerdict.PARTIALLY_COMPLIANT,
                "NON_COMPLIANT": ComplianceVerdict.NON_COMPLIANT,
                "INSUFFICIENT": ComplianceVerdict.INSUFFICIENT_DATA,
            }
            verdict = verdict_map.get(data["verdict"], ComplianceVerdict.INSUFFICIENT_DATA)
            return verdict, data["reasoning"], float(data["confidence"])

        except Exception as e:
            logger.error(f"OpenAI API hatasi: {e}")
            return self._demo_analysis(query)

    @staticmethod
    def _demo_analysis(query: str):
        """OpenAI key olmadan calisir, test icin kullanilir."""
        reasoning = (
            f"[DEMO MOD] '{query}' sorusu icin RAG basariyla calistı. "
            "Gercek analiz icin OpenAI API key gereklidir. "
            "Ilgili standart maddeleri basariyla bulundu ve context olusturuldu."
        )
        return ComplianceVerdict.INSUFFICIENT_DATA, reasoning, 0.5