/**
 * Lectura del StatisticsCache.
 *
 * Las estadísticas se pre-computan en Python (Fase 3) y se cachean en MySQL.
 * Las API routes son lectoras puras: si el cache no tiene la entrada, devuelven
 * 503 con un mensaje explicativo en lugar de calcular en tiempo real.
 */
import { prisma } from "./db";
import { jsonError, jsonOk } from "./utils";
import type { Game, TimeWindow } from "@/types";

export type StatType =
  | "frequency"
  | "distribution"
  | "hot_cold"
  | "gaps"
  | "pairs"
  | "randomness";

interface ReadStatsOptions {
  game: Game;
  statType: StatType;
  timeWindow?: TimeWindow | string; // default "all"
}

/**
 * Lee la entrada del cache. Devuelve null si no existe.
 */
export async function readStatsCache({
  game,
  statType,
  timeWindow = "all",
}: ReadStatsOptions) {
  return prisma.statisticsCache.findUnique({
    where: {
      game_statType_timeWindow: {
        game,
        statType,
        timeWindow,
      },
    },
  });
}

/**
 * Helper para handlers de /api/{game}/stats/{statType}.
 *
 * Si el cache existe, devuelve `jsonOk` con `{ game, timeWindow, ...data, computedAt }`.
 * Si no existe, devuelve 503 con mensaje explicando que el análisis aún no ha corrido.
 */
export async function serveStatsCache(opts: ReadStatsOptions) {
  try {
    const row = await readStatsCache(opts);
    if (!row) {
      return jsonError(
        "Esta estadística aún no ha sido pre-computada. Corre el pipeline de análisis Python (fase 3) y vuelve a intentar.",
        503,
        {
          game: opts.game,
          statType: opts.statType,
          timeWindow: opts.timeWindow ?? "all",
          hint:
            "scraper/main.py --game " +
            opts.game +
            " --mode analyze   (cuando esté implementado)",
        }
      );
    }

    return jsonOk({
      game: row.game,
      statType: row.statType,
      timeWindow: row.timeWindow,
      computedAt: row.computedAt,
      ...(row.data as Record<string, unknown>),
    });
  } catch (err) {
    console.error(`[stats ${opts.game}/${opts.statType}] error:`, err);
    return jsonError("Error interno al consultar el cache de estadísticas", 500);
  }
}
