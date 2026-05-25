"""
Clasificación hot/cold por temperatura — descriptivo, no predictivo.

⚠️ Educativo: la gambler's fallacy es la creencia de que números "fríos"
   tienen más probabilidad de salir pronto. Los sorteos son independientes,
   así que un número que no ha salido en 30 sorteos NO tiene mayor
   probabilidad en el próximo. Esta visualización existe solo para mostrar
   variabilidad muestral, no para "predecir".

Lógica:
    temperatureScore = (recentRate - historicalRate) / historicalRate
    Se trunca a [-1, +1] para que el frontend pueda mapearlo a un color sin
    outliers descontrolados.

    historicalRate = appearances_all_time / total_draws_all_time
    recentRate     = appearances_last_window / window

Categorías por temperatureScore:
    > +0.30  → hot
    > +0.10  → warm
    >= -0.10 → neutral
    > -0.30  → cool
    else     → cold

Output → matches `HotColdResponse`:
    {
        "game": ...,
        "window": int,
        "numbers": [
            {
                "number": int,
                "temperatureScore": float (-1..+1),
                "category": "hot"|"warm"|"neutral"|"cool"|"cold",
                "recentRate": float,
                "historicalRate": float
            }, ...
        ]
    }
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from .loader import GAME_CONFIG, GameName


def _categorize(score: float) -> str:
    if score > 0.30:
        return "hot"
    if score > 0.10:
        return "warm"
    if score >= -0.10:
        return "neutral"
    if score > -0.30:
        return "cool"
    return "cold"


def compute_hot_cold(df: pd.DataFrame, game: GameName, window: int) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    total = int(len(df))

    if total == 0 or window <= 0:
        return {
            "game": game,
            "window": int(window),
            "numbers": [
                {
                    "number": n,
                    "temperatureScore": 0.0,
                    "category": "neutral",
                    "recentRate": 0.0,
                    "historicalRate": 0.0,
                }
                for n in range(config.min_number, config.max_number + 1)
            ],
        }

    effective_window = min(window, total)
    recent_df = df.tail(effective_window)

    all_counter: Counter[int] = Counter()
    for nums in df["numbers"]:
        all_counter.update(nums)

    recent_counter: Counter[int] = Counter()
    for nums in recent_df["numbers"]:
        recent_counter.update(nums)

    payload = []
    for n in range(config.min_number, config.max_number + 1):
        historical_rate = all_counter.get(n, 0) / total
        recent_rate = recent_counter.get(n, 0) / effective_window

        if historical_rate > 0:
            raw_score = (recent_rate - historical_rate) / historical_rate
        else:
            # Sin datos históricos: si aparece en la ventana es "hot" extremo,
            # si no, neutral.
            raw_score = 1.0 if recent_rate > 0 else 0.0

        score = max(-1.0, min(1.0, raw_score))

        payload.append(
            {
                "number": n,
                "temperatureScore": round(score, 4),
                "category": _categorize(score),
                "recentRate": round(recent_rate, 6),
                "historicalRate": round(historical_rate, 6),
            }
        )

    return {"game": game, "window": int(window), "numbers": payload}
