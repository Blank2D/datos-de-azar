/**
 * Helpers de acceso a datos del Kino. Centralizan las queries Prisma para
 * mantener los route handlers delgados y reutilizar la lógica.
 */
import { prisma } from "./db";
import type { KinoDrawDTO, KinoDay } from "@/types";

type PrismaKinoRow = Awaited<ReturnType<typeof prisma.kinoDraw.findFirst>>;

/**
 * Convierte una fila cruda de Prisma a la forma DTO que devuelve el API.
 * Note: `numbers` viene como `Prisma.JsonValue`; asumimos `number[]` porque el
 * scraper SIEMPRE escribe arrays de enteros validados.
 */
export function rowToKinoDTO(row: NonNullable<PrismaKinoRow>): KinoDrawDTO {
  return {
    id: row.id,
    drawNumber: row.drawNumber,
    drawDate: row.drawDate as unknown as string, // serializeForApi lo convierte
    drawDay: row.drawDay as KinoDay,
    numbers: (row.numbers as unknown as number[]) ?? [],
    adicional: row.adicional ?? null,
    prizeJackpot: row.prizeJackpot as unknown as number | null,
    winnersCount: row.winnersCount ?? null,
  };
}

export async function findLatestKinoDraw() {
  return prisma.kinoDraw.findFirst({
    orderBy: [{ drawDate: "desc" }, { drawNumber: "desc" }],
  });
}

export async function findKinoDrawByNumber(drawNumber: number) {
  return prisma.kinoDraw.findUnique({
    where: { drawNumber },
  });
}

export async function findKinoDrawById(id: number) {
  return prisma.kinoDraw.findUnique({
    where: { id },
  });
}

export interface KinoQueryFilters {
  dateRange?: { gte?: Date; lte?: Date };
}

export async function listKinoDraws({
  skip,
  take,
  filters,
}: {
  skip: number;
  take: number;
  filters: KinoQueryFilters;
}) {
  const where = filters.dateRange ? { drawDate: filters.dateRange } : {};

  const [rows, total] = await Promise.all([
    prisma.kinoDraw.findMany({
      where,
      orderBy: [{ drawDate: "desc" }, { drawNumber: "desc" }],
      skip,
      take,
    }),
    prisma.kinoDraw.count({ where }),
  ]);

  return { rows, total };
}
