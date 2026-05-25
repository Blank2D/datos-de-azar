"""
Orquestador del pipeline de análisis.

`run_analysis_pipeline(game)` carga los sorteos, ejecuta todos los módulos
estadísticos, y persiste los resultados en `statistics_cache`.

Las combinaciones (stat_type, time_window) que se computan son las MISMAS
que los endpoints Next.js leen — modificar aquí ⇒ debe modificarse allí.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .cache_writer import upsert_cache_entry
from .distribution import compute_distribution
from .frequency import compute_frequency
from .gaps import compute_gaps
from .hot_cold import compute_hot_cold
from .loader import GameName, load_draws
from .pairs import compute_pairs
from .randomness import compute_randomness


logger = logging.getLogger(__name__)


# Lo que computamos por juego. Cada tupla es (stat_type, time_window).
# Las hot_cold con "50" y "100" coinciden con lo que el endpoint Next.js pide.
COMPUTED_ENTRIES = [
    ("frequency", "all"),
    ("frequency", "last_100"),
    ("frequency", "last_year"),
    ("distribution", "all"),
    ("hot_cold", "50"),
    ("hot_cold", "100"),
    ("gaps", "all"),
    ("pairs", "all"),
    ("randomness", "all"),
]


@dataclass
class PipelineResult:
    game: GameName
    total_draws: int
    entries_written: int
    skipped: int


def _compute_entry(
    stat_type: str, time_window: str, df, game: GameName
) -> dict[str, Any]:
    if stat_type == "frequency":
        return compute_frequency(df, game, time_window)
    if stat_type == "distribution":
        return compute_distribution(df, game)
    if stat_type == "hot_cold":
        return compute_hot_cold(df, game, int(time_window))
    if stat_type == "gaps":
        return compute_gaps(df, game)
    if stat_type == "pairs":
        return compute_pairs(df, game)
    if stat_type == "randomness":
        return compute_randomness(df, game)
    raise ValueError(f"stat_type desconocido: {stat_type!r}")


def run_analysis_pipeline(game: GameName, *, dry_run: bool = False) -> PipelineResult:
    """
    Ejecuta todos los stats para `game` y los persiste en statistics_cache.

    Si la tabla de sorteos está vacía, igual escribe placeholders (cada
    módulo devuelve un payload consistente para totalDraws=0), así los
    endpoints devuelven datos vacíos en lugar de 503.
    """
    logger.info("=== Analysis pipeline: %s ===", game)
    df = load_draws(game)
    total = int(len(df))
    logger.info("Cargados %d sorteos de %s", total, game)

    written = 0
    skipped = 0
    for stat_type, time_window in COMPUTED_ENTRIES:
        try:
            payload = _compute_entry(stat_type, time_window, df, game)
            upsert_cache_entry(
                game=game,
                stat_type=stat_type,
                time_window=time_window,
                data=payload,
                dry_run=dry_run,
            )
            written += 1
        except Exception as exc:
            # No queremos que un módulo roto bloquee a los demás.
            logger.error(
                "Error computando %s/%s/%s: %s — skip",
                game,
                stat_type,
                time_window,
                exc,
            )
            skipped += 1

    logger.info(
        "Pipeline %s OK — escritas %d entries, %d skipped, total_draws=%d",
        game,
        written,
        skipped,
        total,
    )
    return PipelineResult(
        game=game, total_draws=total, entries_written=written, skipped=skipped
    )
