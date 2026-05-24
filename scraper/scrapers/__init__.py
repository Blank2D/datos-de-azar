"""Scrapers de datos-de-azar."""
from .base_scraper import BaseScraper, ScrapedDraw, ScraperError, ValidationError
from .kino_scraper import KinoScraper
from .loto_scraper import LotoScraper

__all__ = [
    "BaseScraper",
    "ScrapedDraw",
    "ScraperError",
    "ValidationError",
    "KinoScraper",
    "LotoScraper",
]
