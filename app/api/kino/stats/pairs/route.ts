/**
 * GET /api/kino/stats/pairs
 *
 * Co-ocurrencias entre números. Devuelve las parejas con mayor `lift`
 * (cociente entre frecuencia observada y esperada bajo independencia).
 * Educativo: en un proceso verdaderamente aleatorio el lift debería ser ~1.
 */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "kino",
    statType: "pairs",
    timeWindow: "all",
  });
}
