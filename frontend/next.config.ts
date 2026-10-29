import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The hosted-demo chat route reads the exported simulations from disk.
  outputFileTracingIncludes: {
    "/api/chat": ["./public/demo/**/*.json"],
  },
};

export default nextConfig;
