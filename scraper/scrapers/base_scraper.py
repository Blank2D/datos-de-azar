"""
Base scraper compartido entre Kino y Loto.

Provee:
- HTTP con User-Agent identificable, delay configurable y retry con backoff
- Logging consistente
- Dataclass `ScrapedDraw` para resultado normalizado
- Excepciones específicas (`ScraperError`, `ValidationError`)
- Hooks abstractos `scrape_latest()` y `scrape_historic()`
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# Constantes compartidas
# ============================================================
USER_AGENT = (
    "Mozilla/5.0 (compatible; DatosDeAzar/1.0; "
    "+https://github.com/Blank2D/datos-de-azar)"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
DEFAULT_DELAY_SECONDS = 1.5
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 3


logger = logging.getLogger(__name__)


# ============================================================
# Excepciones
# ============================================================
class ScraperError(Exception):
    """Error genérico durante el scraping (HTTP, parseo, etc.)."""


class ValidationError(ScraperError):
    """Los datos extraídos no cumplen las reglas del juego."""


# ============================================================
# Resultado normalizado
# ============================================================
@dataclass
class ScrapedDraw:
    """Representación intermedia, independiente del juego."""

    draw_number: int
    draw_date: date
    draw_day: str                       # "wednesday" | "friday" | ...
    numbers: list[int]                  # números principales
    adicional: Optional[int] = None     # solo Kino
    revancha: Optional[list[int]] = None  # solo Loto
    desquite: Optional[list[int]] = None  # solo Loto
    prize_jackpot: Optional[int] = None
    winners_count: Optional[int] = None
    source_url: Optional[str] = None
    extra: dict = field(default_factory=dict)


# ============================================================
# Base abstracta
# ============================================================
class BaseScraper(ABC):
    """
    Clase base. Las subclases definen:
        - GAME_NAME       — "kino" o "loto"
        - EXPECTED_COUNT  — cantidad de números principales (14 o 6)
        - NUMBER_RANGE    — rango válido (1, 25) o (1, 41)
        - VALID_DAYS      — set de días válidos en inglés lower
        - scrape_latest() — último sorteo publicado
        - scrape_historic(start, end) — rango de sorteos pasados
    """

    GAME_NAME: str = ""
    EXPECTED_COUNT: int = 0
    NUMBER_RANGE: tuple[int, int] = (0, 0)
    VALID_DAYS: set[str] = set()

    def __init__(
        self,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.session = self._build_session(max_retries)

    # ---- HTTP ----------------------------------------------
    def _build_session(self, max_retries: int) -> requests.Session:
        sess = requests.Session()
        sess.headers.update(DEFAULT_HEADERS)
        retry = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        return sess

    def fetch(self, url: str, **kwargs) -> requests.Response:
        """GET respetando el delay configurado. Lanza ScraperError ante fallos."""
        logger.debug("GET %s", url)
        try:
            response = self.session.get(url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise ScraperError(f"Error de red al pedir {url}: {exc}") from exc

        if response.status_code >= 400:
            raise ScraperError(
                f"HTTP {response.status_code} en {url}: {response.text[:200]}"
            )

        time.sleep(self.delay_seconds)
        return response

    # ---- Validación común ----------------------------------
    def validate(self, draw: ScrapedDraw) -> None:
        """
        Reglas comunes:
        - draw_number > 0
        - numbers tiene EXPECTED_COUNT elementos
        - cada número está en NUMBER_RANGE
        - no hay duplicados
        - draw_day es un día válido
        Las subclases pueden agregar reglas extra sobreescribiendo.
        """
        if draw.draw_number <= 0:
            raise ValidationError(f"draw_number inválido: {draw.draw_number}")

        if len(draw.numbers) != self.EXPECTED_COUNT:
            raise ValidationError(
                f"Se esperaban {self.EXPECTED_COUNT} números, "
                f"se obtuvieron {len(draw.numbers)}: {draw.numbers}"
            )

        lo, hi = self.NUMBER_RANGE
        for n in draw.numbers:
            if not isinstance(n, int):
                raise ValidationError(f"Número no-entero: {n!r}")
            if not (lo <= n <= hi):
                raise ValidationError(
                    f"Número {n} fuera de rango [{lo}, {hi}]: {draw.numbers}"
                )

        if len(set(draw.numbers)) != len(draw.numbers):
            raise ValidationError(f"Números duplicados: {draw.numbers}")

        if draw.draw_day not in self.VALID_DAYS:
            raise ValidationError(
                f"draw_day inválido para {self.GAME_NAME}: {draw.draw_day!r}"
            )

    # ---- API pública ---------------------------------------
    @abstractmethod
    def scrape_latest(self) -> ScrapedDraw:
        """Devuelve el último sorteo publicado en la fuente oficial."""

    @abstractmethod
    def scrape_historic(
        self, start: Optional[int] = None, end: Optional[int] = None
    ) -> list[ScrapedDraw]:
        """
        Devuelve un rango de sorteos por número.
        Si start/end son None, hace su mejor esfuerzo por traer todo lo disponible.
        """

    # ---- Helpers para subclases ----------------------------
    @staticmethod
    def _day_name_from_date(d: date) -> str:
        """Devuelve el día de la semana en inglés en minúscula ('monday', etc.)."""
        names = [
            "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday",
        ]
        return names[d.weekday()]
