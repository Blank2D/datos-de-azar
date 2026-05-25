"""
Pipeline de análisis estadístico — Fase 3.

Cada módulo computa un tipo de estadística y devuelve un dict con la forma
exacta que esperan los endpoints Next.js en `app/api/{game}/stats/...`.

Los outputs se persisten en la tabla `statistics_cache` vía `cache_writer.py`
con la clave compuesta (game, stat_type, time_window).

Para correr todo:
    python -m scraper.main --game kino --mode analyze
    python -m scraper.main --game loto --mode analyze
"""
from __future__ import annotations

from .distribution import compute_distribution
from .frequency import compute_frequency
from .gaps import compute_gaps
from .hot_cold import compute_hot_cold
from .loader import GAME_CONFIG, GameConfig, load_draws
from .pairs import compute_pairs
from .pipeline import run_analysis_pipeline
from .randomness import compute_randomness

__all__ = [
    "GAME_CONFIG",
    "GameConfig",
    "compute_distribution",
    "compute_frequency",
    "compute_gaps",
    "compute_hot_cold",
    "compute_pairs",
    "compute_randomness",
    "load_draws",
    "run_analysis_pipeline",
]
