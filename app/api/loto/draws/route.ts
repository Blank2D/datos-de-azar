/**
 * GET /api/loto/draws
 *
 * Query params: page, limit, from, to (idénticos al endpoint de Kino).
 */
import type { NextRequest } from "next/server";
import { listLotoDraws, rowToLotoDTO } from "@/lib/loto";
import {
  buildPaginationMeta,
  jsonError,
  jsonOk,
  parseDateRange,
  parsePagination,
} from "@/lib/utils";
import type { LotoDrawDTO, PaginatedResponse } from "@/types";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const params = parsePagination(request.nextUrl.searchParams);
    const dateRange = parseDateRange(request.nextUrl.searchParams);

    const { rows, total } = await listLotoDraws({
      skip: params.skip,
      take: params.limit,
      filters: { dateRange: dateRange ?? undefined },
    });

    const payload: PaginatedResponse<LotoDrawDTO> = {
      data: rows.map(rowToLotoDTO),
      pagination: buildPaginationMeta(total, params),
    };

    return jsonOk(payload);
  } catch (err) {
    console.error("[api/loto/draws] error:", err);
    return jsonError("Error interno al listar sorteos", 500);
  }
}
