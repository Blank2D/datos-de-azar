"""
LotoScraper — extrae sorteos de Loto desde polla.cl

Reglas del juego:
- 6 números del 1 al 41
- Revancha opcional (6 números del 1 al 41)
- Desquite opcional (6 números del 1 al 41)
- Sorteos Martes, Jueves y Domingo a las 21:00 CLT

Fuentes:
- Última jugada: https://www.polla.cl/es/view/resultados/5271
- Histórico:     https://resultadoslotochile.com/  (fallback)

NOTA: El HTML de polla.cl carga muchos resultados en una sola página. Esta
implementación extrae el bloque del primer (último) sorteo. Los bloques de
"Revancha" y "Desquite" se identifican por encabezados de texto cercanos.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .base_scraper import BaseScraper, ScrapedDraw, ScraperError, ValidationError


logger = logging.getLogger(__name__)


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

SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


class LotoScraper(BaseScraper):
    GAME_NAME = "loto"
    EXPECTED_COUNT = 6
    NUMBER_RANGE = (1, 41)
    VALID_DAYS = {"tuesday", "thursday", "sunday"}

    LATEST_URL = "https://www.polla.cl/es/view/resultados/5271"

    # --------------------------------------------------------
    # API pública
    # --------------------------------------------------------
    def scrape_latest(self) -> ScrapedDraw:
        logger.info("Loto: pidiendo último sorteo (%s)", self.LATEST_URL)
        response = self.fetch(self.LATEST_URL)
        draw = self._parse_polla_cl(response.text, source_url=self.LATEST_URL)
        self.validate(draw)
        logger.info("Loto: último sorteo extraído #%s %s", draw.draw_number, draw.numbers)
        return draw

    def scrape_historic(
        self, start: Optional[int] = None, end: Optional[int] = None
    ) -> list[ScrapedDraw]:
        # polla.cl no expone histórico estructurado por URL — se delega a fuente alternativa.
        raise ScraperError(
            "scrape_historic(Loto) aún no implementado. "
            "Para carga inicial usar resultadoslotochile.com o un dump manual."
        )

    # --------------------------------------------------------
    # Parser principal
    # --------------------------------------------------------
    def _parse_polla_cl(self, html: str, source_url: str) -> ScrapedDraw:
        soup = BeautifulSoup(html, "html.parser")

        # 1) Encontrar el bloque del último sorteo. polla.cl lista varios
        #    sorteos; tomamos el primer encabezado "Sorteo N° ..." (más reciente).
        block = self._find_latest_block(soup)
        if block is None:
            # Fallback: trabajar sobre todo el documento
            block = soup

        text = block.get_text(" ", strip=True) if isinstance(block, Tag) else soup.get_text(" ", strip=True)

        draw_number = self._extract_draw_number(text)
        draw_date, draw_day = self._extract_date_and_day(text)

        numbers = self._extract_numbers_for_section(block, "loto")
        revancha = self._extract_numbers_for_section(block, "revancha", optional=True)
        desquite = self._extract_numbers_for_section(block, "desquite", optional=True)

        return ScrapedDraw(
            draw_number=draw_number,
            draw_date=draw_date,
            draw_day=draw_day,
            numbers=numbers,
            revancha=revancha,
            desquite=desquite,
            source_url=source_url,
        )

    @staticmethod
    def _find_latest_block(soup: BeautifulSoup) -> Optional[Tag]:
        """
        Busca el primer contenedor que mencione 'Sorteo' + número.
        Devolvemos el ancestro más cercano que contenga también la lista de bolas.
        """
        for el in soup.find_all(string=re.compile(r"Sorteo\s*N[°ºo]?\s*\d", re.IGNORECASE)):
            parent = el.parent
            # Subir hasta un contenedor que tenga al menos 6 elementos numéricos
            for _ in range(6):
                if parent is None:
                    break
                if isinstance(parent, Tag):
                    digits = re.findall(r"\b\d{1,2}\b", parent.get_text(" ", strip=True))
                    if len(digits) >= 6:
                        return parent
                parent = parent.parent if parent else None
        return None

    # --------------------------------------------------------
    # Extractores
    # --------------------------------------------------------
    @staticmethod
    def _extract_draw_number(text: str) -> int:
        match = re.search(
            r"(?:Sorteo|Concurso)\s*(?:N[°ºo]\.?\s*)?(\d{3,5})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            raise ScraperError("No se encontró el número de sorteo Loto")
        return int(match.group(1))

    @staticmethod
    def _extract_date_and_day(text: str) -> tuple[date, str]:
        match = re.search(
            r"(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+"
            r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            num_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
            if not num_match:
                raise ScraperError("No se encontró la fecha del sorteo Loto")
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

    def _extract_numbers_for_section(
        self, root, section: str, *, optional: bool = False
    ) -> Optional[list[int]]:
        """
        Busca un encabezado/etiqueta que contenga `section` (case-insensitive) y
        toma los siguientes 6 números (1–41) tras esa etiqueta.

        Para `section="loto"` el matching es laxo: si no se encuentra la palabra
        explícitamente, toma los primeros 6 números válidos del bloque.
        """
        if not isinstance(root, Tag):
            soup = BeautifulSoup(str(root), "html.parser")
            root = soup

        text_root = root.get_text(" \n ", strip=True)

        # 1) Intentar localizar la subcadena de la sección y leer los 6 enteros
        #    válidos siguientes en el orden del DOM.
        pattern = re.compile(rf"\b{section}\b", re.IGNORECASE)
        match = pattern.search(text_root)

        if match is None:
            if section == "loto":
                # Fallback: primeros 6 válidos del bloque
                return self._first_n_in_range(text_root, n=6, lo=1, hi=41) or None
            return None if optional else None

        tail = text_root[match.end():]
        nums = self._first_n_in_range(tail, n=6, lo=1, hi=41)
        if nums is None and not optional:
            raise ScraperError(f"No se pudieron extraer 6 números para '{section}'")
        return nums

    @staticmethod
    def _first_n_in_range(text: str, *, n: int, lo: int, hi: int) -> Optional[list[int]]:
        out: list[int] = []
        for raw in re.findall(r"\b(\d{1,2})\b", text):
            val = int(raw)
            if lo <= val <= hi and val not in out:
                out.append(val)
                if len(out) == n:
                    return out
        return out if len(out) == n else None
