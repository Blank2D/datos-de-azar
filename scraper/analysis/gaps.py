"""
Gaps por número: hace cuántos sorteos que cada número no aparece, su
promedio histórico y máximo histórico.

Definiciones (en unidades de "sorteos"):
    currentGap        — número de sorteos desde la última aparición.
                        Si el número apareció en el sorteo más reciente, gap=0.
                        Si nunca apareció, gap = total_draws.
    avgGap            — promedio de los intervalos entre apariciones consecutivas.
    maxHistoricalGap  — máximo intervalo observado entre apariciones.
    lastSeenDraw      — draw_number del último sorteo donde apareció (0 si nunca).

Output → matches `GapsResponse`:
    {
        "game": ...,
        "numbers": [
            {
                "number": int,
                "currentGap": int,
                "avgGap": float,
                "maxHistoricalGap": int,
                "lastSeenDraw": int
            }, ...
        ]
    }
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from .loader import GAME_CONFIG, GameName


def compute_gaps(df: pd.DataFrame, game: GameName) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    total = int(len(df))

    if total == 0:
        return {
            "game": game,
            "numbers": [
                {
                    "number": n,
                    "currentGap": 0,
                    "avgGap": 0.0,
                    "maxHistoricalGap": 0,
                    "lastSeenDraw": 0,
                }
                for n in range(config.min_number, config.max_number + 1)
            ],
        }

    # Mapa: número -> lista de posiciones (0..total-1) en que apareció
    positions: dict[int, list[int]] = {
        n: [] for n in range(config.min_number, config.max_number + 1)
    }
    for idx, nums in enumerate(df["numbers"]):
        for n in nums:
            if n in positions:
                positions[n].append(idx)

    last_position_in_df = total - 1
    payload = []

    for n in range(config.min_number, config.max_number + 1):
        appearances = positions[n]

        if not appearances:
            payload.append(
                {
                    "number": n,
                    "currentGap": total,
                    "avgGap": 0.0,
                    "maxHistoricalGap": total,
                    "lastSeenDraw": 0,
                }
            )
            continue

        # Gaps entre apariciones consecutivas (la cantidad de sorteos vacíos
        # entre dos apariciones es appearances[i] - appearances[i-1]).
        if len(appearances) >= 2:
            intervals = [
                appearances[i] - appearances[i - 1] for i in range(1, len(appearances))
            ]
            avg_gap = sum(intervals) / len(intervals)
            max_historical = max(intervals)
        else:
            # Una sola aparición: el "intervalo" hasta ahora es current_gap, que ya
            # se computa aparte.
            avg_gap = 0.0
            max_historical = 0

        current_gap = last_position_in_df - appearances[-1]
        last_seen_draw = int(df.iloc[appearances[-1]]["draw_number"])

        # max histórico incluye el current_gap si es mayor que los pasados.
        max_historical = max(max_historical, current_gap)

        payload.append(
            {
                "number": n,
                "currentGap": int(current_gap),
                "avgGap": round(float(avg_gap), 3),
                "maxHistoricalGap": int(max_historical),
                "lastSeenDraw": last_seen_draw,
            }
        )

    return {"game": game, "numbers": payload}
