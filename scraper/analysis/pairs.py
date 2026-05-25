"""
Co-ocurrencias entre pares de números.

Lift = P(A y B juntos) / [ P(A) * P(B) ]
       (cuántas veces más frecuente es ver A y B juntos vs. lo que sería
       bajo independencia perfecta).

Bajo independencia perfecta, lift ≈ 1. Lifts altos sugieren correlación
positiva entre los números (no causal — solo descriptiva). En sorteos
verdaderamente aleatorios y con N grande, todos los lifts deberían
converger a ~1.

Output → matches `PairsResponse`:
    {
        "game": ...,
        "topPairs": [
            {"a": int, "b": int, "count": int, "lift": float}, ...
        ]   # ordenado por lift descendente, top N
    }
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any

import pandas as pd

from .loader import GAME_CONFIG, GameName


TOP_N_PAIRS = 50


def compute_pairs(df: pd.DataFrame, game: GameName) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    total = int(len(df))

    if total == 0:
        return {"game": game, "topPairs": []}

    # Frecuencia individual (para calcular P(A))
    single_counter: Counter[int] = Counter()
    pair_counter: Counter[tuple[int, int]] = Counter()

    for nums in df["numbers"]:
        sorted_nums = sorted(set(nums))
        single_counter.update(sorted_nums)
        for a, b in combinations(sorted_nums, 2):
            pair_counter[(a, b)] += 1

    pairs_payload: list[dict[str, Any]] = []
    for (a, b), count in pair_counter.items():
        p_a = single_counter[a] / total
        p_b = single_counter[b] / total
        p_ab = count / total

        if p_a > 0 and p_b > 0:
            lift = p_ab / (p_a * p_b)
        else:
            lift = 0.0

        pairs_payload.append(
            {
                "a": int(a),
                "b": int(b),
                "count": int(count),
                "lift": round(float(lift), 4),
            }
        )

    pairs_payload.sort(key=lambda x: x["lift"], reverse=True)
    top_pairs = pairs_payload[:TOP_N_PAIRS]

    return {"game": game, "topPairs": top_pairs}
