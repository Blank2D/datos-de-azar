/**
 * GET /api/kino/stats/distribution
 *
 * 🔔 La estrella del proyecto.
 *
 * Devuelve la distribución histórica de la SUMA de los 14 números por
 * sorteo, junto con la curva normal teórica y el p-value del test KS.
 * El frontend la dibuja como histograma + campana de Gauss superpuesta.
 */
import { serveStatsCache } from "@/lib/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  return serveStatsCache({
    game: "kino",
    statType: "distribution",
    timeWindow: "all",
  });
}
