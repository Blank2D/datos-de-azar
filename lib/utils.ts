/**
 * Utilidades compartidas por la API y el frontend.
 */
import { NextResponse } from "next/server";

// Serializacion ----------------------------------------------

/**
 * Convierte un valor (incluyendo BigInt y Date anidados) a algo
 * serializable a JSON con los tipos esperados por el contrato del API.
 */
export function serializeForApi<T>(value: T): T {
  if (value === null || value === undefined) return value;
  if (typeof value === "bigint") return Number(value) as unknown as T;
  if (value instanceof Date) {
    const iso = value.toISOString();
    if (iso.endsWith("T00:00:00.000Z")) return iso.slice(0, 10) as unknown as T;
    return iso as unknown as T;
  }
  if (Array.isArray(value)) {
    return value.map((v) => serializeForApi(v)) as unknown as T;
  }
  if (typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = serializeForApi(v);
    }
    return out as unknown as T;
  }
  return value;
}

// Paginacion -------------------------------------------------

export interface PaginationParams {
  page: number;
  limit: number;
  skip: number;
}

export function parsePagination(searchParams: URLSearchParams): PaginationParams {
  const rawPage = Number(searchParams.get("page") ?? "1");
  const rawLimit = Number(searchParams.get("limit") ?? "20");
  const page = Number.isFinite(rawPage) && rawPage >= 1 ? Math.floor(rawPage) : 1;
  const limit =
    Number.isFinite(rawLimit) && rawLimit >= 1
      ? Math.min(Math.floor(rawLimit), 100)
      : 20;
  return { page, limit, skip: (page - 1) * limit };
}

export function buildPaginationMeta(
  total: number,
  params: PaginationParams
): { page: number; limit: number; total: number; pages: number } {
  const pages = params.limit > 0 ? Math.ceil(total / params.limit) : 0;
  return { page: params.page, limit: params.limit, total, pages };
}

// Filtros de fecha -------------------------------------------

export function parseDateRange(
  searchParams: URLSearchParams
): { gte?: Date; lte?: Date } | null {
  const from = searchParams.get("from");
  const to = searchParams.get("to");
  const range: { gte?: Date; lte?: Date } = {};
  if (from) {
    const d = new Date(from);
    if (!Number.isNaN(d.getTime())) range.gte = d;
  }
  if (to) {
    const d = new Date(to);
    if (!Number.isNaN(d.getTime())) range.lte = d;
  }
  return range.gte || range.lte ? range : null;
}

// Respuestas HTTP estandar -----------------------------------

export function jsonOk<T>(data: T, init?: ResponseInit) {
  return NextResponse.json(serializeForApi(data), {
    status: 200,
    ...init,
    headers: { "Cache-Control": "no-store", ...init?.headers },
  });
}

export function jsonError(
  message: string,
  status = 400,
  extra?: Record<string, unknown>
) {
  return NextResponse.json(
    { error: message, ...extra },
    { status, headers: { "Cache-Control": "no-store" } }
  );
}

// Helpers numericos ------------------------------------------

export function clampInt(
  value: number,
  { min, max, fallback }: { min: number; max: number; fallback: number }
): number {
  if (!Number.isFinite(value)) return fallback;
  const v = Math.floor(value);
  if (v < min) return min;
  if (v > max) return max;
  return v;
}

// Proxima fecha de sorteo ------------------------------------

export function nextDrawDate(
  game: "kino" | "loto",
  now: Date = new Date()
): Date {
  const config: Record<
    "kino" | "loto",
    { days: readonly number[]; hour: number }
  > = {
    kino: { days: [3, 5, 0], hour: 22 },
    loto: { days: [2, 4, 0], hour: 21 },
  };
  const { days, hour } = config[game];

  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Santiago",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const parts = Object.fromEntries(
    fmt.formatToParts(now).map((p) => [p.type, p.value])
  );
  const sanY = Number(parts.year);
  const sanM = Number(parts.month) - 1;
  const sanD = Number(parts.day);
  const sanH = Number(parts.hour === "24" ? "0" : parts.hour);
  const sanMin = Number(parts.minute);

  for (let offset = 0; offset < 8; offset++) {
    const candidate = new Date(Date.UTC(sanY, sanM, sanD + offset));
    const dow = candidate.getUTCDay();
    if (!days.includes(dow)) continue;
    if (offset === 0) {
      if (sanH < hour || (sanH === hour && sanMin === 0)) {
        candidate.setUTCHours(hour, 0, 0, 0);
        return candidate;
      }
      continue;
    }
    candidate.setUTCHours(hour, 0, 0, 0);
    return candidate;
  }

  return new Date(now.getTime() + 24 * 60 * 60 * 1000);
}
