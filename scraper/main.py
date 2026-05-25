"""
Punto de entrada del scraper.

Uso:
    python -m scraper.main --game kino --mode latest
    python -m scraper.main --game loto --mode latest
    python -m scraper.main --game kino --mode historic --from 2900 --to 2999
    python -m scraper.main --game kino --mode latest --dry-run
    python -m scraper.main --game kino --mode latest --skip-analyze
    python -m scraper.main --game kino --mode analyze        # solo recomputa stats
    python -m scraper.main --game loto --mode analyze

Códigos de salida:
    0  — OK (incluye 'no_new_data')
    1  — Error de scraping, análisis o validación
    2  — Argumentos inválidos
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .analysis import run_analysis_pipeline
from .config import configure_logging, load_settings
from .models import (
    Game,
    KinoDay,
    KinoDraw,
    LotoDay,
    LotoDraw,
    ScraperLog,
    ScraperStatus,
    get_session,
)
from .scrapers import (
    KinoScraper,
    LotoScraper,
    ScrapedDraw,
    ScraperError,
    ValidationError,
)


logger = logging.getLogger(__name__)


# ============================================================
# Persistencia
# ============================================================
def persist_kino(draw: ScrapedDraw, *, dry_run: bool) -> bool:
    """Inserta un sorteo Kino. Devuelve True si lo insertó, False si ya existía."""
    if dry_run:
        logger.info("[DRY-RUN] Kino #%s — no se persiste", draw.draw_number)
        return True

    with get_session() as session:
        existing = (
            session.query(KinoDraw)
            .filter(KinoDraw.draw_number == draw.draw_number)
            .one_or_none()
        )
        if existing is not None:
            logger.info("Kino #%s ya existe — skip", draw.draw_number)
            return False

        row = KinoDraw(
            draw_number=draw.draw_number,
            draw_date=draw.draw_date,
            draw_day=KinoDay(draw.draw_day),
            numbers=sorted(draw.numbers),
            adicional=draw.adicional,
            prize_jackpot=draw.prize_jackpot,
            winners_count=draw.winners_count,
            source_url=draw.source_url,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.info("Kino #%s — colisión de unique al commit, asumo duplicado", draw.draw_number)
            return False
        logger.info("Kino #%s insertado", draw.draw_number)
        return True


def persist_loto(draw: ScrapedDraw, *, dry_run: bool) -> bool:
    if dry_run:
        logger.info("[DRY-RUN] Loto #%s — no se persiste", draw.draw_number)
        return True

    with get_session() as session:
        existing = (
            session.query(LotoDraw)
            .filter(LotoDraw.draw_number == draw.draw_number)
            .one_or_none()
        )
        if existing is not None:
            logger.info("Loto #%s ya existe — skip", draw.draw_number)
            return False

        row = LotoDraw(
            draw_number=draw.draw_number,
            draw_date=draw.draw_date,
            draw_day=LotoDay(draw.draw_day),
            numbers=sorted(draw.numbers),
            revancha=sorted(draw.revancha) if draw.revancha else None,
            desquite=sorted(draw.desquite) if draw.desquite else None,
            prize_jackpot=draw.prize_jackpot,
            winners_count=draw.winners_count,
            source_url=draw.source_url,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.info("Loto #%s — colisión de unique al commit, asumo duplicado", draw.draw_number)
            return False
        logger.info("Loto #%s insertado", draw.draw_number)
        return True


def log_scraper_run(
    game: Game, status: ScraperStatus, draws_found: int, message: Optional[str], *, dry_run: bool
) -> None:
    if dry_run:
        logger.info("[DRY-RUN] log → %s %s found=%s", game.value, status.value, draws_found)
        return
    try:
        with get_session() as session:
            session.add(
                ScraperLog(
                    game=game, status=status, draws_found=draws_found, message=message
                )
            )
            session.commit()
    except SQLAlchemyError as exc:
        logger.warning("No se pudo escribir ScraperLog: %s", exc)


# ============================================================
# Comandos
# ============================================================
def run_kino_latest(*, dry_run: bool, skip_analyze: bool = False) -> int:
    settings = load_settings()
    scraper = KinoScraper(
        delay_seconds=settings.request_delay_seconds,
        timeout=settings.request_timeout_seconds,
        max_retries=settings.request_max_retries,
    )
    try:
        draw = scraper.scrape_latest()
    except (ScraperError, ValidationError) as exc:
        logger.error("Kino latest falló: %s", exc)
        log_scraper_run(Game.kino, ScraperStatus.error, 0, str(exc), dry_run=dry_run)
        return 1

    inserted = persist_kino(draw, dry_run=dry_run)
    status = ScraperStatus.success if inserted else ScraperStatus.no_new_data
    log_scraper_run(Game.kino, status, 1 if inserted else 0, None, dry_run=dry_run)

    if inserted and not skip_analyze:
        _safe_trigger_analysis("kino", dry_run=dry_run)
    return 0


def run_loto_latest(*, dry_run: bool, skip_analyze: bool = False) -> int:
    settings = load_settings()
    scraper = LotoScraper(
        delay_seconds=settings.request_delay_seconds,
        timeout=settings.request_timeout_seconds,
        max_retries=settings.request_max_retries,
    )
    try:
        draw = scraper.scrape_latest()
    except (ScraperError, ValidationError) as exc:
        logger.error("Loto latest falló: %s", exc)
        log_scraper_run(Game.loto, ScraperStatus.error, 0, str(exc), dry_run=dry_run)
        return 1

    inserted = persist_loto(draw, dry_run=dry_run)
    status = ScraperStatus.success if inserted else ScraperStatus.no_new_data
    log_scraper_run(Game.loto, status, 1 if inserted else 0, None, dry_run=dry_run)

    if inserted and not skip_analyze:
        _safe_trigger_analysis("loto", dry_run=dry_run)
    return 0


def _safe_trigger_analysis(game: str, *, dry_run: bool) -> None:
    """
    Tras un insert exitoso, refrescamos el statistics_cache. Errores en el
    análisis NO deben hacer fallar el scraper (los datos ya están en BD).
    """
    try:
        result = run_analysis_pipeline(game, dry_run=dry_run)  # type: ignore[arg-type]
        logger.info(
            "Análisis %s post-insert: %d entries escritas, %d skipped",
            game,
            result.entries_written,
            result.skipped,
        )
    except Exception as exc:
        logger.warning("Análisis post-insert de %s falló (no crítico): %s", game, exc)


def run_analyze(game: str, *, dry_run: bool) -> int:
    """Modo standalone — recomputa todas las stats sin scrapear."""
    try:
        result = run_analysis_pipeline(game, dry_run=dry_run)  # type: ignore[arg-type]
    except Exception as exc:
        logger.error("Pipeline de análisis %s falló: %s", game, exc)
        return 1

    logger.info(
        "Pipeline %s: total_draws=%d, entries=%d, skipped=%d",
        game,
        result.total_draws,
        result.entries_written,
        result.skipped,
    )
    return 0


def run_kino_historic(start: int, end: int, *, dry_run: bool) -> int:
    settings = load_settings()
    scraper = KinoScraper(
        delay_seconds=settings.request_delay_seconds,
        timeout=settings.request_timeout_seconds,
        max_retries=settings.request_max_retries,
    )
    try:
        draws = scraper.scrape_historic(start=start, end=end)
    except ScraperError as exc:
        logger.error("Kino historic falló: %s", exc)
        log_scraper_run(Game.kino, ScraperStatus.error, 0, str(exc), dry_run=dry_run)
        return 1

    inserted = 0
    for d in draws:
        if persist_kino(d, dry_run=dry_run):
            inserted += 1
    status = ScraperStatus.success if inserted else ScraperStatus.no_new_data
    log_scraper_run(Game.kino, status, inserted, f"historic {start}-{end}", dry_run=dry_run)
    return 0


# ============================================================
# CLI
# ============================================================
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datos-de-azar-scraper",
        description="Scraper de sorteos de Kino y Loto (Chile).",
    )
    parser.add_argument("--game", required=True, choices=["kino", "loto"])
    parser.add_argument(
        "--mode",
        required=True,
        choices=["latest", "historic", "analyze"],
        help=(
            "latest: último sorteo / historic: rango por número de sorteo / "
            "analyze: recomputa statistics_cache sin scrapear"
        ),
    )
    parser.add_argument("--from", dest="start", type=int, help="Sorteo inicial (modo historic)")
    parser.add_argument("--to", dest="end", type=int, help="Sorteo final (modo historic)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No escribe a la BD; solo loggea lo que haría",
    )
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="En modo latest: no recomputar statistics_cache tras un insert",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    settings = load_settings()
    configure_logging(settings.log_level)

    parser = build_parser()
    args = parser.parse_args(argv)
    dry_run = args.dry_run or settings.dry_run

    if args.mode == "latest":
        if args.game == "kino":
            return run_kino_latest(dry_run=dry_run, skip_analyze=args.skip_analyze)
        return run_loto_latest(dry_run=dry_run, skip_analyze=args.skip_analyze)

    if args.mode == "analyze":
        return run_analyze(args.game, dry_run=dry_run)

    # mode == "historic"
    if args.start is None or args.end is None:
        parser.error("--from y --to son obligatorios en modo historic")
        return 2

    if args.game == "kino":
        return run_kino_historic(args.start, args.end, dry_run=dry_run)

    logger.error("Loto historic aún no implementado")
    return 1


if __name__ == "__main__":
    sys.exit(main())
