"""
ComplianceService
Kullanicinin yukledigи teknik raporu standartlarla karsilastirir.
Google Gemini API kullanarak uyumluluk analizi yapar.
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

    def __init__(self, db: Session, openai_api_key: Optional[str] = None):
        self._report_repo = ReportRepository(db)
        self._analysis_repo = AnalysisRepository(db)
        self._extractor = PDFExtractor()
        self._vector_store = VectorStore()

        # .env dosyasindan Gemini key'i oku
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self._api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

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

        try:
            self._report_repo.update_status(saved.id, ReportStatus.PROCESSING)
            doc = self._extractor.extract(file_path)
            self._report_repo.update_status(
                saved.id,
                ReportStatus.COMPLETED,
                extracted_text=doc.full_text,
            )
            logger.info(f"Rapor yuklendi: '{title}' (id={saved.id})")
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
        """RAG ile ilgili maddeleri bulur, Gemini ile analiz yapar."""
        start_time = time.time()

        report = self._report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapor bulunamadi: id={report_id}")
        if not report.extracted_text:
            raise ValueError("Rapor metni henuz cikarilmamis.")

        # RAG: ilgili standart maddelerini bul
        search_results = self._vector_store.search(
            query=query,
            top_k=top_k,
            standard_id=standard_id,
        )

        if not search_results:
            return {
                "status": "no_results",
                "message": "Ilgili standart maddesi bulunamadi.",
                "query": query,
            }

        # Context olustur
        context = "\n\n---\n\n".join([
            f"[Parca {i+1} | Sayfa {r.page_number} | Benzerlik: {r.similarity_score:.2f}]\n{r.text}"
            for i, r in enumerate(search_results)
        ])

        # Gemini ile analiz
        verdict, reasoning, confidence = self._run_ai_analysis(
            report_text=report.extracted_text[:3000],
            context=context,
            query=query,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Sonucu kaydet
        from src.infrastructure.models.orm_models import AnalysisLogModel
        from src.infrastructure.database.connection import SessionLocal
        import json

        try:
            db = SessionLocal()
            log_model = AnalysisLogModel(
                report_id=report_id,
                requirement_id=None,  # NULL olarak kaydet
                verdict=verdict.value,
                ai_reasoning=reasoning,
                confidence_score=confidence,
                retrieved_chunks=json.dumps([r.chunk_id for r in search_results]),
                llm_model_used="gemini-2.5-flash",
                analysis_duration_ms=duration_ms,
            )
            db.add(log_model)
            db.commit()
            db.refresh(log_model)
            log_id = log_model.id
            db.close()
        except Exception as e:
            logger.warning(f"Log kaydedilemedi (analiz devam ediyor): {e}")
            log_id = None

        from src.domain.entities.analysis_log import AnalysisLog as AnalysisLogEntity
        temp_log = AnalysisLogEntity(
            report_id = report_id,
            requirement_id=0,
            verdict=verdict,
            ai_reasoning=reasoning,
            confidence_score=confidence,
        )
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
        report = self._report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapor bulunamadi: id={report_id}")
        summary = self._analysis_repo.get_compliance_summary(report_id)
        summary["report_title"] = report.title
        summary["report_status"] = report.status.value
        return summary

    def list_reports(self, status: Optional[str] = None) -> List[UserReport]:
        rep_status = ReportStatus(status) if status else None
        return self._report_repo.get_all(status=rep_status)

    def _run_ai_analysis(self, report_text: str, context: str, query: str):
        """
        Google Gemini API ile uyumluluk analizi yapar.
        Key yoksa demo mod calisir.
        """
        if not self._api_key:
            logger.warning("API key bulunamadi, demo mod calisiyor.")
            return self._demo_analysis(query)

        try:
            import google.genai as genai

            client = genai.Client(api_key=self._api_key)

            prompt = f"""Sen bir havacilik ve savunma standartlari uzmanisın.
Asagida bir teknik rapordan alinti ve ilgili standart maddeleri verilmistir.

KULLANICI SORUSU:
{query}

TEKNIK RAPOR (ilk 3000 karakter):
{report_text}

ILGILI STANDART MADDELERI:
{context}

Gorev:
1. Teknik raporun bu standart maddelerine uyumlu olup olmadigini analiz et.
2. Asagidaki degerlerden birini sec:
   - COMPLIANT - tam uyumlu
   - PARTIAL - kismi uyumlu
   - NON_COMPLIANT - uyumsuz
   - INSUFFICIENT - yetersiz veri
3. Turkce detayli aciklama yaz.
4. 0.0 ile 1.0 arasinda guven skoru ver.

SADECE asagidaki JSON formatinda yanit ver:
{{
  "verdict": "COMPLIANT",
  "reasoning": "Aciklama buraya...",
  "confidence": 0.85
}}"""

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            raw = response.text.strip()

            # Gemini bazen ```json ``` ile sarar, temizle
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        raw = part
                        break

            data = json.loads(raw.strip())

            verdict_map = {
                "COMPLIANT": ComplianceVerdict.COMPLIANT,
                "PARTIAL": ComplianceVerdict.PARTIALLY_COMPLIANT,
                "NON_COMPLIANT": ComplianceVerdict.NON_COMPLIANT,
                "INSUFFICIENT": ComplianceVerdict.INSUFFICIENT_DATA,
            }

            verdict = verdict_map.get(
                data.get("verdict", "INSUFFICIENT"),
                ComplianceVerdict.INSUFFICIENT_DATA,
            )
            reasoning = data.get("reasoning", "Aciklama alinamadi.")
            confidence = float(data.get("confidence", 0.5))

            logger.info(
                f"Gemini analizi tamamlandi: "
                f"verdict={verdict.value}, confidence={confidence:.2f}"
            )
            return verdict, reasoning, confidence

        except Exception as e:
            logger.error(f"Gemini API hatasi: {e}")
            return self._demo_analysis(query)

    @staticmethod
    def _demo_analysis(query: str):
        """API key olmadan calisir, test icin kullanilir."""
        reasoning = (
            f"[DEMO MOD] '{query}' sorusu icin RAG basariyla calistı. "
            "Gercek analiz icin .env dosyasina Gemini API key ekleyin."
        )
        return ComplianceVerdict.INSUFFICIENT_DATA, reasoning, 0.5