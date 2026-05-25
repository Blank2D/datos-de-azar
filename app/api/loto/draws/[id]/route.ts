/**
 * GET /api/loto/draws/[id]
 */
import {
  findLotoDrawById,
  findLotoDrawByNumber,
  rowToLotoDTO,
} from "@/lib/loto";
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
    let row = await findLotoDrawByNumber(parsed);
    if (!row) row = await findLotoDrawById(parsed);

    if (!row) {
      return jsonError(`No se encontró el sorteo Loto #${parsed}`, 404);
    }
    return jsonOk(rowToLotoDTO(row));
  } catch (err) {
    console.error("[api/loto/draws/[id]] error:", err);
    return jsonError("Error interno al consultar el sorteo", 500);
  }
}
