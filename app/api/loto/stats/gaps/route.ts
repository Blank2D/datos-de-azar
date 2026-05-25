/** GET /api/loto/stats/gaps — brechas sin aparición para Loto. */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "loto",
    statType: "gaps",
    timeWindow: "all",
  });
}
