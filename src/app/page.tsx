import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, Mail, Search } from 'lucide-react';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';
import { getCatalogStats, getFeaturedCourses } from '@/content/catalog';
import {
  heroHighlights,
  learningTracks,
  roadmapItems,
  siteConfig,
} from '@/content/site';

export default function HomePage() {
  const catalogStats = getCatalogStats();
  const featuredCourses = getFeaturedCourses();
  const academyStats = [
    { value: String(catalogStats.courseCount), label: 'course paths' },
    { value: String(catalogStats.moduleCount), label: 'modules' },
    { value: String(catalogStats.availableLessonCount), label: 'video lessons' },
  ];

  return (
    <main>
      <SiteHeader />
      <section className="hero" aria-labelledby="hero-title">
        <Image
          src="/images/legacy-home-image2.jpg"
          alt="Close-up of a printed circuit board"
          fill
          priority
          sizes="100vw"
          className="hero-image"
        />
        <div className="hero-shade" />
        <div className="hero-content">
          <p className="eyebrow">SystemVerilog, SVA, UVM, RTL design</p>
          <h1 id="hero-title">SystemVerilog courses for design and verification.</h1>
          <p className="hero-copy">
            Browse the SystemVerilog Academy course library by topic, module, and lesson. The
            lessons are free to watch on YouTube, with this site keeping the course order easy to
            follow.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/courses">
              <Search aria-hidden="true" />
              <span>Browse courses</span>
            </Link>
            <a className="button button-secondary" href="#tracks">
              <span>View tracks</span>
            </a>
          </div>
        </div>
        <div className="hero-highlights" aria-label="Academy signals">
          {heroHighlights.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>

      <section className="stats-section" aria-label="Legacy academy course library">
        {academyStats.map((item) => (
          <div className="stat-item" key={item.label}>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </section>

      <section id="courses" className="content-section" aria-labelledby="courses-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark">Course previews</p>
            <h2 id="courses-title">Start with the course that matches your next step.</h2>
          </div>
          <p>
            These are a few common entry points from the catalog. Open a course to see its modules,
            lesson order, and video links.
          </p>
        </div>
        <div className="course-grid">
          {featuredCourses.map((course) => (
            <article className="course-card" key={course.title}>
              <div className="course-card-topline">
                <span>{course.category.shortLabel}</span>
                <span>
                  {course.counts.modules} module{course.counts.modules === 1 ? '' : 's'}
                </span>
              </div>
              <h3>{course.title}</h3>
              <p>{course.description}</p>
              <dl>
                <div>
                  <dt>Modules</dt>
                  <dd>{course.counts.modules}</dd>
                </div>
                <div>
                  <dt>Lessons</dt>
                  <dd>{course.counts.lessons}</dd>
                </div>
              </dl>
              <Link href={`/courses/${course.slug}`}>
                <span>Open course</span>
                <ArrowRight aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>
        <div className="section-more-action">
          <Link className="button button-primary" href="/courses">
            <span>Browse all courses</span>
            <ArrowRight aria-hidden="true" />
          </Link>
        </div>
      </section>

      <section id="tracks" className="track-section" aria-labelledby="tracks-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark">Learning tracks</p>
            <h2 id="tracks-title">A practical path through design and verification.</h2>
          </div>
          <p>
            Start with the basics, then build toward RTL coding, verification, assertions, and UVM.
            The catalog keeps those paths separate enough to browse quickly.
          </p>
        </div>
        <div className="feature-grid">
          {learningTracks.map((item) => (
            <article className="feature-card" key={item.title}>
              <item.icon aria-hidden="true" />
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="roadmap" className="roadmap-section" aria-labelledby="roadmap-title">
        <div className="section-heading compact">
          <p className="eyebrow dark">How it works</p>
          <h2 id="roadmap-title">Use the site as the course index.</h2>
        </div>
        <div className="roadmap-list">
          {roadmapItems.map((item, index) => (
            <article className="roadmap-item" key={item.title}>
              <span className="roadmap-index">{String(index + 1).padStart(2, '0')}</span>
              <item.icon aria-hidden="true" />
              <div>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="cta-section" aria-label="Course catalog">
        <div>
          <p className="eyebrow">Course catalog</p>
          <h2>Find the next course and keep the sequence clear.</h2>
        </div>
        <div className="cta-actions">
          <Link className="button button-primary" href="/courses">
            <span>Browse courses</span>
            <ArrowRight aria-hidden="true" />
          </Link>
          <a className="button button-secondary on-dark" href={`mailto:${siteConfig.contactEmail}`}>
            <Mail aria-hidden="true" />
            <span>Contact</span>
          </a>
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
