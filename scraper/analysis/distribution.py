"""
Distribución de la SUMA de números por sorteo.

🔔 La estrella del proyecto — el histograma con la campana de Gauss
   superpuesta es lo que el frontend muestra como gráfico principal.

Concepto educativo: aunque cada número individual es uniforme, la SUMA
de varios números independientes (CLT) tiende a una normal. Esto es lo
que hace que la "campana" emerja en datos genuinamente aleatorios.

Test de bondad de ajuste: usamos Kolmogorov–Smirnov contra una normal
con parámetros teóricos (media y σ del muestreo sin reemplazo, ver
loader.GameConfig). Un p-value > 0.05 ⇒ no rechazamos normalidad.

Output → matches `DistributionResponse` en types/index.ts:
    {
        "game": ...,
        "totalDraws": int,
        "theoreticalMean": float,
        "observedMean": float,
        "observedStd": float,
        "histogram": [{"binCenter": float, "count": int, "density": float}, ...],
        "normalCurve": [{"x": float, "y": float}, ...],
        "ksTest": {"statistic": float, "pValue": float, "isNormal": bool},
        "educationalNote": str
    }
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from .loader import GAME_CONFIG, GameName


# Cantidad de bins del histograma + puntos de la curva normal.
# 40 bins ofrece buena resolución para Kino (rango ~91..273) y Loto (~21..231).
HISTOGRAM_BINS = 40
NORMAL_CURVE_POINTS = 100


def compute_distribution(df: pd.DataFrame, game: GameName) -> dict[str, Any]:
    config = GAME_CONFIG[game]
    total_draws = int(len(df))

    theoretical_mean = config.theoretical_sum_mean
    theoretical_std = config.theoretical_sum_std

    if total_draws == 0:
        return {
            "game": game,
            "totalDraws": 0,
            "theoreticalMean": round(theoretical_mean, 3),
            "observedMean": 0.0,
            "observedStd": 0.0,
            "histogram": [],
            "normalCurve": [],
            "ksTest": {"statistic": 0.0, "pValue": 1.0, "isNormal": True},
            "educationalNote": _educational_note(game, total_draws),
        }

    sums = np.array([sum(nums) for nums in df["numbers"]], dtype=float)
    observed_mean = float(np.mean(sums))
    observed_std = float(np.std(sums, ddof=1)) if total_draws > 1 else 0.0

    # Histograma con bins fijos en el rango teórico, para que comparar
    # juegos en distintos tiempos siempre dé bins consistentes.
    # Kino: min posible = 1+2+...+14 = 105, max = 12+13+...+25 = 266
    # Loto: min = 1+...+6 = 21, max = 36+...+41 = 231
    k = config.numbers_per_draw
    nmin = config.min_number
    nmax = config.max_number
    sum_min = sum(range(nmin, nmin + k))
    sum_max = sum(range(nmax - k + 1, nmax + 1))

    counts, bin_edges = np.histogram(sums, bins=HISTOGRAM_BINS, range=(sum_min, sum_max))
    bin_width = bin_edges[1] - bin_edges[0]
    densities = counts / (total_draws * bin_width) if total_draws > 0 else counts * 0.0

    histogram = [
        {
            "binCenter": round(float((bin_edges[i] + bin_edges[i + 1]) / 2), 3),
            "count": int(counts[i]),
            "density": round(float(densities[i]), 6),
        }
        for i in range(len(counts))
    ]

    # Curva normal teórica — usa σ teórica (preferida) o la observada como fallback.
    sigma_curve = theoretical_std if theoretical_std > 0 else max(observed_std, 1e-9)
    xs = np.linspace(sum_min, sum_max, NORMAL_CURVE_POINTS)
    ys = scipy_stats.norm.pdf(xs, loc=theoretical_mean, scale=sigma_curve)
    normal_curve = [
        {"x": round(float(x), 3), "y": round(float(y), 6)} for x, y in zip(xs, ys)
    ]

    # KS test contra la normal teórica.
    if total_draws >= 8 and theoretical_std > 0:
        ks_stat, ks_p = scipy_stats.kstest(
            sums, "norm", args=(theoretical_mean, theoretical_std)
        )
        ks = {
            "statistic": round(float(ks_stat), 6),
            "pValue": round(float(ks_p), 6),
            "isNormal": bool(ks_p > 0.05),
        }
    else:
        ks = {"statistic": 0.0, "pValue": 1.0, "isNormal": True}

    return {
        "game": game,
        "totalDraws": total_draws,
        "theoreticalMean": round(theoretical_mean, 3),
        "observedMean": round(observed_mean, 3),
        "observedStd": round(observed_std, 3),
        "histogram": histogram,
        "normalCurve": normal_curve,
        "ksTest": ks,
        "educationalNote": _educational_note(game, total_draws),
    }


def _educational_note(game: GameName, total_draws: int) -> str:
    config = GAME_CONFIG[game]
    if total_draws == 0:
        return (
            f"Aún no hay sorteos de {game.capitalize()} en la base. Cuando los haya, "
            "verás cómo la suma de los números por sorteo se distribuye en forma de "
            "campana — un resultado clásico del Teorema Central del Límite."
        )
    return (
        f"Cada uno de los {config.numbers_per_draw} números individuales de "
        f"{game.capitalize()} es uniforme entre {config.min_number} y "
        f"{config.max_number}. Pero al sumar todos los números de un sorteo, "
        "la distribución resultante tiende a una NORMAL (campana de Gauss). "
        "Esto es el Teorema Central del Límite en acción: la suma de variables "
        "independientes converge a una normal, incluso cuando las variables "
        "originales no lo son. Que tu sorteo se ajuste a la curva es señal de "
        "aleatoriedad genuina."
    )
