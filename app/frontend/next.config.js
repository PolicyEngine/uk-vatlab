/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Remove static export settings for Vercel deployment
  // Vercel handles both frontend and API routes
}

module.exports = nextConfig