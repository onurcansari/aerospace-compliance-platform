"""
Reports API Route'lari
"""
import os
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.application.services.compliance_service import ComplianceService
from src.infrastructure.database.connection import get_db

router = APIRouter(prefix="/api/reports", tags=["Reports"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ReportResponse(BaseModel):
    id: int
    title: str
    original_filename: str
    report_type: str
    file_size_kb: float
    status: str


class AnalyzeRequest(BaseModel):
    query: str
    standard_id: Optional[int] = None
    top_k: int = 5


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = ComplianceService(db)
    reports = service.list_reports(status=status)
    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            original_filename=r.original_filename,
            report_type=r.report_type.value,
            file_size_kb=r.file_size_kb,
            status=r.status.value,
        )
        for r in reports
    ]


@router.post("/upload", status_code=201)
async def upload_report(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    report_type: str = Form("DESIGN"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyasi yuklenebilir.")

    report_title = title or file.filename.replace(".pdf", "").replace(".PDF", "")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    service = ComplianceService(db)
    try:
        report = service.upload_report(
            title=report_title,
            file_path=file_path,
            original_filename=file.filename,
            report_type=report_type,
            file_size_bytes=file_size,
        )
        return {
            "message": "Rapor basariyla yuklendi.",
            "report_id": report.id,
            "title": report.title,
            "status": report.status.value,
        }
    except Exception as e:
        logger.error(f"Rapor yukleme hatasi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{report_id}/analyze")
def analyze_report(
    report_id: int,
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    service = ComplianceService(db)
    try:
        result = service.analyze(
            report_id=report_id,
            query=request.query,
            standard_id=request.standard_id,
            top_k=request.top_k,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Analiz hatasi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/summary")
def get_compliance_summary(
    report_id: int,
    db: Session = Depends(get_db),
):
    service = ComplianceService(db)
    try:
        return service.get_compliance_summary(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))