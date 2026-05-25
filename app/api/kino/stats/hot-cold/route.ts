/**
 * GET /api/kino/stats/hot-cold
 *
 * Query params:
 *   - window: cantidad de sorteos recientes a considerar (default 50)
 *
 * Devuelve cada número clasificado en hot/warm/neutral/cool/cold.
 *
 * ⚠️ El frontend debe acompañar siempre esta visualización con la nota:
 *    "Caliente/frío es descriptivo, no predictivo. Los sorteos son
 *     independientes entre sí."
 */
import type { NextRequest } from "next/server";
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const window = request.nextUrl.searchParams.get("window") ?? "50";
  return serveStatsCache({
    game: "kino",
    statType: "hot_cold",
    timeWindow: window,
  });
}
