/** GET /api/loto/stats/distribution — campana de Gauss para Loto. */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "loto",
    statType: "distribution",
    timeWindow: "all",
  });
}
