import Image from 'next/image';
import { ArrowRight, ExternalLink, Mail, PlayCircle, Search } from 'lucide-react';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';
import {
  academyStats,
  coursePreviews,
  heroHighlights,
  learningTracks,
  roadmapItems,
  siteConfig,
} from '@/content/site';

function channelSearchUrl(query: string) {
  return `${siteConfig.youtubeUrl.replace(/\/$/, '')}/search?query=${encodeURIComponent(query)}`;
}

export default function HomePage() {
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
          <div className="hero-brand-lockup">
            <Image
              src="/images/systemverilog-academy-logo.png"
              alt=""
              width={58}
              height={58}
              priority
            />
            <div>
              <p>{siteConfig.name}</p>
              <span>{siteConfig.subtitle}</span>
            </div>
          </div>
          <p className="eyebrow">SystemVerilog, SVA, UVM, RTL design</p>
          <h1 id="hero-title">
            Learn chip design and verification with practical code-first lessons.
          </h1>
          <p className="hero-copy">
            The academy course library is moving to a free YouTube-first model. Start from beginner
            SystemVerilog, then move into RTL design, testbench construction, functional coverage,
            assertions, simulation regions, and UVM.
          </p>
          <div className="hero-actions">
            <a
              className="button button-primary"
              href={siteConfig.youtubeUrl}
              target="_blank"
              rel="noreferrer"
            >
              <PlayCircle aria-hidden="true" />
              <span>Open YouTube channel</span>
              <ExternalLink aria-hidden="true" />
            </a>
            <a className="button button-secondary" href="#courses">
              <Search aria-hidden="true" />
              <span>Preview courses</span>
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
            <h2 id="courses-title">A real course library, now easier to discover.</h2>
          </div>
          <p>
            These paths come from the academy course library. The new site keeps the public
            experience lightweight while pointing learners directly to the YouTube channel for the
            current lessons.
          </p>
        </div>
        <div className="course-grid">
          {coursePreviews.map((course) => (
            <article className="course-card" key={course.title}>
              <div className="course-card-topline">
                <span>{course.topic}</span>
                <span>{course.level}</span>
              </div>
              <h3>{course.title}</h3>
              <p>{course.description}</p>
              <dl>
                <div>
                  <dt>Modules</dt>
                  <dd>{course.modules}</dd>
                </div>
                <div>
                  <dt>Lessons</dt>
                  <dd>{course.lessons}</dd>
                </div>
              </dl>
              <a href={channelSearchUrl(course.query)} target="_blank" rel="noreferrer">
                <span>Find on YouTube</span>
                <ArrowRight aria-hidden="true" />
              </a>
            </article>
          ))}
        </div>
      </section>

      <section id="tracks" className="track-section" aria-labelledby="tracks-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark">Learning tracks</p>
            <h2 id="tracks-title">From first module to reusable verification architecture.</h2>
          </div>
          <p>
            The academy works best when the path is visible: basics first, then RTL, then
            verification, then assertions and UVM with enough code to make the ideas stick.
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
          <p className="eyebrow dark">Next platform</p>
          <h2 id="roadmap-title">The full academy can come back in layers.</h2>
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

      <section className="cta-section" aria-label="YouTube lessons">
        <div>
          <p className="eyebrow">Watch now</p>
          <h2>Browse the free SystemVerilog Academy lessons on YouTube.</h2>
        </div>
        <div className="cta-actions">
          <a
            className="button button-primary"
            href={siteConfig.youtubeUrl}
            target="_blank"
            rel="noreferrer"
          >
            <span>Open channel</span>
            <ArrowRight aria-hidden="true" />
          </a>
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
