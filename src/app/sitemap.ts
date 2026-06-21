import type { MetadataRoute } from 'next';
import { getCatalogCourses } from '@/content/catalog';
import { siteConfig } from '@/content/site';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const courseUrls = getCatalogCourses().map((course) => ({
    url: `https://${siteConfig.domain}/courses/${course.slug}`,
    lastModified: now,
    changeFrequency: 'monthly' as const,
    priority: 0.74,
  }));

  return [
    {
      url: `https://${siteConfig.domain}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 1,
    },
    {
      url: `https://${siteConfig.domain}/courses`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    ...courseUrls,
  ];
}
