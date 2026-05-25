/**
 * Tipos compartidos entre la API, lib/ y el frontend.
 *
 * Estos tipos son la forma SERIALIZADA (lo que viaja en JSON) — no los tipos
 * crudos de Prisma. Las API routes usan `serializeForApi` para convertir
 * BigInt y Date a estos tipos antes de devolver la respuesta.
 *
 * Mantener sincronizado con el contrato del API definido en INSTRUCCIONES_OPUS.md.
 */

// ============================================================
// Enums
// ============================================================

export type Game = "kino" | "loto";

export type KinoDay = "wednesday" | "friday" | "sunday";
export type LotoDay = "tuesday" | "thursday" | "sunday";

// ============================================================
// Sorteos (forma de respuesta del API)
// ============================================================

export interface KinoDrawDTO {
  id: number;
  drawNumber: number;
  drawDate: string;             // "2024-05-15"
  drawDay: KinoDay;
  numbers: number[];            // 14 enteros del 1 al 25
  adicional: number | null;
  prizeJackpot: number | null;  // en CLP
  winnersCount: number | null;
}

export interface LotoDrawDTO {
  id: number;
  drawNumber: number;
  drawDate: string;
  drawDay: LotoDay;
  numbers: number[];            // 6 enteros del 1 al 41
  revancha: number[] | null;
  desquite: number[] | null;
  prizeJackpot: number | null;
  winnersCount: number | null;
}

// ============================================================
// Paginación
// ============================================================

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

// ============================================================
// Estadísticas — leen de StatisticsCache
// ============================================================

export type TimeWindow = "all" | "last_100" | "last_year";

export interface FrequencyEntry {
  number: number;
  appearances: number;
  frequency: number;     // 0..1
  expected: number;      // probabilidad teórica si fuese uniforme
  deviationPct: number;  // ((frequency - expected) / expected) * 100
}

export interface FrequencyResponse {
  game: Game;
  timeWindow: TimeWindow;
  totalDraws: number;
  numbers: FrequencyEntry[];
}

export interface DistributionHistogramBin {
  binCenter: number;
  count: number;
  density: number;
}

export interface DistributionCurvePoint {
  x: number;
  y: number;
}

export interface DistributionResponse {
  game: Game;
  totalDraws: number;
  theoreticalMean: number;
  observedMean: number;
  observedStd: number;
  histogram: DistributionHistogramBin[];
  normalCurve: DistributionCurvePoint[];
  ksTest: {
    statistic: number;
    pValue: number;
    isNormal: boolean;
  };
  educationalNote: string;
}

export type HotColdCategory = "hot" | "warm" | "neutral" | "cool" | "cold";

export interface HotColdEntry {
  number: number;
  temperatureScore: number;  // -1..+1
  category: HotColdCategory;
  recentRate: number;
  historicalRate: number;
}

export interface HotColdResponse {
  game: Game;
  window: number;
  numbers: HotColdEntry[];
}

export interface GapEntry {
  number: number;
  currentGap: number;
  avgGap: number;
  maxHistoricalGap: number;
  lastSeenDraw: number;
}

export interface GapsResponse {
  game: Game;
  numbers: GapEntry[];
}

export interface PairEntry {
  a: number;
  b: number;
  count: number;
  lift: number; // observed / expected
}

export interface PairsResponse {
  game: Game;
  topPairs: PairEntry[];
}

// ============================================================
// Insights (resumen para el home)
// ============================================================

export interface GameInsight {
  hottestNumber: number | null;
  coldestNumber: number | null;
  longestCurrentGap: { number: number; gap: number } | null;
  lastJackpot: { amount: number; drawDate: string } | null;
  nextDrawDate: string;       // ISO con hora
  isRandom: boolean | null;   // resultado del chi-cuadrado
}

export interface InsightsResponse {
  kino: GameInsight;
  loto: GameInsight;
}
