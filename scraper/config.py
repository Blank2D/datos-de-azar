"""
Configuración central del scraper.

Lee variables de entorno (con defaults sensatos para desarrollo local).
Centralizar aquí para que main.py y los scrapers no las consulten ad-hoc.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # ---- Base de datos ----
    database_url: str
    # ---- HTTP / scraping ----
    request_delay_seconds: float
    request_timeout_seconds: int
    request_max_retries: int
    # ---- Comportamiento ----
    log_level: str
    dry_run: bool


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Reconstruir desde las partes individuales si DATABASE_URL no está set
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "dev")
        password = os.getenv("DB_PASS", "devpass")
        name = os.getenv("DB_NAME", "datos_azar")
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"

    return Settings(
        database_url=db_url,
        request_delay_seconds=float(os.getenv("SCRAPER_DELAY_SECONDS", "1.5")),
        request_timeout_seconds=int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "30")),
        request_max_retries=int(os.getenv("SCRAPER_MAX_RETRIES", "3")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        dry_run=_bool_env("DRY_RUN", default=False),
    )


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
