"""
KinoScraper — extrae sorteos de Kino desde loteria.cl

Reglas del juego:
- 14 números del 1 al 25
- Adicional opcional (1 número del 1 al 25)
- Sorteos Miércoles, Viernes y Domingo a las 22:00 CLT

Fuentes:
- Última jugada: https://www.loteria.cl/resultados/resultado-completo/?id=kino
- Histórico:     https://kinohistorico.cl/history/  (fallback)

NOTA: El HTML de loteria.cl cambia ocasionalmente. Los selectores se mantienen
deliberadamente tolerantes (búsqueda por texto, regex, fallback a JSON-LD si
existe). Si el scraper falla en producción, revisar primero el HTML actual de la
página oficial.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Optional

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapedDraw, ScraperError, ValidationError


logger = logging.getLogger(__name__)


# Mapa de nombres de día en español → inglés (canónico del schema)
SPANISH_TO_ENGLISH_DAY = {
    "lunes": "monday",
    "martes": "tuesday",
    "miercoles": "wednesday",
    "miércoles": "wednesday",
    "jueves": "thursday",
    "viernes": "friday",
    "sabado": "saturday",
    "sábado": "saturday",
    "domingo": "sunday",
}

# Meses en español
SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


class KinoScraper(BaseScraper):
    GAME_NAME = "kino"
    EXPECTED_COUNT = 14
    NUMBER_RANGE = (1, 25)
    VALID_DAYS = {"wednesday", "friday", "sunday"}

    LATEST_URL = "https://www.loteria.cl/resultados/resultado-completo/?id=kino"
    HISTORIC_URL_TEMPLATE = "https://kinohistorico.cl/history/?sorteo={n}"

    # --------------------------------------------------------
    # API pública
    # --------------------------------------------------------
    def scrape_latest(self) -> ScrapedDraw:
        logger.info("Kino: pidiendo último sorteo (%s)", self.LATEST_URL)
        response = self.fetch(self.LATEST_URL)
        draw = self._parse_loteria_cl(response.text, source_url=self.LATEST_URL)
        self.validate(draw)
        logger.info("Kino: último sorteo extraído #%s %s", draw.draw_number, draw.numbers)
        return draw

    def scrape_historic(
        self, start: Optional[int] = None, end: Optional[int] = None
    ) -> list[ScrapedDraw]:
        if start is None or end is None:
            raise ScraperError(
                "scrape_historic(Kino) requiere start y end. "
                "Para carga masiva inicial, iterar manualmente."
            )

        results: list[ScrapedDraw] = []
        for n in range(start, end + 1):
            url = self.HISTORIC_URL_TEMPLATE.format(n=n)
            try:
                response = self.fetch(url)
                draw = self._parse_kinohistorico(response.text, n, source_url=url)
                self.validate(draw)
                results.append(draw)
                logger.info("Kino histórico #%s OK", n)
            except (ScraperError, ValidationError) as exc:
                logger.warning("Kino histórico #%s falló: %s", n, exc)
        return results

    # --------------------------------------------------------
    # Parsers
    # --------------------------------------------------------
    def _parse_loteria_cl(self, html: str, source_url: str) -> ScrapedDraw:
        """
        Parser tolerante para el resultado completo del Kino en loteria.cl.

        Estrategia:
        1) Buscar el número de sorteo (p. ej. "Sorteo N° 2999").
        2) Buscar la fecha (p. ej. "Miércoles 21 de Mayo de 2026").
        3) Buscar todos los enteros del 1 al 25 que aparezcan dentro de
           contenedores típicos de las "bolas".
        4) Tomar los primeros 14 únicos en orden de aparición como números
           principales, y el siguiente como adicional si existe.
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        draw_number = self._extract_draw_number(text)
        draw_date, draw_day = self._extract_date_and_day(text)
        numbers, adicional = self._extract_numbers_from_balls(soup)

        return ScrapedDraw(
            draw_number=draw_number,
            draw_date=draw_date,
            draw_day=draw_day,
            numbers=numbers,
            adicional=adicional,
            source_url=source_url,
        )

    def _parse_kinohistorico(
        self, html: str, draw_number_hint: int, source_url: str
    ) -> ScrapedDraw:
        """Parser para kinohistorico.cl (estructura más simple)."""
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        try:
            draw_number = self._extract_draw_number(text)
        except ScraperError:
            draw_number = draw_number_hint

        draw_date, draw_day = self._extract_date_and_day(text)
        numbers, adicional = self._extract_numbers_from_balls(soup)

        return ScrapedDraw(
            draw_number=draw_number,
            draw_date=draw_date,
            draw_day=draw_day,
            numbers=numbers,
            adicional=adicional,
            source_url=source_url,
        )

    # --------------------------------------------------------
    # Extractores de bajo nivel
    # --------------------------------------------------------
    @staticmethod
    def _extract_draw_number(text: str) -> int:
        # Acepta "Sorteo N° 2999", "Sorteo Nº 2999", "Sorteo 2999", "Concurso 2999"
        match = re.search(
            r"(?:Sorteo|Concurso)\s*(?:N[°ºo]\.?\s*)?(\d{3,5})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            raise ScraperError("No se encontró el número de sorteo en la página")
        return int(match.group(1))

    @staticmethod
    def _extract_date_and_day(text: str) -> tuple[date, str]:
        # "Miércoles 21 de Mayo de 2026"
        match = re.search(
            r"(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+"
            r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            # Fallback: solo fecha numérica dd/mm/yyyy
            num_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
            if not num_match:
                raise ScraperError("No se encontró la fecha del sorteo")
            d, m, y = (int(x) for x in num_match.groups())
            dt = date(y, m, d)
            return dt, dt.strftime("%A").lower()

        spanish_day, day_num, month_name, year = match.groups()
        month = SPANISH_MONTHS.get(month_name.lower())
        if month is None:
            raise ScraperError(f"Mes desconocido: {month_name}")

        dt = date(int(year), month, int(day_num))
        english_day = SPANISH_TO_ENGLISH_DAY.get(
            spanish_day.lower(), dt.strftime("%A").lower()
        )
        return dt, english_day

    def _extract_numbers_from_balls(
        self, soup: BeautifulSoup
    ) -> tuple[list[int], Optional[int]]:
        """
        Heurística tolerante: junta los enteros 1–25 que aparecen dentro de
        elementos clasificados como "bola", "ball", "numero", "number" o
        elementos <li>/<span> que contienen solo el número.

        Toma los primeros 14 distintos en orden de aparición como números
        principales y el siguiente (si existe) como adicional.
        """
        candidates: list[int] = []
        seen_nodes: set[int] = set()

        # 1) Selectores típicos de bolas
        candidate_selectors = [
            "[class*='bola']", "[class*='ball']",
            "[class*='numero']", "[class*='number']",
            "li.numero", "span.numero",
        ]
        for sel in candidate_selectors:
            for tag in soup.select(sel):
                node_id = id(tag)
                if node_id in seen_nodes:
                    continue
                seen_nodes.add(node_id)
                num = self._parse_int_strict(tag.get_text(strip=True))
                if num is not None and 1 <= num <= 25:
                    candidates.append(num)

        # 2) Si los selectores no encontraron suficientes, fallback a regex global
        if len(candidates) < self.EXPECTED_COUNT:
            text = soup.get_text(" ", strip=True)
            # Solo enteros aislados en rango
            for raw in re.findall(r"\b(\d{1,2})\b", text):
                n = int(raw)
                if 1 <= n <= 25:
                    candidates.append(n)

        # Tomar primeros EXPECTED_COUNT únicos preservando orden
        principal: list[int] = []
        for n in candidates:
            if n not in principal:
                principal.append(n)
            if len(principal) == self.EXPECTED_COUNT:
                break

        if len(principal) < self.EXPECTED_COUNT:
            raise ScraperError(
                f"No se encontraron {self.EXPECTED_COUNT} números únicos. "
                f"Se obtuvieron: {principal}"
            )

        # Adicional: siguiente número que no esté en `principal`
        adicional: Optional[int] = None
        for n in candidates[len(principal):]:
            if n not in principal:
                adicional = n
                break

        return principal, adicional

    @staticmethod
    def _parse_int_strict(s: str) -> Optional[int]:
        """Devuelve int si el string es exactamente un número entero."""
        s = s.strip()
        if not s.isdigit():
            return None
        try:
            return int(s)
        except ValueError:
            return None
