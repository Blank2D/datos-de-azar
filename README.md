# datos-de-azar

> Análisis estadístico open-source de los sorteos históricos de **Kino** y **Loto** en Chile.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)](https://www.mysql.com/)

## ¿Qué es esto?

Sitio web que scrapea, almacena y analiza estadísticamente los sorteos históricos de los dos juegos de azar más populares de Chile:

- 🎰 **Kino** — Lotería de Concepción (14 números del 1 al 25)
- 🍀 **Loto** — Polla Chilena de Beneficencia (6 números del 1 al 41)

## Disclaimer

Este proyecto es **educativo y estadístico**. **Jamás** sugiere predicciones ni estrategias de juego.

Los juegos de azar tienen **esperanza matemática negativa** y todos los sorteos son **independientes entre sí**. Ningún análisis histórico puede predecir resultados futuros.

Si crees que tienes un problema con el juego, contacta a CONACE.

## Arquitectura

| Capa | Tecnología |
|---|---|
| Frontend + API | Next.js 15 (App Router) + TypeScript |
| Estilos | Tailwind CSS + shadcn/ui |
| Gráficos | Recharts |
| Scraping | Python 3.11+ + SQLAlchemy 2.0 |
| Base de datos | MySQL 8.0 (Hostinger en producción) |
| ORM Next.js | Prisma |
| CI/CD | GitHub Actions (cron post-sorteo) |
| Deploy | Vercel + Hostinger MySQL |

## Estado actual

🚧 **Fase 1 — Fundamentos** (en construcción)

- [x] Estructura del repo
- [x] Schema Prisma (KinoDraw, LotoDraw, StatisticsCache, ScraperLog)
- [x] Docker Compose para MySQL local
- [x] Scrapers Python (Kino + Loto) con validación
- [ ] Seed histórico (~2300 sorteos cada juego)
- [ ] GitHub Actions de scraping automático

## Desarrollo local

```bash
# 1) Levantar MySQL
docker-compose up -d

# 2) Aplicar schema Prisma
cp .env.example .env
npm install
npx prisma migrate dev --name init

# 3) Instalar scraper Python
cd scraper
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4) Correr scrapers
python main.py --game kino --mode latest
python main.py --game loto --mode latest
```

## Estructura

```
datos-de-azar/
├── app/                  # Next.js App Router (frontend + API routes)
├── components/           # React components (charts, layout, etc.)
├── lib/                  # Prisma client, helpers
├── prisma/               # schema.prisma
├── scraper/              # Python: scraping + análisis estadístico
│   ├── scrapers/         # base_scraper, kino_scraper, loto_scraper
│   ├── analysis/         # frequency, distributions, hot_cold, gaps, pairs
│   └── models/           # SQLAlchemy models
├── .github/workflows/    # CI cron post-sorteo
└── docker-compose.yml    # MySQL local
```

## Roadmap

- **Fase 1** — Scaffolding + BD + scrapers ✏️ *en curso*
- **Fase 2** — API Routes Next.js
- **Fase 3** — Análisis estadístico (campana de Gauss, chi-cuadrado, hot/cold)
- **Fase 4** — Frontend Next.js (dashboards, /aprende)
- **Fase 5** — Pulido, SEO, tests

## Licencia

MIT © [Cristóbal](https://github.com/Blank2D)
