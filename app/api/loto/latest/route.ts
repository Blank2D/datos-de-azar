/**
 * GET /api/loto/latest
 */
import { findLatestLotoDraw, rowToLotoDTO } from "@/lib/loto";
import { jsonError, jsonOk } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const row = await findLatestLotoDraw();
    if (!row) {
      return jsonError(
        "No hay sorteos de Loto en la base de datos todavía",
        404
      );
    }
    return jsonOk(rowToLotoDTO(row));
  } catch (err) {
    console.error("[api/loto/latest] error:", err);
    return jsonError("Error interno al consultar el último sorteo", 500);
  }
}
