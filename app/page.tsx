/**
 * Placeholder del home page.
 *
 * El home definitivo (hero con gradientes, últimos resultados, countdown,
 * insights destacados) se construye en Fase 4. Por ahora, esta página solo
 * confirma que Next.js arranca y muestra los endpoints disponibles.
 */
export default function HomePage() {
  const endpoints = [
    { method: "GET", path: "/api/kino/latest", desc: "Último sorteo del Kino" },
    { method: "GET", path: "/api/kino/draws?page=1&limit=20", desc: "Sorteos Kino paginados" },
    { method: "GET", path: "/api/kino/draws/[id]", desc: "Sorteo Kino por número" },
    { method: "GET", path: "/api/kino/stats/frequency", desc: "Frecuencias por número (Kino)" },
    { method: "GET", path: "/api/kino/stats/distribution", desc: "Campana de Gauss (Kino)" },
    { method: "GET", path: "/api/kino/stats/hot-cold", desc: "Caliente/frío (Kino)" },
    { method: "GET", path: "/api/kino/stats/gaps", desc: "Brechas sin aparición (Kino)" },
    { method: "GET", path: "/api/kino/stats/pairs", desc: "Co-ocurrencias (Kino)" },
    { method: "GET", path: "/api/loto/latest", desc: "Último sorteo del Loto" },
    { method: "GET", path: "/api/loto/draws?page=1&limit=20", desc: "Sorteos Loto paginados" },
    { method: "GET", path: "/api/loto/draws/[id]", desc: "Sorteo Loto por número" },
    { method: "GET", path: "/api/loto/stats/frequency", desc: "Frecuencias por número (Loto)" },
    { method: "GET", path: "/api/loto/stats/distribution", desc: "Campana de Gauss (Loto)" },
    { method: "GET", path: "/api/loto/stats/hot-cold", desc: "Caliente/frío (Loto)" },
    { method: "GET", path: "/api/loto/stats/gaps", desc: "Brechas sin aparición (Loto)" },
    { method: "GET", path: "/api/loto/stats/pairs", desc: "Co-ocurrencias (Loto)" },
    { method: "GET", path: "/api/insights", desc: "Resumen agregado para el home" },
  ];

  return (
    <main className="min-h-screen px-6 py-16 max-w-5xl mx-auto">
      <section className="mb-12">
        <h1 className="text-5xl font-bold tracking-tight mb-3">
          <span className="bg-gradient-kino bg-clip-text text-transparent">
            datos
          </span>
          <span className="text-text-muted">-de-</span>
          <span className="bg-gradient-loto bg-clip-text text-transparent">
            azar
          </span>
        </h1>
        <p className="text-text-secondary text-lg max-w-2xl">
          Análisis estadístico open-source de los sorteos históricos del Kino y el
          Loto en Chile. Proyecto en construcción.
        </p>
      </section>

      <section className="rounded-xl border border-border bg-bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">API disponible</h2>
        <ul className="font-mono text-sm space-y-1">
          {endpoints.map((e) => (
            <li key={e.path} className="flex items-baseline gap-3">
              <span className="text-success font-bold w-12 shrink-0">{e.method}</span>
              <code className="text-text-primary">{e.path}</code>
              <span className="text-text-muted ml-auto hidden sm:inline">
                {e.desc}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <p className="mt-12 text-xs text-text-muted text-center">
        Los juegos de azar tienen esperanza matemática negativa. Ningún análisis
        histórico puede predecir resultados futuros.
      </p>
    </main>
  );
}
