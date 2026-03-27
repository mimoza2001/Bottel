import type { MetadataRoute } from 'next';
import { getAllEmployers, getAllJobs, getAllLocations } from '@/lib/db';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://h1bsalary.info';

export default function sitemap(): MetadataRoute.Sitemap {
  const employers = getAllEmployers();
  const jobs = getAllJobs();
  const locations = getAllLocations();

  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${BASE_URL}/company`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${BASE_URL}/job`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${BASE_URL}/location`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
  ];

  const companyRoutes: MetadataRoute.Sitemap = employers.map((e) => ({
    url: `${BASE_URL}/company/${e.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  const jobRoutes: MetadataRoute.Sitemap = jobs.map((j) => ({
    url: `${BASE_URL}/job/${j.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  const locationRoutes: MetadataRoute.Sitemap = locations.map((l) => ({
    url: `${BASE_URL}/location/${l.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  // Top salary page combinations (top 25 employers × all jobs)
  const salaryRoutes: MetadataRoute.Sitemap = employers
    .slice(0, 25)
    .flatMap((e) =>
      jobs.map((j) => ({
        url: `${BASE_URL}/salary/${e.slug}/${j.slug}`,
        lastModified: now,
        changeFrequency: 'weekly' as const,
        priority: 0.9,
      }))
    );

  return [
    ...staticRoutes,
    ...companyRoutes,
    ...jobRoutes,
    ...locationRoutes,
    ...salaryRoutes,
  ];
}
