"""
Smoke test del pipeline de análisis usando sorteos sintéticos en memoria.

NO toca MySQL. Genera DataFrames con la misma forma que `loader.load_draws`
y verifica que cada módulo devuelve un payload con las claves esperadas
por los DTOs de TypeScript (types/index.ts).

Ejecutar:
    cd scraper
    python -m pytest analysis/tests/test_pipeline_synthetic.py -v
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd
import pytest

from scraper.analysis.distribution import compute_distribution
from scraper.analysis.frequency import compute_frequency
from scraper.analysis.gaps import compute_gaps
from scraper.analysis.hot_cold import compute_hot_cold
from scraper.analysis.loader import GAME_CONFIG, slice_window
from scraper.analysis.pairs import compute_pairs
from scraper.analysis.randomness import compute_randomness


# ============================================================
# Fixtures
# ============================================================
def make_synthetic_df(game: str, n_draws: int, seed: int = 42) -> pd.DataFrame:
    """Genera sorteos uniformes random (sin duplicar números dentro de un sorteo).

    Para n_draws=0 devuelve un DataFrame con la misma forma que `load_draws()`
    cuando la tabla está vacía: columnas correctas, cero filas.
    """
    if n_draws == 0:
        return pd.DataFrame(columns=["draw_number", "draw_date", "numbers"]).astype(
            {"draw_number": "int64"}
        )

    rng = random.Random(seed)
    config = GAME_CONFIG[game]
    pool = list(range(config.min_number, config.max_number + 1))
    base_date = date(2024, 1, 1)

    rows = []
    for i in range(n_draws):
        nums = sorted(rng.sample(pool, config.numbers_per_draw))
        rows.append(
            {
                "draw_number": 1000 + i,
                "draw_date": pd.Timestamp(base_date + timedelta(days=i * 2)),
                "numbers": nums,
            }
        )
    return pd.DataFrame.from_records(rows)


# ============================================================
# frequency
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_frequency_shape(game):
    df = make_synthetic_df(game, 200)
    payload = compute_frequency(df, game, "all")
    config = GAME_CONFIG[game]

    assert payload["game"] == game
    assert payload["timeWindow"] == "all"
    assert payload["totalDraws"] == 200
    assert len(payload["numbers"]) == config.pool_size

    # Suma total de apariciones = numbers_per_draw * totalDraws
    total_appearances = sum(n["appearances"] for n in payload["numbers"])
    assert total_appearances == config.numbers_per_draw * 200

    # Cada entry tiene las claves del DTO FrequencyEntry
    expected_keys = {"number", "appearances", "frequency", "expected", "deviationPct"}
    for entry in payload["numbers"]:
        assert set(entry.keys()) == expected_keys
        assert 0 <= entry["frequency"] <= 1


@pytest.mark.parametrize("window", ["all", "last_100", "last_year"])
def test_frequency_windows_run(window):
    df = make_synthetic_df("kino", 200)
    payload = compute_frequency(df, "kino", window)
    assert payload["timeWindow"] == window
    assert payload["totalDraws"] <= 200


def test_frequency_empty_df():
    df = make_synthetic_df("kino", 0)
    payload = compute_frequency(df, "kino", "all")
    assert payload["totalDraws"] == 0
    assert all(entry["appearances"] == 0 for entry in payload["numbers"])


# ============================================================
# distribution
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_distribution_shape(game):
    df = make_synthetic_df(game, 500)
    payload = compute_distribution(df, game)

    expected_top = {
        "game",
        "totalDraws",
        "theoreticalMean",
        "observedMean",
        "observedStd",
        "histogram",
        "normalCurve",
        "ksTest",
        "educationalNote",
    }
    assert set(payload.keys()) == expected_top
    assert payload["totalDraws"] == 500
    assert len(payload["histogram"]) > 0
    assert len(payload["normalCurve"]) > 0

    # KS test debería NO rechazar normalidad con datos uniformes y N=500
    # (la suma converge a normal por CLT).
    assert payload["ksTest"]["pValue"] > 0.01

    for bin_ in payload["histogram"]:
        assert {"binCenter", "count", "density"} == set(bin_.keys())
    for pt in payload["normalCurve"]:
        assert {"x", "y"} == set(pt.keys())


def test_distribution_empty_df():
    df = make_synthetic_df("kino", 0)
    payload = compute_distribution(df, "kino")
    assert payload["totalDraws"] == 0
    assert payload["histogram"] == []
    assert payload["normalCurve"] == []


# ============================================================
# hot_cold
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_hot_cold_shape(game):
    df = make_synthetic_df(game, 200)
    payload = compute_hot_cold(df, game, window=50)
    config = GAME_CONFIG[game]

    assert payload["game"] == game
    assert payload["window"] == 50
    assert len(payload["numbers"]) == config.pool_size

    valid_categories = {"hot", "warm", "neutral", "cool", "cold"}
    for entry in payload["numbers"]:
        assert {"number", "temperatureScore", "category", "recentRate", "historicalRate"} == set(
            entry.keys()
        )
        assert -1.0 <= entry["temperatureScore"] <= 1.0
        assert entry["category"] in valid_categories


def test_hot_cold_window_larger_than_data():
    df = make_synthetic_df("kino", 10)
    payload = compute_hot_cold(df, "kino", window=50)
    # No debe romper aunque la ventana > total sorteos
    assert payload["window"] == 50
    assert len(payload["numbers"]) == 25


# ============================================================
# gaps
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_gaps_shape(game):
    df = make_synthetic_df(game, 100)
    payload = compute_gaps(df, game)
    config = GAME_CONFIG[game]

    assert payload["game"] == game
    assert len(payload["numbers"]) == config.pool_size

    for entry in payload["numbers"]:
        assert {"number", "currentGap", "avgGap", "maxHistoricalGap", "lastSeenDraw"} == set(
            entry.keys()
        )
        assert entry["currentGap"] >= 0
        assert entry["maxHistoricalGap"] >= entry["currentGap"] or entry["lastSeenDraw"] == 0


def test_gaps_known_number_zero():
    """Si un número aparece en el sorteo más reciente, su currentGap es 0."""
    df = make_synthetic_df("kino", 50)
    last_numbers = df.iloc[-1]["numbers"]
    payload = compute_gaps(df, "kino")
    for entry in payload["numbers"]:
        if entry["number"] in last_numbers:
            assert entry["currentGap"] == 0


# ============================================================
# pairs
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_pairs_shape(game):
    df = make_synthetic_df(game, 200)
    payload = compute_pairs(df, game)

    assert payload["game"] == game
    assert isinstance(payload["topPairs"], list)
    assert len(payload["topPairs"]) <= 50

    for pair in payload["topPairs"]:
        assert {"a", "b", "count", "lift"} == set(pair.keys())
        assert pair["a"] < pair["b"]
        assert pair["count"] >= 0
        assert pair["lift"] >= 0


# ============================================================
# randomness
# ============================================================
@pytest.mark.parametrize("game", ["kino", "loto"])
def test_randomness_shape(game):
    df = make_synthetic_df(game, 500)
    payload = compute_randomness(df, game)
    expected = {
        "game",
        "totalDraws",
        "chiSquare",
        "degreesOfFreedom",
        "pValue",
        "isRandom",
        "interpretation",
    }
    assert set(payload.keys()) == expected
    # Con 500 sorteos uniformes random, debería pasar el chi-cuadrado
    assert payload["isRandom"] is True


def test_randomness_insufficient_data():
    df = make_synthetic_df("kino", 10)
    payload = compute_randomness(df, "kino")
    assert payload["isRandom"] is None
    assert "Mínimo recomendado" in payload["interpretation"]


# ============================================================
# slice_window
# ============================================================
def test_slice_window_last_100():
    df = make_synthetic_df("kino", 200)
    sliced = slice_window(df, "last_100")
    assert len(sliced) == 100
    assert sliced.iloc[-1]["draw_number"] == df.iloc[-1]["draw_number"]


def test_slice_window_last_year():
    df = make_synthetic_df("kino", 500)  # 500 sorteos cada 2 días ≈ 2.7 años
    sliced = slice_window(df, "last_year")
    # Debe haber capturado solo los últimos 365 días
    assert len(sliced) < len(df)
    span = (sliced["draw_date"].max() - sliced["draw_date"].min()).days
    assert span <= 365
