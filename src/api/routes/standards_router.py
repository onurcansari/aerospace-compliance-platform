"""
Standards API Route'lari
/api/standards altindaki tum endpoint'ler buradadir.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.application.services.standards_service import StandardsService
from src.infrastructure.database.connection import get_db

router = APIRouter(prefix="/api/standards", tags=["Standards"])


# ── Request / Response Modelleri ──────────────────────────────────────────────

class CreateStandardRequest(BaseModel):
    code: str
    title: str
    standard_type: str   # MIL, CIVIL, INTL
    version: str
    issuing_body: str
    publication_year: int
    description: Optional[str] = None


class StandardResponse(BaseModel):
    id: int
    code: str
    title: str
    standard_type: str
    version: str
    issuing_body: str
    publication_year: int
    description: Optional[str]
    is_indexed: bool
    status: str


# ── Endpoint'ler ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[StandardResponse])
def list_standards(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Tum standartlari listeler."""
    service = StandardsService(db)
    standards = service.list_standards(status=status)
    return [
        StandardResponse(
            id=s.id,
            code=s.code,
            title=s.title,
            standard_type=s.standard_type.value,
            version=s.version,
            issuing_body=s.issuing_body,
            publication_year=s.publication_year,
            description=s.description,
            is_indexed=s.is_indexed,
            status=s.status.value,
        )
        for s in standards
    ]


@router.post("/", response_model=StandardResponse, status_code=201)
def create_standard(
    request: CreateStandardRequest,
    db: Session = Depends(get_db),
):
    """Yeni standart ekler."""
    service = StandardsService(db)
    try:
        standard = service.create_standard(
            code=request.code,
            title=request.title,
            standard_type=request.standard_type,
            version=request.version,
            issuing_body=request.issuing_body,
            publication_year=request.publication_year,
            description=request.description,
        )
        return StandardResponse(
            id=standard.id,
            code=standard.code,
            title=standard.title,
            standard_type=standard.standard_type.value,
            version=standard.version,
            issuing_body=standard.issuing_body,
            publication_year=standard.publication_year,
            description=standard.description,
            is_indexed=standard.is_indexed,
            status=standard.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{standard_id}", response_model=StandardResponse)
def get_standard(standard_id: int, db: Session = Depends(get_db)):
    """Tek bir standart getirir."""
    service = StandardsService(db)
    try:
        s = service.get_standard(standard_id)
        return StandardResponse(
            id=s.id,
            code=s.code,
            title=s.title,
            standard_type=s.standard_type.value,
            version=s.version,
            issuing_body=s.issuing_body,
            publication_year=s.publication_year,
            description=s.description,
            is_indexed=s.is_indexed,
            status=s.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{standard_id}", status_code=204)
def delete_standard(standard_id: int, db: Session = Depends(get_db)):
    """Standart siler."""
    service = StandardsService(db)
    deleted = service.delete_standard(standard_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Standart bulunamadi.")


@router.get("/search/{query}", response_model=list[StandardResponse])
def search_standards(query: str, db: Session = Depends(get_db)):
    """Basliga gore arama yapar."""
    service = StandardsService(db)
    standards = service.search_standards(query)
    return [
        StandardResponse(
            id=s.id,
            code=s.code,
            title=s.title,
            standard_type=s.standard_type.value,
            version=s.version,
            issuing_body=s.issuing_body,
            publication_year=s.publication_year,
            description=s.description,
            is_indexed=s.is_indexed,
            status=s.status.value,
        )
        for s in standards
    ]