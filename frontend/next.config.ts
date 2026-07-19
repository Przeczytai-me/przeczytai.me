import { createMDX } from "fumadocs-mdx/next";
import type { NextConfig } from "next";

const withMDX = createMDX();

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
};

export default withMDX(nextConfig);
