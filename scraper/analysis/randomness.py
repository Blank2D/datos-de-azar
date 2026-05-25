"""
Test global de aleatoriedad usando chi-cuadrado sobre las frecuencias por número.

H0: cada número del pool tiene la misma probabilidad teórica esperada
    (p = k / N, donde k=numbers_per_draw, N=pool_size).
H1: la distribución es no uniforme (algún número tiene sesgo).

Si p-value > 0.05 ⇒ no rechazamos H0 ⇒ los sorteos parecen aleatorios.

Output:
    {
        "game": ...,
        "totalDraws": int,
        "chiSquare": float,
        "degreesOfFreedom": int,
        "pValue": float,
        "isRandom": bool,
        "interpretation": str
    }

Este resultado lo consume `/api/insights` para el flag `isRandom` del home.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd
from scipy import stats as scipy_stats

from .loader import GAME_CONFIG, GameName


def compute_randomness(df: pd.DataFrame, game: GameName) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    total = int(len(df))

    if total < 30:
        return {
            "game": game,
            "totalDraws": total,
            "chiSquare": 0.0,
            "degreesOfFreedom": config.pool_size - 1,
            "pValue": 1.0,
            "isRandom": None,
            "interpretation": (
                "Aún no hay suficientes sorteos para evaluar aleatoriedad de forma "
                f"confiable. Mínimo recomendado: 30 sorteos. Actual: {total}."
            ),
        }

    counter: Counter[int] = Counter()
    for nums in df["numbers"]:
        counter.update(nums)

    observed = [counter.get(n, 0) for n in range(config.min_number, config.max_number + 1)]
    expected_per_number = total * config.expected_per_number
    expected = [expected_per_number] * config.pool_size

    chi_stat, p_value = scipy_stats.chisquare(f_obs=observed, f_exp=expected)
    is_random = bool(p_value > 0.05)

    interpretation = (
        f"p-value = {p_value:.4f} {'>' if is_random else '<='} 0.05 ⇒ "
        f"{'no se rechaza' if is_random else 'se rechaza'} la hipótesis de "
        f"uniformidad. Los sorteos {'parecen' if is_random else 'NO parecen'} "
        "consistentes con un proceso aleatorio uniforme."
    )

    return {
        "game": game,
        "totalDraws": total,
        "chiSquare": round(float(chi_stat), 4),
        "degreesOfFreedom": config.pool_size - 1,
        "pValue": round(float(p_value), 6),
        "isRandom": is_random,
        "interpretation": interpretation,
    }
