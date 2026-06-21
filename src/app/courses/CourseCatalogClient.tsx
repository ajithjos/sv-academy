'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, BookOpenCheck, ExternalLink, PlayCircle, Search, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { CatalogCourse, CourseCategory, CourseCategoryId } from '@/content/catalog';

type CourseCatalogClientProps = {
  courses: CatalogCourse[];
  categories: CourseCategory[];
};

export function CourseCatalogClient({ courses, categories }: CourseCatalogClientProps) {
  const [activeCategory, setActiveCategory] = useState<CourseCategoryId | 'all'>('all');
  const [query, setQuery] = useState('');

  const filteredCourses = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return courses.filter((course) => {
      const matchesCategory = activeCategory === 'all' || course.category.id === activeCategory;

      if (!matchesCategory) {
        return false;
      }

      if (!normalizedQuery) {
        return true;
      }

      const searchableText = [
        course.title,
        course.subtitle,
        course.description,
        course.category.label,
        ...course.modules.map((module) => module.title),
      ]
        .join(' ')
        .toLowerCase();

      return searchableText.includes(normalizedQuery);
    });
  }, [activeCategory, courses, query]);

  return (
    <section className="catalog-browser" aria-labelledby="course-browser-title">
      <div className="catalog-toolbar">
        <div>
          <p className="eyebrow dark">Course library</p>
          <h2 id="course-browser-title">Browse learning paths.</h2>
        </div>
        <label className="catalog-search">
          <Search aria-hidden="true" />
          <span className="sr-only">Search courses</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search topics, tracks, modules"
            type="search"
          />
          {query ? (
            <button type="button" onClick={() => setQuery('')} aria-label="Clear search">
              <X aria-hidden="true" />
            </button>
          ) : null}
        </label>
      </div>

      <div className="catalog-filters" aria-label="Course track filters">
        <button
          type="button"
          className={activeCategory === 'all' ? 'is-active' : undefined}
          onClick={() => setActiveCategory('all')}
          aria-pressed={activeCategory === 'all'}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            type="button"
            key={category.id}
            className={activeCategory === category.id ? 'is-active' : undefined}
            onClick={() => setActiveCategory(category.id)}
            aria-pressed={activeCategory === category.id}
          >
            {category.shortLabel}
          </button>
        ))}
      </div>

      <div className="catalog-result-count" aria-live="polite">
        {filteredCourses.length} course{filteredCourses.length === 1 ? '' : 's'}
      </div>

      {filteredCourses.length > 0 ? (
        <div className="catalog-grid">
          {filteredCourses.map((course) => (
            <article className="catalog-card" key={course.slug}>
              <Link className="catalog-card-media" href={`/courses/${course.slug}`}>
                <Image
                  src={course.thumbnailUrl}
                  alt=""
                  width={480}
                  height={360}
                  sizes="(max-width: 760px) 100vw, (max-width: 1180px) 50vw, 33vw"
                />
                <span>
                  <PlayCircle aria-hidden="true" />
                  {course.counts.availableLessons} videos
                </span>
              </Link>
              <div className="catalog-card-body">
                <div className="course-card-topline">
                  <span>{course.category.shortLabel}</span>
                  <span>
                    {course.counts.modules} module{course.counts.modules === 1 ? '' : 's'}
                  </span>
                </div>
                <h3>
                  <Link href={`/courses/${course.slug}`}>{course.title}</Link>
                </h3>
                <p>{course.description}</p>
                <dl>
                  <div>
                    <dt>Lessons</dt>
                    <dd>{course.counts.lessons}</dd>
                  </div>
                  <div>
                    <dt>Duration</dt>
                    <dd>{course.durationText ?? 'Open'}</dd>
                  </div>
                </dl>
                <div className="catalog-card-status">
                  <BookOpenCheck aria-hidden="true" />
                  <span>
                    {course.counts.missingLessons > 0
                      ? `${course.counts.availableLessons}/${course.counts.lessons} lessons available`
                      : 'All videos available'}
                  </span>
                </div>
                <div className="catalog-card-actions">
                  <Link href={`/courses/${course.slug}`}>
                    <span>Open course</span>
                    <ArrowRight aria-hidden="true" />
                  </Link>
                  {course.youtube.playlistUrl ? (
                    <a href={course.youtube.playlistUrl} target="_blank" rel="noreferrer">
                      <span>Playlist</span>
                      <ExternalLink aria-hidden="true" />
                    </a>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="catalog-empty">
          <h3>No courses match this search.</h3>
          <p>Try a broader topic such as UVM, assertions, coverage, RTL, or beginner.</p>
        </div>
      )}
    </section>
  );
}
