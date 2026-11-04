import type { MetadataRoute } from 'next';
import { api, Package } from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';
  let packages: Package[] = [];
  try { packages = await api<Package[]>('/api/packages'); } catch { /* Sitemap remains valid while the API is unavailable during local setup. */ }
  return [
    { url: base, lastModified: new Date(), changeFrequency: 'weekly', priority: 1 },
    ...packages.map((item) => ({ url: `${base}/packages/${item.slug}`, lastModified: new Date(), changeFrequency: 'weekly' as const, priority: 0.8 })),
  ];
}
