"""
Domain Entity Testleri
Veri modellerinin dogru calistigini test eder.
"""
import pytest
from src.domain.entities.standard import Standard, StandardType, StandardStatus
from src.domain.entities.requirement import Requirement, RequirementCategory
from src.domain.entities.user_report import UserReport, ReportType
from src.domain.entities.analysis_log import AnalysisLog, ComplianceVerdict


# ── Standard Testleri ─────────────────────────────────────────────────────────

class TestStandard:

    def test_standard_olusturma_basarili(self):
        """Normal bir standart olusturulabilmeli."""
        s = Standard(
            code="MIL-STD-810H",
            title="Environmental Engineering",
            standard_type=StandardType.MILITARY,
            version="H",
            issuing_body="DoD",
            publication_year=2019,
        )
        assert s.code == "MIL-STD-810H"
        assert s.is_military is True
        assert s.status == StandardStatus.ACTIVE
        assert s.is_indexed is False

    def test_display_name_dogru(self):
        """Display name dogru formatlanmali."""
        s = Standard(
            code="DO-178C",
            title="Software Considerations",
            standard_type=StandardType.CIVIL,
            version="C",
            issuing_body="RTCA",
            publication_year=2011,
        )
        assert "DO-178C" in s.display_name
        assert "Software Considerations" in s.display_name

    def test_bos_kod_hata_verir(self):
        """Bos kod kabul edilmemeli."""
        with pytest.raises(ValueError):
            Standard(
                code="",
                title="Test",
                standard_type=StandardType.MILITARY,
                version="A",
                issuing_body="DoD",
                publication_year=2020,
            )

    def test_gecersiz_yil_hata_verir(self):
        """1900 oncesi veya 2100 sonrasi yil kabul edilmemeli."""
        with pytest.raises(ValueError):
            Standard(
                code="TEST-001",
                title="Test",
                standard_type=StandardType.MILITARY,
                version="A",
                issuing_body="DoD",
                publication_year=1800,
            )


# ── Requirement Testleri ──────────────────────────────────────────────────────

class TestRequirement:

    def test_requirement_olusturma_basarili(self):
        """Normal bir gereksinim olusturulabilmeli."""
        r = Requirement(
            standard_id=1,
            section_id="Method 514.8",
            title="Vibration Test",
            requirement_text="Equipment shall withstand vibration levels as specified.",
        )
        assert r.standard_id == 1
        assert r.section_id == "Method 514.8"
        assert r.category == RequirementCategory.ENVIRONMENTAL

    def test_full_reference_dogru(self):
        """Referans kodu dogru formatlanmali."""
        r = Requirement(
            standard_id=3,
            section_id="4.2.1",
            title="Test",
            requirement_text="Bu bir test gereksinimidir.",
        )
        assert r.full_reference == "REQ-3-4.2.1"

    def test_kisa_metin_hata_verir(self):
        """Cok kisa gereksinim metni kabul edilmemeli."""
        with pytest.raises(ValueError):
            Requirement(
                standard_id=1,
                section_id="4.1",
                title="Test",
                requirement_text="Kisa",
            )


# ── UserReport Testleri ───────────────────────────────────────────────────────

class TestUserReport:

    def test_rapor_olusturma_basarili(self):
        """Normal bir rapor olusturulabilmeli."""
        r = UserReport(
            title="Radar Tasarim Raporu v2.1",
            file_path="/uploads/radar.pdf",
            report_type=ReportType.DESIGN,
            file_size_bytes=2048000,
        )
        assert r.title == "Radar Tasarim Raporu v2.1"
        assert r.file_size_kb == 2000.0

    def test_bos_baslik_hata_verir(self):
        """Bos baslik kabul edilmemeli."""
        with pytest.raises(ValueError):
            UserReport(
                title="",
                file_path="/uploads/test.pdf",
                report_type=ReportType.TEST,
            )

    def test_analiz_hazir_degil(self):
        """Metni cikarilmamis rapor analize hazir olmamali."""
        r = UserReport(
            title="Test Raporu",
            file_path="/uploads/test.pdf",
            report_type=ReportType.TEST,
        )
        assert r.is_ready_for_analysis is False


# ── AnalysisLog Testleri ──────────────────────────────────────────────────────

class TestAnalysisLog:

    def test_log_olusturma_basarili(self):
        """Normal bir analiz logu olusturulabilmeli."""
        log = AnalysisLog(
            report_id=1,
            requirement_id=2,
            verdict=ComplianceVerdict.COMPLIANT,
            ai_reasoning="Rapor tum gereksinimleri karsilamaktadir.",
            confidence_score=0.92,
        )
        assert log.verdict == ComplianceVerdict.COMPLIANT
        assert log.is_high_confidence is True
        assert log.verdict_label == "Uyumlu"

    def test_gecersiz_confidence_hata_verir(self):
        """0-1 disinda confidence kabul edilmemeli."""
        with pytest.raises(ValueError):
            AnalysisLog(
                report_id=1,
                requirement_id=1,
                verdict=ComplianceVerdict.COMPLIANT,
                ai_reasoning="Bu bir test aciklamasidir.",
                confidence_score=1.5,
            )

    def test_dusuk_confidence(self):
        """0.85 altı confidence dusuk sayilmali."""
        log = AnalysisLog(
            report_id=1,
            requirement_id=1,
            verdict=ComplianceVerdict.PARTIALLY_COMPLIANT,
            ai_reasoning="Kismi uyumluluk tespit edildi.",
            confidence_score=0.70,
        )
        assert log.is_high_confidence is False