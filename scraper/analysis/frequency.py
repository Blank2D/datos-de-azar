"""
Frecuencia de aparición por número.

Output → matches `FrequencyResponse` en types/index.ts:
    {
        "game": "kino" | "loto",
        "timeWindow": "all" | "last_100" | "last_year",
        "totalDraws": int,
        "numbers": [
            {
                "number": int,
                "appearances": int,
                "frequency": float,       # 0..1, observada
                "expected": float,        # probabilidad teórica uniforme
                "deviationPct": float,    # ((freq - expected) / expected) * 100
            },
            ...
        ]
    }
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from .loader import GAME_CONFIG, GameName, slice_window


def compute_frequency(df: pd.DataFrame, game: GameName, time_window: str) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    windowed = slice_window(df, time_window)
    total_draws = int(len(windowed))

    counter: Counter[int] = Counter()
    for nums in windowed["numbers"]:
        counter.update(nums)

    expected_freq = config.expected_per_number
    numbers_payload = []

    for n in range(config.min_number, config.max_number + 1):
        appearances = int(counter.get(n, 0))
        observed_freq = (appearances / total_draws) if total_draws > 0 else 0.0
        deviation_pct = (
            ((observed_freq - expected_freq) / expected_freq) * 100.0
            if expected_freq > 0
            else 0.0
        )
        numbers_payload.append(
            {
                "number": n,
                "appearances": appearances,
                "frequency": round(observed_freq, 6),
                "expected": round(expected_freq, 6),
                "deviationPct": round(deviation_pct, 3),
            }
        )

    return {
        "game": game,
        "timeWindow": time_window,
        "totalDraws": total_draws,
        "numbers": numbers_payload,
    }
