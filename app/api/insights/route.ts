/**
 * GET /api/insights
 *
 * Resumen agregado para el home page: combina lo más destacado de Kino y
 * Loto en una sola llamada para evitar 5+ fetches desde el cliente.
 *
 * Cada campo de stats (hottest, coldest, gap, isRandom) es opcional —
 * devuelve `null` si la entrada correspondiente del StatisticsCache no
 * existe todavía. `lastJackpot` y `nextDrawDate` se computan directamente
 * y no dependen del cache.
 */
import { findLatestKinoDraw } from "@/lib/kino";
import { findLatestLotoDraw } from "@/lib/loto";
import { readStatsCache } from "@/lib/stats";
import { jsonError, jsonOk, nextDrawDate } from "@/lib/utils";
import type {
  GameInsight,
  InsightsResponse,
  HotColdEntry,
  GapEntry,
} from "@/types";

export const dynamic = "force-dynamic";

interface HotColdData {
  numbers?: HotColdEntry[];
}

interface GapsData {
  numbers?: GapEntry[];
}

interface RandomnessData {
  isRandom?: boolean;
}

async function buildKinoInsight(): Promise<GameInsight> {
  const [hotColdRow, gapsRow, randomRow, latestDraw] = await Promise.all([
    readStatsCache({ game: "kino", statType: "hot_cold", timeWindow: "50" }),
    readStatsCache({ game: "kino", statType: "gaps", timeWindow: "all" }),
    readStatsCache({ game: "kino", statType: "randomness", timeWindow: "all" }),
    findLatestKinoDraw(),
  ]);

  const hotCold = (hotColdRow?.data as HotColdData | null)?.numbers ?? null;
  const gaps = (gapsRow?.data as GapsData | null)?.numbers ?? null;
  const random = (randomRow?.data as RandomnessData | null) ?? null;

  return assembleInsight({
    hotCold,
    gaps,
    isRandom: random?.isRandom ?? null,
    lastJackpot: latestDraw
      ? {
          amount: (latestDraw.prizeJackpot as unknown as number | null) ?? 0,
          drawDate: latestDraw.drawDate as unknown as string,
        }
      : null,
    nextDrawDate: nextDrawDate("kino").toISOString(),
  });
}

async function buildLotoInsight(): Promise<GameInsight> {
  const [hotColdRow, gapsRow, randomRow, latestDraw] = await Promise.all([
    readStatsCache({ game: "loto", statType: "hot_cold", timeWindow: "50" }),
    readStatsCache({ game: "loto", statType: "gaps", timeWindow: "all" }),
    readStatsCache({ game: "loto", statType: "randomness", timeWindow: "all" }),
    findLatestLotoDraw(),
  ]);

  const hotCold = (hotColdRow?.data as HotColdData | null)?.numbers ?? null;
  const gaps = (gapsRow?.data as GapsData | null)?.numbers ?? null;
  const random = (randomRow?.data as RandomnessData | null) ?? null;

  return assembleInsight({
    hotCold,
    gaps,
    isRandom: random?.isRandom ?? null,
    lastJackpot: latestDraw
      ? {
          amount: (latestDraw.prizeJackpot as unknown as number | null) ?? 0,
          drawDate: latestDraw.drawDate as unknown as string,
        }
      : null,
    nextDrawDate: nextDrawDate("loto").toISOString(),
  });
}

function assembleInsight(input: {
  hotCold: HotColdEntry[] | null;
  gaps: GapEntry[] | null;
  isRandom: boolean | null;
  lastJackpot: { amount: number; drawDate: string } | null;
  nextDrawDate: string;
}): GameInsight {
  let hottestNumber: number | null = null;
  let coldestNumber: number | null = null;

  if (input.hotCold && input.hotCold.length > 0) {
    const sorted = [...input.hotCold].sort(
      (a, b) => b.temperatureScore - a.temperatureScore
    );
    hottestNumber = sorted[0]?.number ?? null;
    coldestNumber = sorted[sorted.length - 1]?.number ?? null;
  }

  let longestCurrentGap: GameInsight["longestCurrentGap"] = null;
  if (input.gaps && input.gaps.length > 0) {
    const sorted = [...input.gaps].sort((a, b) => b.currentGap - a.currentGap);
    const top = sorted[0];
    if (top) longestCurrentGap = { number: top.number, gap: top.currentGap };
  }

  return {
    hottestNumber,
    coldestNumber,
    longestCurrentGap,
    lastJackpot: input.lastJackpot,
    nextDrawDate: input.nextDrawDate,
    isRandom: input.isRandom,
  };
}

export async function GET() {
  try {
    const [kino, loto] = await Promise.all([
      buildKinoInsight(),
      buildLotoInsight(),
    ]);

    const payload: InsightsResponse = { kino, loto };
    return jsonOk(payload);
  } catch (err) {
    console.error("[api/insights] error:", err);
    return jsonError("Error interno al construir insights", 500);
  }
}
