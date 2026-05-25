import type { Config } from "tailwindcss";

/**
 * Tailwind config — tokens de marca extraídos de los CSS oficiales
 * de loteria.cl y polla.cl. NO modificar sin coordinar con INSTRUCCIONES_OPUS.md.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ============ Sitio (dark mode siempre) ============
        bg: {
          primary: "#0D0F1A",
          card: "#13151F",
          elevated: "#1A1D2E",
        },
        border: {
          DEFAULT: "#2A2D3E",
        },
        text: {
          primary: "#F0F2FF",
          secondary: "#9CA3AF",
          muted: "#6B7280",
        },

        // ============ 🎰 Kino ============
        kino: {
          DEFAULT: "#FF0008",
          primary: "#FF0008",
          dark: "#AB0000",
          orange: "#FF8204",
          "orange-dark": "#E47302",
          blue: "#007BDB",
          navy: "#1A1A2E",
        },

        // ============ 🍀 Loto ============
        loto: {
          DEFAULT: "#DD1923",
          primary: "#DD1923",
          "primary-alt": "#E2001A",
          yellow: "#FFCA00",
          "yellow-alt": "#F9E000",
          green: "#006C21",
          "green-dark": "#05601E",
          orange: "#FF5001",
        },

        // ============ UI compartidos ============
        accent: {
          blue: "#007BDB",
        },
        success: "#22C55E",
        warning: "#F59E0B",
      },
      backgroundImage: {
        "gradient-kino": "linear-gradient(135deg, #AB0000 0%, #FF0008 100%)",
        "gradient-loto": "linear-gradient(135deg, #A01218 0%, #DD1923 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      animation: {
        "ball-pop": "ball-pop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)",
        "fade-in": "fade-in 0.4s ease-out",
        "glow-kino": "glow-kino 2s ease-in-out infinite",
        "glow-loto": "glow-loto 2s ease-in-out infinite",
      },
      keyframes: {
        "ball-pop": {
          "0%": { transform: "scale(0.4)", opacity: "0" },
          "60%": { transform: "scale(1.1)", opacity: "1" },
          "100%": { transform: "scale(1)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "glow-kino": {
          "0%,100%": { boxShadow: "0 0 12px rgba(255,0,8,0.4)" },
          "50%": { boxShadow: "0 0 24px rgba(255,0,8,0.8)" },
        },
        "glow-loto": {
          "0%,100%": { boxShadow: "0 0 12px rgba(221,25,35,0.4)" },
          "50%": { boxShadow: "0 0 24px rgba(221,25,35,0.8)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
