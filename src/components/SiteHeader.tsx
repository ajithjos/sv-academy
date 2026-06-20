import Link from 'next/link';
import Image from 'next/image';
import { ExternalLink, PlayCircle } from 'lucide-react';
import { siteConfig } from '@/content/site';

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand-mark" href="/" aria-label="SystemVerilog Academy home">
        <span className="brand-symbol">
          <Image
            src="/images/systemverilog-academy-logo.png"
            alt=""
            width={28}
            height={28}
            priority
          />
        </span>
        <span>
          {siteConfig.name}
          <small>{siteConfig.subtitle}</small>
        </span>
      </Link>
      <nav className="header-nav" aria-label="Primary navigation">
        <a href="#courses">Courses</a>
        <a href="#tracks">Tracks</a>
        <a className="header-action" href={siteConfig.youtubeUrl} target="_blank" rel="noreferrer">
          <PlayCircle aria-hidden="true" />
          <span>YouTube</span>
          <ExternalLink aria-hidden="true" />
        </a>
      </nav>
    </header>
  );
}
