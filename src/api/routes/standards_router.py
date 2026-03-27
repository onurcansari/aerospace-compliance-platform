"""
Standards API Route'lari
/api/standards altindaki tum endpoint'ler buradadir.
"""
import os
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.application.services.standards_service import StandardsService
from src.infrastructure.database.connection import get_db

router = APIRouter(prefix="/api/standards", tags=["Standards"])


# ── Request / Response Modelleri ─────────────────────────────────────────────

class CreateStandardRequest(BaseModel):
    code: str
    title: str
    standard_type: str
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


class QueryRequest(BaseModel):
    question: Optional[str] = None
    query: Optional[str] = None
    standard_id: Optional[int] = None

    def get_question(self) -> str:
        return self.question or self.query or ""


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


@router.post("/query")
def query_standards(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """Standartlara direkt soru sor, Gemini ile cevap uret."""
    import os, json
    from dotenv import load_dotenv
    from src.rag.vector_store import VectorStore

    soru = request.get_question()
    if not soru:
        raise HTTPException(status_code=400, detail="Soru bos olamaz.")

    # 1. RAG ile ilgili parcalari bul
    store = VectorStore()
    results = store.search(
        query=soru,
        top_k=5,
        standard_id=request.standard_id,
    )

    if not results:
        return {
            "question": soru,
            "status": "no_results",
            "answer": None,
            "sources": [],
        }

    # 2. Context olustur
    context = "\n\n---\n\n".join([
        f"[Sayfa {r.page_number} | Benzerlik: {r.similarity_score:.0%}]\n{r.text}"
        for r in results
    ])

    # 3. Gemini ile dogal dil cevabi uret
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    answer = None

    if api_key:
        try:
            import google.genai as genai
            client = genai.Client(api_key=api_key)

            prompt = f"""Sen bir havacilik ve savunma standartlari uzmanisın.
Asagida bir kullanicinin sorusu ve ilgili standart belgelerinden alinmis parcalar var.

KULLANICI SORUSU:
{soru}

STANDART BELGELERİNDEN İLGİLİ BOLUMLER:
{context}

Gorеvin:
- Soruyu standart belgelerine dayanarak Turkce olarak cevapla.
- Dogal, akici ve anlasilir bir dil kullan — bir uzman gibi konuş.
- Hangi bolumden, hangi sayfadan aldigini referans olarak belirt.
- Eger belgede yeterli bilgi yoksa bunu ac ve net belirt.
- Madde madde veya paragraf seklinde yaz, ham metin kopyalama.
"""

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            answer = response.text.strip()

        except Exception as e:
            logger.error(f"Gemini hatasi: {e}")
            answer = None

    # Gemini yoksa veya hata varsa ham parcalari goster
    if not answer:
        answer = context

    return {
        "question": soru,
        "answer": answer,
        "sources": [
            {
                "page": r.page_number,
                "similarity": f"%{int(r.similarity_score * 100)}",
                "preview": r.text[:300] + "...",
            }
            for r in results
        ],
    }


@router.post("/bulk-index")
async def bulk_index_pdfs(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Birden fazla PDF'i tek seferde yukler ve indeksler."""
    os.makedirs("uploads/standards", exist_ok=True)
    results = []
    service = StandardsService(db)

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({
                "file": file.filename,
                "status": "skipped",
                "reason": "PDF degil",
            })
            continue

        raw_name = file.filename.replace(".pdf", "").replace(".PDF", "")
        code = raw_name.upper().strip()

        try:
            existing = service._repo.get_by_code(code)
            if existing:
                std = existing
            else:
                std = service.create_standard(
                    code=code,
                    title=raw_name,
                    standard_type="MIL" if "MIL" in code else "CIVIL",
                    version="v1",
                    issuing_body="Unknown",
                    publication_year=2020,
                )

            pdf_path = f"uploads/standards/{std.id}_{file.filename}"
            with open(pdf_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            result = service.index_pdf(
                standard_id=std.id,
                pdf_path=pdf_path,
            )

            results.append({
                "file": file.filename,
                "status": "success",
                "standard_id": std.id,
                "code": code,
                "total_pages": result["total_pages"],
                "total_chunks": result["total_chunks"],
            })

        except Exception as e:
            results.append({
                "file": file.filename,
                "status": "error",
                "reason": str(e),
            })

    success = sum(1 for r in results if r["status"] == "success")
    return {
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "results": results,
    }


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


@router.post("/{standard_id}/index-pdf")
async def index_standard_pdf(
    standard_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Standart PDF'ini yukler ve ChromaDB'ye indeksler."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF yuklenebilir.")

    os.makedirs("uploads/standards", exist_ok=True)
    pdf_path = f"uploads/standards/{standard_id}_{file.filename}"

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    service = StandardsService(db)
    try:
        result = service.index_pdf(
            standard_id=standard_id,
            pdf_path=pdf_path,
        )
        return {
            "message": "PDF basariyla indekslendi!",
            "standard_id": standard_id,
            "total_pages": result["total_pages"],
            "total_chunks": result["total_chunks"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))