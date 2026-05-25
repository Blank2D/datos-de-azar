/** GET /api/loto/stats/hot-cold — clasificación caliente/frío para Loto. */
import type { NextRequest } from "next/server";
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const window = request.nextUrl.searchParams.get("window") ?? "50";
  return serveStatsCache({
    game: "loto",
    statType: "hot_cold",
    timeWindow: window,
  });
}
