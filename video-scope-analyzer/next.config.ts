import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    qualities: [75, 100],
  },
  output: 'export',
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return process.env.NODE_ENV === 'development' ? [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ] : [];
  },
};

export default nextConfig;
