from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from loguru import logger
from src.infrastructure.models.orm_models import Base

DATABASE_URL = "sqlite:///./aerospace_compliance.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    logger.info("Veritabani tablolari olusturuluyor...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablolar hazir.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        logger.error(f"Veritabani hatasi, rollback: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as exc:
        logger.error(f"Context DB hatasi: {exc}")
        db.rollback()
        raise
    finally:
        db.close()