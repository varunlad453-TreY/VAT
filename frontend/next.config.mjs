/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",

  // OpenTelemetry instrumentation for Carrier-Grade NOC telemetry
  experimental: {
    instrumentationHook: true,
  },

  // Strangler Fig Reverse Proxy: Rewrite unmigrated legacy routes to legacy static server
  async rewrites() {
    const legacyUrl = process.env.LEGACY_CONSOLE_URL || "http://localhost:3001";
    return [
      {
        source: "/legacy/:path*",
        destination: `${legacyUrl}/:path*`,
      },
      {
        source: "/legacy-console",
        destination: `${legacyUrl}/index.html`,
      },
    ];
  },

  // Carrier-Grade Security & Performance Headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
