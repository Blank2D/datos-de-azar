/**
 * GET /api/kino/stats/frequency
 *
 * Query params:
 *   - window: "all" | "last_100" | "last_year"   (default "all")
 *
 * Devuelve cuántas veces ha salido cada número del 1 al 25, su frecuencia
 * observada vs. la esperada teórica (14/25), y la desviación porcentual.
 */
import type { NextRequest } from "next/server";
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const timeWindow = request.nextUrl.searchParams.get("window") ?? "all";
  return serveStatsCache({
    game: "kino",
    statType: "frequency",
    timeWindow,
  });
}
