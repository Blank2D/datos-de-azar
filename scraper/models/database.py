"""
SQLAlchemy 2.0 models — reflejan el schema Prisma de MySQL.

Mantener sincronizado con: prisma/schema.prisma
Los nombres de tabla y columna (snake_case) deben coincidir con los @@map de Prisma.
"""
from __future__ import annotations

import enum
import os
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


# ============================================================
# Enums — DEBEN coincidir exactamente con los del schema.prisma
# ============================================================
class Game(str, enum.Enum):
    kino = "kino"
    loto = "loto"


class KinoDay(str, enum.Enum):
    wednesday = "wednesday"
    friday = "friday"
    sunday = "sunday"


class LotoDay(str, enum.Enum):
    tuesday = "tuesday"
    thursday = "thursday"
    sunday = "sunday"


class ScraperStatus(str, enum.Enum):
    success = "success"
    error = "error"
    no_new_data = "no_new_data"


# ============================================================
# Base declarativa
# ============================================================
class Base(DeclarativeBase):
    pass


# ============================================================
# 🎰 Kino — 14 números del 1 al 25
# ============================================================
class KinoDraw(Base):
    __tablename__ = "kino_draws"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draw_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    draw_date: Mapped[date] = mapped_column(Date, nullable=False)
    draw_day: Mapped[KinoDay] = mapped_column(
        SAEnum(KinoDay, name="KinoDay", native_enum=True), nullable=False
    )
    numbers: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    adicional: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prize_jackpot: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    winners_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_kino_draws_draw_date", "draw_date"),)

    def __repr__(self) -> str:
        return f"<KinoDraw #{self.draw_number} {self.draw_date} {self.numbers}>"


# ============================================================
# 🍀 Loto — 6 números del 1 al 41
# ============================================================
class LotoDraw(Base):
    __tablename__ = "loto_draws"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draw_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    draw_date: Mapped[date] = mapped_column(Date, nullable=False)
    draw_day: Mapped[LotoDay] = mapped_column(
        SAEnum(LotoDay, name="LotoDay", native_enum=True), nullable=False
    )
    numbers: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    revancha: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    desquite: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    prize_jackpot: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    winners_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_loto_draws_draw_date", "draw_date"),)

    def __repr__(self) -> str:
        return f"<LotoDraw #{self.draw_number} {self.draw_date} {self.numbers}>"


# ============================================================
# 📊 Cache de estadísticas
# ============================================================
class StatisticsCache(Base):
    __tablename__ = "statistics_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game: Mapped[Game] = mapped_column(
        SAEnum(Game, name="Game", native_enum=True), nullable=False
    )
    stat_type: Mapped[str] = mapped_column(String(100), nullable=False)
    time_window: Mapped[str] = mapped_column(
        String(50), nullable=False, default="all", server_default="all"
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "game", "stat_type", "time_window", name="uq_stats_game_type_window"
        ),
    )

    def __repr__(self) -> str:
        return f"<StatisticsCache {self.game.value}/{self.stat_type}/{self.time_window}>"


# ============================================================
# 🪵 Log de ejecuciones del scraper
# ============================================================
class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game: Mapped[Game] = mapped_column(
        SAEnum(Game, name="Game", native_enum=True), nullable=False
    )
    status: Mapped[ScraperStatus] = mapped_column(
        SAEnum(ScraperStatus, name="ScraperStatus", native_enum=True), nullable=False
    )
    draws_found: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_scraper_logs_run_at", "run_at"),)

    def __repr__(self) -> str:
        return f"<ScraperLog {self.game.value} {self.status.value} found={self.draws_found}>"


# ============================================================
# Conexión y sesión
# ============================================================
def _build_database_url() -> str:
    """
    Construye la URL de conexión. Prefiere DATABASE_URL si existe;
    si no, la arma a partir de DB_HOST/DB_USER/DB_PASS/DB_NAME/DB_PORT.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # Prisma usa "mysql://...", SQLAlchemy necesita "mysql+pymysql://..."
        if url.startswith("mysql://") and "+" not in url.split("://")[0]:
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "dev")
    password = os.getenv("DB_PASS", "devpass")
    name = os.getenv("DB_NAME", "datos_azar")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


_engine = None
_SessionLocal = None


def get_engine():
    """Engine singleton (lazy)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            _build_database_url(),
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True,
        )
    return _engine


def get_session() -> Session:
    """Crea una nueva sesión SQLAlchemy. Usar con `with` para cierre automático."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal()


def create_all_tables() -> None:
    """
    Crea las tablas si no existen. ÚTIL solo para tests/desarrollo.
    En producción, las migraciones las maneja Prisma.
    """
    Base.metadata.create_all(get_engine())
