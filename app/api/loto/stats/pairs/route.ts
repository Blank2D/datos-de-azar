/** GET /api/loto/stats/pairs — co-ocurrencias y lift para Loto. */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "loto",
    statType: "pairs",
    timeWindow: "all",
  });
}
