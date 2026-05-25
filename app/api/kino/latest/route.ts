/**
 * GET /api/kino/latest
 *
 * Devuelve el sorteo más reciente del Kino. 404 si la BD está vacía
 * (el scraper aún no ha corrido nunca).
 */
import { findLatestKinoDraw, rowToKinoDTO } from "@/lib/kino";
import { jsonError, jsonOk } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const row = await findLatestKinoDraw();
    if (!row) {
      return jsonError(
        "No hay sorteos de Kino en la base de datos todavía",
        404
      );
    }
    return jsonOk(rowToKinoDTO(row));
  } catch (err) {
    console.error("[api/kino/latest] error:", err);
    return jsonError("Error interno al consultar el último sorteo", 500);
  }
}
