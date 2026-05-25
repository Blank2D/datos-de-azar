/**
 * Helpers de acceso a datos del Loto. Espejo de lib/kino.ts.
 */
import { prisma } from "./db";
import type { LotoDay, LotoDrawDTO } from "@/types";

type PrismaLotoRow = Awaited<ReturnType<typeof prisma.lotoDraw.findFirst>>;

export function rowToLotoDTO(row: NonNullable<PrismaLotoRow>): LotoDrawDTO {
  return {
    id: row.id,
    drawNumber: row.drawNumber,
    drawDate: row.drawDate as unknown as string,
    drawDay: row.drawDay as LotoDay,
    numbers: (row.numbers as unknown as number[]) ?? [],
    revancha: (row.revancha as unknown as number[] | null) ?? null,
    desquite: (row.desquite as unknown as number[] | null) ?? null,
    prizeJackpot: row.prizeJackpot as unknown as number | null,
    winnersCount: row.winnersCount ?? null,
  };
}

export async function findLatestLotoDraw() {
  return prisma.lotoDraw.findFirst({
    orderBy: [{ drawDate: "desc" }, { drawNumber: "desc" }],
  });
}

export async function findLotoDrawByNumber(drawNumber: number) {
  return prisma.lotoDraw.findUnique({ where: { drawNumber } });
}

export async function findLotoDrawById(id: number) {
  return prisma.lotoDraw.findUnique({ where: { id } });
}

export interface LotoQueryFilters {
  dateRange?: { gte?: Date; lte?: Date };
}

export async function listLotoDraws({
  skip,
  take,
  filters,
}: {
  skip: number;
  take: number;
  filters: LotoQueryFilters;
}) {
  const where = filters.dateRange ? { drawDate: filters.dateRange } : {};

  const [rows, total] = await Promise.all([
    prisma.lotoDraw.findMany({
      where,
      orderBy: [{ drawDate: "desc" }, { drawNumber: "desc" }],
      skip,
      take,
    }),
    prisma.lotoDraw.count({ where }),
  ]);

  return { rows, total };
}
