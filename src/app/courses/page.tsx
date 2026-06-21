import type { Metadata } from 'next';
import { BookOpenCheck, LibraryBig, PlayCircle } from 'lucide-react';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';
import {
  courseCategories,
  getCatalogCourses,
  getCatalogStats,
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
  const stats = getCatalogStats();

  return (
    <main>
      <SiteHeader />
      <section className="catalog-hero" aria-labelledby="catalog-title">
        <div className="catalog-hero-content">
          <div>
            <p className="eyebrow">Public course catalog</p>
            <h1 id="catalog-title">SystemVerilog Academy course catalog.</h1>
            <p className="catalog-hero-copy">
              Browse courses by topic, module, and lesson. Start with the foundations, move into
              RTL design, then build verification, assertions, and UVM skills through the academy
              sequence.
            </p>
          </div>
          <div className="catalog-hero-panel" aria-label="Catalog snapshot">
            <div>
              <LibraryBig aria-hidden="true" />
              <span>{stats.courseCount}</span>
              <p>Courses</p>
            </div>
            <div>
              <BookOpenCheck aria-hidden="true" />
              <span>{stats.moduleCount}</span>
              <p>Modules</p>
            </div>
            <div>
              <PlayCircle aria-hidden="true" />
              <span>{stats.availableLessonCount}</span>
              <p>Videos</p>
            </div>
          </div>
        </div>
      </section>

      <CategoryRail categories={courseCategories} />
      <CourseCatalogClient courses={courses} categories={courseCategories} />
      <SiteFooter />
    </main>
  );
}
