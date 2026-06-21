import Image from 'next/image';
import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import {
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Layers3,
  PlayCircle,
} from 'lucide-react';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';
import {
  getCatalogCourses,
  getCourseBySlug,
  getRelatedCourses,
  type CatalogCourse,
  type CatalogLesson,
} from '@/content/catalog';
import { siteConfig } from '@/content/site';

type CoursePageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export function generateStaticParams() {
  return getCatalogCourses().map((course) => ({
    slug: course.slug,
  }));
}

export async function generateMetadata({ params }: CoursePageProps): Promise<Metadata> {
  const { slug } = await params;
  const course = getCourseBySlug(slug);

  if (!course) {
    return {
      title: 'Course Not Found',
    };
  }

  return {
    title: course.title,
    description: course.description,
    alternates: {
      canonical: `https://${siteConfig.domain}/courses/${course.slug}`,
    },
    openGraph: {
      title: `${course.title} | ${siteConfig.name}`,
      description: course.description,
      url: `https://${siteConfig.domain}/courses/${course.slug}`,
      images: [
        {
          url: course.thumbnailUrl,
          width: 480,
          height: 360,
          alt: course.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: course.title,
      description: course.description,
      images: [course.thumbnailUrl],
    },
  };
}

function WatchLink({ lesson }: { lesson: CatalogLesson }) {
  if (!lesson.youtubeUrl) {
    return <span className="lesson-action is-disabled">Pending</span>;
  }

  return (
    <a className="lesson-action" href={lesson.youtubeUrl} target="_blank" rel="noreferrer">
      <span>Watch</span>
      <ExternalLink aria-hidden="true" />
    </a>
  );
}

function CourseSidebar({ course }: { course: CatalogCourse }) {
  return (
    <aside className="course-sidebar" aria-label="Course facts">
      <div className="course-sidebar-block">
        <span className="course-sidebar-label">Track</span>
        <strong>{course.category.label}</strong>
        <p>{course.category.description}</p>
      </div>
      <dl className="course-fact-list">
        <div>
          <dt>
            <Layers3 aria-hidden="true" />
            Modules
          </dt>
          <dd>{course.counts.modules}</dd>
        </div>
        <div>
          <dt>
            <PlayCircle aria-hidden="true" />
            Lessons
          </dt>
          <dd>{course.counts.lessons}</dd>
        </div>
        <div>
          <dt>
            <Clock3 aria-hidden="true" />
            Duration
          </dt>
          <dd>{course.durationText ?? 'Open'}</dd>
        </div>
        <div>
          <dt>
            <CheckCircle2 aria-hidden="true" />
            Available
          </dt>
          <dd>{course.counts.availableLessons}</dd>
        </div>
      </dl>
      <div className="course-sidebar-actions">
        {course.firstLesson?.youtubeUrl ? (
          <a className="button button-primary" href={course.firstLesson.youtubeUrl} target="_blank" rel="noreferrer">
            <PlayCircle aria-hidden="true" />
            <span>Start lesson</span>
            <ExternalLink aria-hidden="true" />
          </a>
        ) : null}
        {course.youtube.playlistUrl ? (
          <a className="button button-secondary light" href={course.youtube.playlistUrl} target="_blank" rel="noreferrer">
            <span>Open playlist</span>
            <ExternalLink aria-hidden="true" />
          </a>
        ) : null}
      </div>
    </aside>
  );
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { slug } = await params;
  const course = getCourseBySlug(slug);

  if (!course) {
    notFound();
  }

  const relatedCourses = getRelatedCourses(course);

  return (
    <main>
      <SiteHeader />
      <section className="course-hero" aria-labelledby="course-title">
        <Image
          src={course.thumbnailUrl}
          alt=""
          fill
          priority
          sizes="100vw"
          className="course-hero-image"
        />
        <div className="course-hero-shade" />
        <div className="course-hero-content">
          <Link className="course-back-link" href="/courses">
            <ArrowLeft aria-hidden="true" />
            <span>Courses</span>
          </Link>
          <p className="eyebrow">{course.category.label}</p>
          <h1 id="course-title">{course.title}</h1>
          <p className="course-hero-copy">{course.description}</p>
          <div className="course-hero-actions">
            {course.firstLesson?.youtubeUrl ? (
              <a className="button button-primary" href={course.firstLesson.youtubeUrl} target="_blank" rel="noreferrer">
                <PlayCircle aria-hidden="true" />
                <span>Start first lesson</span>
                <ExternalLink aria-hidden="true" />
              </a>
            ) : null}
            {course.youtube.playlistUrl ? (
              <a className="button button-secondary" href={course.youtube.playlistUrl} target="_blank" rel="noreferrer">
                <span>Open playlist</span>
                <ExternalLink aria-hidden="true" />
              </a>
            ) : null}
          </div>
          <dl className="course-hero-metrics">
            <div>
              <dt>Modules</dt>
              <dd>{course.counts.modules}</dd>
            </div>
            <div>
              <dt>Lessons</dt>
              <dd>{course.counts.lessons}</dd>
            </div>
            <div>
              <dt>Ready</dt>
              <dd>{course.counts.availableLessons}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{course.durationText ?? 'Open'}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="course-workspace" aria-label="Course outline">
        <CourseSidebar course={course} />
        <div className="module-stack">
          <div className="module-stack-heading">
            <p className="eyebrow dark">Lesson path</p>
            <h2>Modules and lessons</h2>
            <p>
              Each module keeps the academy sequence intact and opens available lessons directly on
              YouTube.
            </p>
          </div>
          {course.modules.map((module) => (
            <details className="module-panel" key={module.id} open={module.index === 1}>
              <summary>
                <span className="module-index">{String(module.index).padStart(2, '0')}</span>
                <span>
                  <strong>{module.title}</strong>
                  <small>
                    {module.availableLessonCount}/{module.lessonCount} lessons
                    {module.durationText ? ` · ${module.durationText}` : ''}
                  </small>
                </span>
              </summary>
              <ol className="lesson-list">
                {module.lessons.map((lesson) => (
                  <li key={lesson.id} className={lesson.status === 'missing' ? 'is-missing' : undefined}>
                    <span className="lesson-index">
                      {module.index}.{lesson.index}
                    </span>
                    <span className="lesson-title">
                      <strong>{lesson.title}</strong>
                      {lesson.youtubeTitle && lesson.youtubeTitle !== lesson.title ? (
                        <small>{lesson.youtubeTitle}</small>
                      ) : null}
                    </span>
                    <span className="lesson-duration">{lesson.durationText ?? ''}</span>
                    <WatchLink lesson={lesson} />
                  </li>
                ))}
              </ol>
            </details>
          ))}
        </div>
      </section>

      <section className="related-section" aria-labelledby="related-title">
        <div className="section-heading compact">
          <p className="eyebrow dark">Keep going</p>
          <h2 id="related-title">Related paths</h2>
        </div>
        <div className="related-grid">
          {relatedCourses.map((related) => (
            <article className="related-card" key={related.slug}>
              <span>{related.category.shortLabel}</span>
              <h3>{related.title}</h3>
              <p>
                {related.counts.modules} modules · {related.counts.availableLessons} videos
              </p>
              <Link href={`/courses/${related.slug}`}>
                <span>Open course</span>
                <ArrowRight aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
