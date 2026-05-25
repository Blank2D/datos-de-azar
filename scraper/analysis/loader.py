"""
Carga sorteos desde MySQL y los normaliza a un DataFrame de pandas.

Toda la fase 3 trabaja sobre el output de este módulo:
    df columns:
        draw_number  int
        draw_date    pandas Timestamp
        numbers      list[int]   (ya ordenados ascendentemente)

Convención: los DataFrames vienen ordenados por `draw_number ASC`, así
las funciones que computan ventanas móviles (hot/cold, gaps) pueden
asumir que `iloc[-1]` es el sorteo más reciente.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd
from sqlalchemy import select

from ..models import Game, KinoDraw, LotoDraw, get_session


GameName = Literal["kino", "loto"]


@dataclass(frozen=True)
class GameConfig:
    """Constantes por juego — usado en frequency, distribution, etc."""

    name: GameName
    numbers_per_draw: int    # Kino: 14, Loto: 6
    pool_size: int           # Kino: 25, Loto: 41
    min_number: int          # 1 (ambos)

    @property
    def max_number(self) -> int:
        return self.min_number + self.pool_size - 1

    @property
    def expected_per_number(self) -> float:
        """Probabilidad teórica de que un número específico aparezca en un sorteo."""
        return self.numbers_per_draw / self.pool_size

    @property
    def theoretical_sum_mean(self) -> float:
        """Media teórica de la suma de números en un sorteo, si fuese muestreo sin reemplazo."""
        n = self.pool_size
        k = self.numbers_per_draw
        return k * (n + 1) / 2

    @property
    def theoretical_sum_std(self) -> float:
        """
        Desviación estándar teórica de la suma, según la fórmula de muestreo sin
        reemplazo: sqrt(k * (N-k) * (N+1) / 12) — distribución hipergeométrica de suma.
        """
        n = self.pool_size
        k = self.numbers_per_draw
        return (k * (n - k) * (n + 1) / 12) ** 0.5


GAME_CONFIG: dict[GameName, GameConfig] = {
    "kino": GameConfig(name="kino", numbers_per_draw=14, pool_size=25, min_number=1),
    "loto": GameConfig(name="loto", numbers_per_draw=6, pool_size=41, min_number=1),
}


def _model_for(game: GameName):
    return KinoDraw if game == "kino" else LotoDraw


def load_draws(game: GameName) -> pd.DataFrame:
    """
    Carga TODOS los sorteos del juego, ordenados por draw_number ASC.

    Devuelve un DataFrame vacío con las columnas correctas si la tabla
    está vacía (útil para los smoke tests).
    """
    model = _model_for(game)
    with get_session() as session:
        stmt = select(model).order_by(model.draw_number.asc())
        rows = session.execute(stmt).scalars().all()

    if not rows:
        return pd.DataFrame(
            columns=["draw_number", "draw_date", "numbers"]
        ).astype({"draw_number": "int64"})

    records = [
        {
            "draw_number": r.draw_number,
            "draw_date": pd.Timestamp(r.draw_date),
            "numbers": sorted(r.numbers),
        }
        for r in rows
    ]
    df = pd.DataFrame.from_records(records)
    df = df.sort_values("draw_number").reset_index(drop=True)
    return df


def slice_window(df: pd.DataFrame, time_window: str) -> pd.DataFrame:
    """
    Aplica una ventana temporal:
        "all"       → todo
        "last_100"  → últimos 100 sorteos por draw_number
        "last_year" → sorteos con draw_date >= (max(draw_date) - 365 días)

    Si el DataFrame está vacío devuelve el mismo DataFrame vacío.
    """
    if df.empty:
        return df

    if time_window == "all":
        return df.copy()
    if time_window == "last_100":
        return df.tail(100).reset_index(drop=True)
    if time_window == "last_year":
        cutoff = df["draw_date"].max() - pd.Timedelta(days=365)
        return df.loc[df["draw_date"] >= cutoff].reset_index(drop=True)

    raise ValueError(f"time_window desconocido: {time_window!r}")
