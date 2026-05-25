"""
Upsert en la tabla `statistics_cache`.

Clave única compuesta: (game, stat_type, time_window).
Para la misma clave, se sobrescribe `data` y se actualiza `computed_at`.

`time_window` siempre es string (incluso para ventanas numéricas como "50"),
para coincidir con el contrato del schema Prisma.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.dialects.mysql import insert as mysql_insert

from ..models import Game, StatisticsCache, get_session


logger = logging.getLogger(__name__)


def upsert_cache_entry(
    game: str,
    stat_type: str,
    time_window: str,
    data: dict[str, Any],
    *,
    dry_run: bool = False,
) -> None:
    """
    Upsert por (game, stat_type, time_window). Usa MySQL `ON DUPLICATE KEY UPDATE`.
    """
    if dry_run:
        logger.info(
            "[DRY-RUN] cache %s/%s/%s — payload size=%d keys",
            game,
            stat_type,
            time_window,
            len(data),
        )
        return

    with get_session() as session:
        stmt = mysql_insert(StatisticsCache).values(
            game=Game(game),
            stat_type=stat_type,
            time_window=str(time_window),
            data=data,
        )
        # En upsert: solo actualizamos `data`. `computed_at` se refresca
        # automáticamente por el `onupdate=func.now()` del modelo.
        stmt = stmt.on_duplicate_key_update(data=stmt.inserted.data)
        session.execute(stmt)
        session.commit()

    logger.info("Cache actualizado: %s/%s/%s", game, stat_type, time_window)
