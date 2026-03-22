"""
Repository Testleri
Veritabani islemlerinin dogru calistigini test eder.
Gercek bir SQLite veritabani kullanir ama test bittikten sonra siler.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.models.orm_models import Base
from src.infrastructure.repositories.repositories import (
    StandardRepository,
    RequirementRepository,
    ReportRepository,
)
from src.domain.entities.standard import Standard, StandardType
from src.domain.entities.requirement import Requirement
from src.domain.entities.user_report import UserReport, ReportType, ReportStatus


# ── Test veritabani kurulumu ───────────────────────────────────────────────────

@pytest.fixture
def db():
    """
    Her test icin temiz bir veritabani olusturur.
    Test bittikten sonra otomatik siler.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


# ── StandardRepository Testleri ───────────────────────────────────────────────

class TestStandardRepository:

    def test_standart_kaydet_ve_getir(self, db):
        """Standart kaydedilip ID ile getirilebilmeli."""
        repo = StandardRepository(db)
        standard = Standard(
            code="MIL-STD-810H",
            title="Environmental Engineering",
            standard_type=StandardType.MILITARY,
            version="H",
            issuing_body="DoD",
            publication_year=2019,
        )
        saved = repo.save(standard)
        db.commit()

        assert saved.id is not None
        found = repo.get_by_id(saved.id)
        assert found is not None
        assert found.code == "MIL-STD-810H"

    def test_kod_ile_getir(self, db):
        """Standart kodu ile getirilebilmeli."""
        repo = StandardRepository(db)
        standard = Standard(
            code="DO-178C",
            title="Software Considerations",
            standard_type=StandardType.CIVIL,
            version="C",
            issuing_body="RTCA",
            publication_year=2011,
        )
        repo.save(standard)
        db.commit()

        found = repo.get_by_code("DO-178C")
        assert found is not None
        assert found.title == "Software Considerations"

    def test_olmayan_standart_none_doner(self, db):
        """Olmayan ID icin None donmeli."""
        repo = StandardRepository(db)
        result = repo.get_by_id(9999)
        assert result is None

    def test_standart_sil(self, db):
        """Standart silinebilmeli."""
        repo = StandardRepository(db)
        standard = Standard(
            code="TEST-001",
            title="Test Standard",
            standard_type=StandardType.MILITARY,
            version="A",
            issuing_body="DoD",
            publication_year=2020,
        )
        saved = repo.save(standard)
        db.commit()

        result = repo.delete(saved.id)
        db.commit()

        assert result is True
        assert repo.get_by_id(saved.id) is None

    def test_basliga_gore_ara(self, db):
        """Basliga gore arama yapilabilmeli."""
        repo = StandardRepository(db)
        repo.save(Standard(
            code="MIL-STD-461G",
            title="Electromagnetic Interference",
            standard_type=StandardType.MILITARY,
            version="G",
            issuing_body="DoD",
            publication_year=2015,
        ))
        db.commit()

        results = repo.search_by_title("Electromagnetic")
        assert len(results) >= 1
        assert any("461G" in s.code for s in results)


# ── ReportRepository Testleri ─────────────────────────────────────────────────

class TestReportRepository:

    def test_rapor_kaydet_ve_getir(self, db):
        """Rapor kaydedilip getirilebilmeli."""
        repo = ReportRepository(db)
        report = UserReport(
            title="Test Raporu",
            file_path="/uploads/test.pdf",
            report_type=ReportType.DESIGN,
            original_filename="test.pdf",
            file_size_bytes=1024,
        )
        saved = repo.save(report)
        db.commit()

        assert saved.id is not None
        found = repo.get_by_id(saved.id)
        assert found.title == "Test Raporu"

    def test_durum_guncelle(self, db):
        """Rapor durumu guncellenebilmeli."""
        repo = ReportRepository(db)
        report = UserReport(
            title="Durum Test Raporu",
            file_path="/uploads/test.pdf",
            report_type=ReportType.TEST,
        )
        saved = repo.save(report)
        db.commit()

        repo.update_status(
            saved.id,
            ReportStatus.COMPLETED,
            extracted_text="PDF icerik metni buraya gelir.",
        )
        db.commit()

        updated = repo.get_by_id(saved.id)
        assert updated.status == ReportStatus.COMPLETED
        assert updated.extracted_text == "PDF icerik metni buraya gelir."