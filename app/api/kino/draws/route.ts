/**
 * GET /api/kino/draws
 *
 * Query params:
 *   - page   (default 1, min 1)
 *   - limit  (default 20, min 1, max 100)
 *   - from   (YYYY-MM-DD, opcional)
 *   - to     (YYYY-MM-DD, opcional)
 *
 * Respuesta: { data: KinoDrawDTO[], pagination: PaginationMeta }
 */
import type { NextRequest } from "next/server";
import { listKinoDraws, rowToKinoDTO } from "@/lib/kino";
import {
  buildPaginationMeta,
  jsonError,
  jsonOk,
  parseDateRange,
  parsePagination,
} from "@/lib/utils";
import type { KinoDrawDTO, PaginatedResponse } from "@/types";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const params = parsePagination(request.nextUrl.searchParams);
    const dateRange = parseDateRange(request.nextUrl.searchParams);

    const { rows, total } = await listKinoDraws({
      skip: params.skip,
      take: params.limit,
      filters: { dateRange: dateRange ?? undefined },
    });

    const payload: PaginatedResponse<KinoDrawDTO> = {
      data: rows.map(rowToKinoDTO),
      pagination: buildPaginationMeta(total, params),
    };

    return jsonOk(payload);
  } catch (err) {
    console.error("[api/kino/draws] error:", err);
    return jsonError("Error interno al listar sorteos", 500);
  }
}
