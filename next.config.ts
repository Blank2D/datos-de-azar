import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  typescript: { ignoreBuildErrors: false },
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [
          { key: "Access-Control-Allow-Origin", value: "*" },
          { key: "Access-Control-Allow-Methods", value: "GET, OPTIONS" },
          { key: "Access-Control-Allow-Headers", value: "Content-Type" },
        ],
      },
    ];
  },
  images: { remotePatterns: [] },
};

export default config;
