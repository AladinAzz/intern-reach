/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config, { dev }) => {
    if (dev) {
      config.cache = false; // Disables webpack file pack cache on Windows/OneDrive to prevent ENOENT pack.gz desync
    }
    return config;
  },
};

export default nextConfig;
