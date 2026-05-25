/**
 * GET /api/kino/draws/[id]
 *
 * El parámetro `id` se interpreta como `drawNumber` (el número de sorteo
 * oficial, ej. 2999). Si no existe ningún sorteo con ese número, se hace
 * un segundo intento usando `id` interno de la tabla.
 */
import {
  findKinoDrawById,
  findKinoDrawByNumber,
  rowToKinoDTO,
} from "@/lib/kino";
import { jsonError, jsonOk } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: idParam } = await params;
  const parsed = Number(idParam);

  if (!Number.isFinite(parsed) || !Number.isInteger(parsed) || parsed <= 0) {
    return jsonError("El parámetro 'id' debe ser un entero positivo", 400);
  }

  try {
    let row = await findKinoDrawByNumber(parsed);
    if (!row) row = await findKinoDrawById(parsed);

    if (!row) {
      return jsonError(`No se encontró el sorteo Kino #${parsed}`, 404);
    }
    return jsonOk(rowToKinoDTO(row));
  } catch (err) {
    console.error("[api/kino/draws/[id]] error:", err);
    return jsonError("Error interno al consultar el sorteo", 500);
  }
}
