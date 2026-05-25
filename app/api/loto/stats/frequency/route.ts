/** GET /api/loto/stats/frequency — espejo del endpoint Kino, números 1-41. */
import type { NextRequest } from "next/server";
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const timeWindow = request.nextUrl.searchParams.get("window") ?? "all";
  return serveStatsCache({
    game: "loto",
    statType: "frequency",
    timeWindow,
  });
}
