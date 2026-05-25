/**
 * GET /api/kino/stats/gaps
 *
 * Para cada número: cuántos sorteos lleva sin aparecer (currentGap), el
 * promedio histórico (avgGap), el máximo histórico (maxHistoricalGap) y
 * el último sorteo en que apareció (lastSeenDraw).
 */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "kino",
    statType: "gaps",
    timeWindow: "all",
  });
}
