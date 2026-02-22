import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Compress responses
  compress: true,

  // Power the header with canonical URL info
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
      {
        // Cache static salary pages for 1 week at CDN
        source: '/salary/:company/:job',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=604800, stale-while-revalidate=86400',
          },
        ],
      },
    ];
  },

  // Silence Turbopack warning (Next.js 16+ default bundler)
  turbopack: {},

  // Webpack config for environments that use webpack instead of Turbopack
  webpack(config, { isServer }) {
    if (isServer) {
      config.externals = config.externals || [];
      if (Array.isArray(config.externals)) {
        config.externals.push('better-sqlite3');
      }
    }
    return config;
  },
};

export default nextConfig;
