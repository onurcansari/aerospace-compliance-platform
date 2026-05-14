from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class StandardModel(Base):
    __tablename__ = "standards"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    code             = Column(String(50), unique=True, nullable=False, index=True)
    title            = Column(String(300), nullable=False)
    standard_type    = Column(String(10), nullable=False)
    version          = Column(String(50), nullable=False)
    issuing_body     = Column(String(200), nullable=False)
    publication_year = Column(Integer, nullable=False)
    description      = Column(Text, nullable=True)
    pdf_path         = Column(String(500), nullable=True)
    is_indexed       = Column(Boolean, default=False, nullable=False)
    status           = Column(String(20), default="ACTIVE", nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    requirements = relationship("RequirementModel", back_populates="standard", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Standard {self.code}>"


class RequirementModel(Base):
    __tablename__ = "requirements"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    standard_id      = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id       = Column(String(100), nullable=False)
    title            = Column(String(300), nullable=False)
    requirement_text = Column(Text, nullable=False)
    category         = Column(String(30), default="ENVIRONMENTAL", nullable=False)
    page_number      = Column(Integer, nullable=True)
    chunk_id         = Column(String(100), nullable=True, unique=True, index=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    standard      = relationship("StandardModel", back_populates="requirements")
    analysis_logs = relationship("AnalysisLogModel", back_populates="requirement")

    def __repr__(self):
        return f"<Requirement {self.section_id}>"


class UserReportModel(Base):
    __tablename__ = "user_reports"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    title             = Column(String(300), nullable=False)
    file_path         = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False, default="")
    report_type       = Column(String(20), nullable=False)
    file_size_bytes   = Column(Integer, default=0)
    status            = Column(String(20), default="PENDING", nullable=False, index=True)
    extracted_text    = Column(Text, nullable=True)
    uploaded_at       = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at      = Column(DateTime, nullable=True)

    analysis_logs = relationship("AnalysisLogModel", back_populates="report")

    def __repr__(self):
        return f"<UserReport {self.title}>"


class AnalysisLogModel(Base):
    __tablename__ = "analysis_logs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    report_id            = Column(Integer, ForeignKey("user_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id       = Column(Integer, ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    
    verdict              = Column(String(20), nullable=False)
    ai_reasoning         = Column(Text, nullable=False)
    confidence_score     = Column(Float, nullable=False)
    retrieved_chunks     = Column(Text, nullable=True)
    llm_model_used       = Column(String(50), default="gpt-4o", nullable=False)
    analysis_duration_ms = Column(Integer, default=0)
    analyzed_at          = Column(DateTime, default=datetime.utcnow, nullable=False)

    report      = relationship("UserReportModel", back_populates="analysis_logs")
    requirement = relationship("RequirementModel", back_populates="analysis_logs")

    def __repr__(self):
        return f"<AnalysisLog report={self.report_id} verdict={self.verdict}>"