from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.domain.entities.analysis_log import AnalysisLog, ComplianceVerdict
from src.domain.entities.requirement import Requirement, RequirementCategory
from src.domain.entities.standard import Standard, StandardStatus, StandardType
from src.domain.entities.user_report import ReportStatus, ReportType, UserReport
from src.domain.interfaces.analysis_repository import IAnalysisRepository
from src.domain.interfaces.report_repository import IReportRepository
from src.domain.interfaces.requirement_repository import IRequirementRepository
from src.domain.interfaces.standard_repository import IStandardRepository
from src.infrastructure.models.orm_models import (
    AnalysisLogModel,
    RequirementModel,
    StandardModel,
    UserReportModel,
)


# ──────────────────────────────────────────────
# StandardRepository
# ──────────────────────────────────────────────

class StandardRepository(IStandardRepository):

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, standard_id: int) -> Optional[Standard]:
        model = self._db.get(StandardModel, standard_id)
        return self._to_entity(model) if model else None

    def get_by_code(self, code: str) -> Optional[Standard]:
        model = (
            self._db.query(StandardModel)
            .filter(StandardModel.code == code.upper())
            .first()
        )
        return self._to_entity(model) if model else None

    def get_all(self, status: Optional[StandardStatus] = None) -> List[Standard]:
        query = self._db.query(StandardModel)
        if status:
            query = query.filter(StandardModel.status == status.value)
        return [self._to_entity(m) for m in query.all()]

    def save(self, standard: Standard) -> Standard:
        if standard.id:
            model = self._db.get(StandardModel, standard.id)
            model.code = standard.code
            model.title = standard.title
            model.standard_type = standard.standard_type.value
            model.version = standard.version
            model.issuing_body = standard.issuing_body
            model.publication_year = standard.publication_year
            model.description = standard.description
            model.pdf_path = standard.pdf_path
            model.is_indexed = standard.is_indexed
            model.status = standard.status.value
            logger.info(f"Standard guncellendi: {standard.code}")
        else:
            model = StandardModel(
                code=standard.code,
                title=standard.title,
                standard_type=standard.standard_type.value,
                version=standard.version,
                issuing_body=standard.issuing_body,
                publication_year=standard.publication_year,
                description=standard.description,
                pdf_path=standard.pdf_path,
                is_indexed=standard.is_indexed,
                status=standard.status.value,
            )
            self._db.add(model)
            self._db.flush()
            logger.info(f"Yeni standard eklendi: {standard.code}")
        return self._to_entity(model)

    def delete(self, standard_id: int) -> bool:
        model = self._db.get(StandardModel, standard_id)
        if not model:
            return False
        self._db.delete(model)
        logger.info(f"Standard silindi: id={standard_id}")
        return True

    def mark_as_indexed(self, standard_id: int) -> None:
        model = self._db.get(StandardModel, standard_id)
        if not model:
            raise ValueError(f"Standard bulunamadi: id={standard_id}")
        model.is_indexed = True
        logger.info(f"Standard indexed olarak isaretlendi: {model.code}")

    def search_by_title(self, query: str) -> List[Standard]:
        term = f"%{query}%"
        models = (
            self._db.query(StandardModel)
            .filter(
                StandardModel.title.ilike(term) | StandardModel.code.ilike(term)
            )
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: StandardModel) -> Standard:
        return Standard(
            id=model.id,
            code=model.code,
            title=model.title,
            standard_type=StandardType(model.standard_type),
            version=model.version,
            issuing_body=model.issuing_body,
            publication_year=model.publication_year,
            description=model.description,
            pdf_path=model.pdf_path,
            is_indexed=model.is_indexed,
            status=StandardStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


# ──────────────────────────────────────────────
# RequirementRepository
# ──────────────────────────────────────────────

class RequirementRepository(IRequirementRepository):

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, requirement_id: int) -> Optional[Requirement]:
        model = self._db.get(RequirementModel, requirement_id)
        return self._to_entity(model) if model else None

    def get_by_standard(self, standard_id: int, category: Optional[RequirementCategory] = None) -> List[Requirement]:
        query = self._db.query(RequirementModel).filter(
            RequirementModel.standard_id == standard_id
        )
        if category:
            query = query.filter(RequirementModel.category == category.value)
        return [self._to_entity(m) for m in query.all()]

    def get_by_chunk_id(self, chunk_id: str) -> Optional[Requirement]:
        model = (
            self._db.query(RequirementModel)
            .filter(RequirementModel.chunk_id == chunk_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def save(self, requirement: Requirement) -> Requirement:
        if requirement.id:
            model = self._db.get(RequirementModel, requirement.id)
            model.section_id = requirement.section_id
            model.title = requirement.title
            model.requirement_text = requirement.requirement_text
            model.category = requirement.category.value
            model.page_number = requirement.page_number
            model.chunk_id = requirement.chunk_id
        else:
            model = RequirementModel(
                standard_id=requirement.standard_id,
                section_id=requirement.section_id,
                title=requirement.title,
                requirement_text=requirement.requirement_text,
                category=requirement.category.value,
                page_number=requirement.page_number,
                chunk_id=requirement.chunk_id,
            )
            self._db.add(model)
            self._db.flush()
        return self._to_entity(model)

    def save_batch(self, requirements: List[Requirement]) -> List[Requirement]:
        models = [
            RequirementModel(
                standard_id=r.standard_id,
                section_id=r.section_id,
                title=r.title,
                requirement_text=r.requirement_text,
                category=r.category.value,
                page_number=r.page_number,
                chunk_id=r.chunk_id,
            )
            for r in requirements
        ]
        self._db.add_all(models)
        self._db.flush()
        logger.info(f"{len(models)} gereksinim toplu kaydedildi.")
        return [self._to_entity(m) for m in models]

    def delete_by_standard(self, standard_id: int) -> int:
        count = (
            self._db.query(RequirementModel)
            .filter(RequirementModel.standard_id == standard_id)
            .delete()
        )
        return count

    @staticmethod
    def _to_entity(model: RequirementModel) -> Requirement:
        return Requirement(
            id=model.id,
            standard_id=model.standard_id,
            section_id=model.section_id,
            title=model.title,
            requirement_text=model.requirement_text,
            category=RequirementCategory(model.category),
            page_number=model.page_number,
            chunk_id=model.chunk_id,
            created_at=model.created_at,
        )


# ──────────────────────────────────────────────
# ReportRepository
# ──────────────────────────────────────────────

class ReportRepository(IReportRepository):

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, report_id: int) -> Optional[UserReport]:
        model = self._db.get(UserReportModel, report_id)
        return self._to_entity(model) if model else None

    def get_all(self, status: Optional[ReportStatus] = None) -> List[UserReport]:
        query = self._db.query(UserReportModel)
        if status:
            query = query.filter(UserReportModel.status == status.value)
        return [self._to_entity(m) for m in query.all()]

    def save(self, report: UserReport) -> UserReport:
        if report.id:
            model = self._db.get(UserReportModel, report.id)
            model.title = report.title
            model.status = report.status.value
            model.extracted_text = report.extracted_text
            model.processed_at = report.processed_at
        else:
            model = UserReportModel(
                title=report.title,
                file_path=report.file_path,
                original_filename=report.original_filename,
                report_type=report.report_type.value,
                file_size_bytes=report.file_size_bytes,
                status=report.status.value,
            )
            self._db.add(model)
            self._db.flush()
            logger.info(f"Yeni rapor kaydedildi: {report.title}")
        return self._to_entity(model)

    def update_status(self, report_id: int, status: ReportStatus, extracted_text: Optional[str] = None) -> None:
        model = self._db.get(UserReportModel, report_id)
        if not model:
            raise ValueError(f"Rapor bulunamadi: id={report_id}")
        model.status = status.value
        if extracted_text is not None:
            model.extracted_text = extracted_text
        if status == ReportStatus.COMPLETED:
            model.processed_at = datetime.utcnow()
        logger.info(f"Rapor durumu guncellendi: id={report_id}, status={status.value}")

    def delete(self, report_id: int) -> bool:
        model = self._db.get(UserReportModel, report_id)
        if not model:
            return False
        self._db.delete(model)
        return True

    @staticmethod
    def _to_entity(model: UserReportModel) -> UserReport:
        return UserReport(
            id=model.id,
            title=model.title,
            file_path=model.file_path,
            original_filename=model.original_filename,
            report_type=ReportType(model.report_type),
            file_size_bytes=model.file_size_bytes,
            status=ReportStatus(model.status),
            extracted_text=model.extracted_text,
            uploaded_at=model.uploaded_at,
            processed_at=model.processed_at,
        )


# ──────────────────────────────────────────────
# AnalysisRepository
# ──────────────────────────────────────────────

class AnalysisRepository(IAnalysisRepository):

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, log_id: int) -> Optional[AnalysisLog]:
        model = self._db.get(AnalysisLogModel, log_id)
        return self._to_entity(model) if model else None

    def get_by_report(self, report_id: int) -> List[AnalysisLog]:
        models = (
            self._db.query(AnalysisLogModel)
            .filter(AnalysisLogModel.report_id == report_id)
            .order_by(AnalysisLogModel.analyzed_at.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_by_requirement(self, requirement_id: int) -> List[AnalysisLog]:
        models = (
            self._db.query(AnalysisLogModel)
            .filter(AnalysisLogModel.requirement_id == requirement_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def save(self, log: AnalysisLog) -> AnalysisLog:
        model = AnalysisLogModel(
            report_id=log.report_id,
            requirement_id=log.requirement_id,
            verdict=log.verdict.value,
            ai_reasoning=log.ai_reasoning,
            confidence_score=log.confidence_score,
            retrieved_chunks=log.retrieved_chunks,
            llm_model_used=log.llm_model_used,
            analysis_duration_ms=log.analysis_duration_ms,
        )
        self._db.add(model)
        self._db.flush()
        logger.info(
            f"Analiz logu kaydedildi: report={log.report_id}, "
            f"verdict={log.verdict.value}, confidence={log.confidence_score:.2f}"
        )
        return self._to_entity(model)

    def get_compliance_summary(self, report_id: int) -> Dict:
        logs = self.get_by_report(report_id)
        if not logs:
            return {"total": 0, "compliant": 0, "non_compliant": 0,
                    "partial": 0, "compliance_rate": 0.0}
        total = len(logs)
        compliant = sum(1 for l in logs if l.verdict == ComplianceVerdict.COMPLIANT)
        non_compliant = sum(1 for l in logs if l.verdict == ComplianceVerdict.NON_COMPLIANT)
        partial = sum(1 for l in logs if l.verdict == ComplianceVerdict.PARTIALLY_COMPLIANT)
        return {
            "total": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "partial": partial,
            "insufficient": total - compliant - non_compliant - partial,
            "compliance_rate": round(compliant / total, 3),
        }

    @staticmethod
    def _to_entity(model: AnalysisLogModel) -> AnalysisLog:
        return AnalysisLog(
            id=model.id,
            report_id=model.report_id,
            requirement_id=model.requirement_id,
            verdict=ComplianceVerdict(model.verdict),
            ai_reasoning=model.ai_reasoning,
            confidence_score=model.confidence_score,
            retrieved_chunks=model.retrieved_chunks,
            llm_model_used=model.llm_model_used,
            analysis_duration_ms=model.analysis_duration_ms,
            analyzed_at=model.analyzed_at,
        )