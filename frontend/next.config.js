/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true, // avoid remote image DoS until configured
  },
}

module.exports = nextConfig
