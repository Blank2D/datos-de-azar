import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"
  ),
  title: {
    default: "datos-de-azar — Estadísticas de Kino y Loto en Chile",
    template: "%s | datos-de-azar",
  },
  description:
    "Análisis estadístico open-source de los sorteos históricos de Kino (Lotería de Concepción) y Loto (Polla Chilena de Beneficencia). Frecuencias, distribuciones y tendencias. Proyecto educativo, no predictivo.",
  keywords: [
    "kino",
    "loto",
    "lotería chile",
    "estadísticas",
    "sorteos chile",
    "open source",
    "datos abiertos",
  ],
  authors: [{ name: "Cristóbal", url: "https://github.com/Blank2D" }],
  creator: "Cristóbal (Blank2D)",
  openGraph: {
    type: "website",
    locale: "es_CL",
    siteName: "datos-de-azar",
    title: "datos-de-azar — Estadísticas de Kino y Loto",
    description:
      "Sorteos históricos del Kino y el Loto analizados estadísticamente. Proyecto open-source y educativo.",
  },
  twitter: {
    card: "summary_large_image",
    title: "datos-de-azar",
    description: "Estadísticas de Kino y Loto en Chile — open-source.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: "#0D0F1A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html
      lang="es-CL"
      className={`${inter.variable} ${jetbrains.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-bg-primary text-text-primary font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
