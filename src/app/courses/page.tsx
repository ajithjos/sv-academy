import type { Metadata } from 'next';
import { PlayCircle } from 'lucide-react';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';
import {
  courseCategories,
  getCatalogCourses,
  type CourseCategory,
} from '@/content/catalog';
import { siteConfig } from '@/content/site';
import { CourseCatalogClient } from './CourseCatalogClient';

export const metadata: Metadata = {
  title: 'Courses',
  description:
    'Browse the SystemVerilog Academy course library with structured modules, lessons, and video links.',
  alternates: {
    canonical: `https://${siteConfig.domain}/courses`,
  },
  openGraph: {
    title: `Courses | ${siteConfig.name}`,
    description:
      'Structured SystemVerilog, RTL design, verification, assertions, and UVM courses.',
    url: `https://${siteConfig.domain}/courses`,
  },
};

function CategoryRail({ categories }: { categories: CourseCategory[] }) {
  return (
    <div className="category-rail" aria-label="Course tracks">
      {categories.map((category) => (
        <article key={category.id}>
          <span>{category.shortLabel}</span>
          <h2>{category.label}</h2>
          <p>{category.description}</p>
        </article>
      ))}
    </div>
  );
}

export default function CoursesPage() {
  const courses = getCatalogCourses();

  return (
    <main>
      <SiteHeader />
      <section className="catalog-hero" aria-labelledby="catalog-title">
        <div className="catalog-hero-content">
          <div>
            <p className="eyebrow">Public course catalog</p>
            <h1 id="catalog-title">SystemVerilog Academy course catalog.</h1>
            <p className="catalog-hero-copy">
              The legacy course library is now free to watch on YouTube. Browse the courses here by
              topic and module, then open the lesson you need.
            </p>
          </div>
          <div className="catalog-hero-note">
            <PlayCircle aria-hidden="true" />
            <p>
              Lessons open on YouTube. More updated material will be added as the academy is
              refreshed.
            </p>
          </div>
        </div>
      </section>

      <CategoryRail categories={courseCategories} />
      <CourseCatalogClient courses={courses} categories={courseCategories} />
      <SiteFooter />
    </main>
  );
}
