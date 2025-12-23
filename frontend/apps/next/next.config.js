const { withTamagui } = require('@tamagui/next-plugin')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    'solito',
    '@athena/ui',
    '@athena/app',
    'tamagui',
    '@tamagui/core',
    '@tamagui/web',
  ],
  experimental: {
    scrollRestoration: true,
  },
}

module.exports = withTamagui({
  config: './tamagui.config.ts',
  components: ['tamagui', '@athena/ui'],
  disableExtraction: process.env.NODE_ENV === 'development',
})(nextConfig)
