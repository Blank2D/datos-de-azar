import { PrismaClient } from "@prisma/client";

/**
 * Singleton de PrismaClient.
 *
 * En desarrollo, Next.js hot-reload crea muchas instancias de módulos lo que,
 * sin esta guarda, abriría una nueva conexión a MySQL en cada cambio. En
 * producción cada lambda/proceso usa una única instancia.
 */

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log:
      process.env.NODE_ENV === "development"
        ? ["query", "warn", "error"]
        : ["warn", "error"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
